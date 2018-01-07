from os import listdir
from os.path import isfile, join
import sys
import os
import subprocess
import random

SLICE_PERCENTAGE = 0.4

def main():
    # too lazy to do argparse, hack using sys
    folder = sys.argv[1]

    if not folder:
        print "Need to specify folder to randomly cleanse"
        sys.exit(1)

    # assume folder is in cwd
    cwd = os.getcwd()
    folder = join(cwd, folder)
    files = [f for f in listdir(folder) if isfile(join(folder, f))]
    random.shuffle(files)

    before_delete = len(files)
    del_count = 0

    for f in files[int(len(files)*0.4):]:
        os.remove(join(folder, f))
        del_count += 1

    print "Deleted %s/%s files from %s" %(del_count, before_delete, folder)

if __name__ == "__main__":
    main()
