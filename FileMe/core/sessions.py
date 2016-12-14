#!/usr/bin/python
# coding: UTF-8
# Author: David
# Email: youchen.du@gmail.com
# Created: 2016-11-08 08:58
# Last modified: 2016-11-15 15:09
# Filename: sessions.py
# Description:
__metaclass__ = type

import hashlib
import socket
import traceback
import time
import os
import logging

from threading import current_thread

from multiprocessing.dummy import Pool, Lock
from random import randint

from settings import *


class _FileMasterSession:
    """
    FileMasterSession is initialized by SERVER during a file session.
    The session is suggested to run on a separated thread rather than
    main thread.
    """

    def __init__(self, remote, filename, files_dir, put_session, coo=None):
        """
        Author: David
        Desc:
                Set the prerequisites for this transmission session.
                target_host is to verify connected host.
                PS is to indicate whether a PUT_SESSION or GET_SESSION.
        """
        self._target_host = remote
        self._files_dir = files_dir
        self._filename = filename.rsplit('\\', 1)[-1]
        self._PS = put_session
        self._coo = coo

    def __call__(self, sock, *args):
        """
        Author: David
        Desc:
                Waitting a client to connect and verify its identity.
                Finish the file session with the verified client over TCP.
                The session will be aborted when reaching the timeout.
        """
        if self._PS:
            open_type = 'wb'
            file_ext = '.downloading'
        else:
            open_type = 'rb'
            file_ext = ''
        try:
            while True:
                sock.settimeout(30)
                client, addr = sock.accept()
                sock.settimeout(None)
                client.settimeout(None)
                if addr[0] != self._target_host:
                    client.send('REJ PUT 301 Source host doesn\'t match')
                    client.close()
                else:
                    _file = os.path.join(self._files_dir, self._filename)
                    _file += file_ext
                    logging.debug('Master session: %s' % _file)
                    if os.path.exists(_file) and self._PS:
                        logging.warning(_file+" already exists")
                        break
                    with open(_file, open_type) as f:
                        # If session is put session then receive bytes.
                        if self._PS:
                            if self._coo:
                                self._coo.create_session_bar(
                                    to_local=True,
                                    source=addr,
                                    filename=self._filename)
                            start = time.time()
                            received_bytes = 0
                            duration_bytes = 0
                            while True:
                                try:
                                    fbts = client.recv(BUF_SIZE)
                                    size, port = map(int, fbts.split(' '))
                                    break
                                except Exception, e:
                                    logging.error(traceback.format_exc())
                                    client.send('False')
                            logging.debug("Receive: "+_file+
                                          " Size: "+str(size))
                            client.send('True')
                            size_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            size_sock.bind(('', 0))
                            size_addr = (addr[0], port)
                            while True:
                                fbts = client.recv(BUF_SIZE)
                                size_sock.sendto(str(len(fbts)), size_addr)
                                if not fbts:
                                    break
                                duration_bytes += len(fbts)
                                f.write(fbts)
                                if self._coo:
                                    now = time.time()
                                    duration = now-start
                                    if duration < 1:
                                        continue
                                    start = now
                                    received_bytes += duration_bytes
                                    progress = 100.0*received_bytes/size
                                    speed = 1.0*duration_bytes/duration
                                    eta = (size-received_bytes)/speed
                                    duration_bytes = 0
                                    self._coo.update_session_bar(
                                        to_local=True,
                                        source=addr,
                                        filename=self._filename,
                                        progress=progress,
                                        speed=speed,
                                        eta=eta)
                            if self._coo:
                                self._coo.delete_session_bar(
                                    to_local=True,
                                    source=addr,
                                    filename=self._filename)
                        else:
                            if self._coo:
                                self._coo.create_session_bar(
                                    to_local=False,
                                    target=addr,
                                    filename=self._filename)
                            size = os.path.getsize(_file)
                            start = time.time()
                            send_bytes = 0
                            duration_bytes = 0
                            while True:
                                client.send(str(size))
                                checked = client.recv(BUF_SIZE)
                                if checked == 'True':
                                    break
                            logging.debug("Send: "+_file+" Size: "+str(size))
                            fbts = f.read(BUF_SIZE)
                            while fbts:
                                client.send(fbts)
                                duration_bytes += len(fbts)
                                fbts = f.read(BUF_SIZE)
                                if self._coo:
                                    now = time.time()
                                    duration = now-start
                                    if duration < 1:
                                        continue
                                    start = now
                                    send_bytes += duration_bytes
                                    progress = 100.0*send_bytes/size
                                    speed = 1.0*duration_bytes/duration
                                    eta = (size-send_bytes)/speed
                                    duration_bytes = 0
                                    self._coo.update_session_bar(
                                        to_local=False,
                                        target=addr,
                                        filename=self._filename,
                                        progress=progress,
                                        speed=speed,
                                        eta=eta)
                            if self._coo:
                                self._coo.delete_session_bar(
                                    to_local=False,
                                    target=addr,
                                    filename=self._filename)
                    if self._PS:
                        new_name = _file.replace(file_ext, '')
                        os.rename(_file, new_name)
                    break
        except socket.timeout:
            logging.warning('FileMasterSession timeout.')
        except IOError:
            logging.error(traceback.format_exc())
            # logging.error("No such file: %s" % (_file))
        except Exception:
            logging.error(traceback.format_exc())
        finally:
            size_sock.close()
            sock.close()


