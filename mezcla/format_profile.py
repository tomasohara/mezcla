#! /usr/bin/env python3
#
# format-profile.py: displays the result of python profiling via cProfile
#
# usage example:
#    python -u -m cProfile -o fubar.profile fubar.py
#    format-profile.py fubar.profile > fubar.profile.list
#------------------------------------------------------------------------
# Notes:
# via http://docs.python.org/3/library/profile.html:
#
# The Stats Class
#
# Analysis of the profiler data is done using the Stats class.
#
# class pstats.Stats(*filenames or profile, stream=sys.stdout)
# ...
# Stats objects have the following methods:
# ...
# 
# sort_stats(*keys)
#
# This method modifies the Stats object by sorting it according to the
# supplied criteria. The argument is typically a string identifying
# the basis of a sort (example: 'time' or 'name').
#
# Valid Arg    Meaning
# 'calls'      call count
# 'cumtime'    cumulative time
# 'filename'   file name
# 'module'     file name
# 'ncalls'     call count
# 'pcalls'     primitive call count
# 'line'       line number
# 'name'       function name
# 'nfl'        name/file/line
# 'stdname'    standard name
# 'tottime'    internal time
#

"""Displays result of python profiling"""

#------------------------------------------------------------------------
# Library packages

# Standard packages
import sys
import pstats

# Local packages
from mezcla import debug
from mezcla.system import getenv_bool, getenv_text, print_stderr

# Env. Constants
PROFILE_KEY = getenv_text(
    "PROFILE_KEY", "cumulative",
    desc="Sort key (e.g., cumtime, filename, ncalls, tottime)")
FULL_PATH = getenv_bool(
    "FULL_PATH", False,
    desc="Show full path in filename field")

#------------------------------------------------------------------------
# Functions

def usage():
    """Displays usage notes for script"""
    print_stderr("""
Usage: {program} profile-log

Notes:
- Use FULL_PATH to include directory for filename
  (e.g., helps to resolve all those __init__.py entries).
- Use PROFILE_KEY to over default sorting (cumulative).
- Main keys: 
       cumtime, filename, ncalls, tottime
- Other keys: 
       module, pcalls, line, name, nfl, stdname
- Alternative keys:
       calls, cumulative, file, time
- Unfortunately, memory profiling is not supported.
- For more details, check following:
    http://docs.python.org/3/library/profile.html

Example (assumes bash):
    $ python -m cProfile -o /tmp/profile.data simple_main_example.py
    $ PROFILE_KEY=calls {program} /tmp/profile.data | head
""".format(program=sys.argv[0]))
    return
                

def main():
    """Entry point for script"""
    debug.trace_fmt(5, "main(): args={v}", v=sys.argv)
    if ((len(sys.argv) < 2) or (sys.argv[1] == "--help")):
        usage()
        sys.exit()
    file = sys.argv[1]

    # Generate listing and sort by cumulative time
    p = pstats.Stats(file)
    if not FULL_PATH:
        p = p.strip_dirs()
    p.sort_stats(PROFILE_KEY).print_stats()
    return

#------------------------------------------------------------------------

if __name__ == '__main__':
    main()
