'''
    Fix all the bad labels that got flipped for some reason
'''
import argparse
import csv
import cv2
import os
from copy import deepcopy
from collections import defaultdict
from datetime import datetime
from utils.image_utils import ImageContainer, ImageObject, \
                              build_labelled_csv_dictionary, \
                              generator_images, \
                              write_to_csv_file, \
                              TRAIN_FOLDER

CSV_FILES = [os.path.join(TRAIN_FOLDER, 'images.csv')]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--debug', type=bool,
                        default=False, help='Debug Mode')
    args = parser.parse_args()
    DEBUG = args.debug

    # build existing labels dict
    csv_dict = {}
    for f in CSV_FILES:
        csv_dict.update(build_labelled_csv_dictionary(f))

    # bad images set -- incase we have repeats
    # this process is not idempotent, so be safe
    bad_images = set()
    with open('bad_images.txt') as f:
        for name in f.readlines():
            bad_images.add("IMG_" + name.strip() + ".jpg")


    for image in generator_images(valid_images=bad_images):
        image.labelled_objects = csv_dict[image.file_name_short]

        for box in image.labelled_objects:
            flipped_coords = \
                    box.get_flipped_coords(image.width, image.height,
                                           both_flip=True)
            box.xmin = flipped_coords[0]
            box.ymin = flipped_coords[1]
            box.xmax = flipped_coords[2]
            box.ymax = flipped_coords[3]

        # draw new box
        if DEBUG:
            image.draw_boxes()
            cv2.imshow('new', image.image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        else:
            csv_dict[image.file_name_short] = image.labelled_objects

    if not DEBUG:
        # dump the entire dict into csv calles images.csv, and use xsiting logic to split labels
        # I should so be using pandas for this stuff...
        # backup old images.csv properly
        try:
            cur_date = datetime.now().strftime('%s')
            os.rename(os.path.join(TRAIN_FOLDER, 'images.csv'),
                      os.path.join(TRAIN_FOLDER, 'images.csv.bak.%s'%(cur_date)))
        except IOError:
            pass
        except Exception as e:
            print e

        write_to_csv_file(CSV_FILES[0], csv_dict)


if __name__ == "__main__":
    main()
