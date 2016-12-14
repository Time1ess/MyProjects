#!/usr/bin/python
# coding: UTF-8
# Author: David
# Email: youchen.du@gmail.com
# Created: 2016-11-15 10:28
# Last modified: 2016-11-15 10:31
# Filename: tests_progress_panel.py
# Description:
import wx
import frames

def main():
    app = wx.App(False)
    frame = frames.ConsFrame(None, 'Fileme')
    frame.add_new_progress_bar('123')
    frame.add_new_progress_bar('234')
    frame.add_new_progress_bar('345')
    frame.add_new_progress_bar('456')
    frame.add_new_progress_bar('567')
    frame.add_new_progress_bar('678')
    frame.add_new_progress_bar('789')
    frame.add_new_progress_bar('890')
    frame.add_new_progress_bar('901')
    frame.add_new_progress_bar('012')
    app.MainLoop()

if __name__ == '__main__':
    main()
