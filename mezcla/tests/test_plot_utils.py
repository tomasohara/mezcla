#! /usr/bin/env python3
#
# Test(s) for ../plot_utils.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_plot_utils.py
#

"""Tests for plot_utils module"""

# Standard packages
## NOTE: this is empty for now

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla.unittest_wrapper import TestWrapper, invoke_tests

# Note: Two references are used for the module to be tested:
#    THE_MODULE:               module object (e.g., <module 'mezcla.main' ...>)
#    TestIt.script_module:     dotted module path (e.g., "mezcla.main")
import mezcla.plot_utils as THE_MODULE

class TestPlotUtils(TestWrapper):
    """Class for testcase definition"""
    # note: script_module used in argument parsing sanity check (e.g., --help)
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.skip
    def test_something(self):
        """TODO: flesh out test for something"""
        debug.trace(4, "TestIt.test_something()")
        self.do_assert(False, "TODO: implement")
        return

    @pytest.mark.xfail
    def test_something_else(self):
        """TODO: flesh out test for something else"""
        debug.trace(4, "TestIt.test_something_else()")
        self.do_assert(False, "TODO: implement")
        return

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
