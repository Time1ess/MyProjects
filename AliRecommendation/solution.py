#!/usr/local/bin/python3
# coding: UTF-8
# Author: David
# Email: youchen.du@gmail.com
# Created: 2016-12-09 20:10
# Last modified: 2016-12-15 09:47
# Filename: solution.py
# Description:
import argparse

from logging import info
from random import choice


from utils import timeit, Progress, save_to_file, load_from_file
from utils import gen_submits, groupby, sorton, date_shift
from utils import save_prediction, MODELS


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
        '--qset', default='',
        help=('use \'load\' to load query set from file'
              ' or \'test\' to test model'))

    parser.add_argument(
        '--precision', default=0.5, type=float,
        help='Filter predicts with precision(0.0-1.0)')

    parser.add_argument(
        '--sampling', default=3, type=int,
        help='Negative samples / Positive samples')

    args = parser.parse_args()

    data_file = args.file_path
    sample_method = args.samples
    qset_method = args.qset
    model_type = args.model
    precision = args.precision
    sampling = args.sampling

    if sample_method != 'load' and sample_method != '':
        raise TypeError('No such sample method')
    if qset_method != 'load' and qset_method != '' and qset_method != 'test':
        raise TypeError('No such test set method')
    if model_type not in MODELS:
        raise TypeError('No such model type')
    if precision < 0 or precision > 1:
        raise ValueError('Wrong precision')
    if sampling <= 0 or sampling > 10:
        raise ValueError('Unreasonalbe sampling rate')

    return data_file, sample_method, qset_method,\
        model_type, precision, sampling


@timeit
def load_data(path='origin_data.csv', fmters=[], sp_date=None):
    info('Loading data...')
    info('Load < %s >' % path)
    data_set = []
    test_set = []
    with open(path, 'r') as f:
        labels = f.readline().strip('\n').split(',')
        for line in f:
            data = line.strip('\n').split(',')
            if sp_date and data[5].startswith(sp_date):
                test_set.append(data)
            else:
                data_set.append(data)

    return data_set, test_set, labels



@timeit
def extract_buys(data_set):
    info('Extracting buys...')
    buy_set = list(filter(lambda x: x[2] == '4', data_set))

    buys = {}
    for uid, iid, btype, geo, icat, time in buy_set:
        buys[uid+':'+iid] = True

    return buy_set, buys



def extract_feature(bhs, ta, iid):
    feature = [0]*8
    _bhs = list(filter(lambda x: x[1] == iid, bhs))
    for _uid, _iid, _btype, _geo, _icat, _time in _bhs:
        _hour = _time[11:13]
        _day = _time[8:10]
        _month = _time[5:7]
        tb = [_month, _day, _hour]
        shift = date_shift(ta, tb)
        if shift > 2:
            continue
        elif shift == 2:
            s = 4
        else:
            s = 0
        if _btype == '4':
            feature[s] += 1
        elif _btype == '3':
            feature[s+1] += 1
        elif _btype == '2':
            feature[s+2] += 1
        else:
            feature[s+3] += 1

    count = len(bhs)
    buy_count = len(list(filter(lambda x: x[2] == '4', bhs)))
    mark_count = len(list(filter(lambda x: x[2] == '2', bhs)))
    cart_count = len(list(filter(lambda x: x[2] == '3', bhs)))
    visit_count = count-(buy_count+mark_count+cart_count)
    feature.append(buy_count/count)
    feature.append(mark_count/count)
    feature.append(cart_count/count)
    feature.append(visit_count/count)

    return feature


@timeit
def extract_tests(user_dict, buys, time='2014-12-17 00'):
    size = len(user_dict.keys())
    pro = Progress(size)
    info('Finding user item relations...')
    finds = {}
    user_items = []
    for _, _bhs in user_dict.items():
        pro.next()
        for uid, iid, btype, geo, icat, time in _bhs:
            if finds.get(uid+':'+iid, False):
                continue
            if buys.get(uid+':'+iid, False):
                buy = 1
            else:
                buy = 0
            user_items.append([uid, iid, buy])
            finds[uid+':'+iid] = True
    pro.end()

    tests = []
    size = len(user_items)
    pro = Progress(size)
    info('Creating test_set...')

    month = time[5:7]
    day = time[8:10]
    hour = time[11:13]
    ta = [month, day, hour]

    for uid, iid, buy in user_items:
        pro.next()
        tests.append(extract_feature(user_dict[uid], ta, iid)+[buy])
    pro.end()
    return user_items, tests



@timeit
def extract_qset(user_dict, buys, time=None):
    info('Extracting query set...')
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
    info('Creating query set...')
    for uid, iid in user_items:
        pro.next()
        tests.append(extract_feature(user_dict[uid], ta, iid))
    pro.end()
    return user_items, tests


