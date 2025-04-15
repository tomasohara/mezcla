#! /usr/bin/env python3
#
# Test(s) for ../os_utils.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_os_utils.py
#
# TODO3: apply mezcla conventions (see tests/template.py).
#

"""Tests for os_utils module"""

# Standard packages
import types

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla import os_utils
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper, invoke_tests

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	         global module object
#    TestWrapper.script_module:  path to file
THE_MODULE = os_utils

class TestOsUtils(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @classmethod
    def setupClass(cls):
        """Per-class initialization"""  # why not docstring inherited (or pylint bug?)
        debug.trace(5, f"TestOsUtils.setupClass({cls})")
        debug.trace_expr(5, __file__, THE_MODULE)
        super().setUpClass(filename=__file__, module=THE_MODULE)
    
    def test_split_extension(self):
        """Ensure test_split_extension works as expected"""
        assert(os_utils.split_extension("fubar.txt") == ("fubar", ".txt"))
        assert(os_utils.split_extension("abc.def.txt") == ("abc.def", ".txt"))

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_02_no_other_functions(self):
        """Make sure no other functions defined in the module"""
        ## TODO3: put helper for this in tests/common_module.py; also,
        ## use monkeypatch to check for new function
        debug.trace(4, f"TestIt.test_02_no_other_functions(); self={self}")
        defined_functions = [
            m for m in dir(THE_MODULE)
            if isinstance(getattr(THE_MODULE, m), types.FunctionType)]
        self.do_assert(not (system.difference(
            defined_functions, ['main', 'split_extension'])))
        return


if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
