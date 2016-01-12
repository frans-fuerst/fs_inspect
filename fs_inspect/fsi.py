#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import math
import logging


class indexer:
    
    def __init__(self):
        # expensive - do it only once
        self._base_dir = os.path.expanduser('~/.fsi/objects')

    def get_path(self, size):
        _result = os.path.join(
            self._base_dir, 
            '/'.join('%d' % size))
        try:
            os.makedirs(_result)
            return (_result, 0)
        except:
            if os.path.exists(os.path.join(_result, 'single.txt')):
                return (_result, 1)
            else:
                # todo: assert existing hash files
                return (_result, 2)

    def add(self, path):
        _file_count = 0
    
        for (_dir, _, files) in os.walk(path):
            for fname in files:
                _fullname = os.path.join(_dir, fname)
                if os.path.islink(_fullname):
                    logging.debug("skipping link %s" % _fullname)
                    continue
                _file_count += 1
                _filesize = os.path.getsize(_fullname)
                _time = os.path.getmtime(_fullname)
                _size_path, _state = self.get_path(_filesize)
                if _state == 0:
                    # file size not registered
                    # create a file with file name and modification date
                    
                    pass
                elif _state == 1:
                    # single file registered
                    pass
                else:
                    # more than one files already registered
                    pass
    
        print(_file_count)


if __name__ == '__main__':
    p = indexer()
    p.add(sys.argv[1])


'''
size_cats: 

    0:    2004 
    1:   14909 ****
    2:   79085 **************************
    3:  169468 ********************************************************
    4:   61196 ********************
    5:   12829 ****
    6:    7339 **
    7:     890 
    8:      47 
    9:      16 

files:  347783
sizes:   55014
folders: 70877

'''

