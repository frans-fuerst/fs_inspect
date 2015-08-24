#!/usr/bin/env python3
# -*- coding: utf-8 -*-

''' this is the fs_tidify core module. import and operate on fs_db
'''

import os
import logging
import hashlib
from functools import partial
import json
import pprint


def sha1_chunked(filename, chunksize=2**15, bufsize=-1):
    """add docstring"""
    # max-limit-of-bytes-in-method-update-of-hashlib-python-module
    # http://stackoverflow.com/questions/4949162
    sha1_hash = hashlib.sha1()
    with open(filename, 'rb', bufsize) as _file:
        for chunk in iter(partial(_file.read, chunksize), b''):
            sha1_hash.update(chunk)
    return sha1_hash


def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

def to_unicode(string):
    if isinstance(string, str):
        return string
    if isinstance(string, bytes):
        return string.decode()
    if isinstance(string, unicode):
        return str(string)
    assert False, "input not str or bytes (but %s)" % type(string)
    
class file_info:
    """add docstring"""
    def __init__(self, name, path):
        self.name = to_unicode(name)
        self.path = to_unicode(path)

    def __eq__(self, other):
        _n_eq = other.name == self.name
        _p_eq = other.path == self.path
        return _n_eq and _p_eq
    
    def __str__(self):
        return os.path.join(self.path, self.name)

    def __repr__(self):
        return str(self)

    def get_hash(self):
        """add docstring"""
        try:
            _fullname = os.path.join(self.path, self.name)
            _hash1 = sha1_chunked(_fullname).hexdigest()

        except MemoryError as ex:
            logging.error( "error, trying to get hash for file '%s' (%d Mb)",
                           _fullname,
                           os.path.getsize(_fullname) / 2 **20 )
            logging.error( "error was '%s'", str(ex))
            raise
        return _hash1


class file_y:
    ''' a file_y object contains one or more descriptions referring to a list
        of files with identical content.
        One file_y object has mulitiple levels of identification which make
        the file distinguishable from each other. E.g. one file_y object can
        hold several files with different sizes:
        root |
             + - 3247 bytes -> [PATH1, PATH2, ...]
             |
             + - 5432 bytes -> [PATH3, PATH4, ...]
    '''

    # level of differentiation
    states = enum('SIZE', 'HASH', 'IDENTICAL')

    def __init__(self, file_info, initial_state=states.SIZE):
        self._state = initial_state
        self._file = file_info  # used with state == SIZE
        self._hashes = None     # used with state == HASH

    def __eq__(self, other):
        _s_eq = other._state == self._state
        _f_eq = other._file == self._file
        _h_eq = other._hashes == self._hashes
        if not _s_eq:
            print('file_y: state differ')
        if not _f_eq:
            print('file_y: file_info differs')
        if not _h_eq:
            print('file_y: hashed files differ')
            print(other._hashes)
            print(self._hashes)
        return (_s_eq and _f_eq and _h_eq)
    
    def get_count(self):
        if self._state is file_y.states.SIZE:
            return 1
        _count = 0
        for _, v in self._hashes.items():
            _count += len(v)
        return _count
    
    def add(self, new_file_info):
        ''' accept new file to register and reorganize tree
        '''
        if self._state is file_y.states.SIZE:
            ''' if this is the first collision then first promote this file_y
                to a subtree for equally sized files and then recursively add
                the file again.
            '''
            self._state = file_y.states.HASH
            self._hashes = {self._file.get_hash(): [self._file]}
            self._file = None
            return self.add(new_file_info)

        elif self._state is file_y.states.HASH:
            _new_hash = new_file_info.get_hash()
            if _new_hash not in self._hashes:
                self._hashes[_new_hash] = [new_file_info]
                return file_y.states.HASH
            else:
                self._hashes[_new_hash].append(new_file_info)
                return file_y.states.IDENTICAL


    def get_similar_files(self):
        if self._state is file_y.states.SIZE:
            return ()
        if self._state is file_y.states.HASH:
            return tuple(f for h, f in self._hashes.items()
                    if len(f) > 1)


class json_encoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, file_info):
            return obj.__dict__
        if isinstance(obj, file_y):
            return {'state': obj._state, 'file': obj._file, 'hashes': obj._hashes}

        return json.JSONEncoder.default(self, obj)


