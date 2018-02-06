'''
    Calculate IOU
'''
import argparse
import os
import tensorflow as tf
from object_detection.utils import label_map_util
import numpy as np
import cv2

# HACK IN PYTHONPATH SO WE CAN USE object_detector_utils
import sys
sys.path.insert(0, os.path.join(os.path.expanduser('~'), 'w3p'))

from object_detector_app.object_detect_single import detect_objects_no_vis 
from training.utils.image_utils import ImageContainer, build_labelled_csv_dictionary, ImageObject

IOU_THRESHOLD = 0.3
IMAGE = "pitcher"
TRAIN_FOLDER = os.path.join(os.path.expanduser('~'), 'w3p', 'training')
IMAGES_FOLDER = os.path.join(TRAIN_FOLDER, IMAGE)
CSV_TEST_FILE = os.path.join(TRAIN_FOLDER, 'test_labels.csv')
MODEL_NAME = 'ssd_mobilenet_pitcher'
PATH_TO_CKPT = os.path.join(TRAIN_FOLDER, MODEL_NAME, 'frozen_inference_graph.pb')
#MODEL_NAME = 'ssd_mobilenet_v1_coco_11_06_2017' 
#PATH_TO_CKPT = os.path.join('/Users/lindawang/w3p/object_detector_app/object_detection/ssd_mobilenet_v1_coco_11_06_2017', 'frozen_inference_graph.pb')
PATH_TO_LABELS = os.path.join(TRAIN_FOLDER, 'label_map.pbtxt')

NUM_CLASSES = 1

# Loading label map
label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES,
                                                            use_display_name=True)
category_index = label_map_util.create_category_index(categories)

iou_res = []

def generator_for_test_image(csv_dict):
    for f in os.listdir(IMAGES_FOLDER):
        if f in csv_dict:
            file_name = os.path.join(IMAGES_FOLDER, f)
            img = ImageContainer(file_name)
            img.labelled_objects = csv_dict[f]
            yield img

def iou(ground_truth, prediction):
    max_xmin = max(ground_truth[0],prediction[0]) # get max from xmins 
    min_xmax = min(ground_truth[1],prediction[1]) # get min from xmaxes
    max_ymin = max(ground_truth[2],prediction[2]) # get max from ymins
    min_ymax = min(ground_truth[3],prediction[3]) # get min from ymaxes
    
    # compute intersection 
    intersection = (min_xmax - max_xmin + 1) * (min_ymax - max_ymin + 1)

    # compute union
    ground_area = (ground_truth[1] - ground_truth[0] + 1) * (ground_truth[3] - ground_truth[2] + 1)
    pred_area = (prediction[1] - prediction[0] + 1) * (prediction[3] - prediction[2] + 1)
    union  = ground_area + pred_area - intersection
    return intersection / float(union)

def main():
    # setup tf session model
    detection_graph = tf.Graph()
    with detection_graph.as_default():
        od_graph_def = tf.GraphDef()
        with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
            serialized_graph = fid.read()
            od_graph_def.ParseFromString(serialized_graph)
            tf.import_graph_def(od_graph_def, name='')

        sess = tf.Session(graph=detection_graph)

    csv_test_dict = build_labelled_csv_dictionary(CSV_TEST_FILE)
    for image in generator_for_test_image(csv_test_dict):
        boxes, scores, classes, num_detections = detect_objects_no_vis(image.image, sess, detection_graph)
        # for scores greater than threshold
        for i in range(len(scores[0])):
            pred_box = []
            ground_box = []
            if scores[0][i] < DETECT_THRESHOLD:
                break
            box = np.squeeze(boxes[0][i])
            pred_box = [box[0]*image.width, box[2]*image.width, box[1]*image.height, box[3]*image.height]
            obj_class = category_index[classes[0][i]]['name']
            img = ImageObject(image.width, image.height, obj_class, box[0]*image.width, box[1]*image.height, box[2]*image.width, box[3]*image.height)
            image.detected_objects.append(img)
            ious = []
            for obj in image.labelled_objects:
                if str(obj.obj_type) == str(obj_class):
                    ground_box = [float(obj.xmin), float(obj.xmax), float(obj.ymin), float(obj.ymax)]
                    ious.append(iou(ground_box,pred_box))
            # calculate iou
            if ground_box and pred_box: 
                iou_res.append(max(ious))
                image.ious.append(max(ious))
        for iou in image.ious:
            if iou >= IOU_THRESHOLD:
                if image.detected_objects
        image.draw_boxes()
        cv2.imshow('original', image.image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        import pdb ; pdb.set_trace()
    
    # print average iou
    print 'average iou: ' , np.average(iou_res)
    print 'max iou: ' , max(iou_res)
    print 'min iou: ' , min(iou_res)

if __name__ == "__main__":
    main()
