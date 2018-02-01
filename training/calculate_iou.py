'''
    Calculate IOU
'''
import argparse
import os

# HACK IN PYTHONPATH SO WE CAN USE object_detector_utils
import sys
sys.path.insert(0, os.path.join(os.path.expanduser('~'), 'w3p'))

#from object_detector_utils 
from training.utils.image_utils import ImageContainer, build_labelled_csv_dictionary

IMAGE = "pitcher"
TRAIN_FOLDER = os.path.join(os.path.expanduser('~'), 'w3p', 'training')
IMAGES_FOLDER = os.path.join(TRAIN_FOLDER, IMAGE)
CSV_TEST_FILE = os.path.join(TRAIN_FOLDER, 'test_labels.csv')

def generator_for_test_image(csv_dict):
    for f in os.listdir(IMAGES_FOLDER):
        if f in csv_dict:
            file_name = os.path.join(IMAGES_FOLDER, f)
            img = ImageContainer(file_name)
            img.labelled_objects = csv_dict[f]
            yield img

def main():
    # setup tf session model
    csv_test_dict = build_labelled_csv_dictionary(CSV_TEST_FILE)
    for image in generator_for_test_image(csv_test_dict):
        import pdb ; pdb.set_trace()

if __name__ == "__main__":
    main()
