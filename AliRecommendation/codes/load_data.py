#!/usr/local/bin/python3
# coding: UTF-8
# Author: David
# Email: youchen.du@gmail.com
# Created: 2016-12-17 09:38
# Last modified: 2016-12-31 09:36
# Filename: load_data.py
# Description:
import os
import argparse

from logging import info
from datetime import datetime

from utils import timeit, Progress, save_to_file, load_from_file, file_retrive

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('file_path', metavar='path', type=str,
                        help='Path to data file')
    parser.add_argument(
        '--cache', default=1, type=int, metavar='cache_type',
        help='Use 0 force to load data from file, default is 1')

    args = parser.parse_args()

    data_file = args.file_path
    cache = args.cache
    return data_file, cache


@timeit
def load_data(path=None, cache=1):
    filename = path.rsplit('/', 1)[-1]
    if not path:
        raise ValueError('No file found.')
    info('Loading data')
    info('Load < %s >' % filename)
    fmters = [int, int, int, str, int,
              lambda x: datetime.strptime(x, '%Y-%m-%d %H')]

    if cache:
        info('Try to Load data set from cache')
        data_set, retrived = file_retrive(filename)
        if retrived:
            info('Retrived data from file cache')
            return data_set
    data_set = []

    with open(path, 'r') as f:
        labels = f.readline().strip('\n').split(',')
        for line in f:
            data = line.strip('\n').split(',')
            # Skip Dec 12th
            if data[5].startswith('2014-12-12') or\
                    data[5].startswith('2014-12-13'):
                continue
            data_set.append(data)
    data_size = len(data_set)
    p = Progress(data_size)
    info('Formatting data_set')
    for idx in range(data_size):
        p.next()
        data_set[idx] = list(map(lambda x, f: f(x), data_set[idx], fmters))
    save_to_file(data_set, filename)
    return data_set


if __name__ == '__main__':
    path, cache = parse_args()
    load_data(path, cache)
