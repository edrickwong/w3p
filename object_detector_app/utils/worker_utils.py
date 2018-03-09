import cv2
import multiprocessing
import socket
import tensorflow as tf
import time

from defaults import *
from multiprocessing import Queue, Pool, Process
from object_detector_utils import ObjectDetector
from profiler_utils import Timer
from utils.app_utils import WebcamVideoStream
from reference_objects_utils import ReferenceObjectsHelper

# logger object for more succicnt output
logger = multiprocessing.get_logger()

class MessageWorker(Process):
    '''
        TODO: add comments, its 2AM, i will add comments tomorrow
    '''
    def __init__(self, request_q, message_q, *args, **kwargs):
        # pop out socket info or use global defined here
        self.tcp_ip = kwargs.pop('tcp_ip', TCP_IP)
        self.tcp_port = kwargs.pop('tcp_port', TCP_PORT)
        self.buffer_size = kwargs.pop('buffer_size', BUFFER_SIZE)

        # check if profiler has been specified
        self.profile = kwargs.pop('profile', False)
        if self.profile:
            logger.warning('Profile has been specified, adding timers to event loop')
            self._timer = None

        # init parent with remaining kwargs
        # we want to do this init first so we can fail on the parent's
        # exception before having to throw our own exception after.
        super(MessageWorker, self).__init__(*args, **kwargs)
        self.request_q = request_q
        self.message_q = message_q

        # also setup socket information here
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind((self.tcp_ip, self.tcp_port))
        self._socket.listen(1)
        self._socket.settimeout(5)
        self._conn = None

        # boolean to see if we should end the event loop
        self.kill_process = False
        self.daemon = True

    def run(self):
        # Wait for incoming connection before doing anything
        self.wait_for_incoming_connection()

        # add timer
        if self.profile:
            self._timer = Timer(MESSAGE_WORKER_TIMES_FILE)

        # Enter Event loop
        logger.debug('Entering event loop for Message Worker')
        while not self.kill_process:
            if self.profile:
                self._timer.start()

            request_data = self._conn.recv(self.buffer_size)
            logger.debug('Request data: %s' %(request_data))
            #print request_data

	    # find object that user is asking for
            obj = None

	    # parse the incoming message
	    for word in request_data.split():
		if word in ALLOWED_CLASSES:
                    # TODO: if the user asks for something that isn't allowed
                    # ie. obj is None after this loop, we should do something
                    # either ask user to repeat or something, this is currently
                    # terrible UX.
		    obj = word
		    break

	    if obj:
		self.request_q.put(obj)
		# print obj

            # TODO: The code below makes an assumption that the flop from request_q
            # to message_q will always work, so in case the request_q fails for
            # some reason, we have no projtection here (because we are going to
            # be sending back an empty message)
            # Solutions:
            #     a) Implement a Timeout (remember we are bounded by a 5s
            #        timeout upstream from google home)
            #     b) more complicated solution would be to use a multiproc lock
            #        ie. we spin until we here from the above procs (similar
            #        to using signals in threads)
	    msg = self.message_q.get()
            logger.debug(msg)
	    self._conn.send(msg)
            if self.profile:
                self._timer.stop()

        if self.profile:
            self._timer.cleanup()

        # clean up socket on close
        logger.debug('Closing socket connection')
        self._conn.close()

    def wait_for_incoming_connection(self):
        while not self._conn:
            try:
                self._conn, _ = self._socket.accept()
                logger.warning('Accepted connection from: %s' %(self._conn))
            except socket.timeout:
                logger.warning('Waiting on connection from Google Assistant')
                time.sleep(1)


class InputFrameWorker(Process):
    '''
        TODO: Add comments
    '''
    def __init__(self, img_input_q, video_source,
                 *args, **kwargs):
        super(InputFrameWorker, self).__init__(*args, **kwargs)
        self.img_input_q = img_input_q
        #self.test_stream()
        self.video_source = video_source

        # kill switch
        self.kill_process = False
        self.daemon = True

    def run(self):
        logger.debug('Entering event loop for input worker')
        self._stream = cv2.VideoCapture(self.video_source)
        # OpenCV doesnt respect these width/height parameters
        #self._stream.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        #self._stream.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        while not self.kill_process:
            logger.warning(self.kill_process)
            ret, frame = self._stream.read()
            if ret:
                self.img_input_q.put(frame)
            else:
                logger.warning('Unable to grab input frame')

    def test_stream(self):
        captured, frame = self._stream.read()
        if not captured:
            logger.debug('Unable to capture stream')


