#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import time
import json
import hashlib
import functools
import subprocess
import contextlib
import shutil
import argparse

DEBUG_MODE = False

class fsi_error(Exception):
    def __init__(self):
        Exception.__init__(self)

class path_exists_error(fsi_error):
    pass

class file_not_found_error(fsi_error):
    pass

class read_permission_error(fsi_error):
    pass

class not_indexed_error(fsi_error):
    def __init__(self, file_instance=None):
        fsi_error.__init__(self)
        self.file_info = file_instance

def fopen(filename, mode='r', buffering=1):
    try:
        return open(filename, mode, buffering)
    except OSError as ex:
        if ex.errno == 2:
            raise file_not_found_error()
        elif ex.errno == 13:
            raise read_permission_error()
        raise

def rmdirs(path):
    try:
        shutil.rmtree(path)
    except OSError as ex:
        if ex.errno == 2:
            raise file_not_found_error()
        elif ex.errno == 13:
            raise read_permission_error()
        raise

@contextlib.contextmanager
def wopen(filename, mode='r', buffering=1):
    with fopen(filename, mode, buffering) as f:
        yield f

def make_dirs(path):
    try:
        os.makedirs(os.path.expanduser(path))
    except OSError as ex:
        if ex.errno == 17:
            raise path_exists_error()
        raise

def load_json(filename):
    return json.load(fopen(filename), encoding='utf-8')

if sys.version_info[0] >= 3:

    def dump_json(data, filename):
        json.dump(data, fopen(filename, 'w'),
                  sort_keys=True,
                  indent=4, separators=(',', ': '))

    def path_join(path1, path2):
        return os.path.join(path1, path2)

else:
    def dump_json(data, filename):
        json.dump(data, fopen(filename, 'w'), encoding='utf-8',
                  sort_keys=True,
                  indent=4, separators=(',', ': '))

    def path_join(path1, path2):
        return os.path.join(path1, path2).decode('utf-8')


