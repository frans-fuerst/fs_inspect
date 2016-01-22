#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import fsi

def test_fsi():
    _basedir = os.path.dirname(__file__)
    _storage_dir = os.path.join(_basedir, 'fsi-storage-test1')
    try:
        fsi.rmdirs(_storage_dir)
    except fsi.file_not_found_error:
        pass
            
    with fsi.indexer(storage_dir=_storage_dir) as i:
        assert os.path.isdir(_storage_dir)
        i.add('.')
    assert False
    
if __name__ == '__main__':
    test_fsi()