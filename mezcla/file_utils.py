#! /usr/bin/env python
#
# Filesystem related functions
#


"""Filesystem related functions"""


# Standard packages
from datetime import datetime
import os
import sys


# Local packages
from mezcla import debug
from mezcla import system
from mezcla import glue_helpers as gh


def path_exist(path):
    """Returns indication that PATH exists"""
    result = os.path.exists(path)
    debug.trace(debug.QUITE_VERBOSE, f'path_exists({path}) => {result}')
    return result


def is_directory(path):
    """Determins wther PATH represents a directory"""
    result = os.path.isdir(path)
    debug.trace(debug.QUITE_DETAILED, f'is_dir({path}) => {result}')
    return result


def is_file(path):
    """Determins wther PATH represents a file"""
    result = os.path.isfile(path)
    debug.trace(debug.QUITE_DETAILED, f'is_file({path}) => {result}')
    return result


def get_directory_listing(path          = '.',
                          recursive     = False,
                          long          = False,
                          readable      = False,
                          return_string = True,
                          make_unicode  = False):
    """Returns files and dirs in PATH"""
    dir_list = []

    # list all files and directories on a folder
    try:
        for root, dirs, files in os.walk(path):
            items = dirs + files
            if recursive:
                # Avoid duplicated filenames adding the relative path
                for item in items:
                    dir_list.append(root + '/' + item)
            else:
                # Only dirs and files in the root dir
                dir_list = items
                break
    except OSError:
        debug.trace(debug.DETAILED, f'Exception during get_directory_listing: {sys.exc_info()}')

    # Long listing
    if long:
        for index, item in enumerate(dir_list):
            dir_list[index] = get_information(item, readable=readable, return_string=return_string)

    # Make unicode
    if make_unicode:
        dir_list = [system.to_unicode(f) for f in dir_list]

    debug.trace(debug.VERBOSE, f'get_directory_listing({path}) => {dir_list}')
    return dir_list


def get_information(path, readable=False, return_string=False):
    """
    This returns information about a directory or file.

    ex:
        get_file_size('somefile.txt')                     -> ('-rwxrwxr-x', 3, 'peter', 'admins',  4096, 'oct 25 01:42', 'somefile.txt')
        get_file_size('somefile.txt', return_string=True) -> "-rwxrwxr-x\t3\tpeter\tadmins\t4096\toct 25 01:42\tsomefile.txt"
    """

    if not path_exist(path):
        return f'cannot access "{path}" No such file or directory'

    ls_result = gh.run(f'ls -l {path}').split(' ') # TODO: use pure python.

    if len(ls_result) < 3:
        return ''

    permissions       = get_permissions(path)
    links             = ls_result[1]
    owner             = ls_result[2]
    group             = ls_result[3]
    size              = ls_result[4] # TODO: format size when readable=True

    # Get modification date
    modification_date = get_modification_date(path)

    if return_string:
        return f'{permissions} {links} {owner} {group} {size} {modification_date} {path}'

    return permissions, links, owner, group, size, modification_date, path


def get_permissions(path):
    """Get RWX permissions of file or dir"""

    result = ''

    # Check if is file or dir, else exit
    if is_file(path):
        result = '-'
    elif is_directory(path):
        result = 'd'
    else:
        return f'cannot access "{path}": No such file or directory'

    # Get permissions of file/dir
    permissions = os.stat(path).st_mode
    mask        = ((0b1 << 9) - 1)
    binary      = bin(permissions & mask)[2:]

    # Convert permissions binary to rwx Unix style
    mold = 'rwx' * 3
    for index, digit in enumerate(binary):
        if digit == '1':
            result += mold[index]
        else:
            result += '-'

    return result


# strftime format code list can be found here: https://www.programiz.com/python-programming/datetime/strftime
def get_modification_date(path, strftime='%b %d %H:%M'):
    """Get last modification date of file"""
    return datetime.fromtimestamp(os.path.getmtime(path)).strftime(strftime).replace(' 0', '  ').lower() if path_exist(path) else 'error'
