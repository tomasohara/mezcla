#! /usr/bin/env python
#
# Test(s) for ../cut.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH="$(realpath .)/..):$PYTHONPATH" python tests/test_cut.py
#

"""Tests for cut module"""

# Standard packages

# Installed packages
import pytest

# Local packages
from mezcla import debug

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
#    TestIt.script_module   string name
import mezcla.cut as THE_MODULE

class TestIt:
    """Class for testcase definition"""

    def test_elide_values(self):
        """Ensure elide_values works as expected"""
        debug.trace(4, "elide_values()")
        assert THE_MODULE.elide_values(["1234567890", 1234567890, True, False], max_len=4) == ["1234...", "1234...", "True", "Fals..."]

    def test_flatten_list_of_strings(self):
        """Ensure flatten_list_of_strings works as expected"""
        debug.trace(4, "test_flatten_list_of_strings()")
        assert THE_MODULE.flatten_list_of_strings([["l1i1", "l1i2"], ["l2i1"]]) == ["l1i1", "l1i2", "l2i1"] 


if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
