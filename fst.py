#!/usr/bin/python
# -*- coding: utf-8 -*-

from fs_tidyfy import FsDb
from optparse import OptionParser

def main():
    usage = "usage: %prog [options] <command> [<folder> [folder2]]"
    parser = OptionParser(usage=usage)

    parser.add_option("-s", "--server", dest="server_host",
                      default="http://127.0.0.1", metavar="host-address",
                      help="server IP/address")

    (options, args) = parser.parse_args()

    if len(args) == 0:
        parser.error("no command given")

    if args[0] == 'help':
        pass

    if args[0] == 'register':
        if len(args) < 2:
            parser.error("no directory to add given")

        fsdb = FsDb()
        for directory in args[1:]:
            print "%d Mb" % (fsdb.register(directory) / 2 ** 20)

if __name__ == "__main__":
    main()
