#!/usr/local/bin/python3
# coding: UTF-8
# Author: David
# Email: youchen.du@gmail.com
# Created: 2016-12-09 20:11
# Last modified: 2016-12-31 10:06
# Filename: utils.py
# Description:
import time
import logging
import sys
import pickle
import os

from logging import info, error
from datetime import timedelta
from datetime import datetime
from collections import defaultdict


fmt = '%(asctime)s %(levelname)s %(message)s'
date_fmt = '%d %m %Y %H:%M:%S'
logging.basicConfig(
    level=logging.DEBUG, filename='AliRec.log',
    format=fmt, datefmt=date_fmt)
MODELS = ['LR', 'RF', 'GBDT', 'KNN']
MODEL_PATH = 'models/'

d1 = timedelta(1)
date_1217 = datetime.strptime('2014-12-17', '%Y-%m-%d').date()

log = logging.getLogger()
stdout_handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(fmt, date_fmt)
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
        self.idx = 1
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
        if self.idx == self.max_times:
            sys.stdout.write('\n')


@timeit
def save_to_file(obj, f, prefix='', suffix='.model'):
    path = MODEL_PATH+prefix+f+suffix
    info('Saving %s' % path)
    _f = open(path, 'wb')
    pickle.dump(obj, _f)


@timeit
def load_from_file(f, prefix='', suffix='.model'):
    path = MODEL_PATH+prefix+f+suffix
    info('Loading %s' % path)
    _f = open(path, 'rb')
    return pickle.load(_f)


def file_retrive(file_path, prefix='', suffix='.model'):
    path = MODEL_PATH+prefix+file_path+suffix
    info('Loading %s' % path)
    if os.path.exists(path):
        try:
            with open(path, 'rb') as _f:
                model = pickle.load(_f)
        except Exception as e:
            error(e)
            return None, False
        else:
            return model, True
    else:
        return None, False


@timeit
def load_subitems(path='tianchi_mobile_recommend_train_item.csv'):
    info('loading subset items')
    items = []
    with open(path, 'r') as f:
        labels = f.readline().strip('\n').split(',')
        for line in f:
            data = line.strip('\n').split(',')
            items.append(data[0])
    return items, labels


@timeit
def gen_submits(precision):
    info('Generating submits')
    lines = []
    with open('ans.txt', 'r') as f:
        for line in f:
            uid, iid, pre = line.strip('\n').rsplit(',')
            pre = float(pre)
            data = [uid, iid]
            if pre >= precision:
                lines.append(data)

    sub_items, _ = load_subitems()
    pro = Progress(len(lines))
    info('Writing submits to file')
    with open('dutir_tianchi_recom_predict_david.txt', 'w') as f:
        for uid, iid in lines:
            pro.next()
            if iid in sub_items:
                f.write(uid+','+iid+'\n')
    pro.end()


@timeit
def groupby(data_set, index):
    info('Grouping data')
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
    info('Sorting data')
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
def save_prediction(uis, predicts, min_probe=0.5):
    with open('ans.txt', 'w') as f:
        size = len(user_items)
        pro = Progress(size)
        for (uid, iid), probe in zip(user_items, predicts):
            pro.next()
            if probe >= min_probe:
                f.write('%s,%s,%.2f\n' % (uid, iid, probe))
        pro.end()
