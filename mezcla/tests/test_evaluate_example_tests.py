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
from mezcla import glue_helpers as gh
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

        # Create valid python file from dummy data (i.e., valid basename and code)
        data = ["def fu(): return 123",
                "# EX: fu() => 123"]
        temp_dir, temp_file = system.split_path(self.temp_file)
        temp_file = my_re.sub("-", "_", temp_file)
        temp_file += ".py"
        temp_base = gh.form_path(temp_dir, temp_file)
        system.write_lines(temp_base, data)

        # Run and evaluate the test
        output = self.run_script(options="--just-output", data_file=temp_base)
        self.do_assert(my_re.search(r">>> fu\(\)\n123", output.strip()))
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_02_TestConverter(self):
        """Test TestConverter class"""
        debug.trace(4, f"TestIt.test_02_TestConverter(); self={self}")
        tc = THE_MODULE.TestConverter()
        self.do_assert(tc.convert("# EX: func() => 987", line_num=1))
        self.do_assert(not tc.convert("# example: func() => 987", line_num=2))
        self.do_assert(my_re.search(r">>> func\(\)\n987\n", tc.get_tests()))
        return
#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
