#!/usr/bin/python
# coding: UTF-8
# Author: David
# Email: youchen.du@gmail.com
# Created: 2016-11-15 10:31
# Last modified: 2016-11-15 10:32
# Filename: tests_addrs_panel.py
# Description:
import wx
import frames

def main():
    app = wx.App(False)
    frame = frames.ConsFrame(None, 'Fileme')
    frame.append_new_addr('123')
    frame.append_new_addr('234')
    frame.append_new_addr('345')
    frame.append_new_addr('456')
    frame.append_new_addr('567')
    frame.append_new_addr('678')
    frame.append_new_addr('789')
    frame.append_new_addr('890')
    frame.append_new_addr('901')
    frame.append_new_addr('012')
    app.MainLoop()

if __name__ == '__main__':
    main()
