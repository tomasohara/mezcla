#! /usr/bin/env python
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
from mezcla.unittest_wrapper import TestWrapper

# Note: Rreference are used for the module to be tested:
#    THE_MODULE:	    global module object
# import mezcla.transpose_data as THE_MODULE


SAMPLE_INPUT = """i_timestamp   | i_ip_addr1 |             i_session_id                 | i_keyword
1384983367.79 | 1138872328 | 003a4a80db5eda5fa5e7359d57afc29ac1fec377 | Staples Retail Office Products
1384983366.04 | 1158147302 | 003b7091f121e03a4ca4e6f8b30e052f78fba19f | Quality
1384983366.04 | 1158147302 | 003b7091f121e03a4ca4e6f8b30e052f78fba19f | Quality
1384948918.84 | 1130098581 | 003bb1e9a137f6cf1ddd58941c6c7a326c9b2c3d | medical assistant"""

SAMPLE_OUTPUT_EXPECTED = """i_timestamp: 1384983367.79 | 1384983366.04 | 1384983366.04 | 1384948918.84
i_ip_addr1: 1138872328 | 1158147302 | . | 1130098581
i_session_id: 003a4a80db5eda5fa5e7359d57afc29ac1fec377 | 003b7091f121e03a4ca4e6f8b30e052f78fba19f | . | 003bb1e9a137f6cf1ddd58941c6c7a326c9b2c3d
i_keyword: Staples Retail Office Products | Quality | . | medical assistant"""

SAMPLE_OUTPUT_ACTUAL = """
i_timestamp   |1384983367.79 |1384983366.04 |1384983366.04 |1384948918.84 
 i_ip_addr1 | 1138872328 | 1158147302 | 1158147302 | 1130098581 
             i_session_id                 | 003a4a80db5eda5fa5e7359d57afc29ac1fec377 | 003b7091f121e03a4ca4e6f8b30e052f78fba19f | 003b7091f121e03a4ca4e6f8b30e052f78fba19f | 003bb1e9a137f6cf1ddd58941c6c7a326c9b2c3d 
 i_keyword| Staples Retail Office Products| Quality| Quality| medical assistant
"""
class TestTransposeData(TestWrapper):
    """Class for testcase definition"""
    script_file = TestWrapper.get_module_file_path(__file__)
    script_module = TestWrapper.get_testing_module_name(__file__)
    use_temp_base_dir = True    # treat TEMP_BASE as directory

    def test_transpose_table(self):
        """Ensure test_transpose_table works as expected"""
        
        debug.trace(4, f"test_transpose_table(); self={self}")
        test_run_command_1 = f'echo "{SAMPLE_INPUT}" > {self.temp_file}'
        test_run_command_2 = f'../transpose_data.py --delim="|" < {self.temp_file}'
        
        gh.run(test_run_command_1)
        output = gh.run(test_run_command_2)
        
        # Problem with output (self.run_script(self.temp_file) returns '')
        # ERROR: ...Full output truncated (1 line hidden), use '-vv' to show
        
        assert (output == SAMPLE_OUTPUT_ACTUAL)
        return

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
    
