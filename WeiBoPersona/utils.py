#!/usr/local/bin/python3
# coding: UTF-8
# Author: David
# Email: youchen.du@gmail.com
# Created: 2016-12-04 09:42
# Last modified: 2016-12-04 19:44
# Filename: utils.py
# Description:
import time
from logging import info


def timeit(func):
    def _timeit(*args, **kwargs):
        s = time.time()
        ans = func(*args, **kwargs)
        e = time.time()
        info('Time cost for <%s>: %.2f s' % (func.__name__, e-s))
        return ans
    return _timeit
