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


class file_info:
    """add docstring"""
    def __init__(self, name, path):
        self.name = name
        self.path = path

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

    @classmethod
    def from_dict(cls, input_dict):
        new_object = cls(None)
        new_object.__dict__.update(input_dict)
        return new_object

    def to_JSON(self):
        return None

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
            return {'state': 'STATE', 'file': obj._file, 'hashes': obj._hashes}

        return json.JSONEncoder.default(self, obj)


class json_decoder(json.JSONDecoder):

    def __init__(self, *args, **kargs):
        json.JSONDecoder.__init__(self, object_hook=self.dict_to_object,
                             *args, **kargs)

    def dict_to_object(self, d):
        if '__type__' not in d:
            return d

        type = d.pop('__type__')
        try:
            dateobj = datetime(**d)
            return dateobj
        except:
            d['__type__'] = type
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
        return (other._files == self._files and
                other._directories == self._directories)

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

        for size, file_y in imported_data['files'].iteritems():
            self._files[size] = file_y.from_dict(file_y)

    def print_statistics(self):
        for f in self._files:
            sim_f = self._files[f].get_similar_files()
            if len(sim_f) == 0:
                continue
            pprint.pprint(sim_f)

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


def test():
    ''' make an overall smoke test and explain a typical workflow
    '''

    fsdb1 = fs_db("fstdb.txt")
    test_directory = os.path.join(os.path.dirname(__file__), 'example_fs')
    # import information about a directory
    fsdb1.register(test_directory)
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
    test()

