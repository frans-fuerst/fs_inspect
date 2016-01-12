#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import math
import logging

# expensive - do it only once
base_dir = os.path.expanduser('~/.fsi/objects')

def get_path(size):
    p = os.path.join(base_dir, '/'.join('%d' % size))
    try:
        os.makedirs(p)
    except:
        pass
    return p

if __name__ == '__main__':
    _sizes = {}
    _size_cats = {}
    _file_count = 0

    _path = sys.argv[1]
    for (_dir, _, files) in os.walk(_path):
        for fname in files:
            _fullname = os.path.join(_dir, fname)
            if os.path.islink(_fullname):
                logging.debug("skipping link %s" % _fullname)
                continue
            _file_count += 1
            _filesize = os.path.getsize(_fullname)
            p = get_path(_filesize)
            #print(p)
            _l1 = math.log(_filesize*_filesize,10) if _filesize > 0 else 0
#            _l2 = math.log(_l1, 10) if _l1 > 0 else 0
            _size_cat = int(_l1)
            #print(_filesize, _size_cat)
            if not _size_cat in _size_cats:
                _size_cats[_size_cat] = 0
            _size_cats[_size_cat] += 1
            if not _filesize in _sizes:
                _sizes[_filesize] = 0
            _sizes[_filesize] += 1

            

    # print(_size_cats)
    print(_file_count)
    print(len(_sizes))
    for s in sorted(_size_cats.keys()):
        print ("%d: %.6d %s" % (s, 
            _size_cats[s], '*' * int(_size_cats[s]/3000)))


'''
size_cats: 

    0: 002004 
    1: 014909 ****
    2: 079085 **************************
    3: 169468 ********************************************************
    4: 061196 ********************
    5: 012829 ****
    6: 007339 **
    7: 000890 
    8: 000047 
    9: 000016 

files: 347783
sizes: 55014

'''

