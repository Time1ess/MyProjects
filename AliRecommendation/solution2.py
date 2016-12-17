#!/usr/local/bin/python3
# coding: UTF-8
# Author: David
# Email: youchen.du@gmail.com
# Created: 2016-12-09 20:10
# Last modified: 2016-12-17 09:21
# Filename: solution2.py
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

    methods = ['load', '', 'test', 'test_load']

    if sample_method not in methods:
        raise TypeError('No such sample method')
    if qset_method not in methods:
        raise TypeError('No such test set method')
    if model_type not in MODELS:
        raise TypeError('No such model type')
    if precision < 0 or precision > 1:
        raise ValueError('Wrong precision')
    if sampling <= 0 or sampling > 100:
        raise ValueError('Unreasonalbe sampling rate')

    return data_file, sample_method, qset_method,\
        model_type, precision, sampling


@timeit
def load_data(path='origin_data.csv', fmters=[], sp_date=None):
    info('Loading data')
    info('Load < %s >' % path)
    data_set = []
    test_set = []
    with open(path, 'r') as f:
        labels = f.readline().strip('\n').split(',')
        for line in f:
            data = line.strip('\n').split(',')
            if sp_date and data[5] > sp_date:
                test_set.append(data)
            else:
                data_set.append(data)
    info('Data set: %d , Test set: %d' % (len(data_set), len(test_set)))
    return data_set, test_set, labels


@timeit
def extract_buys(data_set):
    info('Extracting buys')
    buy_set = list(filter(lambda x: x[2] == '4', data_set))

    buys = defaultdict(list)
    items = defaultdict(partial(defaultdict, int))
    cates = defaultdict(partial(defaultdict, int))
    for uid, iid, btype, geo, icat, time in buy_set:
        buys[uid+':'+iid].append(time[:10])
        items[iid][time[:10]] += 1
        cates[icat][time[:10]] += 1

    return buys, items, cates

def extract_feature(items, cates):
    def _extract_feature_with_info(bhs, ta, iid):
        return _extract_feature(bhs, ta, iid, items, cates)
    return _extract_feature_with_info


def _extract_feature(bhs, ta, iid, items, cates):
    keytime = '2014-%02d-%02d %02d' % tuple(ta)
    feature1 = [0]*9
    icat = None
    _cates = []
    _items = []
    _buy = 0
    _buy_time = 0
    min_time = '24'
    max_time = '00'
    for _uid, _iid, _btype, _geo, _icat, _time in bhs:
        _month = _time[5:7]
        _hour = _time[11:13]
        _day = _time[8:10]
        tb = [_month, _day, _hour]
        shift = date_shift(ta, tb)
        if shift > 14 or shift < 0:
            continue
        if shift == 0:
            if _iid == iid:
                icat = _icat
            if _btype == '3':
                feature1[8] = True
            if _icat not in _cates:
                _cates.append(_icat)
            if _iid not in _items:
                _items.append(_iid)
            if _btype == '4':
                _buy = True
                _buy_time = int(_time[-2:])
            if min_time > _hour:
                min_time = _hour
            if max_time < _hour:
                max_time = _hour
        if shift > 7:  # user behaviors 7-14 days before keyday
            s = 4
        else:  # user behaviors 0-7 days before keyday
            s = 0
        if _btype == '4':
            feature1[s] += 1
        elif _btype == '3':
            feature1[s+1] += 1
        elif _btype == '2':
            feature1[s+2] += 1
        else:
            feature1[s+3] += 1

    feature2 = []
    feature2.append(len(_cates))  # how many cates interact on keyday
    feature2.append(len(_items))  # how many items interact on keyday
    if min_time == '24' and max_time == '00':
        feature2.append(0)
    else:
        feature2.append((int(max_time)-int(min_time))%24)  # how many hours online
    feature2.append(int(max_time))  # when to offline
    feature2.append(_buy)  # buy on keyday?
    feature2.append(_buy_time)  # when buyed on keyday?
    feature2.append(items[iid][keytime[:10]])  # how many items saled on keyday(all)
    feature2.append(cates[icat][keytime[:10]]) # how many items in cate saled on keyday(all)

    # User behaviors
    count = len(bhs)
    buy_count = len(list(filter(lambda x: x[2] == '4', bhs)))
    mark_count = len(list(filter(lambda x: x[2] == '2', bhs)))
    cart_count = len(list(filter(lambda x: x[2] == '3', bhs)))
    visit_count = count-(buy_count+mark_count+cart_count)
    feature2.append(visit_count)
    feature2.append(mark_count)
    feature2.append(cart_count)
    feature2.append(buy_count)
    if buy_count == 0 and visit_count / count > 0.95:  # Robot-like action filter
        feature2.append(True)
    else:
        feature2.append(False)
    feature2.append(visit_count/count)
    feature2.append(cart_count/count)
    feature2.append(mark_count/count)
    feature2.append(buy_count/count)

    # Item and category performances
    si = sum(items[iid].values())
    sc = sum(cates[icat].values())
    feature2.append(si)
    feature2.append(sc)
    if sc == 0:
        feature2.append(0)
    else:
        feature2.append(si/sc)

    def _clean(val):
        if val == 0:
            return -1
        else:
            return val

    feature = feature1
    feature.extend(feature2)

    feature = list(map(lambda x: _clean(x), feature))

    return feature


