'''
    Calculate IOU
'''
import argparse
import os
import tensorflow as tf

# HACK IN PYTHONPATH SO WE CAN USE object_detector_utils
import sys
sys.path.insert(0, os.path.join(os.path.expanduser('~'), 'w3p'))

from object_detector_app.object_detect_single import detect_objects_no_vis 
from training.utils.image_utils import ImageContainer, build_labelled_csv_dictionary

IMAGE = "pitcher"
TRAIN_FOLDER = os.path.join(os.path.expanduser('~'), 'w3p', 'training')
IMAGES_FOLDER = os.path.join(TRAIN_FOLDER, IMAGE)
CSV_TEST_FILE = os.path.join(TRAIN_FOLDER, 'test_labels.csv')
MODEL_NAME = 'ssd_mobilenet_v1_coco_2017_11_17/01-26-2018'
PATH_TO_CKPT = os.path.join(TRAIN_FOLDER, MODEL_NAME, 'output_inference.pb')
#MODEL_NAME = 'ssd_mobilenet_v1_coco_11_06_2017' 
#PATH_TO_CKPT = os.path.join('/Users/lindawang/w3p/object_detector_app/object_detection/ssd_mobilenet_v1_coco_11_06_2017', 'frozen_inference_graph.pb')

def generator_for_test_image(csv_dict):
    for f in os.listdir(IMAGES_FOLDER):
        if f in csv_dict:
            file_name = os.path.join(IMAGES_FOLDER, f)
            img = ImageContainer(file_name)
            img.labelled_objects = csv_dict[f]
            yield img

def main():
    # setup tf session model
    detection_graph = tf.Graph()
    with detection_graph.as_default():
        od_graph_def = tf.GraphDef()
        with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
            serialized_graph = fid.read()
            od_graph_def.ParseFromString(serialized_graph)
            import pdb ; pdb.set_trace()
            tf.import_graph_def(od_graph_def, name='')

        sess = tf.Session(graph=detection_graph)

    csv_test_dict = build_labelled_csv_dictionary(CSV_TEST_FILE)
    for image in generator_for_test_image(csv_test_dict):
        boxes, scores, classes, num_detections = detect_objects_no_vis(image.image, sess, detection_graph)
        obj = classes[0][0]
        import pdb ; pdb.set_trace()

if __name__ == "__main__":
    main()
