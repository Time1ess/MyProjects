#!/usr/local/bin/python3
# coding: UTF-8
# Author: David
# Email: youchen.du@gmail.com
# Created: 2016-12-09 13:44
# Last modified: 2016-12-09 14:07
# Filename: padas_test.py
# Description:
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt


s = pd.Series([1, 3, 5, np.nan, 6, 8])
print(s)

dates = pd.date_range('20130101', periods=6)
print(dates)

df = pd.DataFrame(np.random.randn(6, 4), index=dates, columns=list('ABCD'))
print(df)

df2 = pd.DataFrame(
    {'A': 1.,
     'B': pd.Timestamp('20130102'),
     'C': pd.Series(1, index=list(range(4)), dtype='float'),
     'D': np.array([3]*4, dtype='int32'),
     'E': pd.Categorical(['test', 'train', 'test', 'train']),
     'F': 'foo' })
print(df2)
print(df2.dtypes)

print(df.head())
print(df.tail(3))

print(df.index)
print(df.columns)
print(df.values)

print(df.describe())
print(df.T)

print(df.sort_index(axis=1, ascending=False))
print(df.sort_values(by='B', ascending=False))

print(df['A'])

print(df[0:3])
print('---')
print(df['20130102':'20130104'])

print(df.loc[dates[0]])
print(df.loc[:, ['A', 'B']])
print(df.loc['20130102':'20130104', ['A', 'B']])

print(df.iloc[3])
print(df[df > 0])
df2 = df.copy()
df2['E'] = ['one', 'one', 'two', 'three', 'four', 'three']

print(df2)
print(df2[df2['E'].isin(['two', 'four'])])
