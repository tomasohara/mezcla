#! /usr/bin/env python
#
# Note: Test for working around ":double import" issue. See
#    See https://stackoverflow.com/questions/43393764/python-3-6-project-structure-leads-to-runtimewarning
# Also see
#    https://stackoverflow.com/questions/4042905/what-is-main-py
#

"""Entry point for mezcla"""

# Standard module(s)
import os
import re
import sys

if __name__ == '__main__':
    sys.stderr.write(f"Warning: {__file__} is not intended to be run standalone.\n")
    module = "__module__"
    # ex: /home/tomohara/python/Mezcla/mezcla/__main__.py => "mezcla"
    sep = re.escape(os.path.sep)
    match = re.search(fr"([^{sep}]*){sep}[^{sep}]*$", __file__)
    if match:
        module = match.group(1)
    sys.stderr.write(f"Likewise for the package (e.g., via 'python -m {module}')\n")
