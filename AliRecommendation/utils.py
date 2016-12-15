#!/usr/local/bin/python3
# coding: UTF-8
# Author: David
# Email: youchen.du@gmail.com
# Created: 2016-12-09 20:11
# Last modified: 2016-12-15 09:57
# Filename: utils.py
# Description:
__metaclass__ = type
import time
import logging
import sys
import pickle

from logging import info
from collections import defaultdict


fmt = '%(asctime)s %(levelname)s %(message)s'
date_fmt = '%d %m %Y %H:%M:%S'
logging.basicConfig(
    level=logging.DEBUG, filename='solution.log',
    format=fmt, datefmt=date_fmt)
MODELS = ['LR', 'RF', 'GBDT', 'KNN']

log = logging.getLogger()
stdout_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(fmt, datefmt)
stdout_handler.setFormatter(formatter)
log.addHandler(stdout_handler)


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
        if self.percent < 1:
            self.percent = 1
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


@timeit
def save_to_file(obj, f):
    info('Saving %s...' % f)
    _f = open(f, 'wb')
    pickle.dump(obj, _f)


@timeit
def load_from_file(f):
    info('Loading %s...' % f)
    _f = open(f, 'rb')
    return pickle.load(_f)

@timeit
def gen_submits(precision):
    lines = []
    with open('ans.txt', 'r') as f:
        for line in f:
            data, pre = line.strip('\n').rsplit(',', 1)
            pre = float(pre)
            if pre >= precision:
                lines.append(data)

    info('Generating submits...')
    pro = Progress(len(lines))
    with open('dutir_tianchi_recom_predict_david.txt', 'w') as f:
        for line in lines:
            pro.next()
            f.write(line+'\n')
    pro.end()


@timeit
def groupby(data_set, index):
    info('Grouping data...')
    group_dict = defaultdict(list)
    size = len(data_set)
    pro = Progress(size)
    for line in data_set:
        pro.next()
        key = line[index]
        group_dict[key].append(line)
    pro.end()

    return group_dict


@timeit
def sorton(group_dict):
    info('Sorting data...')
    size = len(group_dict.keys())
    pro = Progress(size)
    for value in group_dict.values():
        pro.next()
        value.sort(key=lambda x: (x[2], x[5]), reverse=True)
    pro.end()


def date_shift(ta=None, tb=None):
    ta = list(map(lambda x: int(x), ta))
    tb = list(map(lambda x: int(x), tb))
    shift = 0
    shift += (ta[0]-tb[0])*30
    shift += ta[1]-tb[1]
    shift += 1 if ta[2] >= tb[2] else 0
    return shift


@timeit
def save_prediction(user_items, predicts, min_probe=0.5):
    with open('ans.txt', 'w') as f:
        size = len(user_items)
        pro = Progress(size)
        for (uid, iid), probe in zip(user_items, predicts):
            pro.next()
            if probe >= min_probe:
                f.write('%s,%s,%.2f\n' % (uid, iid, probe))
        pro.end()
