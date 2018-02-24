'''
    Downsample (technically upsample too) images in the folder to specfiied
    sizes
'''
import argparse
import csv
import cv2
import os
from utils.image_utils import ImageContainer, ImageObject, \
                              build_labelled_csv_dictionary, \
                              generator_images, \
                              write_to_csv_file

TRAIN_FOLDER = os.path.join(os.path.expanduser('~'), 'w3p', 'training')
CSV_FILES = [os.path.join(TRAIN_FOLDER, 'images.csv')]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-bad', '--bad_images', type=bool,
                        default=False, help='Show bad images only')
    args = parser.parse_args()
    bad_images_only = args.bad_images

    # bad images set -- incase we have repeats
    # this process is not idempotent, so be safe
    bad_images = None
    if bad_images_only:
        bad_images = set()
        with open('bad_images.txt') as f:
            for name in f.readlines():
                bad_images.add("IMG_" + name.strip() + ".jpg")

    # build existing labels dict
    csv_dict = {}
    for f in CSV_FILES:
        csv_dict.update(build_labelled_csv_dictionary(f))

    for image in generator_images(valid_images=bad_images):
        image.labelled_objects = csv_dict[image.file_name_short]
        image.draw_boxes()
        print image
        cv2.imshow('ground truth for: %s' %(image.file_name), image.image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
