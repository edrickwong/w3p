import tensorflow as tf
import numpy as np
import cv2

# defaults will have relevant pythonpath stuff
from defaults import *

from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util

class ObjectDetector(object):
    '''
        TODO: Add comments + design considerations
    '''
    def __init__(self):
        # need this for visualization
        self.label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
        self.categories = label_map_util.convert_label_map_to_categories(self.label_map,
                                                                         max_num_classes=NUM_CLASSES,
                                                                         use_display_name=True)
        self.category_index = label_map_util.create_category_index(self.categories)

        self._detection_graph = None
        self._sess = None

        self.load_tf_graph()

    def detect_objects_visualize(self, image_np):
        '''
            Given an image, run the loaded model for inference to detect objects.
            Only classes define in defaults allowed_classes will be shown.

            This function is slightly different from the detect_objects method
            in that, this one draws rectangles/visualizations on the image that
            is passed in and returns this modified image back.

            Inputs:
              image_np:: numpy representation of an image

            Outputs:
              image_np:: modified input image with detected visualizations
        '''
	# Expand dimensions since the model expects images to have shape: [1, None, None, 3]
	image_np_expanded = np.expand_dims(image_np, axis=0)
	image_tensor = self._detection_graph.get_tensor_by_name('image_tensor:0')

	# Each box represents a part of the image where a particular object was detected.
	boxes = self._detection_graph.get_tensor_by_name('detection_boxes:0')

	# Each score represent how level of confidence for each of the objects.
	# Score is shown on the result image, together with the class label.
	scores = self._detection_graph.get_tensor_by_name('detection_scores:0')
	classes = self._detection_graph.get_tensor_by_name('detection_classes:0')
	num_detections = self._detection_graph.get_tensor_by_name('num_detections:0')

	# Actual detection.
	(boxes, scores, classes, num_detections) = self._sess.run(
	    [boxes, scores, classes, num_detections],
	    feed_dict={image_tensor: image_np_expanded})

	# Only show boxes around these classes
	for i in range(len(scores[0])):
	    if self.category_index[classes[0][i]]['name'] not in ALLOWED_CLASSES:
	        scores[0][i] = 0

        vis_util.visualize_boxes_and_labels_on_image_array(
            image_np,
            np.squeeze(boxes),
            np.squeeze(classes).astype(np.int32),
            np.squeeze(scores),
            self.category_index,
            use_normalized_coordinates=True,
            line_thickness=8,
            min_score_thresh=DETECT_THRESHOLD)

        return image_np

    def detect_objects(self, image_np):
        '''
            Given an image, run the loaded model for inference to detect objects.
            Only classes define in defaults allowed_classes will be shown.

            Inputs::
              image_np: Numpy representation of image in question

            Outputs::
              class_box: Dictionary of detected object and related bounding boxes
        '''
	# Expand dimensions since the model expects images to have shape: [1, None, None, 3]
	image_np_expanded = np.expand_dims(image_np, axis=0)
	image_tensor = self._detection_graph.get_tensor_by_name('image_tensor:0')

	# Each box represents a part of the image where a particular object was detected.
	boxes = self._detection_graph.get_tensor_by_name('detection_boxes:0')

	# Each score represent how level of confidence for each of the objects.
	# Score is shown on the result image, together with the class label.
	scores = self._detection_graph.get_tensor_by_name('detection_scores:0')
	classes = self._detection_graph.get_tensor_by_name('detection_classes:0')
	num_detections = self._detection_graph.get_tensor_by_name('num_detections:0')

	# Actual detection.
	(boxes, scores, classes, num_detections) = self._sess.run(
	    [boxes, scores, classes, num_detections],
	    feed_dict={image_tensor: image_np_expanded})

        class_box = {}
        confidence_scores = {}
        max_width = 0

	# Only show boxes around these classes
	for i in range(len(scores[0])):
	    if self.category_index[classes[0][i]]['name'] not in ALLOWED_CLASSES:
	        scores[0][i] = 0
            else:
		if scores[0][i] >= DETECT_THRESHOLD:
		    obj = self.category_index[classes[0][i]]['name']
		    if obj == 'person':
			box = np.squeeze(boxes[0][i])
			width = abs(box[3] - box[1])
			if width < max_width:
			    continue
			max_width = width
		    class_box[obj] = np.squeeze(boxes[0][i])
            confidence_scores[obj] = scores[0][i]
        return class_box, confidence_scores

    def load_tf_graph(self):
        self._detection_graph = tf.Graph()
        with self._detection_graph.as_default():
            od_graph_def = tf.GraphDef()
	    with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
		serialized_graph = fid.read()
		od_graph_def.ParseFromString(serialized_graph)
		tf.import_graph_def(od_graph_def, name='')

        self._sess = tf.Session(graph=self._detection_graph)

    def cleanup(self):
        self._sess.close()
