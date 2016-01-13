#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import math
import logging


class indexer:
    
    def __init__(self):
        # expensive - do it only once
        self._file_dir = os.path.expanduser('~/.fsi/files')
        self._name_dir = os.path.expanduser('~/.fsi/name')
        self._name_components = []
        
    def _get_name_index(self, word):
        assert word != ''
        if word in self._name_components:
            return self._name_components.index(word)
        self._name_components.append(word)
        return len(self._name_components) - 1
    
    def _get_name_components(self, path):
        #assert: '/{}'" not in path
        return '/'.join((str(self._get_name_index(n)) for n in path[1:].split('/')))
    
    def _restore_name(self, packed_path):
        return '/' + '/'.join((self._name_components[i] 
                         for i in (int(c) for c in packed_path.split('/'))))
    
    def get_path(self, size):
        _result = os.path.join(
            self._file_dir, 
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
            _dir = os.path.abspath(_dir)
            _basename = os.path.basename(_dir)
            if _basename in ('.git', '.svn', '__pycache__'):
                # todo: ignore does not work with walk - research
                logging.info('ignore %s' % _dir)
                continue
            
            for fname in files:
                _fullname = os.path.join(_dir, fname)
                assert _fullname[0] == '/'
                if os.path.islink(_fullname):
                    logging.debug("skipping link %s" % _fullname)
                    continue
                _file_count += 1
                if _file_count % 1000 == 0:
                    print(_file_count)
                _filesize = os.path.getsize(_fullname)
                _time = int(os.path.getmtime(_fullname) * 100)
                _size_path, _state = self.get_path(_filesize)
                
                _packed_name = self._get_name_components(_fullname)
#                assert (self._restore_name(_packed_name) == _fullname)
#                print(_fullname)
#                print(_packed_name)
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
    logging.basicConfig(level=logging.INFO)
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