class json_decoder(json.JSONDecoder):

    def __init__(self, *args, **kargs):
        json.JSONDecoder.__init__(self, object_hook=self.dict_to_object,
                             *args, **kargs)

    def dict_to_object(self, d):
        if 'name' in d and 'path' in d:
            return file_info(**d)
        if 'state' in d:
            r = file_y(d['file'], d['state'])
            if 'hashes' in d and d['hashes'] is not None:
                r._hashes = {k.encode(): v for k, v in d['hashes'].items()}
            return r
        return d


class fs_db:
    ''' a fs_db instance holds all information about files and directories
        which have been imported and can answer questions about them
    '''

    def __init__(self, import_export_file = None):
        self._ie_file = import_export_file
        self._files = {}
        self._directories = {}

    def __eq__(self, other):
        # print("__eq__: files equal: %s" % other._files == self._files)
        # print("__eq__: files dirs:  %s" % other._directories == self._directories)
        _f_eq = other._files == self._files
        _d_eq = other._directories == self._directories
        if not _f_eq:
            print('fs_db: files differ')
            print(other._files.keys() == self._files.keys())
            print(other._files.keys())
            print(self._files.keys())
            
            print(other._files.values() == self._files.values())
        if not _d_eq:
            print('fs_db: directories differ')
        return (_f_eq and _d_eq)

    def to_JSON(self):
        return json.dumps(
            { 'directories': self._directories,
              'files': self._files},
            cls=json_encoder,
            # default=lambda o: o.__dict__,
            sort_keys=True,
            indent=4)

    def from_JSON(self, json_data):
        imported_data = json.loads(json_data, cls=json_decoder)
        self._directories = imported_data['directories']
        self._files = {int(k): v for k, v in imported_data['files'].items()}

    def get_count(self):
        count = 0
        for f in self._files:
            count += self._files[f].get_count()
        return count
    
    def print_statistics(self):
        for f in self._files:
            sim_f = self._files[f].get_similar_files()
            if len(sim_f) == 0:
                continue
            pprint.pprint(sim_f)
        print("%d files in total " % self.get_count())

    def register(self, path):
        ''' takes a path to investigate and traverses it to
            index all contained files
        '''
        _totalsize = 0
        _path = os.path.abspath(path)
        logging.debug(_path)
        for (_dir, _, files) in os.walk(_path):
            for fname in files:
                _fullname = os.path.join(_dir, fname)
                if os.path.islink(_fullname):
                    logging.debug("skipping link %s" % _fullname)
                    continue

                _file_info = file_info(fname, _dir)

                _filesize = os.path.getsize(_fullname)

                logging.debug( "handle: %s (%d)", _fullname, _filesize)

                if not _filesize in self._files:
                    # simple case: file size does not exist yet, so just
                    #              fill the size => file container
                    self._files[_filesize] = file_y(_file_info)
                else:
                    # collision: size is taken, so we have to treat this
                    #            entry as a 'folder' for equally sized files
                    _collision_type = self._files[_filesize].add(_file_info)
                    logging.info("collision (%d): %s",
                                 _collision_type, _fullname)


                #logging.debug("%s", _hash1)
                _totalsize += _filesize

        self.export_to_fs()
        return _totalsize

    def export_to_fs(self):
        with open(self._ie_file, 'w') as export_file:
            export_file.write(self.to_JSON())

    def import_from_fs(self):
        self.from_JSON(open(self._ie_file).read())


def test_smoketest():
    ''' make an overall smoke test and explain a typical workflow
    '''

    fsdb1 = fs_db("fstdb.txt")
    test_directory = os.path.join(os.path.dirname(__file__), 'example_fs')
    # import information about a directory
    assert fsdb1.get_count() == 0
    fsdb1.register(test_directory)
    assert fsdb1.get_count() == 5
    fsdb1.print_statistics()

    # persist imported information to fs
    fsdb1.export_to_fs()

    # load persisted information
    fsdb2 = fs_db("fstdb.txt")
    fsdb2.import_from_fs()

    if not fsdb1 == fsdb2:
        print('--')
        fsdb1.print_statistics()
        print('--')
        fsdb2.print_statistics()
        print('--')
        
    assert fsdb1 == fsdb2, "equality after loading"

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    test_smoketest()

