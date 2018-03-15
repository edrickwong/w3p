import os
import sys

###
## PYTHONPATH defaults and stuff
###
home_folder = os.path.expanduser('~')
if 'justin' in home_folder:
    W3P = os.path.join(home_folder, 'Github', 'w3p')
else:
    W3P = os.path.join(home_folder, 'w3p')

TRAIN_FOLDER = os.path.join(W3P, 'training')
APP_FOLDER = os.path.join(W3P, 'object_detector_app')

# add both train and w3p to pythonpath
# again this is super hacky, but without having a set environment,
# just going to hack this in
sys.path.insert(0, TRAIN_FOLDER)
sys.path.insert(0, W3P)
sys.path.insert(0, APP_FOLDER)

###
##  Defaults related to object detection inference
##  TODO: make this interchangble (so we can add in new models easily
###
MODEL_NAME = 'ssd_mobilenet_v1_coco_11_06_2017' #'ssd_mobilenet_v1_coco_11_06_2017'
LABEL_MAP = 'mscoco_label_map.pbtxt' #'label_map.pbtxt' #'mscoco_label_map.pbtxt'
PATH_TO_CKPT = os.path.join(APP_FOLDER, 'object_detection', MODEL_NAME, 'frozen_inference_graph.pb')
PATH_TO_LABELS = os.path.join(APP_FOLDER, 'object_detection', 'data', LABEL_MAP)
DETECT_THRESHOLD = 0.4
NUM_CLASSES = 90

ALLOWED_CLASSES = ['person','bottle','knife','spoon','fork','cup','bowl','dog']

###
##  Defaults related to socket and communication
###
TCP_IP = '127.0.0.1'
TCP_PORT = 1315
BUFFER_SIZE = 1024


###
##  Reference landmarks file
###
REFERENCE_OBJECTS_FILE = os.path.join(APP_FOLDER, 'reference_objects.yaml')

