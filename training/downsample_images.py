'''
    Downsample (technically upsample too) images in the folder to specfiied
    sizes
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
    parser.add_argument('-w', '--width', dest='width', type=int,
                        default=640, help='New Width in px.')
    parser.add_argument('-he', '--height', type=int,
                        default=480, help='New Height in px.')
    parser.add_argument('-d', '--debug', type=bool,
                        default=False, help='Debug Mode')
    parser.add_argument('-s', '--save', type=bool,
                        default=False, help='Save csv file')

    args = parser.parse_args()
    DEBUG = args.debug
    new_width = args.width
    new_height = args.height
    save_csv_file = args.save

    # build existing labels dict
    csv_dict = {}
    for f in CSV_FILES:
        csv_dict.update(build_labelled_csv_dictionary(f))

    for image in generator_images():
        image.labelled_objects = csv_dict[image.file_name_short]
        image.image = cv2.resize(image.image, (new_width, new_height),
                                 interpolation = cv2.INTER_LINEAR)
        image.is_original = False

        for box in image.labelled_objects:
            box.resize_coords(new_width, new_height)

        if DEBUG:
            image.draw_boxes()
            cv2.imshow('original %s' %(image.file_name), image.image)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        else:
            image.save_image()
            csv_dict[image.file_name_short] = image.labelled_objects

    if DEBUG:
        return

    # dump the entire dict into csv calles images.csv, and use xsiting logic to split labels
    # I should so be using pandas for this stuff...
    # backup old images.csv properly
    if save_csv_file:
        try:
            cur_date = datetime.now().strftime('%s')
            os.rename(os.path.join(TRAIN_FOLDER, 'images.csv'),
                      os.path.join(TRAIN_FOLDER, 'images.csv.bak.%s'%(cur_date)))
        except IOError:
            pass
        except Exception as e:
            print e

        write_to_csv_file(CSV_FILES[0], csv_dict)

    print "Finished downsampling images"

if __name__ == "__main__":
    main()
