import cv2

def main():
    cam = cv2.VideoCapture(0)
    sa, img = cam.read()
    import pdb ; pdb.set_trace()
    cv2.imshow('capture', img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    if s:
	imwrite("stuff.jpg", img)

if __name__ == "__main__":
    main()
