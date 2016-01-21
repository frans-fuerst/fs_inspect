fs_inspect - understand your filesystem
=======================================

fs_tidify is a command line tool designed to quickly retrieve information
about your files and folders which help you to get rid of doublettes and
find out what you should make backups of.

For example you can find out which files inside a given folder you should
make a backup of

    `fsi finduniques ./some/folder`

Or you could find doublettes inside a given folder:

    `fsi doublettes ./some/folder`

fs_tidify is content sensitive so renaming or touching files won't make them
treated as different.


fs_tidify aims at answering the following questions:

* is there anything in a given directory without a recent backup?
* are there doublettes of a given file or a number of files apart from 
  intended backups?
* do two given folders have the same content?
* are there files with same content but different names?
* are there files with same names but different content?

