#!/usr/bin/python
# coding: UTF-8
# Author: David
# Email: youchen.du@gmail.com
# Created: 2016-11-08 20:15
# Last modified: 2016-11-15 19:52
# Filename: main.py
# Description:
__metaclass__ = type

import os
import wx
import time

from threading import Thread

from gui.frames import ConsFrame
from core.settings import *
from core.manager import TransferManager
from core.sessions import SessionManager
from controllers import Coordinator


def main():
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)
    coo = Coordinator()
    m = TransferManager(9005, files_dir='files', hook=coo.message_hook)
    coo.set_manager(m)
    app = wx.App(False)
    frame = ConsFrame(None, 'FileMe')
    coo.set_gui(frame)
    frame.set_coordinator(coo)
    sm = SessionManager(m, 10, m._files_dir, coo)
    m.add_session_manager(sm)
    m.start()
    m.add_user_confirm_func('PUT', frame.confirm_action)
    m.add_user_confirm_func('GET', frame.confirm_action)
    app.MainLoop()
    m.terminate()

if __name__ == '__main__':
    main()
