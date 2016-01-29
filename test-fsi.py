#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import coverage

# TODO: test following symlinks to directories
#       test symlinks to equal directories
#       test: .fsi-content is equal Python2/3
#       test: .fsi-content is equal with or without abortion via CTRL-C
#       test: .fsi-content is equal after 1st and 2nd run
#       if file content/size has changed old reference has to be deleted
#       introduce a corresponding directory based search folder

class cov:
    def __enter__(self):
        self._cov = coverage.coverage()
        self._cov.start()
        return self

    def __exit__(self, *arg):
        self._cov.stop()
        self._cov.save()
        self._cov.html_report()

def test_fsi():
    with cov():
        import fsi
        def test_fs_erase(path):
            try:
                fsi.rmdirs(path)
            except fsi.file_not_found_error:
                pass

        def test_fs_populate(path):
            dir1 = os.path.join(path, 'dir1')
            dir2 = os.path.join(path, 'dir2')
            fsi.make_dirs(dir1)
            fsi.make_dirs(dir2)
            open(os.path.join(dir1, 'file_a'), 'w').write('content1')
            open(os.path.join(dir1, 'file_c'), 'w').write('content2')
            open(os.path.join(dir2, 'file_b'), 'w').write('content1')
        _basedir = os.path.dirname(__file__)
        _storage_dir = os.path.join(_basedir, 'fsi-storage-test1')
        _test_fs = os.path.join(_basedir, 'test_fs')
        try:
            fsi.rmdirs(_storage_dir)
        except fsi.file_not_found_error:
            pass

        with cov() as c:
            pass

        with fsi.indexer(storage_dir=_storage_dir) as i:
            test_fs_erase(_test_fs)
            assert os.path.isdir(_storage_dir)
            try:
                i.add(_test_fs)
                assert False, 'exception should be thrown'
            except fsi.file_not_found_error:
                pass
            test_fs_populate(_test_fs)
            result = i.add(_test_fs)
            assert result['file_count'] == 3

if __name__ == '__main__':
    test_fsi()