import cv2
import multiprocessing
import socket
import tensorflow as tf

from defaults import *
from multiprocessing import Queue, Pool, Process
#from user_feedback_utils import UserFeedbackGenerator
from object_detector_utils import ObjectDetector


class MessageWorker(Process):
    '''
        TODO: add comments, its 2AM, i will add comments tomorrow
    '''
    def __init__(self, request_q, message_q, *args, **kwargs):
        # pop out socket info or use global defined here
        self.tcp_ip = kwargs.pop('tcp_ip', TCP_IP)
        self.tcp_port = kwargs.pop('tcp_port', TCP_PORT)
        self.buffer_size = kwargs.pop('buffer_size', BUFFER_SIZE)

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
        self._conn = None

        # boolean to see if we should end the event loop
        self.kill_process = False

    def run(self):
        # Wait for incoming connection before doing anything
        self.wait_for_incoming_connection()

        # Enter Event loop
        while not self.kill_process:
            request_data = self._conn.recv(self.buffer_size)
            print request_data

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
		print obj

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
	    self._conn.send(msg)
	    print(msg)

    def wait_for_incoming_connection(self):
        while not self._conn:
            self._conn, _ = self._socket.accept()
            print 'Waiting on mock connection from Google Assistant'
            time.sleep(1)


class OutputImageStreamWorker(Process):
    '''
        TODO: Add comments
    '''
    def __init__(self, img_input_q, img_output_q, *args, **kwargs):
        super(OutputImageStreamWorker, self).__init__(*args, **kwargs)
        self.input_img_q = img_input_q
        self.output_img_q = img_output_q

        # FOR SOME GOD DAMN REASON TENSORFLOW ISN'T FORK SAFE
        # SO CAN'T INITIALIZE HERE, HAVE TO INIT AFTER THE PARENT
        # HAS FORKED INTO CHILD...
        self._object_detector = None

        # Bool to kill event loop
        self.kill_process = False

    def run(self):
        self._object_detector = ObjectDetector()

        # Enter Event loop for worker
        while not self.kill_process:
            # grab most recent frame img_input_q and convert to RGB
            # as expected by model
            frame = self.input_img_q.get()
	    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # do inference for frame capture
	    out_image = self._object_detector.detect_objects_visualize(frame_rgb)
            self.output_img_q.put(frame_rgb)

        # should do with __enter__ and __exit__ methods, but w.e for now
        self._object_detector.cleanup()


class ObjectDetectoResponseWorker(Process):
    def __init__(self, img_input_q, request_q, message_q, *args, **kwargs):
        super(ObjectDetectoResponseWorker, self).__init__(*args, **kwargs)
        self.input_img_q = img_input_q
        self.request_q = request_q
        self.message_q = message_q

        # FOR SOME GOD DAMN REASON TENSORFLOW ISN'T FORK SAFE
        # SO CAN'T INITIALIZE HERE, HAVE TO INIT AFTER THE PARENT
        # HAS FORKED INTO CHILD...
        self._object_detector = None

        # Bool to kill event loop
        self.kill_process = False

    def run(self):
	# Load object detector after parent process forks
        self._object_detector = ObjectDetector()

        # Enter Event loop for worker
        while not self.kill_process:
            # block until the MessageWorker puts something in the
            # request_q
            obj_to_find = self.request_q.get()

            # grab most recent frame img_input_q and convert to RGB
            # as expected by model
            frame = self.input_img_q.get()
	    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # do inference for frame capture
	    detected_objects = self._object_detector.detect_objects(frame_rgb)

            # construct message that we should pass back to user based on
            # detected objects
            msg = self.build_msg(detected_objects)

            # add msg to message_q
            self.message_q.put(msg)

        self._object_detector.cleanup()

    def build_msg(self, obj_to_find, detected_objects):
        msg = ''

	if 'person' not in detected_objects:
            msg = 'Cannot locate user.'
	elif obj_to_find not in detected_objects:
	    msg = 'Unable to locate %s in current view' %(obj_to_find)
	else:
	    mid_p = (detected_objects.get('person')[1] \
			+ detected_objects.get('person')[3])/2
	    mid_o = (detected_objects.get(obj)[1] \
		    + detected_objects.get(obj)[1])/2
	    if mid_p < mid_o:
		msg = obj_to_find + ' is to your left'
	    else:
		msg = obj_to_find + ' is to your right'

        return msg

    def load_stationary_objects(self):
        pass
