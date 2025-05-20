#! /usr/bin/env python3
#
# Tests for transpose_data module
#
# Notes:
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_transpose_data.py
#

"""Tests for transpose_data module"""

# Standard packages
import re

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla.unittest_wrapper import trap_exception
from mezcla.my_regex import my_re
from mezcla import system

# Note: Rreference are used for the module to be tested:
#    THE_MODULE:	    global module object
import mezcla.transpose_data as THE_MODULE

## TODO4: move to header comments
# SAMPLE_INPUT = """i_timestamp   | i_ip_addr1 |             i_session_id                 | i_keyword
# 1384983367.79 | 1138872328 | 003a4a80db5eda5fa5e7359d57afc29ac1fec377 | Staples Retail Office Products
# 1384983366.04 | 1158147302 | 003b7091f121e03a4ca4e6f8b30e052f78fba19f | Quality
# 1384983366.04 | 1158147302 | 003b7091f121e03a4ca4e6f8b30e052f78fba19f | Quality
# 1384948918.84 | 1130098581 | 003bb1e9a137f6cf1ddd58941c6c7a326c9b2c3d | medical assistant"""
#
# SAMPLE_OUTPUT_EXPECTED = """i_timestamp: 1384983367.79 | 1384983366.04 | 1384983366.04 | 1384948918.84
# i_ip_addr1: 1138872328 | 1158147302 | . | 1130098581
# i_session_id: 003a4a80db5eda5fa5e7359d57afc29ac1fec377 | 003b7091f121e03a4ca4e6f8b30e052f78fba19f | . | 003bb1e9a137f6cf1ddd58941c6c7a326c9b2c3d
# i_keyword: Staples Retail Office Products | Quality | . | medical assistant"""
#
# SAMPLE_OUTPUT_ACTUAL = """
# i_timestamp   |1384983367.79 |1384983366.04 |1384983366.04 |1384948918.84 
#  i_ip_addr1 | 1138872328 | 1158147302 | 1158147302 | 1130098581 
#              i_session_id                 | 003a4a80db5eda5fa5e7359d57afc29ac1fec377 | 003b7091f121e03a4ca4e6f8b30e052f78fba19f | 003b7091f121e03a4ca4e6f8b30e052f78fba19f | 003bb1e9a137f6cf1ddd58941c6c7a326c9b2c3d 
#  i_keyword| Staples Retail Office Products| Quality| Quality| medical assistant
#  """

## OLD:
## class TestTransposeData(TestWrapper):
##     """Class for testcase definition"""
##     script_file = TestWrapper.get_module_file_path(__file__)
##     script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
##     use_temp_base_dir = True    # treat TEMP_BASE as directory
##
##     def test_transpose_table(self):
##         """Ensure test_transpose_table works as expected"""
##         tmp_cmd_1 = self.get_temp_file()
##         tmp_cmd_2 = self.get_temp_file()
##         debug.trace(4, f"test_transpose_table(); self={self}")
##         test_run_command_1 = f'echo "{SAMPLE_INPUT}" > {tmp_cmd_1}'
##         test_run_command_2 = f'../transpose_data.py --delim="|" < {tmp_cmd_1} > {tmp_cmd_2}'
##
##         gh.run(test_run_command_1)
##         gh.run(test_run_command_2)
##
##         # Problem with output (self.run_script(self.temp_file) returns '')
##         # ERROR: ...Full output truncated (1 line hidden), use '-vv' to show
##         # FIXED 1: Replaced self.temp_file with self.get_temp_file
##         # FIXED 2: Replaced self.run_script with gh.read_file
##         # FIXED 3: Replaced == with in comparing output and SAMPLE_OUTPUT
##         # NOTE 1: Changing the position of """ in SAMPLE_OUTPUT varies the output
##
##         output = gh.read_file(tmp_cmd_2)
##         assert (output in SAMPLE_OUTPUT_ACTUAL)
##         return

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
    invoke_tests(__file__)