class _FileSlaveSession:
    """
    FileSlaveSession is initialized by CLIENT during a file session.
    The session is suggested to run on a separated thread rather than
    main thread.
    """

    def __call__(self, host, port, file_path, put_session, coo=None):
        """
        Author: David
        Desc:
                Connect to host:port and to PUT or GET specified file.
                The session will be aborted when reaching the timeout.
        """
        if put_session:
            open_type = 'rb'
        else:
            open_type = 'wb'
        try:
            sock = socket.socket()
            sock.settimeout(10)
            sock.connect((host, port))
            sock.settimeout(None)
            addr = (host, port)
            logging.debug('Slave Session: %s %d' % (file_path, put_session))
            if os.path.exists(file_path) and  not put_session:
                logging.warning(_file+" already exists")
                sock.close()
                return
            with open(file_path, open_type) as f:
                if put_session:
                    if coo:
                        coo.create_session_bar(
                            to_local=False,
                            target=addr,
                            filename=file_path)
                    size = os.path.getsize(file_path)
                    while True:
                        try:
                            size_port = randint(20000, 21000)
                            size_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            size_sock.bind(('0.0.0.0', size_port))
                            break
                        except Exception, e:
                            size_port = randint(20000, 21000)
                            continue
                    logging.debug("Send: "+file_path+" Size: "+str(size))
                    while True:
                        try:
                            sock.send('%d %d' % (size, size_port))
                            check_m = sock.recv(BUF_SIZE)
                            if check_m == 'True':
                                break
                        except Exception, e:
                            continue
                    start = time.time()
                    send_bytes = 0
                    duration_bytes = 0
                    fbts = f.read(BUF_SIZE)
                    while fbts:
                        sock.send(fbts)
                        msg, _ = size_sock.recvfrom(BUF_SIZE)
                        duration_bytes += int(msg)
                        fbts = f.read(BUF_SIZE)
                        if coo:
                            now = time.time()
                            duration = now-start
                            if duration < 1:
                                continue
                            start = now
                            send_bytes += duration_bytes
                            progress = 100.0*send_bytes/size
                            speed = 1.0*duration_bytes/duration
                            eta = (size-send_bytes)/speed
                            duration_bytes = 0
                            coo.update_session_bar(
                                to_local=False,
                                target=addr,
                                filename=file_path,
                                progress=progress,
                                speed=speed,
                                eta=eta)
                    if coo:
                        coo.delete_session_bar(
                            to_local=False,
                            target=addr,
                            filename=file_path)
                else:
                    if coo:
                        coo.create_session_bar(
                            to_local=True,
                            source=addr,
                            filename=file_path)
                    start = time.time()
                    received_bytes = 0
                    duration_bytes = 0
                    logging.debug("Receive: "+file_path+" Size: "+str(size))
                    logging.debug('receive file size')
                    while True:
                        try:
                            fbts = sock.recv(BUF_SIZE)
                            size = int(fbts)
                            break
                        except ValueError:
                            sock.send('False')
                        except Exception, e:
                            logging.error(e)
                    sock.send('True')
                    while True:
                        fbts = sock.recv(BUF_SIZE)
                        if not fbts:
                            break
                        duration_bytes += len(fbts)
                        f.write(fbts)
                        if coo:
                            now = time.time()
                            duration = now-start
                            if duration < 1:
                                continue
                            start = now
                            received_bytes += duration_bytes
                            progress = 100.0*received_bytes/size
                            speed = 1.0*duration_bytes/duration
                            eta = (size-received_bytes)/speed
                            duration_bytes = 0
                            coo.update_session_bar(
                                to_local=True,
                                source=addr,
                                filename=file_path,
                                progress=progress,
                                speed=speed,
                                eta=eta)
                        if coo:
                            coo.delete_session_bar(
                                to_local=True,
                                source=addr,
                                filename=file_path)
        except socket.timeout:
            logging.warning("FileSlaveSession timeout")
        except Exception, e:
            logging.error(traceback.format_exc())
        finally:
            size_sock.close()
            sock.close()


