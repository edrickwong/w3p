import os
import cv2
import time
import argparse
import multiprocessing
import numpy as np
import socket
import tensorflow as tf

from utils.app_utils import FPS, WebcamVideoStream
from utils.misc_utils import is_using_tensorflow_gpu
from multiprocessing import Queue, Pool, Process
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util
from object_detection.worker_utils import MessageWorker
from tts import PythonTTS, cmdLineTTS

CWD_PATH = os.getcwd()

# Path to frozen detection graph. This is the actual model that is used for the object detection.
MODEL_NAME = 'ssd_mobilenet_v1_coco_11_06_2017'
PATH_TO_CKPT = os.path.join(CWD_PATH, 'object_detection', MODEL_NAME, 'frozen_inference_graph.pb')

# List of the strings that is used to add correct label for each box.
PATH_TO_LABELS = os.path.join(CWD_PATH, 'object_detection', 'data', 'mscoco_label_map.pbtxt')

NUM_CLASSES = 90

# Loading label map
label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES,
                                                            use_display_name=True)
category_index = label_map_util.create_category_index(categories)

# Kitchen items
allowed_classes = ['person','bottle','knife','spoon','fork','cup','bowl','dog']

# Detect Threshold
DETECT_THRESHOLD = 0.2


def detect_objects(image_np, sess, detection_graph):
    # Expand dimensions since the model expects images to have shape: [1, None, None, 3]
    image_np_expanded = np.expand_dims(image_np, axis=0)
    image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')

    # Each box represents a part of the image where a particular object was detected.
    boxes = detection_graph.get_tensor_by_name('detection_boxes:0')

    # Each score represent how level of confidence for each of the objects.
    # Score is shown on the result image, together with the class label.
    scores = detection_graph.get_tensor_by_name('detection_scores:0')
    classes = detection_graph.get_tensor_by_name('detection_classes:0')
    num_detections = detection_graph.get_tensor_by_name('num_detections:0')

    # Actual detection.
    (boxes, scores, classes, num_detections) = sess.run(
        [boxes, scores, classes, num_detections],
        feed_dict={image_tensor: image_np_expanded})
    # Wanted objects
    class_box = {}
    max_width = 0
    # Only show boxes around these classes
    for i in range(len(scores[0])):
        if category_index[classes[0][i]]['name'] not in allowed_classes:
            scores[0][i] = 0
        else:
            if scores[0][i] >= DETECT_THRESHOLD:
                obj = category_index[classes[0][i]]['name']
                if obj == 'person':
                    box = np.squeeze(boxes[0][i])
                    width = abs(box[3] - box[1])
                    if width < max_width:
                        continue
                    max_width = width
                class_box[obj] = np.squeeze(boxes[0][i])

    # Visualization of the results of a detection.
    vis_util.visualize_boxes_and_labels_on_image_array(
        image_np,
        np.squeeze(boxes),
        np.squeeze(classes).astype(np.int32),
        np.squeeze(scores),
        category_index,
        use_normalized_coordinates=True,
        line_thickness=8,
        min_score_thresh=DETECT_THRESHOLD)
    return image_np, class_box


def worker(input_q, output_q, request_q, message_q):
    # Load a (frozen) Tensorflow model into memory.
    detection_graph = tf.Graph()
    with detection_graph.as_default():
        od_graph_def = tf.GraphDef()
        with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
            serialized_graph = fid.read()
            od_graph_def.ParseFromString(serialized_graph)
            tf.import_graph_def(od_graph_def, name='')

        sess = tf.Session(graph=detection_graph)

    image = ''
    mes = ''
    fps = FPS().start()
    out = cmdLineTTS

    while True:
        fps.update()
        frame = input_q.get()
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image, objects = detect_objects(frame_rgb, sess, detection_graph)
        # dont block if nothing is there
        try:
            obj = request_q.get(block=False)
        except:
            obj = None

        if obj:
            # try to build output message from objects
            if 'person' not in objects:
                msg = 'Cannot locate user.'
            elif obj not in objects:
                msg = 'Unable to locate %s in current view' %(obj)
            else:
                mid_p = (objects.get('person')[1] \
                            + objects.get('person')[3])/2
                mid_o = (objects.get(obj)[1] \
                        + objects.get(obj)[1])/2
                if mid_p < mid_o:
                    msg = obj + ' is to your left'
                else:
                    msg = obj + ' is to your right'

            print 'worker here'
            message_q.put(msg)
        output_q.put(image)

    fps.stop()
    sess.close()

