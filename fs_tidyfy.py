#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
from optparse import OptionParser

class FsDb:

    def __init__(self, import_export_file = None):
        self._ie_file = import_export_file

    def register(self, path):
        for (path, dirs, files) in os.walk(os.path.abspath(path)):
            for fname in files:
                fullname = os.path.join(path, fname)
                print fullname

def test():
    fsdb = FsDb("fstdb.txt")
    fsdb.register("./example_fs")

if __name__ == "__main__":
    test()
