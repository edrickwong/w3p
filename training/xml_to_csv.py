'''
    Adopted from https://github.com/datitran/raccoon_dataset.git

    Updated main and caught a couple of random edge cases based on how the
    directories were hardcoded for their example

    Usage::: `python xml_to_csv.py {folder_name_with_xml_annotations}`
'''
import os
import sys
import glob
import pandas as pd
import xml.etree.ElementTree as ET


def xml_to_csv(path):
    xml_list = []
    for xml_file in glob.glob(path + '/*.xml'):
        tree = ET.parse(xml_file)
        root = tree.getroot()
        for member in root.findall('object'):
            value = (root.find('filename').text,
                     int(root.find('size')[0].text),
                     int(root.find('size')[1].text),
                     member[0].text,
                     int(member[4][0].text),
                     int(member[4][1].text),
                     int(member[4][2].text),
                     int(member[4][3].text)
                     )
            xml_list.append(value)
    column_name = ['filename', 'width', 'height', 'class', 'xmin', 'ymin', 'xmax', 'ymax']
    xml_df = pd.DataFrame(xml_list, columns=column_name)
    return xml_df


def main():
    folder = sys.argv[1]
    image_path = os.path.join(os.getcwd(), folder)
    xml_df = xml_to_csv(image_path)
    if xml_df.empty:
        print "No data found to annotate. Quitting"
        sys.exit(1)
    xml_df.to_csv('images.csv', index=None)
    print('Successfully converted xml to csv.')


if __name__ == "__main__":
    main()
