#!/usr/local/bin/python3
# coding: UTF-8
# Author: David
# Email: youchen.du@gmail.com
# Created: 2016-12-09 20:11
# Last modified: 2016-12-13 17:06
# Filename: utils.py
# Description:
__metaclass__ = type
import time
import logging
import sys

from logging import info


logging.basicConfig(
    stream=sys.stdout, level=logging.DEBUG,
    format=('%(asctime)s %(levelname)s %(message)s'),
    datefmt='%d %m %Y %H:%M:%S')


def timeit(func):
    def _timeit(*args, **kwargs):
        s = time.time()
        ans = func(*args, **kwargs)
        e = time.time()
        info('Time cost for <%s>: %.2f s' % (func.__name__, e-s))
        return ans
    return _timeit


class Progress:
    def __init__(self, max_times):
        self.idx = 0
        self.max_times = max_times
        self.percent = int(max_times/100)
        self.t1 = time.time()

    def next(self):
        if self.idx % self.percent == 0:
            pro = int(100*self.idx/self.max_times)
            sys.stdout.flush()
            t = time.time()
            etas, etam, etah = [0]*3
            etas = (100-pro)*(t-self.t1)/pro if pro != 0 else 0
            eta_msg = '%2d s ' % ((1+etas)%60)
            if etas > 60:
                etam, etas = int(etas/60), etas%60
                if etam > 60:
                    etah, etam = int(etam/60), etam%60
            if etam:
                eta_msg = '%2d m ' % (etam%60) + eta_msg
            else:
                eta_msg = ' '*5+eta_msg
            if etah:
                eta_msg = '%2d h ' % (etah%24) + eta_msg
            else:
                eta_msg = ' '*5+eta_msg
            sys.stdout.write('>>> Progress: %2d %%\t\t\tETA: %s <<<\r' % (pro, eta_msg))
        self.idx += 1

    def end(self):
        sys.stdout.write('\n')
