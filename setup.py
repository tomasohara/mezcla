#! /usr/bin/env python
#
# Notes:
# - Simple installer for subset of scripts under Github
#       https://github.com/tomasohara/misc-utility
# - Based on following:
#       https://stackoverflow.com/questions/1471994/what-is-setup-py
#

"""Simple installer"""

from distutils.core import setup

## OLD:
## PYTHON_MODULE_NAMES = """
##     debug
##     glue_helpers
##     html_utils
##     my_regex
##     system
##     text_utils
## """.split()

setup(name='tomas_misc',
      packages=['tomas_misc'],
      version='1.0',
      ## OLD: py_modules=PYTHON_MODULE_NAMES,
      author="Tom O'Hara",
      # TODO: email="t0mas0hara@gmail.com",
      description="""
Package with core modules from https://github.com/tomasohara/misc-utility
""")
