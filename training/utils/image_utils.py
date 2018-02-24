import cv2
import csv
import os
from random import randint
from collections import defaultdict

BLUE = (0,0,200)
RED = (200,0,0)

ITEMS = ["kettle", "bottle", "bowl", "cup"]
TRAIN_FOLDER = os.path.join(os.path.expanduser('~'), 'w3p', 'training')
IMAGES_FOLDER = [os.path.join(TRAIN_FOLDER, item) for item in ITEMS]

def generate_random_rgb_color():
    return (randint(0,255), randint(0,255), randint(0,255))


def generator_images(valid_images=None):
    for folder in IMAGES_FOLDER:
        for f in os.listdir(folder):
            full_file_name = os.path.join(folder, f)
            if valid_images and f not in valid_images:
                continue
            if os.path.isfile(full_file_name):
                img = ImageContainer(full_file_name)
                yield img


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
        self.ious = []
        self.precision = []

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

    def save_image(self, folder=None):
        if self.is_original:
            raise AlreadySavedException('Trying to save original image')

        if self.image_updated:
            raise DirtyImageException('This image has external artifacts that'\
                                      ' shouldnt be saved to mess up pipeline')

        cv2.imwrite(self.file_name, self.image)

    @property
    def file_name_short(self):
        return self.file_name.split('/')[-1]

    def draw_boxes(self, thickness=3):
        if not self.detected_objects:
            for box in self.labelled_objects:
                self.image_updated = True
                cv2.rectangle(self.image, box.left_corner, box.right_corner,
                              generate_random_rgb_color(), thickness)
        else:
            print 'here'
            for box in self.labelled_objects:
                self.image_updated = True
                cv2.rectangle(self.image, box.left_corner, box.right_corner, (0,0,255), thickness)
            for box in self.detected_objects:
                self.image_updated = True
                print box.left_corner
                cv2.rectangle(self.image, box.left_corner, box.right_corner, (255,0,0), thickness)


class ImageObject(object):
    def __init__(self, width, height, obj_type, xmin, ymin, xmax, ymax):
        self.obj_type = obj_type
        self.height = int(height)
        self.width = int(width)
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

    def verify_coords(self, ignore_image_dims=False):
        # we are initalizing these objects all over the place, so lets just
        # do a sanity check to make sure the bounding boxes make sense
        # ie. xmax > xmin and ymax > ymin
        if self.xmax < self.xmin:
            raise ValueError('xmax for a bounding box must be greater than xmin')

        if self.ymax < self.ymin:
            raise ValueError('ymax for a bounding box must be greater than ymin')

        if ignore_image_dims:
            return

        if self.height and self.ymax > self.height:
            raise ValueError('ymax for bounding box has to be less than '\
                             'height of image')

        if self.width and self.xmax > self.width:
            raise ValueError('ymax for bounding box has to be less than '\
                             'height of image')

    def resize_coords(self, new_width, new_height, update_dims=True):
        # update bounding box coordinates if image is being downsampled or
        # upsamped
        self.xmin = int((float(new_width)/self.width) * self.xmin)
        self.xmax = int((float(new_width)/self.width) * self.xmax)
        self.ymin = int((float(new_height)/self.height) * self.ymin)
        self.ymax = int((float(new_height)/self.height) * self.ymax)

        if update_dims:
            self.width = new_width
            self.height = new_height

        self.verify_coords(ignore_image_dims=update_dims)

    def __str__(self):
        return '%s::%s,%s,%s,%s' %(self.obj_type,
                                   self.xmin,
                                   self.xmax,
                                   self.ymin,
                                   self.ymax)
    def __repr__(self):
        return '%s::%s,%s,%s,%s' %(self.obj_type,
                                   self.xmin,
                                   self.ymin,
                                   self.xmax,
                                   self.ymax)

def build_labelled_csv_dictionary(csv_file_name):
    res = defaultdict(list)

    with open(csv_file_name) as csv_file:
        csvreader = csv.reader(csv_file)
        for row in csvreader:
            # skip first row
            if 'filename' == row[0]:
                continue
            res[row[0]].append(ImageObject(*row[1:]))

    return res

def write_to_csv_file(csv_file_name, csv_dict):
    with open(os.path.join(TRAIN_FOLDER, csv_file_name), 'wb') as f:
        csv_writer = csv.writer(f, delimiter=",")
        title_row = ['filename', 'width', 'height', 'class', 'xmin', 'ymin',
                     'xmax', 'ymax']
        csv_writer.writerow(title_row)
        for file_name, objects in csv_dict.iteritems():
            for obj in objects:
                row = [file_name, obj.width, obj.height, obj.obj_type,
                       obj.xmin, obj.ymin, obj.xmax, obj.ymax]
                csv_writer.writerow(row)
