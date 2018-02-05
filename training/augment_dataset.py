'''
    Augment the picture dataset by flipping the images on horizontal
    and or vertical scale.
'''
import argparse
import cv2
import os
from collections import defaultdict
from utils.image_utils import ImageContainer, ImageObject, build_labelled_csv_dictionary

IMAGE = "pitcher"
TRAIN_FOLDER = os.path.join(os.path.expanduser('~'), 'w3p', 'training')
IMAGES_FOLDER = os.path.join(TRAIN_FOLDER, IMAGE)
CSV_FILES = [os.path.join(TRAIN_FOLDER, 'test_labels.csv'),
             os.path.join(TRAIN_FOLDER, 'train_labels.csv')]

def generator_images():
    for f in os.listdir(IMAGES_FOLDER):
        full_file_name = os.path.join(IMAGES_FOLDER, f)
        if os.path.isfile(full_file_name):
            img = ImageContainer(full_file_name)
            yield img

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-ver', '--vertical', dest='vertical', type=bool,
                        default=False, help='Flip Vertically.')
    args = parser.parse_args()

    FLIP_ARG = 1 if args.vertical else 0

    # build existing labels dict
    csv_dict = {}
    for f in CSV_FILES:
        csv_dict.update(build_labelled_csv_dictionary(f))

    for image in generator_images():
        image.labelled_objects = csv_dict[image.file_name_short]
        new_image_name = image.file_name_short.split('.')[0] + 'f' + '.' + image.file_name_short.split('.')[1]
        updated_image = ImageContainer(new_image_name, lazy_load=True)
        updated_image.image = cv2.flip(image.image, FLIP_ARG)
        updated_image.original = False
        for box in image.labelled_objects:
            new_coords = box.get_flipped_coords(image.width, image.height, FLIP_ARG)
            updated_image.labelled_objects.append(ImageObject(box.obj_type,
                                                              *new_coords))

        image.draw_boxes()
        updated_image.draw_boxes()
        cv2.imshow('original', image.image)
        cv2.imshow('flipped', updated_image.image)
        import pdb ; pdb.set_trace()

if __name__ == "__main__":
    main()
