import cv2
import csv
from random import randint
from collections import defaultdict

def generate_random_rgb_color():
    return (randint(0,255), randint(0,255), randint(0,255))

class AlreadySavedException(Exception):
    pass


class DirtyImageException(Exception):
    pass


class ImageContainer(object):
    '''
        Generic class for a single image. Defined by image_name and location
    '''
    def __init__(self, file_name, lazy_load=False):
        self.file_name = file_name

        # if its an original image, or it was rotated or flipped
        self.is_original = True

        # if we draw a rectangle for bounding boxes, we shouldnt save
        # because it could mess up the pipeline
        self.image_updated = False

        # other container variables about image which we init later
        # lazy load the image so we don't blow up memory
        self.image = None
        self.width = None
        self.height = None
        self.detected_objects = []
        self.labelled_objects = []

        if not lazy_load:
            self.read_image()

    def read_image(self):
        if not self.image:
            self.image = cv2.imread(self.file_name)
            self.height, self.width, _ = self.image.shape

    def __str__(self):
        return self.file_name

    def __repr__(self):
        return self.file_name

    def save_file(self):
        if self.is_original:
            # Log something here about not being able to overrwrite originals
            # Just for data integrity sake here
            raise AlreadySavedException('Trying to save original image')

        if self.image_updated:
            raise DirtyImageException('This image has external artifacts that'\
                                      ' shouldnt be saved to mess up pipeline')

    @property
    def file_name_short(self):
        return self.file_name.split('/')[-1]

    def write_labelled_objects_into_csv(self, csv_file):
        pass

    def draw_boxes(self, thickness=3):
        for box in self.labelled_objects:
            self.image_updated = True
            cv2.rectangle(self.image, box.left_corner, box.right_corner,
                          generate_random_rgb_color(), thickness)


class ImageObject(object):
    def __init__(self, obj_type, xmin, ymin, xmax, ymax):
        self.obj_type = obj_type
        self.xmin = int(xmin)
        self.xmax = int(xmax)
        self.ymin = int(ymin)
        self.ymax = int(ymax)

        self.verify_coords()

    @property
    def left_corner(self):
        return (self.xmin, self.ymin)

    @property
    def right_corner(self):
        return (self.xmax, self.ymax)

    def __eq__(self, obj):
        return self.obj_type == obj.obj_type and self.xmin == obj.xmin \
                 and self.xmax == obj.xmax and self.ymin == obj.ymin \
                 and self.ymax == obj.ymax

    def __cmp__(self, obj):
        if self.obj_type != obj.obj_type:
            return float('inf')

    def get_flipped_coords(self, width, height, vertical_flip=False):
        if vertical_flip:
            # flip along the y-axis
            # ymin ymax stay the same
            new_xmax = width - self.xmin
            new_xmin = width - self.xmax
            return new_xmin, self.ymin, new_xmax, self.ymax
        else:
            # flip along the x-axis
            # xmin xmax stay the same
            new_ymin = height - self.ymax
            new_ymax = height - self.ymin
            return self.xmin, new_ymin, self.xmax, new_ymax

    def verify_coords(self):
        # we are initalizing these objects all over the place, so lets just
        # do a sanity check to make sure the bounding boxes make sense
        # ie. xmax > xmin and ymax > ymin
        if self.xmax < self.xmin:
            raise ValueError('xmax for a bounding box must be greater than xmin')

        if self.ymax < self.ymin:
            raise ValueError('ymax for a bounding box must be greater than ymin')

    def __str__(self):
        return '%s::%s,%s,%s,%s' %(self.obj_type,
                                   self.xmin,
                                   self.xmax,
                                   self.ymin,
                                   self.ymax)
    def __repr__(self):
        return '%s::%s,%s,%s,%s' %(self.obj_type,
                                   self.xmin,
                                   self.xmax,
                                   self.ymin,
                                   self.ymax)

def build_labelled_csv_dictionary(csv_file_name):
    res = defaultdict(list)

    with open(csv_file_name) as csv_file:
        csvreader = csv.reader(csv_file)
        for row in csvreader:
            # skip first row
            if 'filename' == row[0]:
                continue
            res[row[0]].append(ImageObject(*row[3:]))

    return res
