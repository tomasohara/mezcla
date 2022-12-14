#! /usr/bin/env python
#
# Test(s) for ../keras_param_search.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_keras_param_search.py
#

"""Tests for keras_param_search module"""

# Standard packages

# Installed packages
import pytest

# Local packages
from mezcla import debug

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
## TODO: fix ModuleNotFoundError: No module named 'keras'
## import mezcla.keras_param_search as THE_MODULE

class TestKerasParamSearch:
    """Class for testcase definition"""

    def test_round3(self):
        """Ensure round3 works as expected"""
        debug.trace(4, "test_round3()")
        ## TODO: WORK-IN=PROGRESS

    def test_non_negative(self):
        """Ensure non_negative works as expected"""
        debug.trace(4, "test_non_negative()")
        ## TODO: WORK-IN=PROGRESS

    def test_create_feature_mapping(self):
        """Ensure create_feature_mapping works as expected"""
        debug.trace(4, "test_create_feature_mapping()")
        assert THE_MODULE.create_feature_mapping(['c', 'b', 'b', 'a']) == {'c':0, 'b':1, 'a':2}

    def test_create_keras_model(self):
        """Ensure create_keras_model works as expected"""
        debug.trace(4, "test_create_keras_model()")
        ## TODO: WORK-IN=PROGRESS

    ## TODO: test MyKerasClassifier class
    ## TODO: test main


if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
