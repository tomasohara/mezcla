#! /usr/bin/env python3
#
# Test(s) for ../test_simple_main_example.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_simple_main_example.py
#

"""Tests for simple_main_example module"""

# Standard packages
## TODO: from collections import defaultdict

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla.my_regex import my_re
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
#    TestIt.script_module:              path to file
import mezcla.simple_main_example as THE_MODULE

class TestSimpleMainExample(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_data_file(self):
        """Tests run_script w/ data file"""
        debug.trace(4, f"TestIt.test_data_file(); self={self}")
        data = ["fubar1", "FUBAR2", "", "FuBART"]
        system.write_lines(self.temp_file, data)
        # Line mode
        output = self.run_script(options="", data_file=self.temp_file)
        self.do_assert(my_re.search(r"fubar1", output.strip()))
        self.do_assert(not my_re.search(r"FUBAR2", output.strip()))
        self.do_assert(not my_re.search(r"FuBART", output.strip()))
        # Para mode
        output = self.run_script(options="--para", data_file=self.temp_file)
        self.do_assert(my_re.search(r"FUBAR2", output.strip()))
        # Entire file
        output = self.run_script(options="--entire", data_file=self.temp_file)
        self.do_assert(my_re.search(r"FuBART", output.strip()))
        return

    def test_fitler_class(self):
        """Test SimpleFilter"""
        filter_inst = THE_MODULE.SimpleFilter(r"^\s*M(oo|u)law\s*$", flags=my_re.IGNORECASE)
        self.do_assert(filter_inst.include("MooLaw"))
        self.do_assert(filter_inst.include(" MULAW"))
        self.do_assert(not filter_inst.include("Mucho MooLaw"))
        self.do_assert(not filter_inst.include("MooLAW galore"))

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
