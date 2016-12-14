#!/usr/local/bin/python3
# coding: UTF-8
# Author: David
# Email: youchen.du@gmail.com
# Created: 2016-12-03 20:18
# Last modified: 2016-12-04 19:34
# Filename: models.py
# Description:
from collections import namedtuple


Weibo = namedtuple('Weibo', ['retweet_cnt', 'review_cnt', 'source',
                             'time', 'content'])
provsString = '''
    东北,辽宁,吉林,黑龙江
    华北,河北,山西,内蒙古,北京,天津
    华东,山东,江苏,安徽,浙江,台湾,福建,江西,上海
    华中,河南,湖北,湖南
    华南,广东,广西,海南,香港,澳门
    西南,云南,重庆,贵州,四川,西藏
    西北,新疆,陕西,宁夏,青海,甘肃
    境外,其他,海外
    None,None
    '''
provs = {}
for line in provsString.split('\n'):
    items = line.split(',')
    for item in items[1:]:
        provs[item] = items[0].strip()


class User:
    def __init__(self, uid=None, gender=None, birthday=None, location=None,
                 weibo=''):
        self.uid = uid
        self.gender = gender
        self.birthday = self.get_birth(birthday)
        self.location = self.get_loc(location)
        self.weibo = weibo

    @staticmethod
    def get_birth(birth):
        if birth is None:
            return None
        year = int(birth)
        if year >= 1990:
            return '1990+'
        elif year >= 1980:
            return '1980-1989'
        else:
            return '1979-'

    @staticmethod
    def get_loc(loc):
        if loc is None:
            return None
        loc = loc.split(' ')[0]
        return provs[loc]

    def __repr__(self):
        return '(%d, %s, %s, %s)' % (self.uid, self.gender,
                                     self.birthday, self.location)

    def add_fans(self, uid):
        self.fans.append(uid)

    def add_fans_plural(self, uids):
        self.fans.extend(uids)

    def add_weibo(self, weibo):
        self.weiboes.append(weibo)

    def add_weibo_plural(self, weiboes):
        self.weiboes.extend(weiboes)
