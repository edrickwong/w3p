'''
    Augment the picture dataset by flipping the images on horizontal
    and or vertical scale.
'''
import argparse
import csv
import cv2
import os
from collections import defaultdict
from datetime import datetime
from utils.image_utils import ImageContainer, ImageObject, build_labelled_csv_dictionary

IMAGE = "pitcher"
TRAIN_FOLDER = os.path.join(os.path.expanduser('~'), 'w3p', 'training')
IMAGES_FOLDER = os.path.join(TRAIN_FOLDER, IMAGE)
CSV_FILES = [os.path.join(TRAIN_FOLDER, 'test_labels.csv'),
             os.path.join(TRAIN_FOLDER, 'train_labels.csv')]
TRAINING_PERCENTAGE = 0.7

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
    parser.add_argument('-d', '--debug', type=bool,
                        default=False, help='Debug mode')
    args = parser.parse_args()
    DEBUG = args.debug
    FLIP_ARG = 0 if args.vertical else 1
    FLIP_LETTER = 'v' if args.vertical else 'h'

    # build existing labels dict
    csv_dict = {}
    for f in CSV_FILES:
        csv_dict.update(build_labelled_csv_dictionary(f))

    for image in generator_images():
        image.labelled_objects = csv_dict[image.file_name_short]
        new_image_name = image.file_name_short.split('.')[0] + '_' + FLIP_LETTER + '.' + image.file_name_short.split('.')[1]
        new_image_name = os.path.join(IMAGES_FOLDER, new_image_name)
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
    try:
        cur_date = datetime.now().strftime('%s')
        os.rename(os.path.join(TRAIN_FOLDER, 'images.csv'),
                  os.path.join(TRAIN_FOLDER, 'images.csv.bak.%s'%(cur_date)))
    except IOError:
        pass
    except Exception as e:
        print e

    # write cur csv_dict
    with open(os.path.join(TRAIN_FOLDER, 'images.csv'), 'wb') as f:
        csv_writer = csv.writer(f, delimiter=",")
        title_row = ['filename', 'width', 'height', 'class', 'xmin', 'ymin',
                     'xmax', 'ymax']
        csv_writer.writerow(title_row)
        for file_name, objects in csv_dict.iteritems():
            for obj in objects:
                row = [file_name, obj.width, obj.height, obj.obj_type,
                       obj.xmin, obj.ymin, obj.xmax, obj.ymax]
                csv_writer.writerow(row)


if __name__ == "__main__":
    main()
