#! /usr/bin/env python
# 
# Miscellanous utilities for ipython usage
#
# Note:
# - This is idiosyncractic code based on Tom O'Hara's ipython startup file
#   (~/.ipython/profile_default/startup/25-quarter.py).
# - To faciliate importing functions and variables for testing purposes (e.g., EX tests),
#   use import_module_globals as illustrated in second example below.
#

"""
Adhoc stuff for ipython.

Simple usage:
    from mezcla.ipython_utils import *

Advanced usage:
    import mezcla.ipython_utils
    reload(mezcla.ipython_utils)
    import_module_globals = mezcla.ipython_utils.import_module_globals
    import_module_globals("mezcla.misc_utils", globals_dict=builtins.globals());
    (TYPICAL_EPSILON, VALUE_EPSILON)
    >>>
    (1e-06, 0.001)

Misc. usage:
    set_xterm_title(f"ipython: {os.getcwd()}")
"""

# Note: most imports are done for the sake of ipython usage
#
# pylint: disable=unused-import

# Standard modules
import builtins
from collections import defaultdict, namedtuple
import json
import math
import os
import random
import re
import sys
from importlib import reload

# Installed modules
import numpy as np
import pandas as pd
import sklearn

# Local modules
import mezcla
from mezcla import debug
from mezcla import html_utils
from mezcla import main
from mezcla.main import Main
from mezcla import system
from mezcla.my_regex import my_re
from mezcla import data_utils as du
from mezcla import glue_helpers as gh
from mezcla import tpo_common as tpo

# Constants
TL = debug.TL

# Environment options
# Note: These are just intended for internal options, not for end users.
# It also allows for enabling options in one place rather than four
# (e.g., [Main member] initialization, run-time value, and argument spec., along
# with string constant definition).
#
TODO_FUBAR = system.getenv_bool("TODO_FUBAR", False,
                                description="TODO:Fouled Up Beyond All Recognition processing")

#-------------------------------------------------------------------------------
# Global Variables
#
# Note:
# - intended to faciliate experimentation in ipython
# - crytic names for historical reasons (and since hash and list reserved words)
#

h = {'a': 1, 'b': 2, 'c': 3}
l = [1, 2, 3]
t = "some text"
text = t
    
#-------------------------------------------------------------------------------
# Helper functions

def grep_obj_methods(obj, pattern, flags=None):
    """Return methods for OBJ matching PATTERN (with optional re.search FLAGS)"""
    # EX: grep_obj_methods(str, "strip") => ["lstrip", "strip", "rstrip"]
    if flags is None:
        flags = re.IGNORECASE
    return list(m for m in dir(obj) if re.search(pattern, m, flags))


def import_module_globals(module_name, include_private=False, include_dunder=False, globals_dict=None, ignore_errors=None):
    """Import MODULE_NAME optionally with INCLUDE_PRIVATE and INCLUDE_DUNDER and setting GLOBALS_DICT"""
    # note: intended to support reloading modules imported in ipython via 'from module import *'
    # TODO3: find a cleaner way of doing this (e.g., via import support)
    # EX: import_module_globals("mezcla.misc_utils", globals_dict=builtins.globals()); VALUE_EPSILON => 1e-3
    # pylint: disable=eval-used,exec-used
    if globals_dict is None:
        globals_dict = builtins.globals()
    if ignore_errors is None:
        ignore_errors = False
    
    # Get list of modules attributes (e.g., variables)
    module_attrs = []
    try:
        import_command = f"import {module_name}"
        exec(import_command)
        module = eval(module_name)
        module_attrs = dir(module)
    except:
        if not ignore_errors:
            system.print_exception_info(import_command)
        else:
            debug.trace_exception(5, import_command)

    # Import each individually
    for var in module_attrs:

        # Optionally, include "dunder" attributes like __name__ or private ones like _name
        include = True
        if var.startswith("__"):
            if not include_dunder:
                include = False
                debug.trace(7, f"excluding dunder attribute {var!r}")
        elif (var.startswith("_") and not include_private):
            include = False
            debug.trace(7, f"excluding private attribute {var!r}")

        # Import the value
        if include:
            ## OLD: import_desc = (f"importing value of {module_name}'s {var}")
            import_desc = (f"importing {var} from {module_name}")
            debug.trace(5, import_desc)
            try:
                globals_dict[var] = eval(f"{module_name}.{var}")
            except:
                debug.trace_exception(4, import_desc)
    return


def pr_dir(obj):
    """Print dir listing for OBJ"""
    print(dir(obj))


def set_xterm_title(title=None):
    """Set xterm TITLE via set_xterm_title.bash
    Note:
    - Uses set_xterm_title.bash from https://github.com/tomasohara/shell-scripts.
    - The TITLE can use environment variables (e.g., "ipython [$CONDA_PREFIX]").
    """
    # Sample result: "ipython: /home/tomohara/mezcla: Py3.10(base)"
    if title is None:
        title = "ipython $PWD"
    gh.issue(f'set_xterm_title.bash "{title}"')
    
#-------------------------------------------------------------------------------
# Helper class

class Fubar():
    """Dummy class used for cut-n-paste of method code"""
    pass

#-------------------------------------------------------------------------------
# Initialization

self = Fubar()

dummy_main = main.Main([])

#-------------------------------------------------------------------------------
    
if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    debug.trace(5, f"module __doc__: {__doc__}")
    debug.assertion("TODO:" not in __doc__)
    system.print_stderr(f"Warning: {__file__} is not intended to be run standalone\n")
