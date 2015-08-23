#!/usr/bin/env python3
# -*- coding: utf-8 -*-

''' this is the fs_tidify core module. import and operate on FsDb
'''

import os
import logging
import hashlib
from functools import partial
import json
import pprint

def sha1_chunked(filename, chunksize=2**15, bufsize=-1):
    """add docstring"""
    # http://stackoverflow.com/questions/4949162/max-limit-of-bytes-in-method-update-of-hashlib-python-module
    sha1_hash = hashlib.sha1()
    with open(filename, 'rb', bufsize) as _file:
        for chunk in iter(partial(_file.read, chunksize), b''):
            sha1_hash.update(chunk)
    return sha1_hash

class FileInfo:
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

class FileY:
    """add docstring"""

    def __init__(self, file_info, initial_state=0):
        self.state = initial_state
        self.file_info = file_info
        self.files = None

    @classmethod
    def from_dict(cls, input_dict):
        new_object = cls(None)
        new_object.__dict__.update(input_dict)
        return new_object

    def add(self, new_file_info):
        """add docstring"""
        if self.state == 0:
            # if this is the first collision then first promote this FileY
            # to a 'folder' for equally sized files
            self.state = 1
            self.files = {self.file_info.get_hash(): FileY(self.file_info, 2)}
            self.file_info = None
            return self.add(new_file_info)

        elif self.state == 1:
            _new_hash = new_file_info.get_hash()
            if not _new_hash in self.files:
                self.files[_new_hash] = FileY(new_file_info, 2)
                return 2
            else:
                self.files[_new_hash].add(new_file_info)
                return 2

        elif self.state == 2:
            self.state = 3
            self.files = [self.file_info, new_file_info]
            self.file_info = None
            return 3

        elif self.state == 3:
            self.files.append(new_file_info)
            return 3

    def get_similar_files(self):
        if self.state == 0:
            return []
        if self.state == 1:
            return [self.files[x].get_similar_files() for x in self.files
                    if self.files[x].get_similar_files() != []]
        if self.state == 2:
            return []
        if self.state == 3:
            return self.files

class FsDb:
    """a FsDb instance holds all information about files and directories
       which have been imported and can answer questions about them
    """

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
            default=lambda o: o.__dict__,
            sort_keys=True,
            indent=4)

    def from_JSON(self, json_data):
        imported_data = json.loads(json_data)
        self._directories = imported_data['directories']

        for size, file_y in imported_data['files'].iteritems():
            self._files[size] = FileY.from_dict(file_y)

    def print_statistics(self):
        for f in self._files:
            sim_f = self._files[f].get_similar_files()
            if len(sim_f) == 0:
                continue
            pprint.pprint(sim_f)

    def register(self, path):
        """takes a path to investigate and traverses it to
           index all contained files
           """
        _totalsize = 0
        _path = os.path.abspath(path)
        logging.debug(_path)
        for (path, _, files) in os.walk(_path):
            for fname in files:
                _fullname = os.path.join(path, fname)
                if os.path.islink(_fullname):
                    logging.debug("skipping link %s" % _fullname)
                    continue

                _file_info = FileInfo(fname, path)

                _filesize = os.path.getsize(_fullname)

                logging.debug( "handle: %s", _fullname )

                if not _filesize in self._files:
                    # simple case: file size does not exist yet, so just
                    #              fill the size => file container
                    self._files[_filesize] = FileY(_file_info)
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
        with open('fst.export.json', 'w') as export_file:
            export_file.write(self.to_JSON())

    def import_from_fs(self):
        self.from_JSON(open('fst.export.json').read())


def test():
    ''' make an overall smoke test and explain a typical workflow 
    '''
    
    fsdb1 = FsDb("fstdb.txt")
    test_directory = os.path.join(os.path.dirname(__file__), 'example_fs')
    # import information about a directory
    fsdb1.register(test_directory)
    fsdb1.print_statistics()

    # persist imported information to fs
    fsdb1.export_to_fs()

    # load persisted information
    fsdb2 = FsDb("fstdb.txt")
    fsdb2.import_from_fs()

    if not fsdb1 == fsdb2:
        print('--')
        fsdb1.print_statistics()
        print('--')
        fsdb2.print_statistics()
        print('--')
    assert fsdb1 == fsdb2, "equality after loading"

if __name__ == "__main__":
    test()