def sha1_external(filename):
    ''' fast with large files '''
    output = subprocess.Popen(
        ["sha1sum", filename.encode('utf-8')],
        stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
    # todo: check plausibility (length, "permission denied", etc)
    return output.split(' ')[0]


def sha1_internal(filename, chunksize=2**15, bufsize=-1):
    ''' fast with small files '''
    # max-limit-of-bytes-in-method-update-of-hashlib-python-module
    # http://stackoverflow.com/questions/4949162
    sha1_hash = hashlib.sha1()
    with wopen(filename, 'rb', bufsize) as _file:
        for chunk in iter(functools.partial(_file.read, chunksize), b''):
            sha1_hash.update(chunk)
    return sha1_hash.hexdigest()


class file_info:

    def __init__(self, filename, word_store=None):
        assert filename[0] == '/'
        self._fullname = filename
        self._size = None
        self._packed_path = None
        self._sha1 = None
        self._mdate = None
        self._word_store = word_store

    def __str__(self):
        return self._fullname

    def path(self):
        return self._fullname

    def basename(self):
        return os.path.basename(self._fullname)

    def size(self):
        if self._size is None:
            self._size = os.path.getsize(self._fullname)
        return self._size

    def mdate(self):
        if self._mdate is None:
            self._mdate = str(int(os.path.getmtime(self._fullname) * 100))
        return self._mdate

    @staticmethod
    def fast_sha1(filename, size):
        if size < 50000:
            return sha1_internal(filename)
        else:
            return sha1_external(filename)

    def hash_sha1(self):
        if self._sha1 is None:
            self._sha1 = file_info.fast_sha1(self._fullname, self.size())
        return self._sha1

    def hash_file_path(self, size_path):
        return os.path.join(size_path, self.hash_sha1())

    def is_normal_file(self):
        return (os.path.isfile(self._fullname) and
                not os.path.islink(self._fullname))

    def packed_path(self):
        ''' turn "/home/user/some/directory" into index based string
            e.g. "2.7.4.9"'''
        #todo: assert: '/{}'" not in path
        if self._packed_path is None:
            assert self._word_store is not None
            self._packed_path = self._word_store.get_packed(self._fullname)
        return self._packed_path


class indexer:

    class name_component_store:

        def __init__(self):
            self._idx_to_word = {}
            self._word_to_idx = {}
            self._size = 0
            self._dirty = False

        def __len__(self):
            return self._size

        def _get_index(self, word, const):
            assert word != ''
            if word in self._word_to_idx:
                return self._word_to_idx[word]
            if const:
                raise not_indexed_error()
            self._dirty = True
            _index = self._size
            self._size += 1
            self._word_to_idx[word] = _index
            self._idx_to_word[_index] = word
            return _index

        def get_packed(self, path, const=False):
            return '.'.join(
                (str(self._get_index(n, const))
                 for n in path[1:].split('/')))

        def restore(self, packed_path):
            ''' opposite of _get_name_components(): restores the original path
                on the filesystem '''
            return '/' + '/'.join((
                self[i] for i in (int(c) for c in packed_path.split('.'))))

        def __getitem__(self, index):
            return self._idx_to_word[index]

        def save(self, filename):
            if self._dirty:
                dump_json(self._word_to_idx, filename)
            self._dirty = False

        def load(self, filename):
            _idx2word = {}
            try:
                _word2idx = load_json(filename)
            except file_not_found_error:
                # file does not exist - just exit
                return
            for word, idx in _word2idx.items():
                _idx2word[idx] = word
            self._idx_to_word, self._word_to_idx, self._size = (
                _idx2word, _word2idx, len(_idx2word))

        def __eq__(self, other):
            if (self._size == other._size and
                self._idx_to_word == other._idx_to_word and
                self._word_to_idx == other._word_to_idx):
                return True
            else:
                print(self._size, other._size)
                print(len(self._idx_to_word), len(other._idx_to_word))
                print(len(self._word_to_idx), len(other._word_to_idx))
                k1 = sorted(self._word_to_idx.keys())
                k2 = sorted(other._word_to_idx.keys())
                for i in range(len(k1)):
                    print(k1[i], k2[i])
                return False

    def __init__(self, storage_dir='~/.fsi'):
        _storage_dir = os.path.expanduser(storage_dir)
        self._ignore_pattern = ('.git', '.svn', '__pycache__', '.fsi')
        try:
            make_dirs(_storage_dir)
        except path_exists_error:
            pass

        self._bysize_dir = os.path.join(_storage_dir, 'sizes')
        self._name_file = os.path.join(_storage_dir, 'name_parts.txt')
        self._name_component_store = indexer.name_component_store()
        self._tracked_dirs_filename = os.path.join(_storage_dir, 'tracked_dirs')

        self._name_component_store.load(self._name_file)
        self._tracked_directories = self._load_tracked_dir_list()

    def tracked_dir_list(self) -> list:
        return self._tracked_directories

    def _load_tracked_dir_list(self):
        try:
            _result = load_json(self._tracked_dirs_filename)
        except file_not_found_error:
            # todo: assert isempty(self._bysize_dir)
            assert not os.path.exists(self._name_file)
            _result = []

        assert isinstance(_result, list)
        return _result

    def _save_tracked_dir_list(self):
        dump_json(self._tracked_directories, self._tracked_dirs_filename)

    def __enter__(self):
        return self

    def __exit__(self, data_type, value, tb):
        if DEBUG_MODE:
            # store and load to debug structure for test purposes
            t = time.time()
            self._name_component_store.save(self._name_file)
            logging.debug("save: %.2fs", time.time() - t)
            _test_store = indexer.name_component_store()
            t = time.time()
            _test_store.load(self._name_file)
            logging.debug("load: %.4fs", time.time() - t)
            assert _test_store == self._name_component_store
        else:
            self._name_component_store.save(self._name_file)
        self._save_tracked_dir_list()

    @staticmethod
    def _store_single_file(size_path, name):
        ''' write a file with meta information about a single file '''
        with wopen(os.path.join(size_path, 'dirinfo'), 'w') as _f:
            _f.write("single ")
            _f.write(name)

    @staticmethod
    def _read_dirinfo(directory):
        return fopen(os.path.join(directory, 'dirinfo')).readline().split(' ')

    @staticmethod
    def _hashed_files(filename):
        _lines = (l.strip().split() for l in fopen(filename).readlines())
        # return ((h.strip(), d.strip()) for h, d in _lines)
        return {h.strip(): d.strip() for h, d in _lines}

    @staticmethod
    def _write_file_reference(file_obj, file_instance):
        file_obj.write(file_instance.packed_path())
        file_obj.write(" ")
        file_obj.write(file_instance.mdate())
        file_obj.write("\n")

    def _get_size_path(self, file_instance):
        ''' returns a tuple with a path representing the file's size and the
            status of the path.
            Creates it if not existent. status is 0 for path did not exist yet,
            1 for path exists with a 'dirinfo' and 1 for path exists with
            several file information.
        '''
        _result = os.path.join(
            self._bysize_dir,
            '/'.join('%d' % file_instance.size()))

        try:
            make_dirs(_result)
            return (_result, None)
        except path_exists_error:
            try:
                _dirinfo = indexer._read_dirinfo(_result)
                return (_result, _dirinfo)
            except file_not_found_error:
                return (_result, None)
                # todo: assert existing hash files

    def _get_state(self, file_instance):
        ''' checks whether the file is indexed and it has duplicates
        '''
        _size_path, _state = self._get_size_path(file_instance)

        if _state is None:
            return False, None, None
        else:
            if _state[0] == 'single':
                return True, True, {}
            elif _state[0] == 'multi':
                try:
                    _hashed_files = indexer._hashed_files(
                        os.path.join(_size_path, file_instance.packed_path()))
                    return True, False, _hashed_files
                except file_not_found_error:
                    return True, False, {}
            else:
                assert False

    def _add_file(self, file_instance):
        _size_path, _state = self._get_size_path(file_instance)
        _packed_path = file_instance.packed_path()

        if DEBUG_MODE:
            assert (self._name_component_store.restore(_packed_path) ==
                    file_instance.path())

        # logging.debug("%s => %s", filename, _packed_path)
        # print(_packed_path, _time)

        if DEBUG_MODE:
            assert (sha1_internal(file_instance.path()) ==
                    sha1_external(file_instance.path()))

        # === no state changing operations before
        # === red exception safety line ===============================
        # === no exceptions after

        if _state is None:
            # file size not registered
            # create a file with file name and modification date
            indexer._store_single_file(_size_path, _packed_path)
        else:
            if _state[0] == 'single':
                _other_packed_path = _state[1]
                if _packed_path == _other_packed_path:
                    # we found the reference to the current file
                    # so nothing has changed and nothing left to do
                    pass
                else:
                    # we found another file with the same file - we have
                    # to turn this entry into a multi-entry
                    #print('collision')
                    indexer._promote_to_multi(
                        _size_path,
                        file_info(
                            self._name_component_store.restore(_other_packed_path),
                            self._name_component_store),
                        file_instance)

            elif _state[0] == 'multi':
                # we found a file size folder which contains one or more file
                # references with hashes and modification date so we have to
                # add the current files' information
                indexer._update_multi(_size_path, file_instance)
            else:
                # everything else should not happen
                assert False

    @staticmethod
    def _promote_to_multi(size_path, other_file, new_file):
        ''' turn a single file entry into a multi file entry
        '''
        # todo raise if any hash cannot be computed
        # todo raise if second file does not exist

        # === red exception safety line ========================================

        dir_info_fn = os.path.join(size_path, 'dirinfo')
        if new_file.hash_sha1() == other_file.hash_sha1():
            logging.debug('found identical: %s %s',
                          new_file.path(), other_file.path())
            hash_fn = os.path.join(size_path, new_file.hash_sha1())
            with wopen(dir_info_fn, 'w') as fd, wopen(hash_fn, 'w') as fh1:
                fd.write('multi')
                indexer._write_file_reference(fh1, other_file)
                indexer._write_file_reference(fh1, new_file)
        else:
            hash1_fn = os.path.join(size_path, other_file.hash_sha1())
            hash2_fn = os.path.join(size_path, new_file.hash_sha1())
            with wopen(dir_info_fn, 'w') as fd, \
                 wopen(hash1_fn, 'w') as fh1, \
                 wopen(hash2_fn, 'w') as fh2:
                fd.write('multi')
                indexer._write_file_reference(fh1, other_file)
                indexer._write_file_reference(fh2, new_file)

        os.symlink(other_file.hash_sha1(),
                   os.path.join(size_path, other_file.packed_path()))
        os.symlink(new_file.hash_sha1(),
                   os.path.join(size_path, new_file.packed_path()))

    @staticmethod
    def _update_multi(size_path, file_instance):
        ''' we have to update a given dirinfo file. with a given file
            specification'''
        assert os.path.exists(os.path.join(size_path, 'dirinfo'))

        # symlink name to hash file e.g. /2/3/7/2/2.6.1.23 -> 410ae0d2bcadca8..
        _composite_path = os.path.join(size_path, file_instance.packed_path())

        try:
            # try to read list of file with same hash - might fail when no
            # duplicate file has been registered yet
            _hashed_files = indexer._hashed_files(_composite_path)
        except file_not_found_error:
            # file does not exist - create it with one entry
            with wopen(file_instance.hash_file_path(size_path), 'w') as fh:
                indexer._write_file_reference(fh, file_instance)
            os.symlink(file_instance.hash_sha1(), _composite_path)
            return

        if file_instance.packed_path() in _hashed_files:
            # check file mdate
            if _hashed_files[file_instance.packed_path()] == file_instance.mdate():
                # file reference is up to date - nothing to do
                pass
            else:
                # hash and link correspond but the file could have been altered
                # since the hash has changed
                # assert False
                pass

        else:
            # the current file is not contained in the respective hash file
            # should this happen? there should be no link then
            pass

    def _walk(self, path, callback):
        for (_dir, _dirs, files) in os.walk(path, topdown=True):
            _dirs[:] = [d for d in _dirs if d not in self._ignore_pattern]

            _dir = os.path.realpath(_dir)
            for fname in files:
                _file = file_info(path_join(_dir, fname), self._name_component_store)

                if not _file.is_normal_file():
                    # we ignore symlinks, device files, pipes, etc.
                    continue

                if _file.size() == 0:
                    # we even ignore empty files
                    continue

                try:
                    callback(_file)
                except not_indexed_error as ex:
                    ex.file_info = _file
                    raise

    def _is_tracked(path: str) -> tuple:
        ''' returns a tuple containing whether or not a given path is already
            being tracked and which path it's being tracked by
        '''
        for p in self._tracked_directories:
            if _path.startswith(p):
                return True, p
        return False, None

    def add(self, path):
        _path = os.path.realpath(os.path.expanduser(path))

        if not os.path.exists(_path):
            raise file_not_found_error()

        for p in self._tracked_directories:
            if _path.startswith(p):
                print('"%s" is already tracked via "%s"' % (path, p))
                return

        def not_contained(p1, p2):
            if p1.startswith(p2):
                print('Already tracked folder "%s" will be replaced' % p1)
                return False
            return True
        self._tracked_directories = [
            p for p in self._tracked_directories if not_contained(p, _path)]

        self._tracked_directories.append(_path)

        _result = {"file_count": 0,
                   "total_size": 0}

        def file_adder(file_instance, stats):
            try:
                _t = time.time()
                self._add_file(file_instance)
                _t = time.time() - _t
                stats['total_size'] += file_instance.size()
            except read_permission_error:
                logging.warning('cannot handle "%s": read permission denied',
                                file_instance.path())
            except KeyboardInterrupt:
                raise

            stats['file_count'] += 1

            if file_instance.size() >= 10 ** 6:
                logging.debug("%s: %s bytes, %.1fms, %.2fMb/ms",
                              file_instance.basename(),
                              '{0:,}'.format(file_instance.size()), _t * 1000,
                              file_instance.size() / (2 << 20) / (_t  * 1000))

        self._walk(_path, lambda x: file_adder(x, _result))

        logging.info("added %d files with a total of %s bytes",
                     _result['file_count'],
                     '{0:,}'.format(_result['total_size']))
        return _result

    def diff(self, dir1, dir2):
        _dir1 = os.path.realpath(dir1)
        _dir2 = os.path.realpath(dir2)
        assert os.path.isdir(_dir1)
        assert os.path.isdir(_dir2)
        assert (_dir1 != _dir2
                ), "directories must not be same"
        assert (not (_dir1.startswith(_dir2) or _dir2.startswith(_dir1))
                ), "directories must not be subdirectories of each other"

        def _dir_differ(file_instance, other_dir, result):
            _registered, _, _duplicates = self._get_state(file_instance)
            if not _registered:
                raise not_indexed_error(file_instance)
            elif len(_duplicates) == 0:
                logging.warning('single: %s', file_instance.path())
            else:
                # the file has at least one duplicate - we now have to check
                # if at least one of them is located in `other_dir`
                _file_in_other_dir = False
                for f, d in _duplicates.items():
                    if not f.startswith(other_dir):
                        continue
                    _file = file_info(self._name_component_store.restore(f))

                    if not _file.is_normal_file():
                        logging.warning(
                            'possible duplicate invalid: %s', _file.path())
                        continue
                    if not _file.mdate() == d:
                        logging.warning(
                            'possible duplicate might have been modified: %s',
                            _file.path())
                        continue
                    _file_in_other_dir = True
                    break

                if not _file_in_other_dir:
                    result.append(file_instance)

        _not_in_1 = []
        _not_in_2 = []

        self._walk(_dir1, lambda _file: _dir_differ(
            _file,
            self._name_component_store.get_packed(_dir2, const=True) + '.',
            _not_in_2))

        self._walk(_dir2, lambda _file: _dir_differ(
            _file,
            self._name_component_store.get_packed(_dir1, const=True) + '.',
            _not_in_1))

        if len(_not_in_2) > 0:
            print('only in "%s":' % _dir1)
            for d in _not_in_2:
                print("    %s" % d.path())
        if len(_not_in_1) > 0:
            print('only in "%s":' % _dir2)
            for d in _not_in_1:
                print("    %s" % d.path())

    def check_redundancy(self, directory, invert=False):
        _dir = os.path.realpath(directory)
        assert os.path.isdir(_dir)

        def _dup_finder(file_instance, packed_dir, invert, result):
            ''' will check file_instance for duplicates _outside_ of
                <packed_dir> if <invert> is False <result> will contain the
                list of files which have copies outside <packed_dir>
                if <invert> is True, <result> will contain the list of files
                which are only located in <packed_dir> (where it might be
                duplicate)
            '''
            _registered, _, _duplicates = self._get_state(file_instance)
            if not _registered:
                raise not_indexed_error(file_instance)
            _found = False
            for p in _duplicates:
                if p.startswith(packed_dir):
                    # we found a duplicate of <file_instance> which is
                    # located inside of <packed_path>
                    continue
                _found = True
                if not invert:
                    # we found a duplicate outside given direcory.
                    # in case we do an non-inverted search we now know
                    # this file is duplicated and can be added to the result
                    if not file_instance in result:
                        result[file_instance] = []
                    result[file_instance].append(p)
                else:
                    break

            if invert:
                if not _found:
                    result[file_instance] = None

            return

        _result = {}
        self._walk(_dir, lambda _file: _dup_finder(
            _file,
            self._name_component_store.get_packed(_dir, const=True) + '.',
            invert,
            _result))

        if invert:
            # we checked for redundancy for all files
            if len(_result) == 0:
                print('all files redundant')
            else:
                for p in _result:
                    print(p.path())
                print('.. without copy')
        else:
            # we searched for files with redundand copyies
            if len(_result) == 0:
                print('directory is free of redundancy')
            else:
                for p in _result:
                    print(p.path())
                    for c in _result[p]:
                        print("   " + self._name_component_store.restore(c))
                print('.. are redundant')


def clear_index(storage_dir: str) -> None:
    # todo: to be atomic, first move directory, then delete it
    print('removing %s..' % storage_dir)
    rmdirs(os.path.expanduser(storage_dir))
    print('all index removed')


def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('--verbose', '-v',     action='count', default = 0)
    parser.add_argument('--debug', '-d',       action='store_true')
    parser.add_argument('--const', '-c',       action='store_true')
    parser.add_argument('--rebuild', '-r',     action='store_true')
    parser.add_argument('--invert', '-i',      action='store_true')
    parser.add_argument('--storage-dir', '-s', default='~/.fsi')
    parser.add_argument('COMMAND')
    parser.add_argument('PATH', nargs='*')

    args = parser.parse_args()

    if args.debug:
        global DEBUG_MODE
        DEBUG_MODE = True

    _level = logging.INFO
    if args.verbose >= 1:
        _level = logging.INFO
    if args.verbose >= 2:
        _level = logging.DEBUG

    logging.basicConfig(level=_level)
    logging.debug('.'.join((str(e) for e in sys.version_info)))

    if args.rebuild:
        clear_index(args.storage_dir)

    try:
        if args.COMMAND == 'clear':
            clear_index(args.storage_dir)

        elif args.COMMAND == 'info':
            with indexer(args.storage_dir) as _indexer:
                print('indexed directories:')
                for i in _indexer.tracked_dir_list():
                    print("  ", i)

        elif args.COMMAND == 'add':
            with indexer(args.storage_dir) as _indexer:
                for p in args.PATH:
                    logging.info("ADD to index: '%s'", p)
                    _indexer.add(p)

        elif args.COMMAND == 'check-dups':
            with indexer(args.storage_dir) as _indexer:
                logging.info("check four duplicates in '%s'", args.PATH[0])
                for d in args.PATH:
                    _indexer.check_redundancy(d, invert=args.invert)

        elif args.COMMAND == 'check-redundancy':
            with indexer(args.storage_dir) as _indexer:
                logging.info("check four duplicates in '%s'", args.PATH[0])
                for d in args.PATH:
                    _indexer.check_redundancy(d, invert=True)

        elif args.COMMAND == 'diff':
            if len(args.PATH) != 2:
                raise parser.error(
                    "please provide exactly 2 directories to compare")
            with indexer(args.storage_dir) as _indexer:
                logging.info("DIFF directories '%s' and '%s'",
                             args.PATH[0], args.PATH[1])
                _indexer.diff(args.PATH[0], args.PATH[1])
        else:
            pass

    except KeyboardInterrupt:
        print("aborted")

    except not_indexed_error as ex:
        print('file "%s" is not up to date - please re-index the '
              'according folder using `fsi add`' % ex.file_info.path())

if __name__ == '__main__':
    main()