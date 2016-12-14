#!/usr/local/bin/python3
# coding: UTF-8
# Author: David
# Email: youchen.du@gmail.com
# Created: 2016-12-09 20:10
# Last modified: 2016-12-14 10:42
# Filename: solution.py
# Description:
import pickle
import argparse

from collections import defaultdict
from logging import info
from random import choice

from sklearn.linear_model.logistic import LogisticRegression as LR
from sklearn.ensemble import RandomForestClassifier as RF

from utils import timeit, Progress


MODELS = ['LR', 'RF']


def parse_args():
    parser = argparse.ArgumentParser(
        description='Arguments to control prediction.')
    parser.add_argument('file_path', metavar='path', type=str,
                        help='Path to data file')
    parser.add_argument(
        '--samples', default='',
        help='use \'load\' to load samples from file')

    parser.add_argument(
        '--model', default='LR',
        help='Select model for classifying.')

    parser.add_argument(
        '--tests', default='',
        help='use \'load\' to load test set from file')

    parser.add_argument(
        '--precision', default=0.5, type=float,
        help='Filter predicts with precision(0.0-1.0)')

    parser.add_argument(
        '--sampling', default=3, type=int,
        help='Negative samples / Positive samples')

    args = parser.parse_args()

    data_file = args.file_path
    sample_method = args.samples
    tests_method = args.tests
    model_type = args.model
    precision = args.precision
    sampling = args.sampling

    if sample_method != 'load' and sample_method != '':
        raise TypeError('No such sample method')
    if tests_method != 'load' and tests_method != '':
        raise TypeError('No such test set method')
    if model_type not in MODELS:
        raise TypeError('No such model type')
    if precision < 0 or precision > 1:
        raise ValueError('Wrong precision')
    if sampling <= 0 or sampling > 10:
        raise ValueError('Unreasonalbe sampling rate')

    return data_file, sample_method, tests_method,\
        model_type, precision, sampling


@timeit
def load_data(path='origin_data.csv', fmters=[]):
    info('Load < %s >' % path)
    data_set = []
    with open(path, 'r') as f:
        labels = f.readline().strip('\n').split(',')
        for line in f:
            data = line.strip('\n').split(',')
            if fmters:
                data = list(map(lambda d, f: f(d) if f else d, data, fmters))
            data_set.append(data)

    return data_set, labels


@timeit
def groupby(data_set, index):
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
    size = len(group_dict.keys())
    pro = Progress(size)
    for value in group_dict.values():
        pro.next()
        value.sort(key=lambda x: (x[2], x[5]), reverse=True)
    pro.end()


@timeit
def extract_buys(data_set):
    buy_set = list(filter(lambda x: x[2] == '4', data_set))

    buys = {}

    for uid, iid, btype, geo, icat, time in buy_set:
        buys[uid+':'+iid] = True

    return buy_set, buys


def date_shift(ta=None, tb=None):
    ta = list(map(lambda x: int(x), ta))
    tb = list(map(lambda x: int(x), tb))
    shift = 0
    shift += (ta[0]-tb[0])*30
    shift += ta[1]-tb[1]
    shift += 1 if ta[2] >= tb[2] else 0
    return shift


def extract_feature(bhs, ta):
    """
    特征选取 对于第k天
    前一天内进行交互的(购买、收藏、加购物车、访问)
    前两天...
    一周内...
    正样本: 第k天购买
    负样本: 第k天未购买
    """
    feature = [0]*12
    for _uid, _iid, _btype, _geo, _icat, _time in bhs:
        _hour = _time[11:13]
        _day = _time[8:10]
        _month = _time[5:7]
        tb = [_month, _day, _hour]
        shift = date_shift(ta, tb)
        if shift > 7:
            continue
        elif shift <= 1:
            s = 0
        elif shift <= 2:
            s = 4
        else:
            s = 8
        if _btype == '4':
            feature[s] += 1
        if _btype == '3':
            feature[s+1] += 1
        elif _btype == '2':
            feature[s+2] += 1
        else:
            feature[s+3] += 1
    return feature


@timeit
def extract_tests(user_dict, buys, time=None):
    month = time[5:7]
    day = time[8:10]
    hour = time[11:13]
    ta = [month, day, hour]

    user_items = []
    size = len(user_dict.keys())
    pro = Progress(size)
    info('Finding user item relations...')
    finds = {}
    for _, _bhs in user_dict.items():
        pro.next()
        for uid, iid, btype, geo, icat, time in _bhs:
            if buys.get(uid+':'+iid, False) or finds.get(uid+':'+iid, False):
                continue
            user_items.append([uid, iid])
            finds[uid+':'+iid] = True
    pro.end()

    tests = []
    size = len(user_items)
    pro = Progress(size)
    info('Creating test_set...')
    for uid, iid in user_items:
        pro.next()
        bhs = list(filter(lambda x: x[1] == iid, user_dict[uid]))
        tests.append(extract_feature(bhs, ta))
    pro.end()
    return user_items, tests


