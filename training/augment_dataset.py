'''
    Augment the picture dataset by flipping the images on horizontal
    and or vertical scale.
'''
import argparse
import csv
import cv2
import os
import random
from collections import defaultdict
from datetime import datetime
from utils.image_utils import ImageContainer, ImageObject, build_labelled_csv_dictionary, write_to_csv_file, generator_images, TRAIN_FOLDER, IMAGES_FOLDER, write_to_csv_file

CSV_FILES = [os.path.join(TRAIN_FOLDER, 'images.csv')]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-ver', '--vertical', dest='vertical', type=bool,
                        default=False, help='Flip Vertically.')
    parser.add_argument('-d', '--debug', type=bool,
                        default=False, help='Debug mode')
    parser.add_argument('-p', '--prob', type=float,
                        default=1, help='Probability image gets flipped')

    args = parser.parse_args()
    DEBUG = args.debug
    FLIP_ARG = 0 if args.vertical else 1
    FLIP_LETTER = 'v' if args.vertical else 'h'
    probability = args.prob

    if FLIP_LETTER == 'v':
        probability = 0.4

    # build existing labels dict
    csv_dict = {}
    for f in CSV_FILES:
        csv_dict.update(build_labelled_csv_dictionary(f))

    random.seed(13)

    for image in generator_images():
        # skip with a P(1 - probability) chance
        if random.random() > probability:
            continue
        image.labelled_objects = csv_dict[image.file_name_short]
        new_image_name = image.file_name_short.split('.')[0] + '_' + FLIP_LETTER + '.' + image.file_name_short.split('.')[1]
        new_image_name = os.path.join(image.folder_name, new_image_name)
        updated_image = ImageContainer(new_image_name, lazy_load=True)
        updated_image.image = cv2.flip(image.image, FLIP_ARG)
        updated_image.is_original = False
        # for the flipped image add in the flipped bounding boxes
        for box in image.labelled_objects:
            new_coords = box.get_flipped_coords(image.width, image.height, FLIP_ARG)
            updated_image.labelled_objects.append(ImageObject(image.width,
                                                              image.height,
                                                              box.obj_type,
                                                              *new_coords))

        if DEBUG:
            image.draw_boxes()
            updated_image.draw_boxes()
            cv2.imshow('original', image.image)
            cv2.imshow('flipped', updated_image.image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
            break
        else:
            # add the updated image back into csv
            csv_dict[updated_image.file_name_short] = updated_image.labelled_objects
            # save flipped image
            updated_image.save_image(IMAGES_FOLDER)

    # dump the entire dict into csv calles images.csv, and use xsiting logic to split labels
    # I should so be using pandas for this stuff...
    # backup old images.csv properly
    if not DEBUG:
        try:
            cur_date = datetime.now().strftime('%s')
            os.rename(os.path.join(TRAIN_FOLDER, 'images.csv'),
                      os.path.join(TRAIN_FOLDER, 'images.csv.bak.%s'%(cur_date)))
        except IOError:
            pass
        except Exception as e:
            print e

        write_to_csv_file(os.path.join(TRAIN_FOLDER, 'images.csv'),
                          csv_dict)
        print 'Finished writing csv file'


if __name__ == "__main__":
    main()
