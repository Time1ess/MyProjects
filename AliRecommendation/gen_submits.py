#!/usr/local/bin/python3
# coding: UTF-8
# Author: David
# Email: youchen.du@gmail.com
# Created: 2016-12-13 19:55
# Last modified: 2016-12-13 20:02
# Filename: gen_submits.py
# Description:
precision = float(input('Minimum precision:'))
lines = []
with open('ans.txt', 'r') as f:
    for line in f:
        data, pre = line.strip('\n').rsplit(',', 1)
        pre = float(pre)
        if pre >= precision:
            lines.append(data)

with open('dutir_tianchi_recom_predict_david.txt', 'w') as f:
    for line in lines:
        f.write(line+'\n')
