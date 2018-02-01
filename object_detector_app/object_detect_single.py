import os
import cv2
import datetime
import time
import argparse
import multiprocessing
import numpy as np
import tensorflow as tf

from utils.app_utils import FPS, WebcamVideoStream
from multiprocessing import Queue, Pool
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util

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


def detect_objects_no_vis(image_np, sess, detection_graph):
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

    return (boxes, scores, classes, num_detections)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-img', '--image', dest='image', type=str,
                        default='dog.jpg', help='Name of Picture')
    parser.add_argument('-out', '--out_image', dest='out_img', type=str,
                        default='out.jpg', help='Name of Picture')
    args = parser.parse_args()

    NUM_ITERATIONS = 100
    execution_times = []

    detection_graph = tf.Graph()
    with detection_graph.as_default():
        od_graph_def = tf.GraphDef()
        with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
            serialized_graph = fid.read()
            od_graph_def.ParseFromString(serialized_graph)
            tf.import_graph_def(od_graph_def, name='')

        sess = tf.Session(graph=detection_graph)

    for _ in xrange(NUM_ITERATIONS):
        start_time = datetime.datetime.now()
        image = cv2.imread(args.image, -1)
        out_img = detect_objects(image, sess, detection_graph)
        end_time = datetime.datetime.now()
        execution_times.append((end_time - start_time).total_seconds())

        #frame_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        #out_rgb = cv2.cvtColor(out_img, cv2.COLOR_RGB2BGR)
        #cv2.imwrite('out.jpg', out_rgb)

    # print summary here
    execution_times = np.array(execution_times, dtype=np.float)
    print "\n\n\n ----- SUMMARY -------- \n"
    print "Average runtime: %ss" %(np.average(execution_times))
    print "Std Dev: %ss " %(np.std(execution_times))
    print "95th percentile: %ss" %(np.percentile(execution_times, 95))
    print "99th percentile: %ss" %(np.percentile(execution_times, 99))