class OutputImageStreamWorker(Process):
    '''
        TODO: Add comments
    '''
    def __init__(self, img_input_q, img_output_q,
                 *args, **kwargs):
        super(OutputImageStreamWorker, self).__init__(*args, **kwargs)
        self.input_img_q = img_input_q
        self.output_img_q = img_output_q

        # FOR SOME GOD DAMN REASON TENSORFLOW ISN'T FORK SAFE
        # SO CAN'T INITIALIZE HERE, HAVE TO INIT AFTER THE PARENT
        # HAS FORKED INTO CHILD...
        self._object_detector = None
        self._ref_obj_helper = None

        # Bool to kill event loop
        self.kill_process = False
        self.daemon = True

    def run(self):
        # encapsulate the necessary helper objects
        self._object_detector = ObjectDetector()
        self._ref_obj_helper = None

        # Enter Event loop for worker
        while not self.kill_process:
            # grab most recent frame img_input_q and convert to RGB
            # as expected by model
            frame = self.input_img_q.get()

            # HACK:: Anshuman 03/08/2019
            # We need the dimensions of the frames, since OpenCV can't actually
            # set the width/height for the camera input across all cameras.
            # So we are going to look at the input frame to determine the size
            # needed, so we can pass in normalized coordinates but work
            # with denormalized/real coordinates.
            if not self._ref_obj_helper:
                height, width, _ = frame.shape
                self._ref_obj_helper = ReferenceObjectsHelper(width, height)

	    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            logger.debug('got input frame')
            # do inference for frame capture
	    out_image = self._object_detector.detect_objects_visualize(frame_rgb)
            self._ref_obj_helper.visualize_reference_objects(out_image)
            self.output_img_q.put(out_image)

        # should do with __enter__ and __exit__ methods, but w.e for now
        self._object_detector.cleanup()


