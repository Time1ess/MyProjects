#!/usr/local/bin/python3
# coding: UTF-8
# Author: David
# Email: youchen.du@gmail.com
# Created: 2016-12-09 20:10
# Last modified: 2016-12-16 21:56
# Filename: solution3.py
# Description:
import argparse

from logging import info
from collections import defaultdict
from functools import partial
from random import choice, shuffle


from utils import timeit, Progress, save_to_file, load_from_file
from utils import gen_submits, groupby, sorton, date_shift
from utils import save_prediction, MODELS

def parse_args():
    parser = argparse.ArgumentParser(
        description='Arguments to control prediction.')
    parser.add_argument('file_path', metavar='path', type=str,
                        help='Path to data file')
    args = parser.parse_args()

    data_file = args.file_path
    return data_file


@timeit
def load_data(path='origin_data.csv', fmters=[], sp_date=None):
    info('Loading data')
    info('Load < %s >' % path)
    data_set = []
    with open(path, 'r') as f:
        labels = f.readline().strip('\n').split(',')
        for line in f:
            data = line.strip('\n').split(',')
            data_set.append(data)
    return data_set


@timeit
def main():
    info('>>>>>>     New Prediction Session     <<<<<<')

    data_file = parse_args()

    data_set = load_data(data_file)
    predicts = []

    for uid, iid, btype, geo, cate, time in data_set:
        if time.startswith('2014-12-17'):
            if btype == '3':
                predicts.append([uid, iid])

    with open('dutir_tianchi_recom_predict_david.txt', 'w') as f:
        for uid, iid in predicts:
            f.write(uid+','+iid+'\n')

if __name__ == '__main__':
    main()