def request_worker(request_q, message_q, socket_connection):
    while not socket_connection.conn:
        socket_connection.conn, addr = socket_connection.s.accept()
        print 'Waiting on mock connection from Google Assistant'
        time.sleep(1)

    while True:
        # listen on socket for incoming messages
        request_data = socket_connection.conn.recv(BUFFER_SIZE)

        print request_data
        obj = None
        # parse the incoming message
        for word in request_data.split():
            if word in allowed_classes:
                obj = word
                break

        if obj:
            request_q.put(obj)
            print obj

        msg = message_q.get()
        socket_connection.conn.send(msg)
        print(msg)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-src', '--source', dest='video_source', type=int,
                        default=0, help='Device index of the camera.')
    parser.add_argument('-wd', '--width', dest='width', type=int,
                        default=480, help='Width of the frames in the video stream.')
    parser.add_argument('-ht', '--height', dest='height', type=int,
                        default=360, help='Height of the frames in the video stream.')
    parser.add_argument('-num-w', '--num-workers', dest='num_workers', type=int,
                        default=1, help='Number of workers.')
    parser.add_argument('-q-size', '--queue-size', dest='queue_size', type=int,
                        default=5, help='Size of the queue.')
    parser.add_argument('-obj','--object', dest='object', type=str,
                        default='bottle',help='Object to search for.')
    args = parser.parse_args()

    logger = multiprocessing.log_to_stderr()
    logger.setLevel(multiprocessing.SUBDEBUG)

    # override num workers if tensorflow gpu is being used
    num_workers = args.num_workers
    if is_using_tensorflow_gpu() and num_workers > 1:
        print "Using GPU, not allowed to multiproc workers."
        num_workers = 1

    # we need to moderate the number of workers that get spawned
    # for cpu depending on the number of cpus/vpcus avaiable
    # if not we are def going to run into some random perf
    # (too much context switching between IO filled workers
    else:
        num_workers = min(multiprocessing.cpu_count(),
                          num_workers)

    # need 4 queues to pass relevant information between the various
    # procs.
    input_q = Queue(maxsize=args.queue_size)
    output_q = Queue(maxsize=args.queue_size)
    request_q = Queue(maxsize=args.queue_size)
    message_q = Queue(maxsize=args.queue_size)

    pool = Pool(num_workers, worker, (input_q, output_q, request_q, message_q))

    # interface with google home/flask client
    msg_worker = MessageWorker(request_q, message_q)
    msg_worker.start()

    video_capture = WebcamVideoStream(src=args.video_source,
                                      width=args.width,
                                      height=args.height).start()
    fps = FPS().start()

    while True:  # fps._numFrames < 120
        frame = video_capture.read()
        input_q.put(frame)

        t = time.time()
        output_rgb = cv2.cvtColor(output_q.get(), cv2.COLOR_RGB2BGR)
        cv2.imshow('Video', output_rgb)
        fps.update()

        # print('[INFO] elapsed time: {:.2f}'.format(time.time() - t))

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    fps.stop()
    print('[INFO] elapsed time (total): {:.2f}'.format(fps.elapsed()))
    print('[INFO] approx. FPS: {:.2f}'.format(fps.fps()))

    msg_worker.join()
    pool.terminate()
    video_capture.stop()
    while True:
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()
