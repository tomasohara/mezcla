#! /usr/bin/env python
#
# Test(s) for ../rgb_color_name.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_rgb_color_name.py
#

"""Tests for rgb_color_name module"""

# Standard packages
import re

# Installed packages
import pytest

# Local packages
from mezcla.unittest_wrapper import TestWrapper
from mezcla import debug
from mezcla import system
from mezcla import glue_helpers as gh

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
import mezcla.rgb_color_name as THE_MODULE

class TestRgbColorName(TestWrapper):
    """Class for testcase definition"""
    script_file = TestWrapper.get_module_file_path(__file__)
    script_module = TestWrapper.get_testing_module_name(__file__)

    def test_data_file(self):
        """Makes sure colors annotated as expected"""
        debug.trace(4, "TestRgbColorName.test_data_file()")

        content = (
            'Extracted colors:\n'
            '(255, 0, 0):  72.98% (1888)\n'
            '(0, 255, 0):  24.35% (630)\n'
            '(0, 0, 255):   2.67% (69)\n'
            '\n'
            'Pixels in output: 2587 of 11648\n'
        )
        system.write_file(self.temp_file, content)
        #   =>
        #   <(255, 0, 0), red>    :  33.33% (1)
        #   <(0, 255, 0), lime>    :  33.33% (1)
        #   <(0, 0, 255), blue>    :  33.33% (1)        
        output = self.run_script("", self.temp_file)
        self.do_assert(re.search(r"<\(0, 255, 0\), lime>", output))
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_rgb_regex(self):
        """Test the regex for RGB specification"""
        debug.trace(4, "test_rgb_regex()")
        script = THE_MODULE.Script(skip_args=True)
        self.do_assert(script.rgb_regex == r'\((0?x?[0-9A-F]+), (0?x?[0-9A-F]+), (0?x?[0-9A-F]+)\)')
        line = "(39, 39, 39)   :  24.35% (630)"
        script.process_line(line)
        self.do_assert("<(39, 39, 39), darkslategray>" in self.get_stdout())
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
