#!/usr/local/bin/python3
# coding: UTF-8
# Author: David
# Email: youchen.du@gmail.com
# Created: 2016-12-30 19:30
# Last modified: 2016-12-31 10:06
# Filename: model_prediction.py
# Description:
import argparse

from logging import info
from random import shuffle
from utils import load_from_file, save_to_file, file_retrive
from utils import Progress, timeit, d1, MODELS


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('dp', metavar='data_set_name', type=str,
                        help='The name of the data set')
    parser.add_argument('model', metavar='model', type=str,
                        choices = MODELS,
                        help='The name of the model type')
    parser.add_argument('sampling_rate', metavar='max_sampling_rate', type=float,
                        help='Sampling rate(not buy / buy)')
    parser.add_argument('training_rate', metavar='training_rate', type=float,
                        help='Train set size / feature set size')
    parser.add_argument('--test', metavar='test_mode', type=int, default=1,
                        choices = [0, 1], help='Determine if is in test mode')
    parser.add_argument('--threshold', metavar='threshold', type=float,
                        default=0.8, help='Determine if is in test mode')
    parser.add_argument(
        '--cache', default=1, type=int, metavar='cache_type',
        help='Use 0 force to load classifier from cache, default is 1')

    args = parser.parse_args()

    data_path = args.dp
    model = args.model
    srate = args.sampling_rate
    trate = args.training_rate
    test = args.test
    threshold = args.threshold
    cache = args.cache

    return data_path, model, srate, trate, test, threshold, cache


def resampling(cbs, ncbs, cnbs, ncnbs, rate):
    info('Resampling feature set')

    s1 = len(cbs)
    s2 = len(ncbs)
    s3 = len(cnbs)
    s4 = len(ncnbs)
    info('CART_BUY size: %d' % s1)
    info('NO_CART_BUY size: %d' % s2)
    info('CART_NO_BUY size: %d' % s3)
    info('NO_CART_NO_BUY size: %d' % s4)

    if s2/s1 <= rate and s4/s3 <= rate:
        info('Already satisfied, no need to resampling')
    if s2/s1 > rate:
        ts = int(s1*rate)
        shuffle(ncbs)
        ncbs = ncbs[:ts]
    if s4/s3 > rate:
        ts = int(s3*rate)
        shuffle(ncnbs)
        ncnbs = ncnbs[:ts]

    info('After resampling')
    s1 = len(cbs)
    s2 = len(ncbs)
    s3 = len(cnbs)
    s4 = len(ncnbs)
    info('CART_BUY size: %d' % s1)
    info('NO_CART_BUY size: %d' % s2)
    info('CART_NO_BUY size: %d' % s3)
    info('NO_CART_NO_BUY size: %d' % s4)

    return cnbs, ncnbs


def feature_set_devide(data_path, srate, trate, test=True, fset=None):
    info('Devide feature set into train set and test set')
    if fset:
        cbs, ncbs, cnbs, ncnbs = fset
    else:
        info('Load feature set from cache')
        cbs, r1 = file_retrive('CART_BUY-'+data_path)
        ncbs, r2 = file_retrive('NO_CART_BUY-'+data_path)
        cnbs, r3 = file_retrive('CART_NO_BUY-'+data_path)
        ncnbs, r4 = file_retrive('NO_CART_NO_BUY-'+data_path)
        if not all([r1, r2, r3, r4]):
            raise ValueError('Feature set not found.')

    cnbs, ncnbs= resampling(cbs, ncbs, cnbs, ncnbs, srate)

    if not test:
        trate = 1

    s1 = len(cbs)
    s2 = len(ncbs)
    s3 = len(cnbs)
    s4 = len(ncnbs)

    cbs_train = cbs[:int(s1*trate)]
    cbs_test = cbs[int(s1*trate):]
    ncbs_train = ncbs[:int(s2*trate)]
    ncbs_test = ncbs[int(s2*trate):]
    cnbs_train = cnbs[:int(s3*trate)]
    cnbs_test = cnbs[int(s3*trate):]
    ncnbs_train = ncnbs[:int(s4*trate)]
    ncnbs_test = ncnbs[int(s4*trate):]

    train_set = [cbs_train, cnbs_train, ncbs_train, ncnbs_train]
    test_set = [cbs_test, cnbs_test, ncbs_test, ncnbs_test]

    info('Train set cbs for clf1: %d' % len(train_set[0]))
    info('Train set cnbs for clf1: %d' % len(train_set[1]))
    info('Train set ncbs for clf2: %d' % len(train_set[2]))
    info('Train set ncnbs for clf2: %d' % len(train_set[3]))
    info('Test set cbs for clf1: %d' % len(test_set[0]))
    info('Test set cnbs for clf1: %d' % len(test_set[1]))
    info('Test set ncbs for clf2: %d' % len(test_set[2]))
    info('Test set ncnbs for clf2: %d' % len(test_set[3]))

    return train_set, test_set

