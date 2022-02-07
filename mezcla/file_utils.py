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

    debug.trace(debug.USUAL, (f'get_directory_listing(path="{path}",\n'
                              f'                      recursive={recursive},\n'
                              f'                      long={long},\n'
                              f'                      readable={readable},\n'
                              f'                      return_string={return_string},\n'
                              f'                      make_unicode={make_unicode})'))

    result_list = []

    # list all files and directories on a folder
    try:
        for root, dirs, files in os.walk(path):
            items = dirs + files
            if recursive:
                # Avoid duplicated filenames adding the relative path
                for item in items:
                    result_list.append(root + '/' + item)
            else:
                # Only dirs and files in the root dir
                result_list = items
                break
        debug.trace(debug.DETAILED, f'get_directory_listing() - files and dirs founded: {result_list}')
    except OSError:
        debug.trace(debug.DETAILED, f'get_directory_listing() - exception: {sys.exc_info()}')

    # Long listing
    if long:
        for index, item in enumerate(result_list):
            result_list[index] = get_information(item, readable=readable)
        debug.trace(debug.DETAILED, f'get_directory_listing() - long listing: {result_list}')

        # Convert to a uniform string
        # NOTE: This could be a new function.
        if return_string and result_list:

            new_list     = [''] * len(result_list)
            fields_count = len(result_list[0])

            for field_index in range(fields_count):

                # Get max lenght of field
                max_field_len = 0
                for item in result_list:
                    field         = str(item[field_index])
                    field_len     = len(field)
                    max_field_len = max(max_field_len, field_len)

                # Append field to new list
                for item_index, item in enumerate(result_list):
                    field = str(item[field_index])
                    new_list[item_index] += field.ljust(max_field_len) + ' '

            result_list = new_list

    # Make unicode
    if make_unicode:
        result_list = [system.to_unicode(f) for f in result_list]

    debug.trace(debug.USUAL, (f'get_directory_listing() => {result_list}'))
    return result_list


def get_information(path, readable=False, return_string=False):
    """
    This returns information about a directory or file.

    ex:
        get_file_size('somefile.txt')                     -> ('-rwxrwxr-x', 3, 'peter', 'admins',  4096, 'oct 25 01:42', 'somefile.txt')
        get_file_size('somefile.txt', return_string=True) -> "-rwxrwxr-x\t3\tpeter\tadmins\t4096\toct 25 01:42\tsomefile.txt"
    """

    if not path_exist(path):
        return f'cannot access "{path}" No such file or directory'

    # TODO: use pure python.
    ls_flags = '-ld' if is_directory(path) else '-l'
    ls_result = gh.run(f'ls {ls_flags} {path}').split(' ')

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
