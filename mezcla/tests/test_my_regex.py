#! /usr/bin/env python
#
# Test(s) for ../my_regex.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH="$(realpath .)/..):$PYTHONPATH" python tests/test_my_regex.py
#

"""Tests for my_regex module"""

# Standard packages
import re
import unittest

# Installed packages
## TODO: import pytest

# Local packages
from mezcla.unittest_wrapper import TestWrapper
from mezcla import debug

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
#    TestIt.script_module   string name
import mezcla.my_regex as THE_MODULE

class TestIt(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__)
    my_re = THE_MODULE.my_re

    def test_simple_regex(self):
        """"Test regex search with capturing"""
        debug.trace(4, "test_simple_regex()")
        if not self.my_re.search(r"(\w+)\W+(\w+)", ">scrap ~!@\n#$ yard<",
                                 re.MULTILINE):
            self.fail("simple regex search failed")
        self.assertEqual(self.my_re.group(1), "scrap")
        self.assertEqual(self.my_re.group(2), "yard")
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    unittest.main()

