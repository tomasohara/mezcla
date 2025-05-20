#! /usr/bin/env python3
#
# Test(s) for ../evaluate_example_tests.py
#
# Notes:
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_evaluate_example_tests.py
#

"""Tests for evaluate_example_tests module"""

# Standard modules
## TODO: from collections import defaultdict

# Installed modules
import pytest

# Local modules
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla import debug
from mezcla.my_regex import my_re
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                        global module object
#    TestIt.script_module:              path to file
import mezcla.evaluate_example_tests as THE_MODULE

#------------------------------------------------------------------------

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.xfail                   # TODO: remove xfail
    ## DEBUG: @trap_exception            # TODO: remove when debugged
    def test_01_data_file(self):
        """Tests run_script w/ data file"""
        debug.trace(4, f"TestIt.test_01_data_file(); self={self}")
        data = ["def fu(): return 123",
                "# EX: fu() => 123"]
        system.write_lines(self.temp_file, data)
        output = self.run_script(options="--output", data_file=self.temp_file)
        self.do_assert(my_re.search(r">>> fu\(\)\n123", output.strip()))
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_02_TestConverter(self):
        """Test TestConverter class"""
        debug.trace(4, f"TestIt.test_02_TestConverter(); self={self}")
        tc = THE_MODULE.TestConverter()
        self.do_assert(tc.convert("# EX: func() => 987", 1))
        self.do_assert(not tc.convert("# example: func() => 987", 1))
        self.do_assert(my_re.search(r">>> func\(\)\n987\n", tc.get_tests()))
        return
#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
