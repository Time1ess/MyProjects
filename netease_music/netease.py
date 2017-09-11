#!/usr/bin/env python3
# coding: UTF-8
# Author: David
# Email: youchen.du@gmail.com
# Created: 2017-09-10 20:00
# Last modified: 2017-09-11 10:24
# Filename: netease.py
# Description:
import base64
import json
import requests

from Crypto.Cipher import AES


class NetEaseMusic:
    headers = {
        'Referer': 'http://music.163.com/',
        'User-Agent': (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87'
            ' Safari/537.36'),
    }
    default_param2 = '010001'
    default_param3 = (
        '00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b7251'
        '52b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ec'
        'bda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d81'
        '3cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7')
    default_param4 = '0CoJUm6Qyw8W8jud'
    encSecKey = (
        'babc57ca9e9ffb0a879ae290ac6cba6f60620aa9ae3b36a84585e23bbc73d73b13'
        'a2ebab4aa2ee80544d255727adc5a04db613d77d02a62a52b3a03134d16f191d54'
        '675f560f797c7f03e3a30c43df8b1b49878fd225b62f5f78041427debc3e95b935'
        '82f130618630702621da4eda9c71af91836cc39ab3b760b033643a1889')

    @staticmethod
    def get_comment_url(uid):
        url = ('http://music.163.com/weapi/v1/resource/comments/R_SO_4_'
               '{}?csrf_token=')
        return url.format(uid)

    @staticmethod
    def get_music_url(uid):
        url = 'http://music.163.com/weapi/song/enhance/player/url?csrf_token='
        return url

    @staticmethod
    def get_comment_param(uid, page):
        offset = (page - 1) * 20
        rid = '"rid":"R_SO_4_{}"'.format(uid)
        param = '{'+rid
        param += ',"offset":"{}","total":"{}","limit":"20",'.format(
            offset, 'true' if page == 0 else 'false')
        param += '"csrf_token":""}'
        return param

    @staticmethod
    def get_music_param(uid):
        param = '{"ids":"['+uid+']","br":128000,"csrf_token":""}'
        return param

    def get_comment_payload(self, uid, page=1, param2=default_param2,
                            param3=default_param3, param4=default_param4):
        param1 = self.get_comment_param(uid, page)
        rand_str = '0' * 16
        encText = self.AESEncrypt(param1, param4)
        encText = self.AESEncrypt(encText.decode(), rand_str)
        return encText, self.encSecKey

    def get_music_payload(self, uid, param2=default_param2,
                          param3=default_param3, param4=default_param4):
        param1 = self.get_music_param(uid)
        rand_str = '0' * 16
        encText = self.AESEncrypt(param1, param4)
        encText = self.AESEncrypt(encText.decode(), rand_str)
        return encText, self.encSecKey

    def get_json(self, uid, type, *args, **kwargs):
        url_attr = 'get_{}_url'.format(type)
        if not hasattr(self, url_attr):
            raise AttributeError('No such type')
        url = getattr(self, url_attr)(uid)

        param_attr = 'get_{}_payload'.format(type)
        if not hasattr(self, param_attr):
            raise AttributeError('No such type')
        params, encSecKey = getattr(self, param_attr)(uid, *args, **kwargs)
        data = {
            'params': params,
            'encSecKey': encSecKey,
        }
        resp = requests.post(url, data=data, headers=self.headers)
        jd = json.loads(resp.content)
        return jd

    @staticmethod
    def AESEncrypt(message, key, iv='0102030405060708'):
        pad = 16 - len(message) % 16
        message += pad * chr(pad)
        encryptor = AES.new(key, AES.MODE_CBC, iv)
        encrypted_text = encryptor.encrypt(message)
        encoded_text = base64.b64encode(encrypted_text)
        return encoded_text


def main():
    uid = '504835560'
    nem = NetEaseMusic()
    print(nem.get_json(uid, 'music'))
    print(nem.get_json(uid, 'comment'))


if __name__ == '__main__':
    main()
