#!/usr/local/bin/python3
# coding: UTF-8
# Author: David
# Email: youchen.du@gmail.com
# Created: 2017-06-03 19:42
# Last modified: 2017-06-03 21:44
# Filename: main.py
# Description:
import requests
import json
import re
import os

TEST = False
DOWNLOAD_PICS = False

user_id = '3082822153'  # Search user id


def make_url(value, **kwargs):
    if not value:
        raise ValueError()
    url = 'https://m.weibo.cn/api/container/getIndex?type=uid&value=' + value
    for key, val in kwargs.items():
        url += '&{}={}'.format(key, val)
    return url


sess = requests.session()
if TEST:
    with open('info.json') as f:
        data = json.load(f)
else:
    url = make_url(user_id)
    print('GET', url)
    resp = sess.get(url)
    data = json.loads(resp.text)

for tab in data['tabsInfo']['tabs']:
    if tab['title'] == '微博':
        weibo_container_id = tab['containerid']
        break

info = {}
info['uid'] = data['userInfo']['id']
info['screen_name'] = data['userInfo']['screen_name']
info['description'] = data['userInfo']['description']

for key, val in info.items():
    print(key, ':', val)

cards = []
if TEST:
    with open('weibo.json') as f:
        data = json.load(f)
    cards.extend(data['cards'])
else:
    cnt = 1
    while True:
        print('GET', url)
        url = make_url(user_id, containerid=weibo_container_id,
                       page=cnt)
        cnt += 1
        resp = sess.get(url)
        data = json.loads(resp.text)
        if not data['cards']:
            break
        cards.extend(data['cards'])

strip_tag = re.compile(r'<.*?>')
weibos = []
for card in cards:
    weibo = card['mblog']
    item = {}
    item['id'] = weibo['id']
    item['content'] = strip_tag.sub('', weibo['text'])
    item['source'] = weibo['source']
    item['pics'] = []
    if weibo.get('pics', None):
        for pic in weibo['pics']:
            if pic.get('large', None):
                item['pics'].append(pic['large']['url'])
            else:
                item['pics'].append(pic['url'])
    if weibo.get('retweeted_status', None) and \
            weibo['retweeted_status'].get('pics', None):
        for pic in weibo['retweeted_status']['pics']:
            if pic.get('large', None):
                item['pics'].append(pic['large']['url'])
            else:
                item['pics'].append(pic['url'])
    weibos.append(item)

path = '{}_pics'.format(info['uid'])
if not os.path.exists(path):
    os.mkdir(path)
for weibo in weibos:
    print(weibo['content'])
    if DOWNLOAD_PICS and weibo['pics']:
        print('Has pics', len(weibo['pics']))
        for idx, pic_url in enumerate(weibo['pics']):
            pic = requests.get(pic_url)
            if pic.status_code == 200:
                fname = '{}_{}.png'.format(weibo['id'], idx)
                with open(os.path.join(path, fname), 'wb') as f:
                    f.write(pic.content)
            else:
                print('Download failed')
