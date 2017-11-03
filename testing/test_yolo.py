import sys
import os
#HACK:: Anshuman 11/04 Add w3p into PYTHONPATH
#        for relative imports
w3p_path = os.path.join(os.path.expanduser('~'), 'w3p')
sys.path.insert(0, w3p_path)

from testing.detectors import YoloDarknet
from testing.config import *

YOLO_TYPE = 'tiny'

def main():
    base_cmd = "cd ~/darknet && ./darknet detector test cfg/voc.data cfg/tiny-yolo-voc.cfg tiny-yolo.weights"
    yd = YoloDarknet(YOLO_TYPE, base_cmd)
    yd.run()
    yd.print_summary()

if __name__ == "__main__":
    main()
