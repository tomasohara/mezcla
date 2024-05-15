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

    ## NOTE: All the tests are passing, thus keeping the xfail mark
    def helper_rgb_color_name(self, cmd_option:str, file_content:str):
        data_file = gh.create_temp_file(contents=file_content)
        output = self.run_script(options=cmd_option, data_file=data_file)
        return output

    @pytest.mark.xfail
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
        
    @pytest.mark.xfail
    def test_rgb_regex(self):
        """Test the regex for RGB specification"""
        debug.trace(4, "test_rgb_regex()")

        ## OLD:
        # script = THE_MODULE.Script(skip_args=True)
        # self.do_assert(script.rgb_regex == r'\((0?x?[0-9A-F]+), (0?x?[0-9A-F]+), (0?x?[0-9A-F]+)\)')
        # line = "(39, 39, 39)   :  24.35% (630)"
        # script.process_line(line)
        # self.do_assert("<(39, 39, 39), darkslategray>" in self.get_stdout())
        
        ## OLD: 
        # rgb_regex_val = r'\\((\\d+),\\s*(\\d+),\\s*(\\d+)\\)'
        # option = f'--rgb-regex {rgb_regex_val}'

        option = f"--rgb-regex '\\((\\d+),\\s*(\\d+),\\s*(\\d+)\\)'"
        color_tuple = "(0, 255, 0)"
        color = "lime"
        helper_output = self.helper_rgb_color_name(
            cmd_option=option,
            file_content=color_tuple
        )
        assert color in helper_output
    
    @pytest.mark.xfail
    def test_rgb_hex3(self):
        """Test the hex3 option"""
        debug.trace(4, "test_rgb_hex3()")
        option = "--hex3"
        hex3_val = "#f45"
        color = "tomato"
        helper_output = self.helper_rgb_color_name(
            cmd_option=option,
            file_content=hex3_val
        )
        assert color in helper_output

        ## OLD:
        # data_file = gh.create_temp_file(contents=hex3_val)
        # output = self.run_script(
        #     data_file=data_file,
        #     options=option
        # )
        # assert color in output

    @pytest.mark.xfail
    def test_rgb_hex6(self):
        """Test the hex6 option"""
        debug.trace(4, "test_rgb_hex3()")
        option = "--hex6"
        hex6_val = "#a36651"
        color = "sienna"
        helper_output = self.helper_rgb_color_name(
            cmd_option=option,
            file_content=hex6_val
        )
        assert color in helper_output

        ## OLD:
        # data_file = gh.create_temp_file(contents=hex6_val)
        # output = self.run_script(
        #     data_file=data_file,
        #     options=option
        # )
        # assert color in output
    
    @pytest.mark.xfail
    def test_rgb_show_hex(self):
        """Test the show-hex option"""
        debug.trace(4, "test_rgb_shiw_hex()")
        option = "--show-hex"
        color_tuple = "(39, 54, 251)"
        color = "royalblue"
        color_hex = "0x2736FB"
        helper_output = self.helper_rgb_color_name(
            cmd_option=option,
            file_content=color_tuple
        )
        assert color in helper_output
        assert color_hex in helper_output

        ## OLD: Without helper functions
        # data_file = gh.create_temp_file(contents=color_tuple)
        # output = self.run_script(
        #     data_file=data_file,
        #     options=option
        # )
        # assert color and color_hex in output

    @pytest.mark.xfail
    def test_rgb_hex(self):
        """Test the hex option"""
        debug.trace(4, "test_rgb_hex()")
        option = "--hex"
        color_tuple = "(145, 128, 43)"
        color = "yellow"
        helper_output = self.helper_rgb_color_name(
            cmd_option=option,
            file_content=color_tuple
        )
        assert color in helper_output

        ## OLD:
        # data_file = gh.create_temp_file(contents=color_tuple)
        # output = self.run_script(
        #     data_file=data_file,
        #     options=option
        # )
        # assert color in output

    @pytest.mark.xfail
    def test_rgb_skip_direct(self):
        """Test the skip-direct option"""
        debug.trace(4, "test_rgb_skip_direct()")

        ## NOTE: Variation of colorname for --hex and --skip-direct option
        ## NOTE: --skip-direct provides more precision with color names
        # ricekiller@pop-os:~/mezcla/mezcla$ python3 rgb_color_name.py --skip-direct input.txt
        # <(145, 128, 43), olivedrab>
        # ricekiller@pop-os:~/mezcla/mezcla$ python3 rgb_color_name.py --hex input.txt
        # <(145, 128, 43), yellow>

        option = "--skip-direct"
        color = "olivedrab"
        color_tuple = "(145, 128, 43)"
        helper_output = self.helper_rgb_color_name(
            cmd_option=option,
            file_content=color_tuple
        )
        assert color in helper_output

        ## OLD: WIthout helper function
        # data_file = gh.create_temp_file(contents=color_tuple)
        # output = self.run_script(
        #     data_file=data_file,
        #     options=option
        # )
        # assert color in output
        
#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