@timeit
def train_clf(cbs, cnbs, ncbs, ncnbs, model_type):
    info('Training %s' % model_type)
    if model_type == 'LR':
        from sklearn.linear_model.logistic import LogisticRegression as LR
        clf1 = LR(n_jobs=-1)
        clf2 = LR(n_jobs=-1)
    elif model_type == 'RF':
        from sklearn.ensemble import RandomForestClassifier as RF
        clf1 = RF(n_jobs=-1)
        clf2 = RF(n_jobs=-1)
    elif model_type == 'GBDT':
        from sklearn.ensemble import GradientBoostingClassifier as GBDT
        clf1 = GBDT()
        clf2 = GBDT()
    elif model_type == 'KNN':
        from sklearn.neighbors import KNeighborsClassifier as KNN
        clf1 = KNN(n_jobs=-1, n_neighbors=9)
        clf2 = KNN(n_jobs=-1, n_neighbors=9)
    clf1.fit(cbs+cnbs, [1]*len(cbs)+[0]*len(cnbs))
    clf2.fit(ncbs+ncnbs, [1]*len(ncbs)+[0]*len(ncnbs))
    if model_type == 'LR':
        pass
    elif model_type in ['RF', 'GBDT']:
        info('Feature importance in %s - clf1:' % model_type)
        info(clf1.feature_importances_)
        info('Feature importance in %s - clf2:' % model_type)
        info(clf2.feature_importances_)
    return clf1, clf2


@timeit
def model_buildup(data_path, model_type, train_set, cache=None):
    info('Build up model < %s >' % model_type)
    if cache:
        info('Try to load classifiers from cache')
        clf1, r1 = file_retrive('CLF1-'+model_type+'-'+data_path)
        clf2, r2 = file_retrive('CLF2-'+model_type+'-'+data_path)
        if r1 and r2:
            info('Classifiers has been build up from cache')
            return clf1, clf2
        else:
            info('Loaded classifiers failed, try to build up')
    clf1, clf2 = train_clf(*train_set, model_type)

    save_to_file(clf1, 'CLF1-'+model_type+'-'+data_path)
    save_to_file(clf2, 'CLF2-'+model_type+'-'+data_path)
    return clf1, clf2


@timeit
def prediction(clf1, clf2, pre_set1, pre_set2):
    info('Predicting')
    pres1 = clf1.predict_proba(pre_set1)
    pres2 = clf2.predict_proba(pre_set2)
    return pres1, pres2

@timeit
def precision(cbs, cnbs, ncbs, ncnbs, pcbs, pcnbs, pncbs, pncnbs, threshold):
    def _thres(probs):
        if probs[0] >= threshold:
            return 0
        else:
            return 1
    p1 = list(map(lambda x: _thres(x), pcbs))
    p2 = list(map(lambda x: _thres(x), pcnbs))
    r1 = len(list(cbs))
    r2 = len(list(cnbs))
    rpb = 0  # rpb: right num for predict buy 
    fpb = 0
    rpnb = 0
    fpnb = 0
    rpb += p1.count(1)
    fpb += p1.count(0)
    rpnb += p2.count(0)
    fpnb += p2.count(1)
    info('Status for clf1:')
    info('Precision: %.2f' % (100*rpb/len(p1)))

    p3 = list(map(lambda x: _thres(x), pncbs))
    p4 = list(map(lambda x: _thres(x), pncnbs))
    r3 = len(list(ncbs))
    r4 = len(list(ncnbs))
    rpb = 0  # rpb: right num for predict buy 
    fpb = 0
    rpnb = 0
    fpnb = 0
    rpb += p3.count(1)
    fpb += p3.count(0)
    rpnb += p4.count(0)
    fpnb += p4.count(1)

    info('Status for clf2:')
    info('Precision: %.2f' % (100*rpb/len(p3)))


@timeit
def predict_answer(data_path, clf1, clf2, threshold):
    info('Predict answer')
    pre1, r1 = file_retrive('PREDICTION_SET1-'+data_path)
    pre2, r2 = file_retrive('PREDICTION_SET2-'+data_path)
    if not all([r1, r2]):
        raise ValueError('Error encountered when loading prediction set')

    def _thres(probs):
        if probs[0] >= threshold:
            return 0
        else:
            return 1
    uis1 = list(map(lambda x: x[:2], pre1))
    uis2 = list(map(lambda x: x[:2], pre2))
    pre1 = list(map(lambda x: x[2:], pre1))
    pre2 = list(map(lambda x: x[2:], pre2))

    with open('ans.txt', 'w') as f:
        if pre1:
            pres1 = clf1.predict_proba(pre1)
            p1 = list(map(lambda x: _thres(x), pres1))
            size = len(p1)
            pro = Progress(size)
            for [uid, iid], buy in zip(uis1, p1):
                pro.next()
                if buy:
                    f.write('%d,%d\n' % (uid, iid))
        if pre2:
            pres2 = clf2.predict_proba(pre2)
            p2 = list(map(lambda x: _thres(x), pres2))
            size = len(p2)
            pro = Progress(size)
            for [uid, iid], buy in zip(uis2, p2):
                pro.next()
                if buy:
                    f.write('%d,%d\n' % (uid, iid))


if __name__ == '__main__':
    data_path, model_type, srate, trate, test, threshold, cache = parse_args()
    train_set, test_set = feature_set_devide(data_path, srate, trate, test)
    clf1, clf2 = model_buildup(data_path, model_type, train_set, cache)
    if test:
        cbs, cnbs, ncbs, ncnbs = test_set
        pre_cb, pre_ncb = prediction(clf1, clf2, cbs, ncbs)
        pre_cnb, pre_ncnb = prediction(clf1, clf2, cnbs, ncnbs)
        precision(cbs, cnbs, ncbs, ncnbs, pre_cb,
                  pre_cnb, pre_ncb, pre_ncnb, threshold)
    else:
        predict_answer(data_path, clf1, clf2, threshold)
