import os
import cv2
import datetime
import time
import argparse
import multiprocessing
import numpy as np
import tensorflow as tf

from utils.object_detector_utils import ObjectDetector
from utils.reference_objects_utils import ReferenceObjectsHelper

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-img', '--image', dest='image', type=str,
                        default='linda.jpg', help='Name of Picture')
    parser.add_argument('-out', '--out_image', dest='out_img', type=str,
                        default='out.jpg', help='Name of Picture')
    args = parser.parse_args()

    obj = ObjectDetector()

    # also draw the reference objects
    mixin = ReferenceObjectsHelper()

    image = cv2.imread(args.image, -1)
    image = cv2.resize(image, (640, 480),
                       interpolation = cv2.INTER_LINEAR)
    frame_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    out_img = obj.detect_objects_visualize(frame_rgb)

    mixin.visualize_reference_objects(out_img)

    cv2.imshow('orig', out_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
