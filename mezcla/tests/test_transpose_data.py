#! /usr/bin/env python
#
# Tests for transpose_data module
#
# Notes:
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_transpose_data.py
#

"""Tests for transpose_data module"""

# Standard modules
## NOTE: this is empty for now

# Installed modules
import pytest

# Local modules
from mezcla import debug
from mezcla.unittest_wrapper import TestWrapper
from mezcla.unittest_wrapper import trap_exception
from mezcla.my_regex import my_re
from mezcla import system

# Note: Rreference are used for the module to be tested:
#    THE_MODULE:	    global module object
import mezcla.transpose_data as THE_MODULE

class TestTransposeData(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.xfail                   # TODO: remove xfail
    @trap_exception
    def test_data_file(self):
        """Makes sure simple transposition works as expected"""
        debug.trace(4, f"TestIt.test_data_file(); self={self}")
        data = ["H1\tH2", "v1\tv2"]
        system.write_lines(self.temp_file, data)
        output = self.run_script(options="", data_file=self.temp_file)
        self.do_assert(my_re.search(r"H1.*v1", output.strip()))
        self.do_assert(not my_re.search(r"v1.*v2", output.strip()))
        return


if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
