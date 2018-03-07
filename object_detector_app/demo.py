import os
import cv2
import time
import argparse
import multiprocessing
import numpy as np
import socket
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

logger = multiprocessing.log_to_stderr()

def get_my_camera_frame_specs(video_source):
    stream = cv2.VideoCapture(video_source)
    ret, frame = stream.read()
    if ret:
        height, width, _ = frame.shape
        stream.release()
        return height, width
    else:
        logger.warning('Unable to get input from camera source')
        raise Exception('Unable to setup camera')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-src', '--source', dest='video_source', type=int,
                        default=0, help='Device index of the camera.')
    # opencv doesnt allow me to set these parameters off hand
    #parser.add_argument('-wd', '--width', dest='width', type=int,
    #                    default=480, help='Width of the frames in the video stream.')
    #parser.add_argument('-ht', '--height', dest='height', type=int,
    #                    default=360, help='Height of the frames in the video stream.')
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

    # HACK:: Anshuman 03/06/18
    # Since CV2 doesn't respect frame width and height dimensions across
    # all cameras, we need to be able to support normalized components
    # unfortunately, what that means is that we need to capture the width
    # and height in the input stream and let the other workers know about
    # what the width/height of the expected frame is, so we are going to
    # open the video stream, read the frame and get the specs as part of
    # the setup process. before actually forking
    logger.warning('Gathering information about your specific camera..')
    video_source = args.video_source
    height, width = get_my_camera_frame_specs(video_source)
    logger.warning('Finished gathering information..')

    logger.warning('Spawning all relevant workers')
    # input stream worker
    input_worker = InputFrameWorker(input_q,
                                    video_source)
    input_worker.start()

    # output stream workers, required to visualize inference on the
    # fly
    if visualize_output:
        output_image_stream_workers = []
        for _ in xrange(num_workers):
            worker = OutputImageStreamWorker(input_q, output_q, width, height)
            worker.start()
            output_image_stream_workers.append(worker)

    # workers required to interface with google home/flask client
    msg_worker = MessageWorker(request_q, message_q)
    msg_worker.start()
    response_worker = ObjectDetectoResponseWorker(input_q, request_q, message_q,
                                                  width, height)
    response_worker.start()

    # Parent event loop
    logger.debug('Entering parent process event loop')
    while True:
        try:
            if visualize_output:
                output_rgb = cv2.cvtColor(output_q.get(), cv2.COLOR_RGB2BGR)
                cv2.imshow('Video', output_rgb)
                #logger.warning('Showing output')
                #logger.warning(output_rgb.shape)
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
