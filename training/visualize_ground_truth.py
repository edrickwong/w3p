'''
    Downsample (technically upsample too) images in the folder to specfiied
    sizes
'''
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
    # build existing labels dict
    csv_dict = {}
    for f in CSV_FILES:
        csv_dict.update(build_labelled_csv_dictionary(f))

    for image in generator_images():
        image.labelled_objects = csv_dict[image.file_name_short]
        image.draw_boxes()
        cv2.imshow('ground truth for: %s' %(image.file_name), image.image)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
