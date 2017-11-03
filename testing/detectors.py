import sys
import os
import datetime
import pickle
import numpy as np
from subprocess import Popen, PIPE

class ObjectDetector(object):
    '''
        Base Class, all object detectors testing should inherit
        from this class
    '''
    def __init__(self):
        self.execution_times = []

    def detect_object(self):
        raise NotImplementedError('Should be overidden in class')


class CmdObjectDetector(ObjectDetector):
    '''
        Command Line Object detector class. Any detection algorithms
        we use that cannot directly be called from python with a hook,
        for now will be called using subprocess and the stdout
        will be processed to return data

        We define execution time of one run as the amount of time
        the subprocess to complete ie. once the process returns.
        Don't count the parsing time as part of execution time,
        because we might be able to change the underlying output
        to speed up the parsing.
    '''
    def __init__(self):
        super(CmdObjectDetector, self).__init__()

    def parse_out(self):
        raise NotImplementedError('Should be overriden in child')


class YoloDarknet(CmdObjectDetector):
    def __init__(self, yolo_type, base_cmd):
        super(YoloDarknet, self).__init__()
        self.yolo_type = yolo_type # tiny, normal
        self.base_cmd = base_cmd
        self.stdout = None # Store stdout most recent run
        self.objects_detected = {} # Parsed objects
        self.total_runs = 0
        self.successes = 0
        self.cur_iteration = 0

    def parse_out(self):
        if not self.stdout:
            print 'No stdout, returning'

        # seperate into lines
        stdout = self.stdout.strip().split('\n')

        # First Line is the time taken
        try:
            execution_time = float(stdout[0].split()[-2])
            self.execution_times.append(execution_time)
        except Exception as e:
            print 'Unable to get time taken'
            print stdout
            return

        # Remaining lines are all the objects detected
        try:
            for l in stdout[1:]:
                obj, probability = l.split(':')
                probability = probability.replace('%', '')
                self.objects_detected[obj] = float(probability)
        except Exception as e:
            print 'Unable to parse output properly'
            print stdout
            return

        # if we return here, means we were able to parse the output
        # this is a successful run
        self.total_runs += 1

    def run_single(self, img_file):
        # build cmd with img_file
        cmd = self.base_cmd + " %s" %(img_file)

        p = Popen(cmd, stdout=PIPE, stderr=PIPE, shell=True)
        self.stdout, stderr = p.communicate()

        # catch any weird errors
        if p.returncode != 0:
            print 'Invalid returncode: '
            print stdout
            print stderr
            return

        self.parse_out()

    #def run(self, folder, item):
    #    # each folder should contain images with a kitchen item
    #    # in question
    #    pass

    def run(self, img_file='data/dog.jpg', iterations=20):
        for i in xrange(iterations):
            print_bucket = iterations/4
            if i % print_bucket == 0:
                print '%s/%s' %(i, iterations)
            self.cur_iteration = i
            self.run_single(img_file)

    # dump data so we don't lose results ever
    def dump_data(self):
        now = datetime.datetime.now().strftime('%s')
        with open('out_%s_%s.pik' %(self.yolo_type, now), 'w') as f:
            pickle.dump(self.execution_times, f)

    def print_summary(self):
        try:
            self.execution_times = np.array(self.execution_times, dtype=np.float)
            print "Average runtime: %ss" %(np.average(self.execution_times))
            print "Std Dev: %ss " %(np.std(self.execution_times))
            print "95th percentile: %ss" %(np.percentile(self.execution_times, 95))
            print "99th percentile: %ss" %(np.percentile(self.execution_times, 99))

        except Exception as e:
            print "failed on %s" %(self.cur_iteration)
            self.dump_data()
            self.print_summary()
            print e
            import pdb ; pdb.set_trace()
