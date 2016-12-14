#!/usr/local/bin/python3
# coding: UTF-8
# Author: David
# Email: youchen.du@gmail.com
# Created: 2016-12-03 20:49
# Last modified: 2016-12-04 19:45
# Filename: logistic.py
# Description:
from logging import info
from collections import defaultdict

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model.logistic import LogisticRegression as LR

from dataset import load_dataset
from utils import timeit

FEATURE_NUMS = 10000

t_users, t_weiboes, v_users, v_weiboes = load_dataset()

# Reduce weiboes to ONE weibo
info('Reduce weiboes')


@timeit
def reduce_weiboes(_weiboes):
    wbs = defaultdict(str)
    for uid, wb_list in _weiboes.items():
        for wb in wb_list:
            wbs[uid] += wb.content
    return wbs


wbs = reduce_weiboes(t_weiboes)
v_wbs = reduce_weiboes(v_weiboes)

wbs.update(v_wbs)
users = t_users+v_users
for user in users:
    user.weibo = wbs.get(user.uid, '')


info('Calculate TF-IDFS')


@timeit
def cal_tf_idfs():
    _tf_idf = TfidfVectorizer(max_features=FEATURE_NUMS)
    tf_idfs = _tf_idf.fit_transform(list(map(lambda x: x.weibo, users)))
    return tf_idfs


tf_idfs = cal_tf_idfs()


@timeit
def logistic_on_attr(users, attr, sep_idx=3200):
    classifier = LR()
    classifier.fit(tf_idfs[:sep_idx],
                   list(map(lambda x: getattr(x, attr), users[:sep_idx])))
    for idx, user in enumerate(users[sep_idx:], sep_idx):
        setattr(user, attr, classifier.predict(tf_idfs[idx]))


info('Classify gender')
logistic_on_attr(users, 'gender')

info('Classify birthday')
logistic_on_attr(users, 'birthday')

info('Classify location')
logistic_on_attr(users, 'location')

@timeit
def write_file(users, name='final.csv'):
    with open(name, 'w') as f:
        f.write('uid,age,gender,province\n')
        for user in users[3200:]:
            f.write('%s,%s,%s,%s\n' % (user.uid, user.birthday[0],
                                       user.gender[0], user.location[0]))


info('Write answer to file')
write_file(users)
