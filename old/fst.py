#!/usr/bin/env python3
# -*- coding: utf-8 -*-

''' this is the fs_tidify command line client 

    possible commands:
    fst add <dir>            # registeres a folder
    fst update <dir>         # registeres a folder
    fst diff <dir1> <dir2>   # prints files which are only in dir1 or in dir2
    fst uniques <dir1>       # prints files which are not in any other registered folder
    fst show-copies <path>   # 
    
    [ ] support .fst-ignore files
    [ ] recognize moved files / directories
    [ ] refactor to client/server mode for speed
'''

from fs_tidify import fs_db
import logging
from optparse import OptionParser

def main():

    """add docstring"""

    usage = "usage: %prog [options] <command> [<folder> [folder2]]"
    parser = OptionParser(usage=usage)

    parser.add_option("-s", "--server", dest="server_host",
                      default="http://127.0.0.1", metavar="host-address",
                      help="server IP/address")
    parser.add_option("-v", "--verbose", dest="verbose",
                      action="store_true", default = False,
                      help = "be more verbose")
    (options, args) = parser.parse_args()
    
    if options.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    if len(args) == 0:
        parser.error("no command given")
        return -1

    elif args[0] == 'help':
        return 0

    elif args[0] in  ('a', 'add'):
        if len(args) < 2:
            parser.error("no directory to add given")

        fsdb = fs_db('fst.json')
        for directory in args[1:]:
            logging.info( "%d Mb", (fsdb.register(directory) / 2 ** 20) )
            fsdb.export_to_fs('fst.export.json')

        fsdb.print_statistics()

    elif args[0] in ('up', 'update'):
        print("not yet implemented")
        
    elif args[0] in ('show-copies'):
        fsdb = fs_db('fst.json')
        fsdb.import_from_fs()
        fsdb.print_statistics()

if __name__ == "__main__":
    logging.basicConfig(
        format='%(asctime)s %(levelname)s [%(name)s] %(message)s',
        datefmt="%y%m%d-%H%M%S")
    logging.getLogger().setLevel(logging.INFO)

    logging.addLevelName( logging.CRITICAL, '(CRITICAL)' )
    logging.addLevelName( logging.ERROR,    '(EE)' )
    logging.addLevelName( logging.WARNING,  '(WW)' )
    logging.addLevelName( logging.INFO,     '(II)' )
    logging.addLevelName( logging.DEBUG,    '(DD)' )
    logging.addLevelName( logging.NOTSET,   '(NA)' )

    main()
