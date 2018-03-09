# %%

import cv2
import multiprocessing
import socket
import tensorflow as tf
import time

from defaults import *
from multiprocessing import Queue, Pool, Process
from object_detector_utils import ObjectDetector
from utils.app_utils import WebcamVideoStream
from reference_objects_utils import ReferenceObjectsHelper

# %%
helper = ReferenceObjectsHelper()
list = helper.reference_objects
print(len(list))
print(list[1].real_width)
print(list[1].midpoint[0])
