import os
import cv2
import time
import argparse
import multiprocessing
import numpy as np
import os
import socket
import signal
import sys
import subprocess
import tensorflow as tf

from utils.misc_utils import is_using_tensorflow_gpu
# I know the below is bad practice (importing *)
# TODO: Right a proper configManager to load in defaults
from utils.defaults import *
from utils.worker_utils import MessageWorker, OutputImageStreamWorker, \
                               ObjectDetectoResponseWorker, \
                               InputFrameWorker

from multiprocessing import Queue, Pool, Process
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util

def cleanup_existing_processes():
    grep_arg = 'python %s' %(sys.argv[0])
    cmd = 'ps aux | grep \'%s\' | grep -v grep' %(grep_arg)
    p = subprocess.Popen(cmd, shell=True,
                         stdout=subprocess.PIPE)
    out, err = p.communicate()
    pids_to_kill = []
    my_pid = os.getpid()

    for line in out.splitlines():
        if 'PID' in line:
            continue
        line = line.split()
        pid = int(line[1])
        #start_time = line[-4]
        # don't kill current process
        if pid != my_pid:
            pids_to_kill.append(pid)

    print 'Sending sigkill to pids: %s' %(pids_to_kill)
    for pid in pids_to_kill:
        os.kill(pid, signal.SIGKILL)

    if err:
        print err
        return False

    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-src', '--source', dest='video_source', type=int,
                        default=0, help='Device index of the camera.')
    parser.add_argument('-wd', '--width', dest='width', type=int,
                        default=480, help='Width of the frames in the video stream.')
    parser.add_argument('-ht', '--height', dest='height', type=int,
                        default=360, help='Height of the frames in the video stream.')
    parser.add_argument('-num-w', '--num-workers', dest='num_workers', type=int,
                        default=1, help='Number of workers.')
    parser.add_argument('-q-size', '--queue-size', dest='queue_size', type=int,
                        default=10, help='Size of the queue.')
    parser.add_argument('--visualize', dest='visualize',
                        action='store_true', help='show visualization')
    parser.add_argument('--no-visualize', dest='visualize',
                        action='store_false', help='do not show visualiation')
    parser.add_argument('--debug', dest='debug',
                        action='store_true', help='show visualization')
    parser.add_argument('--no-debug', dest='debug',
                        action='store_false', help='do not show visualiation')
    parser.set_defaults(debug=False)
    parser.set_defaults(visualize=True)
    args = parser.parse_args()

    # boolean to determine if inference should be visualized
    visualize_output = args.visualize
    logger = multiprocessing.log_to_stderr()
    if args.debug:
        logger.setLevel(multiprocessing.SUBDEBUG)
    else:
        logger.setLevel(multiprocessing.SUBWARNING)

    # cleanup existing processes..
    # All the underlying workers/threads are daemon threads/procs respectively.
    # This means that there is a chance that some of their resources, ie.
    # file handles and sockets haven't  been cleaned up gracefully because of
    # orphaned procs. Different kernels implement different methods of garbage
    # collection to cleanup these orphaned resources which might lead to some
    # unwanted/weird errors.
    logger.warning('Attempting to cleaning up any other instances of %s' \
                    %(sys.argv[0]))
    if cleanup_existing_processes():
        logger.warning('Cleaned up other processes, starting main app')
    else:
        logger.warning('Ran into unexpected error trying to close other procs' \
                       ' Continuing with the app')

    # override num workers if tensorflow gpu is being used
    num_workers = args.num_workers
    if is_using_tensorflow_gpu() and num_workers > 1:
        print "Using GPU, not allowed to multiproc workers."
        num_workers = 1

    # we need to moderate the number of workers that get spawned
    # for cpu depending on the number of cpus/vpcus avaiable
    # if not we are def going to run into some random perf
    # (too much context switching between IO filled workers
    else:
        num_workers = min(multiprocessing.cpu_count(),
                          num_workers)

    # need 4 queues to pass relevant information between the various
    # procs.
    input_q = Queue(maxsize=args.queue_size)
    output_q = Queue(maxsize=args.queue_size)
    request_q = Queue(maxsize=args.queue_size)
    message_q = Queue(maxsize=args.queue_size)

    # input stream worker
    input_worker = InputFrameWorker(args.video_source,
                                    args.width,
                                    args.height,
                                    input_q)
    input_worker.start()

    # output stream workers, required to visualize inference on the
    # fly
    if visualize_output:
        output_image_stream_workers = []
        for _ in xrange(num_workers):
            worker = OutputImageStreamWorker(input_q, output_q)
            worker.start()
            output_image_stream_workers.append(worker)

    # workers required to interface with google home/flask client
    msg_worker = MessageWorker(request_q, message_q)
    msg_worker.start()
    response_worker = ObjectDetectoResponseWorker(input_q, request_q, message_q)
    response_worker.start()

    # Parent event loop
    logger.debug('Entering parent process event loop')
    while True:
        try:
            if visualize_output:
                output_rgb = cv2.cvtColor(output_q.get(), cv2.COLOR_RGB2BGR)
                cv2.imshow('Video', output_rgb)
                #logger.debug('Showing output')
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        except KeyboardInterrupt:
            break

    # TODO: Make kill process a multiproc semaphore/lock/signal that all the
    # processes can just interface with
    input_worker.kill_process = True
    input_worker.join()
    msg_worker.kill_process = True
    msg_worker.join()
    response_worker.kill_process = True
    response_worker.join()

    # splitting the kill signal and join will lead to slightly more
    # concurrency
    if visualize_output:
        for worker in output_image_stream_workers:
            worker.kill_process = True

        for worker in output_image_stream_workers:
            worker.join()

    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