class SessionManager:
    """
    SessionManager is in charge of creating and maintaining session pool.
    """
    def __init__(self, transfermanager, session_count, files_dir='', coo=None):
        """
        Author: David
        Desc:
                maxs defines how much sessions run concurrently.
                curs defines how much sessions are running now.
                wq is for storing delayed jobs due to given maxs.
        """
        self._tm = transfermanager
        self._maxs = session_count
        self._curs = 0
        self._files_dir = files_dir
        self._wq = []
        self._pl = Pool()
        self._lock = Lock()
        self._coo = coo

    def __call__(self, *args):
        """
        Author: David
        Desc:
                When a SessionManager instance is called, it will maintain
                the current session count and fetch another job from wq if
                wq is not empty.
        """
        self._lock.acquire()
        self._curs -= 1
        self._lock.release()
        if self._wq:
            args = self._wq.pop(0)
            args[0](*args[1:])

    def _get_session(self, local, remote_ip, msg_port, port,
                     filename, force, delayed):
        """
        Author: David
        Desc:
                Init a GET session on SERVER, it will try to bind to local ip
                and given port, it will try another port if given port has been
                used and force is not set to True, or it will return reject
                message when force is set to True.
        """
        fms = _FileMasterSession(remote_ip, filename,
                                 self._files_dir, False, self._coo)
        while True:
            try:
                sock = socket.socket()
                sock.bind((local, port))
                sock.listen(1)
            except Exception, e:
                logging.warning(traceback.format_exc())
                if e.errno == 48 and force:
                    return (401, port)
                elif e.errno == 48 and not force:
                    port = randint(10000, 15000)
                else:
                    return (603, port)
            else:
                break
        try:
            self._lock.acquire()
            self._pl.apply_async(fms, args=(sock,),
                                 callback=self)
            self._curs += 1
            self._lock.release()
        except Exception, e:
            logging.warning(traceback.format_exc())
        if delayed:
            # notify remote_ip:msg_port that session has been dispatched.
            msg = self._tm._sgt_m(remote_ip, port, filename)
            self._tm.notify(msg, remote_ip)
        return (600, port)

    def get_session(self, local, remote, msg_port, port, filename, force):
        """
        Author: David
        Desc:
                Check if curs of SessionManager is reached its maxs, if True
                then put the job in wq, else run it now.
        """
        if self._curs >= self._maxs:
            self._wq.append(
                (self._get_session, local, remote,
                 msg_port, port, filename, force, True))
        else:
            return self._get_session(
                local, remote, msg_port, port, filename, force, False)
        return (402, port)

    def _put_session(self, local, remote_ip, msg_port, port,
                     filename, force, delayed):
        """
        Author: David
        Desc:
                Init a PUT session on SERVER, it will try to bind to local ip
                and given port, it will try another port if given port has been
                used and force is not set to True, or it will return reject
                message when force is set to True.

                [TODO]: merge _put_session and _get_session
        """
        fms = _FileMasterSession(remote_ip, filename,
                                 self._files_dir, True, self._coo)
        while True:
            try:
                sock = socket.socket()
                sock.bind((local, port))
                sock.listen(1)
            except Exception, e:
                logging.warning(traceback.format_exc())
                if e.errno == 48 and force:
                    return (401, port)
                elif e.errno == 48 and not force:
                    port = randint(10000, 15000)
                else:
                    return (403, port)
            else:
                break
        try:
            self._lock.acquire()
            self._pl.apply_async(fms, args=(sock,),
                                 callback=self)
            self._curs += 1
            self._lock.release()
        except Exception, e:
            logging.warning(traceback.format_exc())
        if delayed:
            # Should notify local:msg_port that session has been created.
            msg = self._tm._spt_m(remote_ip, port, filename)
            self._tm.notify(msg, remote_ip)
        return (400, port)

    def put_session(self, local, remote, msg_port, port, filename, force):
        """
        Author: David
        Desc:
                Check if curs of SessionManager is reached its maxs, if True
                then put the job in wq, else run it now.
        """
        if self._curs >= self._maxs:
            self._wq.append(
                (self._put_session, local, remote,
                 msg_port, port, filename, force, True))
        else:
            return self._put_session(
                local, remote, msg_port, port, filename, force, False)
        return (402, port)

    def _feed_get_session(self, host, port, file_path):
        """
        Author: David
        Desc:
                Init a GET session on CLIENT and run it.
        """
        fss = _FileSlaveSession()
        self._lock.acquire()
        file_path = os.path.join(self._files_dir, file_path)
        self._pl.apply_async(
            fss,
            args=(host, port, file_path, False, self._coo),
            callback=self)
        self._curs += 1
        self._lock.release()
        return 700

    def feed_get_session(self, host, port, file_path):
        """
        Author: David
        Desc:
                Check if curs of SessionManager is reached its maxs, if True
                then put the job in wq, else run it now.
        """
        if self._curs >= self._maxs:
            self._wq.append((self._feed_get_session, host, port, file_path))
        else:
            return self._feed_get_session(host, port, file_path)
        return 502

    def _feed_put_session(self, host, port, file_path):
        """
        Author: David
        Desc:
                Init a PUT session on CLIENT and run it.
        """
        fss = _FileSlaveSession()
        self._lock.acquire()
        self._pl.apply_async(
            fss,
            args=(host, port, file_path, True, self._coo),
            callback=self)
        self._curs += 1
        self._lock.release()
        return 500

    def feed_put_session(self, host, port, file_path):
        """
        Author: David
        Desc:
                Check if curs of SessionManager is reached its maxs, if True
                then put the job in wq, else run it now.
        """
        if self._curs >= self._maxs:
            self._wq.append((self._feed_put_session, host, port, file_path))
        else:
            return self._feed_put_session(host, port, file_path)
        return 502

    def terminate(self):
        """
        Author: David
        Desc:
                Close session pool.
        """
        while True:
            self._lock.acquire()
            if self._curs == 0:
                self._pl.close()
                self._pl.terminate()
                self._pl.join()
                self._lock.release()
                break
            else:
                self._lock.release()
                time.sleep(3)
