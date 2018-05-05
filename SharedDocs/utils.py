import os
import os.path as osp
import shutil
import time
import hashlib

from threading import Lock
from pathlib import Path


def create_new_doc(uid):
    """Create a new document along its lock file."""
    os.mkdir(osp.join('data', uid))
    Path(osp.join('data', uid, 'default.md')).touch()


def doc_exists(uid):
    return osp.exists(osp.join('data', uid))


def build_doc_path(uid, fname='default.md'):
    return osp.join('data', uid, fname)


def read_doc(uid, fname='default.md'):
    with open(build_doc_path(uid, fname), 'r') as f:
        return ''.join(f.readlines())


def copy_doc(src, dst):
    shutil.copy(src, dst)


def cat(fpath):
    print(os.popen('cat %s' % fpath).read())


def merge_docs(doc_uid, sync_uid, my_doc):
    """Three-way merge.

    diff3 myfile oldfile(sync_uid) yourfile(doc_uid)
    """
    myfile = build_doc_path(doc_uid, sync_uid + '_tmp.md')
    oldfile = build_doc_path(doc_uid, sync_uid + '.md')
    yourfile = build_doc_path(doc_uid)
    tmpfile = build_doc_path(doc_uid, 'tmp.md')
    with open(myfile, 'w') as f:
        f.write(my_doc)
    cmd = 'diff3 -3m %s %s %s > %s' % (myfile, oldfile, yourfile, tmpfile)
    os.popen(cmd).read()
    copy_doc(tmpfile, yourfile)
    copy_doc(tmpfile, oldfile)


def get_sync_uid(request):
    sha1 = hashlib.sha1()
    sha1.update(request.environ['REMOTE_ADDR'].encode())
    sha1.update(request.environ['HTTP_USER_AGENT'].encode())
    return sha1.hexdigest()


class DocumentLock(object):
    _doc_locks = {}
    global_lock = Lock()

    def __init__(self, doc_uid):
        self.doc_uid = doc_uid

    def __enter__(self):
        doc_uid = self.doc_uid
        if doc_uid not in self._doc_locks:
            with self.global_lock:
                if doc_uid not in self._doc_locks:
                    self._doc_locks[doc_uid] = Lock()
        self.lock = self._doc_locks[doc_uid]
        self.lock.acquire()

    def __exit__(self, exc_type, exc_value, traceback):
        self.lock.release()
