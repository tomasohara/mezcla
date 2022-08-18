#! /usr/bin/env python
#
# Test(s) for ../data_utils.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH="$(realpath .)/..):$PYTHONPATH" python tests/test_data_utils.py
#

"""Tests for data_utils module"""

# Standard packages

# Installed packages
import pytest

# Local packages
from mezcla import debug

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
#    TestIt.script_module   string name
import mezcla.data_utils as THE_MODULE

class TestIt:
    """Class for testcase definition"""

    def test_read_csv(self):
        """Ensure read_csv works as expected"""
        debug.trace(4, "test_read_csv()")
        ## TODO: WORK-IN=PROGRESS

    def test_to_csv(self):
        """Ensure to_csv works as expected"""
        debug.trace(4, "test_to_csv()")
        ## TODO: WORK-IN=PROGRESS

    def test_lookup_df_value(self):
        """Ensure lookup_df_value works as expected"""
        debug.trace(4, "test_lookup_df_value()")
        ## TODO: WORK-IN=PROGRESS

    def test_lookup_df_value(self):
        """Ensure lookup_df_value works as expected"""
        debug.trace(4, "test_lookup_df_value()")
        ## TODO: WORK-IN=PROGRESS


if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
