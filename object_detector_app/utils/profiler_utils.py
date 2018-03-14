import socket
import numpy as np

from datetime import datetime
from multiprocessing import get_logger
from random import choice

from defaults import *

logger = get_logger()

class Timer(object):
    def __init__(self, file_name):
        # open file handle with no buffer, cuz we can't seem to cleanly close
        # the file handle from the fact that we can't catch ctrl-c properly..
        # without any buffering, the data will be written instantly to file
        self._f = open(file_name, 'wb', 0)
        self.start_time = None

        self.cur_flush_count = 0

    def start(self):
        self.start_time = datetime.now()

    def stop(self):
        time_elapsed = (datetime.now() - self.start_time).microseconds / 1000
        logger.debug('time elapsed: %s' %(time_elapsed))
        self._f.write('%s\n' %(time_elapsed))
        # reset
        self.reset()

    def reset(self):
        self.start_time = None

    def cleanup(self):
        self._f.close()

class Profiler(object):
    ALLOWED_ITEMS = ["bottle", "cup", "bowl"]

    def __init__(self, iterations=1000, *args, **kwargs):
        # First iteration doesnt count, it will take longer
        # because of the opencv hack we have in place, so adding +1 here
        # to compensate, same in the summarizer
        self.iterations = iterations + 1

        # pop out socket info or use global defined here
        self.tcp_ip = kwargs.pop('tcp_ip', TCP_IP)
        self.tcp_port = kwargs.pop('tcp_port', TCP_PORT)
        self.buffer_size = kwargs.pop('buffer_size', BUFFER_SIZE)

        # also setup socket information here
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect_to_socket()

    def run_test(self):
        for i in xrange(self.iterations):
            if i % int((0.1 * (self.iterations - 1))) == 0:
                logger.warning('Iteration: %s/%s' %(i, self.iterations))
            item = choice(self.ALLOWED_ITEMS)
            self._socket.send(item)
            reply = self._socket.recv(self.buffer_size)

        self._socket.close()

    def connect_to_socket(self):
        while True:
            try:
                self._socket.connect((self.tcp_ip, self.tcp_port))
                break
            except:
                logger.warning('Socket not ready yet, trying in 5s')
                time.sleep(5)

    def print_summary_results(self):
	print "\n ----- SUMMARY -------- \n"
        print "Message worker results:"
        self.print_results_for_file(MESSAGE_WORKER_TIMES_FILE)

        print "\n\nObject detector worker results:"
        self.print_results_for_file(OBJECT_DETECT_TIMES_FILE)

    def print_results_for_file(self, file_name):
        with open(file_name) as f:
            data = f.read()

        try:
            # Ignore first run to account for bootstrapping of helpers
            # due to OpenCV bug
            data = [int(x) for x in data.split()[1:]]
        except Exception as e:
            logger.critical('Unable to parse log file')
            logger.critical(e)
            return

        data = np.array(data, dtype=np.float)
	print "Average runtime: %s ms" %(np.average(data))
	print "Std Dev: %s ms " %(np.std(data))
	print "95th percentile: %s ms" %(np.percentile(data, 95))
	print "99th percentile: %s ms" %(np.percentile(data, 99))
