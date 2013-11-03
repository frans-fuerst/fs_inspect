#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import hashlib
from optparse import OptionParser

class FsDb:

    def __init__(self, import_export_file = None):
        self._ie_file = import_export_file

    def register(self, path):
        _totalsize = 0
        for (path, dirs, files) in os.walk(os.path.abspath(path)):
            for fname in files:
                _fullname = os.path.join(path, fname)
                if os.path.islink(_fullname):
                    continue
                _hash = hashlib.sha1(open(_fullname).read()).hexdigest()
                #print _fullname, "(%s)" % fname
                #print _hash
                _totalsize += os.path.getsize(_fullname)
        return _totalsize

def test():
    fsdb = FsDb("fstdb.txt")
    fsdb.register("./example_fs")

if __name__ == "__main__":
    test()