@timeit
def extract_tests(user_dict, buys, items, cates, key_day_list):
    info('Finding user item relations')

    month = key_day_list[0]
    day = key_day_list[1]
    buy_day = '2014-%02d-%02d' % (month, day+1)
    key_day = '2014-%02d-%02d' % (month, day)
    ta = [month, day, 0]

    user_items = []
    size = len(user_dict.keys())
    pro = Progress(size)
    finds = {}
    for _, _bhs in user_dict.items():
        pro.next()
        for uid, iid, btype, geo, icat, _time in _bhs:
            if finds.get(uid+':'+iid, False):
                continue
            bd = buys.get(uid+':'+iid, False)
            if bd and buy_day in bd:
                buy = 1
            else:
                buy = 0
            user_items.append([uid, iid, buy])
            finds[uid+':'+iid] = True
    pro.end()

    info('Creating test set')
    tests = []
    size = len(user_items)
    pro = Progress(size)

    extract = extract_feature(items, cates)

    for uid, iid, buy in user_items:
        pro.next()
        tests.append(extract(user_dict[uid], ta, iid)+[buy])
    pro.end()
    return user_items, tests


@timeit
def extract_qset(user_dict, buys, items, cates, key_day_list):
    info('Extracting query set')
    month = key_day_list[0]
    day = key_day_list[1]
    ta = [month, day, 0]
    fst = '2014-%02d-%02d' % (int(month), int(day))
    info('FST: %s' % fst)

    user_items = []
    size = len(user_dict.keys())
    pro = Progress(size)
    info('Finding user item relations')
    finds = {}
    for _, _bhs in user_dict.items():
        pro.next()
        for uid, iid, btype, geo, icat, _time in _bhs:
            if not _time.startswith(fst):
                continue
            if finds.get(uid+':'+iid, False):
                continue
            user_items.append([uid, iid])
            finds[uid+':'+iid] = True
    pro.end()

    info('Creating query set')
    qset = []
    size = len(user_items)
    info('User items: %d' % size)
    pro = Progress(size)

    extract = extract_feature(items, cates)
    for uid, iid in user_items:
        pro.next()
        qset.append(extract(user_dict[uid], ta, iid))
    pro.end()
    return user_items, qset

def extract_samples_2(data_set, user_dict,
                      items, cates, sampling, key_day_list):
    info('Extracting samples for %02d-%02d' % (key_day_list[0], key_day_list[1]))
    month = key_day_list[0]
    day = key_day_list[1]
    buy_day = '2014-%02d-%02d' % (month, day+1)
    key_day = '2014-%02d-%02d' % (month, day)

    ss1 = []  # interact in key_day and add to cart
    ss1_n = []  # interact in key_day and add to cart

    for uid, bhs in user_dict.items():
        buy_day_buys = list(map(lambda x: x[1],
                           filter(lambda y: y[5].startswith(buy_day) and
                                      y[2] == '4',
                                  bhs)))
        rbhs_key_day = list(filter(lambda x: x[5].startswith(key_day), bhs))
        processed = set()
        for uid, iid, btype, geo, icat, time in rbhs_key_day:
            if iid in processed:
                continue
            processed.add(iid)
            if iid in buy_day_buys:
                ss1.append([uid, iid, 1])
            elif iid not in buy_day_buys:
                ss1_n.append([uid, iid, 0])

    shuffle(ss1_n)
    size = len(ss1)
    ss1_n = ss1_n[:min(sampling*len(ss1), len(ss1_n))]
    ss1.extend(ss1_n)
    size_n = len(ss1)-size

    extract = extract_feature(items, cates)

    ta = [month, day, 0]
    fs_1 = map(lambda arg: extract(user_dict[arg[0]], ta, arg[1])+[arg[2]], ss1)
    fs_1 = list(fs_1)


    return fs_1, size, size_n



@timeit
def extract_samples(data_set, buy_set, user_dict, buys, sampling):
    info('Extracting samples')
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
            uid, iid = record[:2]
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
def train_clf(fs_1, model_type):
    info('Training %s' % model_type)
    info('fs1 samples: %d' % len(fs_1))
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
    feature = list(map(lambda x: x[:-1], fs_1))
    res = list(map(lambda x: x[-1], fs_1))
    clf.fit(feature, res)
    if model_type == 'LR':
        pass
    elif model_type == 'RF':
        info('Feature importance in RF:')
        info(clf.feature_importances_)
    elif model_type == 'GBDT':
        info('Feature importance in RF:')
        info(clf.feature_importances_)
    return clf


