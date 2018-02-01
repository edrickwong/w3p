'''
    Augment the picture dataset by flipping the images on horizontal
    and or vertical scale.
'''
import argparse
from collections import defaultdict
import os
from utils.image_utils import ImageContainer, build_labelled_csv_dictionary

IMAGE = "pitcher"
TRAIN_FOLDER = os.path.join(os.path.expanduser('~'), 'w3p', 'training')
IMAGES_FOLDER = os.path.join(TRAIN_FOLDER, IMAGE)
CSV_FILES = [os.path.join(TRAIN_FOLDER, 'test_labels.csv'),
             os.path.join(TRAIN_FOLDER, 'train_labels.csv')]

def generate_images():
    for f in os.listdir(IMAGES_FOLDER):
        full_file_name = os.path.join(IMAGES_FOLDER, f)
        if os.path.isfile(full_file_name):
            yield ImageContainer(full_file_name)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-hor', '--horizontal', dest='horizontal', type=bool,
                        default=True, help='Flip Horizontally.')
    parser.add_argument('-ver', '--vertical', dest='vertical', type=bool,
                        default=False, help='Flip Vertically.')
    args = parser.parse_args()

    csv_dict_test = build_labelled_csv_dictionary(CSV_FILES[0])
    csv_dict_label = build_labelled_csv_dictionary(CSV_FILES[1])

    for image in generate_images():
        import pdb ; pdb.set_trace()

if __name__ == "__main__":
    main()
