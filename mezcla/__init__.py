#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
Mezcla is Spanish for mixture, and this repository contains a variety of Python scripts.

Miscellaneous Python scripts developed over the course of several independent consulting projects. This also includes some code samples I adapted from publicly available source. (The code is not proprietary in nature. For example, it was not "borrowed" from proprietary source files, nor based on proprietary processes.)

Spoiler alter: this is not "Pythonic python": I'm more into R&D than production programming. Nonetheless, there's a some useful scripts here, so I made the repository available. It is public in the spirit of open source software. 
 
This repository is licensed under the GNU Lesser General Public Version 3 (LGPLv3). See LICENSE.txt.

Adhoc usage:

    from mezcla import *
    debug.trace(TL.DEFAULT, "Hey")
    debug.trace(TL.DETAILED, "Joe")

Tom O'Hara
Feb 2022
"""
__VERSION__ = '1.3.6'
__version__ = __VERSION__

# Standard module(s)
import sys

# Note: requires python 3 or higher
PYTHON3_PLUS = (sys.version_info[0] >= 3)
assert PYTHON3_PLUS, "Python 3 or higher: ¡por favor!"

# Local modules
# Define most common imports for causual usage
# Note: avoids syntax error is debug and system import directly
## TODO
## debug = None
## mezcla = None
## system = None
## if PYTHON3_PLUS:
##     ## TODO: get relative imports to work
##     ## from . import debug
##     ## from .mezcla import debug
##     import mezcla
##     from mezcla import debug
##     from mezcla import system
##     TL = debug.TL
##     ## DEBUG: debug.trace_expr(TL.DEFAULT, debug, mezcla, system, TL)
## else:
##     TL = None
## TODO: drop mezcla
import mezcla
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import system

# Constants
TL = debug.TL

# Expose commonly used modules
# TODO: drop mezcla
__all__ = ["debug", "gh", "mezcla", "system", "TL"]
