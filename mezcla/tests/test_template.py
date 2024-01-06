#! /usr/bin/env python
#
# Test(s) for ../template.py
#
# Notes:
# - This is simple test of module not the test template (see ./template.py).
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_template.py
#

"""Tests for template module"""

# Standard packages
import re

# Installed packages
import pytest

# Local packages
from mezcla.unittest_wrapper import TestWrapper
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
import mezcla.template as THE_MODULE


class TestTemplate(TestWrapper):
    """Class for testcase definition"""
    script_file = TestWrapper.get_module_file_path(__file__)
    script_module = TestWrapper.get_testing_module_name(__file__)

    def test_01_data_file(self):
        """Makes sure to-do grep works as expected"""
        debug.trace(4, "TestTemplate.test_01_data_file()")
        data = ["TEMP", "TODO", "DONE"]
        gh.write_lines(self.temp_file, data)
        # note: the support for --TODO-arg placeholder involves grepping for TODO
        output = self.run_script("--TODO-arg", self.temp_file)
        assert re.search(r"arg1 line \(2\): TODO", output.strip())
        return

    def test_02_captured_input_line(self):
        """Ensure that lines are correctly processed and 
        irrelevant lines are effectively ignored"""
        debug.trace(4, "test_02_captured_input_line()")
        data = "hey"
        ## BAD:
        ## self.run_script(env_options=f"echo {data} | DEBUG_LEVEL=4", log_file=self.temp_file)
        ## assert f"Ignoring line (1): {data}" in gh.read_file(self.temp_file)
        data_file = f"{self.temp_file}.txt"
        log_file = f"{self.temp_file}.log"
        system.write_lines(data_file, ["data"])
        self.run_script(env_options="DEBUG_LEVEL=4", data_file=data_file, log_file=log_file)
        stdout = self.get_stdout()
        self.do_assert(f"Ignoring line (1): {data}", stdout)
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
