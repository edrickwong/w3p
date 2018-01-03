from cv2 import *

def main():
    cam = VideoCapture(0)
    s, img = cam.read()
    if s:
	imwrite("stuff.jpg", img)

if __name__ == "__main__":
    main()
