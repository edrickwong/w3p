import os
import cv2
import time
import argparse
import multiprocessing
import numpy as np
import socket
import tensorflow as tf

from utils.app_utils import FPS, WebcamVideoStream
from utils.misc_utils import is_using_tensorflow_gpu
# I know the below is bad practice (importing *)
# TODO: Right a proper configManager to load in defaults
from utils.defaults import *
from utils.worker_utils import MessageWorker, OutputImageStreamWorker, \
                               ObjectDetectoResponseWorker

from multiprocessing import Queue, Pool, Process
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as vis_util

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
    parser.add_argument('-vis','--visualize', type=bool,
                        default=True, help='Object to search for.')
    parser.add_argument('-d', '--debug', type=bool,
                        default=False, help='if in debug mode or not.')
    args = parser.parse_args()

    # boolean to determine if inference should be visualized
    visualize_output = args.visualize

    logger = multiprocessing.log_to_stderr()
    if args.debug:
        logger.setLevel(multiprocessing.SUBDEBUG)
    else:
        logger.setLevel(multiprocessing.SUBWARNING)

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

    # Video capture continuously
    video_capture = WebcamVideoStream(src=args.video_source,
                                      width=args.width,
                                      height=args.height).start()

    # Parent event loop
    logger.debug('Entering parent process event loop')
    while True:
        try:
            frame = video_capture.read()
            input_q.put(frame)

            if visualize_output:
                output_rgb = cv2.cvtColor(output_q.get(), cv2.COLOR_RGB2BGR)
                cv2.imshow('Video', output_rgb)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        except KeyboardInterrupt:
            break

    # TODO: Make kill process a multiproc semaphore/lock/signal that all the
    # processes can just interface with
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

    # Cleanup remaining resources
    video_capture.stop()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
