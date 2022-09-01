#! /usr/bin/env python
#
# Test(s) for ../merge_files.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH="$(realpath .)/..):$PYTHONPATH" python tests/test_merge_files.py
#

"""Tests for merge_files module"""

# Standard packages

# Installed packages
import pytest

# Local packages
from mezcla import debug

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
#    TestIt.script_module   string name
import mezcla.merge_files as THE_MODULE

class TestIt:
    """Class for testcase definition"""

    def test_get_timestamp(self):
        """Ensure get_timestamp works as expected"""
        debug.trace(4, "test_get_timestamp()")
        ## TODO: solve flaky test
        ## assert THE_MODULE.get_timestamp("/vmlinuz") == "2021-04-15 04:24:54"

    def test_get_numeric_timestamp(self):
        """Ensure get_numeric_timestamp works as expected"""
        debug.trace(4, "test_get_numeric_timestamp()")
        ## TODO: solve flaky test
        ## assert THE_MODULE.get_numeric_timestamp("/vmlinuz") == 1618478694.0

    ## TODO: test Script class

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
