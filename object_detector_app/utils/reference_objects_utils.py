import cv2
import time
import yaml

from defaults import *
from training.utils.image_utils import ImageObject, WHITE
from object_detection.utils.visualization_utils import draw_bounding_box_on_image_array

from os.path import getmtime
from multiprocessing import get_logger
from threading import Thread

logger = get_logger()


class ReferenceObjectsHelper(object):
    '''
        I tried creating this as a mixin, but apparently mixins
        and Process don't play well together..
        SIGH.. I hate multiproc in 2.7 -_-
    '''
    CHECK_INTERVAL = 5

    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.reference_objects = []
        self.load_reference_objects()

        self._worker_thread = Thread(target=self.check_for_ref_file_change)
        self._worker_thread.daemon = True
        self._worker_thread.start()

    def load_reference_objects(self, load_fresh=False):
        if load_fresh:
            self.reference_objects = []

        try:
            for item in yaml.load(open(REFERENCE_OBJECTS_FILE)):
                if type(item) == dict:
                    self.reference_objects.append(ReferenceObject(self.width,
                                                                  self.height,
                                                                  **item))
                else:
                    logger.warning('Invalid entry type for Reference Object')
        except TypeError:
            logger.warning('Invalid entry type for Reference Object')
        # dont raise on any errors cuz we are goign to be reloading on change
        except:
            pass

    def visualize_reference_objects(self, img):
        '''
            Draw rectangles around the reference objects in the
            given image
        '''
        for ref_obj in self.reference_objects:
            ref_obj.draw_bounding_box(img)
        return img

    def check_for_ref_file_change(self):
        # enter event loop for this guy
        last_mtime = getmtime(REFERENCE_OBJECTS_FILE)
        while True:
            cur_mtime = getmtime(REFERENCE_OBJECTS_FILE)
            # rely on modified time which according to python docs is a cross
            # platform call to check if we need to reload the objects
            if cur_mtime != last_mtime:
                logger.warning('Detected a change in reference file. Reloading file')
                self.load_reference_objects(load_fresh=True)
                last_mtime = cur_mtime
            time.sleep(self.CHECK_INTERVAL)


class ReferenceObject(ImageObject):
    '''
        Templated after the generic ImageObject used in training.

        With two other args:
            real_size = real_size of the object
            real_width = real_width of the object
    '''
    def __init__(self, width, height,
                 passing_normalized_coords=True, **kwargs):

        # for the dimensions variable denormalize coords
        if passing_normalized_coords:
            self.xmin = int(kwargs.pop('xmin') * width)
            self.xmax = int(kwargs.pop('xmax') * width)
            self.ymin = int(kwargs.pop('ymin') * height)
            self.ymax = int(kwargs.pop('ymax') * height)

        # Feeling lazy af right now and violating one of the zens of
        # python... but going to do initalization implicitly rather
        # than explicitly
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

        logger.warning(self)
