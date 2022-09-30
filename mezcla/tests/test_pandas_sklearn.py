#! /usr/bin/env python
#
# Test(s) for ../pandas_sklearn.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_pandas_sklearn.py
#

"""Tests for pandas_sklearn module"""

# Standard packages
## NOTE: this is empty for now

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.unittest_wrapper import TestWrapper

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
import mezcla.pandas_sklearn as THE_MODULE

# Constants
EXAMPLES = f'{gh.dir_path(__file__)}/../examples'
RESOURCES = f'{gh.dir_path(__file__)}/resources'
IRIS_EXAMPLE = f'{EXAMPLES}/iris.csv'
IRIS_OUTPUT = f'{EXAMPLES}/iris.csv'

class TestPandasSklearnUtils:
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


class TestPandasSklearn(TestWrapper):
    """Class for testcase definition"""
    script_file = TestWrapper.get_module_file_path(__file__)
    script_module = TestWrapper.get_testing_module_name(__file__)

    def test_main_without_args(self):
        """Ensure main without args works as expected"""
        debug.trace(4, "test_main_without_args()")
        ## TODO: for some reason, the output differs from used in tests files and with command-line
        output = self.run_script(data_file='')
        assert 'Usage:' in gh.read_file(output)

    def test_normal_usage(self):
        """Ensure main without args works as expected"""
        debug.trace(4, "test_normal_usage()")
        ## TODO: for some reason, the output differs from used in tests files and with command-line
        output = self.run_script(data_file=IRIS_EXAMPLE)
        assert output + '\n' == gh.read_file(IRIS_OUTPUT)


if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