@timeit
def extract_samples(data_set, buy_set, user_dict, buys, sampling):
    info('Extracting samples...')
    poss = []
    negs = []

    # Positive samples
    info('Extracting positive samples')
    for uid, iid, btype, geo, icat, time in buy_set:
        month = time[5:7]
        day = time[8:10]
        hour = time[11:13]
        ta = [month, day, hour]
        poss.append(extract_feature(user_dict[uid], ta, iid))

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

        feature = extract_feature(user_dict[uid], ta, iid)
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
    info('Training %s...' % model_type)
    if model_type == 'LR':
        from sklearn.linear_model.logistic import LogisticRegression as LR
        clf = LR(n_jobs=-1)
    elif model_type == 'RF':
        from sklearn.ensemble import RandomForestClassifier as RF
        clf = RF(n_jobs=-1)
    elif model_type == 'GBDT':
        from sklearn.ensemble import GradientBoostingClassifier as GBDT
        clf = GBDT()
    elif model_type == 'KNN':
        from sklearn.neighbors import KNeighborsClassifier as KNN
        clf = KNN(n_jobs=-1, n_neighbors=9)
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
    elif model_type == 'GBDT':
        info(clf.feature_importances_)

    return clf


@timeit
def prediction(clf, samples, threshold=0.5):
    def _thres(val):
        if val >= threshold:
            return 1
        else:
            return 0
    info('Predicting...')
    predicts = clf.predict_proba(samples)
    _p = list(map(lambda x: _thres(x[1]), predicts))
    _origin_p = list(map(lambda x: x[1], predicts))

    return _p, _origin_p


@timeit
def precision(predicts, reals=None, pre=None):
    if not reals:
        buys = len(list(filter(lambda x: x > pre, predicts)))
        not_buys = len(predicts)-buys
        info('Predicted buys: %d, Predicted not buys: %d' % (buys, not_buys))
        return
    right_buy = 0
    false_buy = 0
    right_not_buy = 0
    false_not_buy = 0
    for i, buy in enumerate(reals, 0):
        if predicts[i] == buy and buy == 1:
            right_buy += 1
        elif predicts[i] == buy and buy == 0:
            right_not_buy += 1
        elif predicts[i] != buy and buy == 1:
            false_not_buy += 1
        elif predicts[i] != buy and buy == 0:
            false_buy += 1
    try:
        p = 100.* right_buy / (right_buy+false_buy)
    except ZeroDivisionError:
        p = 0
    try:
        r = 100.* right_buy / (right_buy+false_not_buy)
    except ZeroDivisionError:
        r = 0
    if p == 0 and r == 0:
        f1 = 0
    else:
        f1 = 2*p*r/(p+r)
    info('Right buys: %d, Right not buys: %d' % (right_buy, right_not_buy))
    info('False buys: %d, False not buys: %d' % (false_buy, false_not_buy))
    info('F1: %.2f, Precision: %.2f, Recall: %.2f' % (f1, p, r))


@timeit
def main():
    data_file, sample_method, qset_method,\
        model_type, pre, sampling = parse_args()

    data_prefix = data_file.split('.')[0]+'_'

    if sample_method != 'load' or qset_method != 'load':
        if qset_method == 'test':
            data_set, test_set, _ = load_data(data_file, sp_date='2014-12-17')
            test_user_dict = groupby(test_set, 0)
            sorton(test_user_dict)
            test_buy_set, test_buys = extract_buys(test_set)
        else:
            data_set, _, _ = load_data(data_file, sp_date='2014-12-17')

        user_dict = groupby(data_set, 0)
        sorton(user_dict)
        buy_set, buys = extract_buys(data_set)

    if sample_method == 'load':
        poss = load_from_file(data_prefix+'poss.model')
        negs = load_from_file(data_prefix+'negs.model')
    else:
        poss, negs = extract_samples(data_set, buy_set, user_dict,
                                     buys, sampling)
        save_to_file(poss, data_prefix+'poss.model')
        save_to_file(negs, data_prefix+'negs.model')

    clf = train_clf(poss, negs, model_type)

    if qset_method == 'load':
        user_items = load_from_file(data_prefix+'user_items.model')
        qset = load_from_file(data_prefix+'query_set.model')
        tests = qset
    elif qset_method == 'test':
        user_items, tests = extract_tests(test_user_dict, test_buys)
        reals = list(map(lambda x: x[-1], tests))
        tests = list(map(lambda x: x[:-1], tests))
    else:
        user_items, tests = extract_qset(user_dict, buys, '2014-12-18 00')

        save_to_file(user_items, data_prefix+'user_items.model')
        save_to_file(tests, data_prefix+'query_set.model')

    predicts, origin_predicts = prediction(clf, tests, pre)

    if qset_method == 'test':
        precision(predicts, reals=reals)
    else:
        precision(predicts, pre=pre)
        save_prediction(user_items, origin_predicts, pre)
        gen_submits(pre)
    info('Memory recoverying...')


if __name__ == '__main__':
    main()
