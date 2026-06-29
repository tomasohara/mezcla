#! /usr/bin/env python3
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
version = "1.4.0.8"
__VERSION__ = version
__version__ = __VERSION__

# Standard module(s)
import sys
import builtins
## DEBUG: sys.stderr.write(f"{__file__=}\n")

# Note: requires python 3 or higher
# TODO2: upgrade checks to cover 3.6 (mandatory) and 3.8+ (practical)
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

# Optional helpers for import context
def _in_ipython() -> bool:
    """Whether running under an active IPython/Jupyter session"""
    get_ipython = getattr(builtins, "get_ipython", None)
    if callable(get_ipython):
        return bool(get_ipython())
    return (("ipykernel" in sys.modules) or ("IPython" in sys.modules))

# Set convenience exports based on runtime mode.
if _in_ipython():
    # FYI to make import source explicit in interactive sessions.
    print("FYI: mezcla using ipython_utils imports: debug, gh, my_re, system, TL")
    from mezcla.ipython_utils import debug, gh, my_re, system, TL  # pylint: disable=ungrouped-imports
    __all__ = ["debug", "gh", "my_re", "system", "TL", "__VERSION__"]
else:
    __all__ = ["__VERSION__"]

## PREVIOUS:
## NOTE: See __main__.py
## debug.trace(TL.DETAILED, f"mezcla version: {__VERSION__}")
