#! /usr/bin/env python3
#
# Functions for operating system related access, such as running command or
# getting environment values.
#
# TODO:
# - Move functions from system.py here.
#

"""OS utilities: mainly wrappers around os package"""

# Standard modules
import os

# Local modules
from mezcla import debug
from mezcla import system

# Constants
TL = debug.TL


def split_extension(path):
    """Returns basename and extension for PATH"""
    result = os.path.splitext(path)
    try:
        filename_proper, ext = result
        debug.assertion(system.remove_extension(path) == filename_proper)
        debug.assertion(system.get_extension(path) == ext[1:])
    except:
        pass
    debug.trace(5, f"split_extension({path}) => {result}")
    return result

## TEMP: define dummy function for tests/test_os_utils.py
##
## def some_other_function():
##     """Used for testing test_02_no_other_functions"""
##     return

def main(*args, **kwargs):
    """Supporting code for command-line processing"""
    debug.trace_fmtd(6, "main{a}; kw=", a=args, kw=kwargs)
    system.print_stderr("Warning: {f} not intended for direct invocation!",
                        f=system.filename_proper(__file__))
    return

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    debug.trace(5, f"module __doc__: {__doc__}")
    debug.assertion("TODO:" not in __doc__)
    main()
