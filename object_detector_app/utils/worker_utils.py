import multiprocessing
from multiprocessing import Queue, Pool, Process
from user_feedback_utils import UserFeedbackGenerator

# TODO: Split globals up inot their own file ie. a ConfigManager of sorts
# socket globals
TCP_IP = '127.0.0.1'
TCP_PORT = 1315
BUFFER_SIZE = 1024
ALLOWED_CLASSES = ['person','bottle','knife','spoon','fork','cup','bowl','dog']


class MessageWorker(Process):
    '''
        TODO: add comments, its 2AM, i will add comments tomorrow
    '''
    def __init__(self, request_q, message_q, **kwargs):
        # pop out socket info or use global defined here
        self.tcp_ip = kwargs.pop(tcp_ip, TCP_IP)
        self.tcp_port = kwargs.pop(tcp_port, TCP_PORT)
        self.buffer_size = kwargs.pop(buffer_size, BUFFER_SIZE)

        # init parent with remaining kwargs
        # we want to do this init first so we can fail on the parent's
        # exception before having to throw our own exception after.
        super(MessageWorker, self).__init__(**kwargs)
        self.request_q = request_q
        self.message_q = message_q

        # also setup socket information here
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.bind(tcp_ip, tcp_port)
        self._socket.listen(1)
        self._conn = None

        # boolean to see if we should end the event loop
        self.kill_process = False

    def run(self):
        # Wait for incoming connection before doing anything
        self.wait_for_incoming_connection()

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
    pass


class ObjectDetectorWorker(Process):
    pass

