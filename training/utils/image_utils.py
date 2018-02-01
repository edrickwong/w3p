import cv2
import csv
from collections import defaultdict

class ImageContainer(object):
    '''
        Generic class for a single image. Defined by image_name and location
    '''
    def __init__(self, file_name, lazy_load=False):
        self.file_name = file_name
        # if its an original image, or it was rotated or flipped
        self.is_original = True

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
            return False

    @property
    def file_name_short(self):
        return self.file_name.split('/')[-1]

    def write_labelled_objects_into_csv(self, csv_file):
        pass


class ImageObject(object):
    def __init__(self, obj_type, xmin, xmax, ymin, ymax):
        self.obj_type = obj_type
        self.xmin = xmin
        self.xmax = xmax
        self.ymin = ymin
        self.ymax = ymax

    def __eq__(self, obj):
        return self.obj_type == obj.obj_type and self.xmin == obj.xmin \
                 and self.xmax == obj.xmax and self.ymin == obj.ymin \
                 and self.ymax == obj.ymax

    def __cmp__(self, obj):
        if self.obj_type != obj.obj_type:
            return float('inf')

    def get_flipped_coords(self, width, height, vertical_flip=False):
        pass

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
