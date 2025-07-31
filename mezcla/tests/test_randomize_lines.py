#! /usr/bin/env python3
#
# Test(s) for ../randomize_lines.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_randomize_lines.py
#

"""Tests for randomize_lines module"""

# Standard packages
## NOTE: this is empty for now

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla import system
from mezcla import tpo_common as tpo
from mezcla.unittest_wrapper import TestWrapper, invoke_tests

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
import mezcla.randomize_lines as THE_MODULE

class TestRandomizeLines(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_data_file(self):
        """Tests run_script w/ data file"""
        debug.trace(4, f"TestIt.test_data_file(); self={self}")
        NUM_LINES = 100
        data = [f"line {l}" for l in range(NUM_LINES)]
        system.write_lines(self.temp_file, data)
        ## TODO: add use_stdin=True to following if no file argument
        output = self.run_script(options="--percent 10", data_file=self.temp_file)
        random_lines = output.splitlines()
        debug.trace_values(5, random_lines)
        self.do_assert(len(random_lines) == 10)
        self.do_assert(tpo.is_subset(random_lines, data))
        return


if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
