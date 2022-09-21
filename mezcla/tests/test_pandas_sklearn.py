#! /usr/bin/env python
#
# Test(s) for ../pandas_sklearn.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH="$(realpath .)/..):$PYTHONPATH" python tests/test_pandas_sklearn.py
#

"""Tests for pandas_sklearn module"""

# Standard packages
## NOTE: this is empty for now

# Installed packages
import pytest

# Local packages
from mezcla import debug

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
import mezcla.pandas_sklearn as THE_MODULE

class TestPandasSklearn:
    """Class for testcase definition"""

    def test_create_feature_mapping(self):
        """Ensure create_feature_mapping works as expected"""
        debug.trace(4, "test_create_feature_mapping()")
        assert THE_MODULE.create_feature_mapping(['c', 'b', 'b', 'a']) == {'c':0, 'b':1, 'a':2}

    def test_show_ablation(self):
        """Ensure show_ablation works as expected"""
        debug.trace(4, "test_show_ablation()")
        ## TODO: WORK-IN-PROGRESS

    def test_show_precision_recall(self):
        """Ensure show_precision_recall works as expected"""
        debug.trace(4, "test_show_precision_recall()")
        ## TODO: WORK-IN-PROGRESS

    def test_show_average_precision_recall(self):
        """Ensure show_average_precision_recall works as expected"""
        debug.trace(4, "test_show_average_precision_recall()")
        ## TODO: WORK-IN-PROGRESS

    def test_main(self):
        """Ensure main works as expected"""
        debug.trace(4, "test_main()")
        ## TODO: WORK-IN-PROGRESS


if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
