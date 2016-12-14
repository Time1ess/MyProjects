#!/usr/local/bin/python3
# coding: UTF-8
# Author: David
# Email: youchen.du@gmail.com
# Created: 2016-12-03 20:09
# Last modified: 2016-12-04 19:34
# Filename: dataset.py
# Description:
import time
import logging
import sys

from logging import info
from collections import defaultdict

from models import User, Weibo
from utils import timeit

logging.basicConfig(
    stream=sys.stdout, level=logging.DEBUG,
    format=('%(asctime)s %(filename)s [line:%(lineno)d] '
            '%(levelname)s %(message)s'),
    datefmt='%a, %d %b %Y %H:%M:%S')


@timeit
def load_users(path='train/train_labels.txt'):
    users = []
    with open(path, 'r') as f:
        for line in f:
            u = User(*line.strip('\n').split('||'))
            users.append(u)
    return users


@timeit
def load_fans(path='train/train_links.txt'):
    fans = {}
    with open(path, 'r') as f:
        for line in f:
            user, *rest = line.strip('\n').split(' ')
            fans[user] = rest
    return fans


@timeit
def load_weiboes(path='train/train_status.txt'):
    weiboes = defaultdict(list)

    with open(path, 'r') as f:
        for line in f:
            uid, *rest = line.strip('\n').split(',', 5)
            wb = Weibo(*rest)
            weiboes[uid].append(wb)
    return weiboes


@timeit
def load_stopwords(path='stopwords.txt'):
    stopwords = {}
    with open(path, 'r') as f:
        for line in f:
            word = line.strip('\n')
            stopwords[word] = True
    return stopwords


@timeit
def load_dataset():
    info('Load users')
    users = load_users()
    # info('Load fans')
    # fans = load_fans()
    info('Load weiboes')
    weiboes = load_weiboes()
    # info('Load stopwords')
    # stopwords = load_stopwords()

    info('Load valid users')
    valid_users = load_users('valid/valid_nolabel.txt')
    info('Load valid weiboes')
    valid_weiboes = load_weiboes('valid/valid_status.txt')

    return users, weiboes, valid_users, valid_weiboes


@timeit
def test():
    s = time.time()
    load_users()
    e = time.time()
    print('Load labels costs: %.2f s' % (e-s))
    s = time.time()
    load_fans()
    e = time.time()
    print('Load fans costs: %.2f s' % (e-s))
    s = time.time()
    load_weiboes()
    e = time.time()
    print('Load fans costs: %.2f s' % (e-s))


def main():
    load_dataset()


if __name__ == '__main__':
    main()