class ObjectDetectoResponseWorker(Process):
    '''
        TODO: Add comments
    '''
    def __init__(self, img_input_q, request_q, message_q,
                 *args, **kwargs):

        # check if profiler has been specified
        self.profile = kwargs.pop('profile', False)
        if self.profile:
            logger.warning('Profile has been specified, adding timers to event loop')
            self._timer = None

        super(ObjectDetectoResponseWorker, self).__init__(*args, **kwargs)
        self.input_img_q = img_input_q
        self.request_q = request_q
        self.message_q = message_q

        # FOR SOME GOD DAMN REASON TENSORFLOW ISN'T FORK SAFE
        # SO CAN'T INITIALIZE HERE, HAVE TO INIT AFTER THE PARENT
        # HAS FORKED INTO CHILD...
        self._object_detector = None
        self._ref_obj_helper = None

        # Bool to kill event loop
        self.kill_process = False
        self.daemon = True

    def run(self):
	# Load object detector after parent process forks
        self._object_detector = ObjectDetector()

        if self.profile:
            self._timer = Timer(OBJECT_DETECT_TIMES_FILE)

        # Enter Event loop for worker
        logger.debug('Entering event loop for object detector response worker')
        while not self.kill_process:
            if self.profile:
                self._timer.start()
            # block until the MessageWorker puts something in the
            # request_q
            obj_to_find = self.request_q.get()

            # grab most recent frame img_input_q and convert to RGB
            # as expected by model
            frame = self.input_img_q.get()

            # HACK:: Anshuman 03/08/2019
            # We need the dimensions of the frames, since OpenCV can't actually
            # set the width/height for the camera input across all cameras.
            # So we are going to look at the input frame to determine the size
            # needed, so we can pass in normalized coordinates but work
            # with denormalized/real coordinates.
            if not self._ref_obj_helper:
                height, width, _ = frame.shape
                self._ref_obj_helper = ReferenceObjectsHelper(width, height)

	    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # do inference for frame capture
	    detected_objects, confidence_scores = self._object_detector.detect_objects(frame_rgb)

            # construct message that we should pass back to user based on
            # detected objects
            msg = self.build_msg(obj_to_find, detected_objects, confidence_scores)

            # add msg to message_q
            self.message_q.put(msg)
            if self.profile:
                self._timer.stop()

        if self.profile:
            self._timer.cleanup()
        self._object_detector.cleanup()

    def closest_left_edge_distance(self,obj_xmin, obj_xmax,ref_xmin,ref_xmax):
        #check if object is infront of reference
        #
        #
        # YO DAMN LOGIC NOT CORRECT HERE
        if ref_xmin <= obj_xmin <= ref_xmax:
            print('left edge numbers: 0')
            return 0
        else:
            #if reference is left of object, should return negative distance
            print('left edge numbers')
            print('obj_xmin :' + str(obj_xmin))
            print('obj_xmax: ' + str(obj_xmax))
            print('ref_xmax: ' + str(ref_xmax))
            print(ref_xmax-obj_xmin)
            return obj_xmin-ref_xmax

    def closest_right_edge_distance(self,obj_xmin, obj_xmax,ref_xmin,ref_xmax):
        #check if object is infront of reference
        if ref_xmin <= obj_xmax <= ref_xmax:
            print('right edge numbers: 0')
            return 0
        else:
            #if reference is right of object, should return negative distance
            print('right edge numbers')
            print('obj_xmin: ' + str(obj_xmin))
            print('obj_xmax: ' + str(obj_xmax))
            print('ref_xmax: ' + str(ref_xmin))
            print(ref_xmin-obj_xmax)
            return obj_xmax-ref_xmin

    def calculate_nearest_reference(self, obj_to_find, detected_objects):
        '''
        returns
            distance to closest reference object edge
            reference is left or right (0:left, 1:right)
        '''
        self.ref_list = self._ref_obj_helper.reference_objects

        obj_x = [detected_objects.get(obj_to_find)[1],
                detected_objects.get(obj_to_find)[3]]
        obj_y = [detected_objects.get(obj_to_find)[0],
                detected_objects.get(obj_to_find)[2]]

        left_distances = [self.closest_left_edge_distance(obj_x[0],obj_x[1], x.norm_xmin, x.norm_xmax)
                for x in self.ref_list]
        right_distances = [self.closest_right_edge_distance(obj_x[0],obj_x[1], x.norm_xmin, x.norm_xmax)
                for x in self.ref_list]

        if 0 in left_distances:
            return self.ref_list[left_distances.index(0)], 0, 0
        elif 0 in right_distances:
            return self.ref_list[right_distances.index(0)], 1, 0
        else:
            left_min = min(left_distances)
            right_min = min(right_distances)
            if left_min < right_min:
                return self.ref_list[left_distances.index(left_min)],0, left_min
            else:
                return self.ref_list[right_distances.index(right_min)],1, right_min


    def build_msg(self, obj_to_find, detected_objects, confidence_scores):
        msg = ''

        '''
            self.reference_objects has a list of
            ReferenceObject items that contain hard coded
            objects
        '''
	if 'person' not in detected_objects:
            msg = 'Cannot locate user.'
	elif obj_to_find not in detected_objects:
	    msg = 'Unable to locate %s in current view' %(obj_to_find)
	else:
	    # mid_p = (detected_objects.get('person')[1] \
		# 	+ detected_objects.get('person')[3])/2
	    # mid_o = (detected_objects.get(obj_to_find)[1] \
		#     + detected_objects.get(obj_to_find)[1])/2
	    # if mid_p < mid_o:
		# msg = obj_to_find + ' is to your left'
	    # else:
		# msg = obj_to_find + ' is to your right'
        # print msg
        # return msg
            uncertainty_threshold = 0.6
            uncertain_start = "I'm not certain but I think the {0}".format(obj_to_find)
            certain_start = "I see the {0} and it ".format(obj_to_find)
            reference, location, distance = self.calculate_nearest_reference(obj_to_find, detected_objects)
            if distance == 0:
                msg = " is in front of the " + reference.obj_type
            elif location == 0:
                msg = " is " + str(distance) + " left of " + reference.obj_type
            else:
                msg = " is " + str(distance) + " right of " + reference.obj_type


            msg = (uncertain_start + msg) if confidence_scores[obj_to_find] < uncertainty_threshold else (certain_start + msg)
        return msg
