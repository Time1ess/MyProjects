#!/usr/local/bin/python3
# coding: UTF-8
# Author: David
# Email: youchen.du@gmail.com
# Created: 2016-12-04 19:17
# Last modified: 2016-12-04 19:34
# Filename: diff.py
# Description:


def reconstruct(path='ans.txt'):
    data = {}
    with open(path, 'r') as f:
        for line in f:
            uid, birth, gender, loc = line.strip('\n').split(',')
            data[uid] = (birth, gender, loc)
    return data


mine = reconstruct()
other = reconstruct('temp.csv')

cnt = 0
for uid, (birth, gender, loc) in mine.items():
    obirth, ogender, oloc = other[uid]
    if birth != obirth or ogender != gender or oloc != loc:
        cnt += 1
print('Total: %d' % len(mine))
print('Diff: %d' % cnt)
print('Diff rate: %.2f' % (cnt/len(mine)))