@timeit
def extract_samples(data_set, buy_set, user_dict, buys, sampling):
    poss = []
    negs = []

    # Positive samples
    info('Extracting positive samples')
    for uid, iid, btype, geo, icat, time in buy_set:
        month = time[5:7]
        day = time[8:10]
        hour = time[11:13]
        ta = [month, day, hour]
        bhs = list(filter(lambda x: x[1] == iid, user_dict[uid]))

        # Buy only, but not visit or mark or add to cart
        if len(bhs) == 1:
            continue
        poss.append(extract_feature(bhs[1:], ta))

    # Negative samples
    info('Extracting negative samples')
    pos_size = len(poss)
    pro = Progress(pos_size*sampling)
    cnt = 0
    while True:
        while True:
            record = choice(data_set)
            uid = record[0]
            iid = record[1]
            if not buys.get(uid+':'+iid, False):
                break
        time = record[5]
        month = time[5:7]
        day = time[8:10]
        hour = time[11:13]
        ta = [month, day, hour]
        bhs = list(filter(lambda x: x[1] == iid, user_dict[uid]))

        feature = extract_feature(bhs, ta)
        if any(feature):
            pro.next()
            cnt += 1
            negs.append(feature)
        if cnt == sampling*pos_size:
            break
    pro.end()

    return poss, negs


@timeit
def train_clf(poss, negs, model_type):
    if model_type == 'LR':
        clf = LR(n_jobs=-1)
    elif model_type == 'RF':
        clf = RF(n_estimators=100, n_jobs=-1)
    poss_r = [1 for i in range(len(poss))]
    negs_r = [0 for i in range(len(negs))]
    poss += negs
    poss_r += negs_r
    clf.fit(poss, poss_r)
    if model_type == 'LR':
        pass
    elif model_type == 'RF':
        info('Feature importance in RF:')
        info(clf.feature_importances_)

    return clf


@timeit
def prediction(clf, samples):
    predicts = clf.predict_proba(samples)
    predicts = list(map(lambda x: x[1], predicts))

    return predicts


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


@timeit
def save_to_file(obj, f):
    _f = open(f, 'wb')
    pickle.dump(obj, _f)


@timeit
def load_from_file(f):
    _f = open(f, 'rb')
    return pickle.load(_f)


@timeit
def precision(predicts, reals):
    real_buys = 0
    predict_buys = 0
    right_predict = 0
    for i, buy in enumerate(reals, 0):
        if buy == 1:
            real_buys += 1
            if predicts[i] == 1:
                right_predict += 1
        if predicts[i] == 1:
            predict_buys += 1
    try:
        p = 100.*right_predict/real_buys
    except ZeroDivisionError:
        p = 0
    try:
        r = 100.*right_predict/predict_buys
    except ZeroDivisionError:
        r = 0
    if p == 0 and r == 0:
        f1 = 0
    else:
        f1 = 2*p*r/(p+r)
    info('Real buys: %d, Right predict: %d' % (real_buys, right_predict))
    info('F1: %.2f, Precision: %.2f, Recall: %.2f' % (f1, p, r))


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
def main():
    data_file, sample_method, tests_method,\
        model_type, pre, sampling = parse_args()

    if sample_method != 'load' or tests_method != 'load':
        info('Loading data...')
        data_set, _ = load_data(data_file)

        info('Grouping data...')
        user_dict = groupby(data_set, 0)

        info('Sorting data...')
        sorton(user_dict)

        info('Extracting buys...')
        buy_set, buys = extract_buys(data_set)

    info('Extracting samples...')
    if sample_method == 'load':
        info('Loading samples...')
        poss = load_from_file('poss.model')
        negs = load_from_file('negs.model')
    else:
        poss, negs = extract_samples(data_set, buy_set, user_dict,
                                     buys, sampling)

        info('Saving samples...')
        save_to_file(poss, 'poss_12f.model')
        save_to_file(negs, 'negs_12f.model')

    info('Training %s...' % model_type)
    clf = train_clf(poss, negs, model_type)

    info('Extracting test_set...')
    if tests_method == 'load':
        info('Loading user_items...')
        user_items = load_from_file('user_items.model')

        info('Loading test set...')
        tests = load_from_file('test_set.model')
    else:
        user_items, tests = extract_tests(user_dict, buys, '2014-12-18 00')

        info('Saving models...')
        save_to_file(user_items, 'user_items_12f.model')
        save_to_file(tests, 'test_set_12f.model')

    info('Predicting...')
    predicts = prediction(clf, tests)

    save_prediction(user_items, predicts, 0.30)
    gen_submits(pre)
    info('Memory recoverying...')


if __name__ == '__main__':
    main()
