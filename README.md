fs_inspect - understand your filesystem
=======================================

`fs_inspect` is a command line tool designed to quickly retrieve information
about your files and folders which help you to get rid of doublettes and
find out what you should make backups of.

Key features are:

* when comparing folders the file content matters - not the directory structure
* once indexed a folder can be processed very quickly
* platform independent


*Development status*: currently the `add` command is working on a experimental 
basis, `diff`, `check-dups` and `heck-backup` are expected to work soon.


Here are some examples for how you can youse `fs_inspect` (or `fsi` for short):

    `fsi add ./some/folder`

This will inspect the folder's content using sha1 checksums where needed and
store the information in your filesystem.

    `fsi diff ./some/folder ./some_other/folder`

Compare the two folders contents - no matter how the folder structure looks like
and how the files are named. You will get two lists of files which are contained
in each of the folders and not in the other.

    `fsi check-dups ./some/folder`

Lists all files located in `./some/folder` which have duplicates somewhere.

    `fsi check-backup ./some/folder`

Acts like `check-dups` but will report every file which has backup somewhere.


fs_inspect aims at answering the following questions:

* is there anything in a given directory without a recent backup?
* are there doublettes of a given file or a number of files apart from 
  intended backups?
* do two given folders have the same content?
* are there files with same content but different names?
* are there files with same names but different content?


In comparison to a usual directory differ `fsi` behaves different in some 
ways. Please note that `fsi` does not aim at being a better directory differ
(yet) but wants to give a rough hint where to have a closer look without
struggling with restructured directories or renamed files. Here are some
differences in behavior you should know:

* when handling files **symbolic links are ignored**
* files with **size 0 are ignored**
* `fsi` only recognizes equal files on a *binary basis* (using a hash of a
  file). Files which only differ in spaces etc. are just identified as 
  different. Please use tools like `meld`, `hexdiff` etc. for further 
  investigation.