@timeit
def prediction(clf, samples, threshold=0.5):
    def _thres(val):
        if val >= threshold:
            return 1
        else:
            return 0
    info('Predicting')
    predicts = clf.predict_proba(samples)
    _origin_p = list(map(lambda x: x[1], predicts))
    _p = list(map(lambda x: _thres(x), _origin_p))

    return _p, _origin_p


@timeit
def precision(predicts, reals=None, pre=None, origin=None):
    if not reals:
        buys = len(list(filter(lambda x: x > pre, predicts)))
        not_buys = len(predicts)-buys
        info('Predicted buys: %d, Predicted not buys: %d' % (buys, not_buys))
        return
    right_buy = 0
    false_buy = 0
    right_not_buy = 0
    false_not_buy = 0
    buy_avg = 0
    false_buy_avg = 0
    false_not_buy_avg = 0
    for i, buy in enumerate(reals, 0):
        if predicts[i] == buy and buy == 1:
            buy_avg += origin[i]
            right_buy += 1
        elif predicts[i] == buy and buy == 0:
            right_not_buy += 1
        elif predicts[i] != buy and buy == 1:
            false_not_buy_avg += origin[i]
            false_not_buy += 1
        elif predicts[i] != buy and buy == 0:
            false_buy_avg += origin[i]
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

    try:
        buy_avg /= right_buy
    except ZeroDivisionError:
        buy_avg = 0
    try:
        false_buy_avg /= false_buy
    except ZeroDivisionError:
        false_buy_avg = 0
    try:
        false_not_buy_avg /= false_not_buy
    except ZeroDivisionError:
        false_not_buy_avg= 0

    info('Avg for predicting buy(right): %.2f' % buy_avg)
    info('Avg for false predicting buy(should not buy): %.2f' % false_buy_avg)
    info('Avg for false not predicting buy(should buy): %.2f' % false_not_buy_avg)


@timeit
def main():
    info('>>>>>>     New Prediction Session     <<<<<<')
    data_file, sample_method, qset_method,\
        model_type, pre, sampling = parse_args()

    data_prefix = data_file.split('.')[0]+'_'

    if sample_method != 'load' or qset_method != 'load':
        data_set, _, _ = load_data(data_file)

        user_dict = groupby(data_set, 0)
        sorton(user_dict)
        buys, items, cates = extract_buys(data_set)

    if sample_method == 'load':
        fs_1 = load_from_file('fs_1', data_prefix)
    else:
        fs_1 = []
        ps = 0
        ns = 0
        for day in range(25, 31):
            t_fs_1, tps, tns = extract_samples_2(
                data_set, user_dict, items, cates, sampling, [11, day])
            fs_1.extend(t_fs_1)
            ps += tps
            ns += tns

        if qset_method == '':
            end = 17
        else:
            end = 15
        for day in range(1, end):
            if day == 12 or day == 13:
                continue
            t_fs_1, tps, tns = extract_samples_2(
                data_set, user_dict, items, cates, sampling, [12, day])
            fs_1.extend(t_fs_1)
            ps += tps
            ns += tns
        info('Positive samples: %d, Negative samples: %d' % (ps, ns))
        save_to_file(fs_1, 'fs_1', data_prefix)

    clf = train_clf(fs_1, model_type)

    if qset_method == 'load':
        user_items = load_from_file('user_items', data_prefix)
        qset = load_from_file('query_set', data_prefix)
        tests = qset
    elif qset_method == 'test':
        user_items, tests = extract_tests(user_dict, buys, items, cates, [12, 16])
        reals = list(map(lambda x: x[-1], tests))
        tests = list(map(lambda x: x[:-1], tests))

        save_to_file(reals, 'test_reals', data_prefix)
        save_to_file(tests, 'test_tests', data_prefix)
        save_to_file(user_items, 'user_items', data_prefix)
    elif qset_method == 'test_load':
        user_items = load_from_file('user_items', data_prefix)
        tests = load_from_file('test_tests', data_prefix)
        reals = load_from_file('test_reals', data_prefix)
    else:
        user_items, qset = extract_qset(user_dict, buys, items, cates, [12, 17])
        tests = qset
        save_to_file(user_items, 'user_items', data_prefix)
        save_to_file(tests, 'query_set', data_prefix)

    predicts, origin_predicts = prediction(clf, tests, pre)

    if qset_method == 'test' or qset_method == 'test_load':
        precision(predicts, reals=reals, origin=origin_predicts)
    else:
        precision(predicts, pre=pre)
        save_prediction(user_items, origin_predicts, pre)
        gen_submits(pre)
    info('Memory recoverying')


if __name__ == '__main__':
    main()
