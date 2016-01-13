#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import math
import logging
import time
import timeit
import json
import hashlib
import functools
import subprocess

def sha1_external(filename):
    ''' fast with large files '''
    output = subprocess.Popen(["sha1sum", filename], stdout=subprocess.PIPE).communicate()[0].decode()
    return output.split(' ')[0]

def sha1_internal(filename, chunksize=2**15, bufsize=-1):
    ''' fast with small files '''
    # max-limit-of-bytes-in-method-update-of-hashlib-python-module
    # http://stackoverflow.com/questions/4949162
    sha1_hash = hashlib.sha1()
    with open(filename, 'rb', bufsize) as _file:
        for chunk in iter(functools.partial(_file.read, chunksize), b''):
            sha1_hash.update(chunk)
    return sha1_hash.hexdigest()


class indexer:

    class name_component_store:
        def __init__(self):
            self._idx_to_word = {}
            self._word_to_idx = {}
            self._size = 0

        def __len__(self):
            return self._size

        def get_index(self, word):
            assert word != ''
            if word in self._word_to_idx:
                return self._word_to_idx[word]
            _index = self._size
            self._size += 1
            self._word_to_idx[word] = _index
            self._idx_to_word[_index] = word
            return _index

        def __getitem__(self, index):
            return self._idx_to_word[index]
        
        def save(self, filename):
            json.dump(self._word_to_idx, open(filename, 'w'))

        def load(self, filename):
            _idx2word = {}
            _word2idx = json.load(open(filename))
            for word, idx in _word2idx.items():
                _idx2word[idx] = word
            self._idx_to_word, self._word_to_idx, self._size = (
                _idx2word, _word2idx, len(_idx2word))

        def __eq__(self, other):
            return (self._size == other._size and
                    self._idx_to_word == other._idx_to_word and
                    self._word_to_idx == other._word_to_idx)
            
    def __init__(self):
        # expensive - do it only once
        self._file_dir = os.path.expanduser('~/.fsi/files')
        self._name_file = os.path.expanduser('~/.fsi/name_parts.txt')
        self._name_component_store = indexer.name_component_store()

    def __enter__(self):
        self._name_component_store.load(self._name_file)
        return self

    def __exit__(self, data_type, value, tb):
        t = time.time()
        self._name_component_store.save(self._name_file)
        logging.debug("save: %.2fs", time.time() - t)
        _test_store = indexer.name_component_store()
        t = time.time()
        _test_store.load(self._name_file)
        logging.debug("load: %.4fs", time.time() - t)
        assert _test_store == self._name_component_store

    def _get_name_components(self, path):
        #assert: '/{}'" not in path
        return '/'.join((str(self._name_component_store.get_index(n))
                             for n in path[1:].split('/')))

    def _restore_name(self, packed_path):
        return '/' + '/'.join((self._name_component_store[i]
                         for i in (int(c) for c in packed_path.split('/'))))

    def _store_single_file(self, size_path, name, mod_time):
        with open(os.path.join(size_path, 'single.txt'), 'w') as _f:
            _f.write(name)
            _f.write(" ")
            _f.write(str(mod_time))
            
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
        _perf_measure_t = time.time()
        _total_size = 0
        
        for (_dir, _dirs, files) in os.walk(path, topdown=True):
            _dirs[:] = [d for d in _dirs if d not in ('.git', '.svn', '__pycache__')]

            _dir = os.path.abspath(_dir)
            for fname in files:
                _fullname = os.path.join(_dir, fname)
                assert _fullname[0] == '/'
                if not os.path.isfile(_fullname):
                    #logging.debug("skipping link %s" % _fullname)
                    continue
                try:
                    _filesize = os.path.getsize(_fullname)
                    _time = int(os.path.getmtime(_fullname) * 100)
                except:
                    logging.warn('permission denied: "%s"', _fullname)
                    continue

                _file_count += 1
                _total_size += _filesize

                if _file_count % 1000 == 0:
                    _t = time.time()
                    logging.debug("performance info: #files:%d, %.2fms/file, #words:%d",
                        _file_count,
                        (_t - _perf_measure_t),
                        len(self._name_component_store) / 2)
                    _perf_measure_t = _t

                _size_path, _state = self.get_path(_filesize)

                _packed_name = self._get_name_components(_fullname)
                assert (self._restore_name(_packed_name) == _fullname)
                # logging.debug("%s => %s", _fullname, _packed_name)
                # print(_packed_name, _time)
                _t = time.time()
                if _filesize < 60000:
                    _hash = sha1_internal(_fullname)
                else:
                    _hash = sha1_external(_fullname)
                _t = time.time() - _t
                    
                logging.debug("%s, %d, %s, %d", fname, _filesize, _hash, _t * 1000)
    
                if _state == 0:
                    # file size not registered
                    # create a file with file name and modification date
                    self._store_single_file(_size_path, _packed_name, _time)
                    pass
                elif _state == 1:
                    # single file registered
                    pass
                else:
                    # more than one files already registered
                    pass

        print(_file_count, 'frame: {0:,} bytes'.format(_total_size))


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    with indexer() as p:
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

