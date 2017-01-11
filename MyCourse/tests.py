#!/usr/local/bin/python3
# coding: UTF-8
# Author: David
# Email: youchen.du@gmail.com
# Created: 2017-01-08 09:48
# Last modified: 2017-01-11 09:14
# Filename: tests.py
# Description:
from CourseHelper import CourseHelper 
from private_data import username, password
# proxies={'http':'http://127.0.0.1:8888'}
proxies = {}
ch = CourseHelper(username, password, proxies = proxies)
choice = ''
while True:
    choice = ch.help_my_course()
    if choice == '':
        break
ch.start()
