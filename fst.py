#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""add docstring"""

from fs_tidyfy import FsDb
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

    if args[0] == 'help':
        pass

    if args[0] in  ('a', 'add'):
        if len(args) < 2:
            parser.error("no directory to add given")

        fsdb = FsDb()
        for directory in args[1:]:
            logging.info( "%d Mb", (fsdb.register(directory) / 2 ** 20) )

        fsdb.print_statistics()

    if args[0] in  ('up', 'update'):
        print("not yet implemented")


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
