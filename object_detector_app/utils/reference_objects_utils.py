import cv2
import yaml

from defaults import *
from training.utils.image_utils import ImageObject, WHITE
from object_detection.utils.visualization_utils import draw_bounding_box_on_image_array
from multiprocessing import get_logger
from ctypes import c_float

logger = get_logger()


class ReferenceObjectsHelper(object):
    '''
        I tried creating this as a mixin, but apparently mixins
        and Process don't play well together..
        SIGH.. I hate multiproc in 2.7 -_-
    '''
    def __init__(self, width, height):
        try:
            self.width = width.value
            self.height = height.value
        except Exception as e:
            logger.warning('Expecting width and height to be ctype objects.' \
                           ' They are of type %s.' %(type(width)))
            self.width = width
            self.height = height

        self.reference_objects = []
        self.load_reference_objects()

    def load_reference_objects(self):
        for item in yaml.load(open(REFERENCE_OBJECTS_FILE)):
            self.reference_objects.append(ReferenceObject(self.width,
                                                          self.height,
                                                          **item))

    def visualize_reference_objects(self, img):
        '''
            Draw rectangles around the reference objects in the
            given image
        '''
        for ref_obj in self.reference_objects:
            ref_obj.draw_bounding_box(img)
        return img


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

    def draw_bounding_box(self, img):
        draw_bounding_box_on_image_array(img,
                                         self.ymin,
                                         self.xmin,
                                         self.ymax,
                                         self.xmax,
                                         color='white',
                                         thickness=6,
                                         display_str_list=(self.obj_type, ),
                                         use_normalized_coordinates=False)

