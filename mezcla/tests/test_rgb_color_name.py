#! /usr/bin/env python3
#
# Test(s) for ../rgb_color_name.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_rgb_color_name.py
#
# TODO2:
# - Likewise remove long-in-place xfail's in other test files (unless brittle).
#
## UPDATE 02 Sep 26: paramwterizes hex3 and hex6 tests

"""Tests for rgb_color_name module"""

# Standard packages
import re

# Installed packages
import pytest
from unittest_parametrize import ParametrizedTestCase, parametrize

# Local packages
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import system
from mezcla.my_regex import my_re
from mezcla.misc_utils import unzip
import mezcla.tests.common_module as cm

# Note: Two references are used for the module to be tested:
#    THE_MODULE:            global module object
import mezcla.rgb_color_name as THE_MODULE

class TestRgbColorName(TestWrapper, ParametrizedTestCase):
    """Class for testcase definition"""
    script_file = TestWrapper.get_module_file_path(__file__)
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    def helper_rgb_color_name(self, cmd_option:str, file_content:str, **kwargs):
        """Runs script over FILE_CONTENT using CMD_OPTION
        Note: keyword args for run_script passed along (e.g., env_options and log_file
        """
        ## TODO3: cmd_option => cmd_options (for consistency with run_script); similarly for file_content
        data_file = self.create_temp_file(contents=file_content)
        output = self.run_script(options=cmd_option, data_file=data_file, **kwargs)
        return output

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
        # =>
        #   <(255, 0, 0), red>:  72.98% (1888)
        #   <(0, 255, 0), lime>:  24.35% (630)
        #   <(0, 0, 255), blue>:   2.67% (69)
        output = self.run_script("", self.temp_file)
        self.do_assert(re.search(r"<\(0, 255, 0\), lime>", output))
        return
        
    def test_rgb_regex(self):
        """Test the regex for RGB specification"""
        debug.trace(4, "test_rgb_regex()")
        option = "--rgb-regex '\\((\\d+),\\s*(\\d+),\\s*(\\d+)\\)'"
        color_tuple = "(0, 255, 0)"
        color = "lime"
        helper_output = self.helper_rgb_color_name(
            cmd_option=option,
            file_content=color_tuple
        )
        assert color in helper_output

    @parametrize(
        "hex3_val, color",
        [("#f45", "tomato"),
         ("#ddd", "gainsboro"),
         ("#eee", "whitesmoke"),
         ## TODO: ("xHHH", "color"),
        ])
    def test_rgb_hex3(self, hex3_val, color):
        """Test the hex3 option"""
        debug.trace(4, f"test_rgb_hex3({hex3_val}, {color})")
        debug.assertion(my_re.search(r"^#[0-9a-f]{3}$", hex3_val))
        option = "--hex3"
        helper_output = self.helper_rgb_color_name(
            cmd_option=option,
            file_content=hex3_val
        )
        # example: <#ddd, gainsboro>
        ## TODO4?:
        ## clean_hex = hex3_val.replace(',', '')
        ## assert f"<{clean_hex}, {color}>" in helper_output
        assert f"<{hex3_val}, {color}>" in helper_output

    @parametrize(
        "hex6_val, color",
        [("#a36651", "sienna"),
         ("#f5deb3", "wheat"),
         ("#7fff00", "chartreuse"),
         ## TODO: ("xHHHHHH", "color"),
        ])
    def test_rgb_hex6(self, hex6_val, color):
        """Test the hex6 option"""
        debug.trace(4, f"test_rgb_hex6({hex6_val}, {color})")
        debug.assertion(my_re.search(r"^#[0-9a-f]{6}$", hex6_val))
        option = "--hex6"
        helper_output = self.helper_rgb_color_name(
            cmd_option=option,
            file_content=hex6_val
        )
        # example: <#f5deb3, wheat>
        assert color in helper_output

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

    @pytest.mark.skipif(cm.SKIP_EXPECTED_ERRORS, reason=cm.SKIP_EXPECTED_REASON)
    def test_bad_regex(self):
        """Verify invalid regex flagged"""
        temp_log_file = self.get_temp_file() + ".log"
        output = self.helper_rgb_color_name(
            cmd_option="--rgb-regex '(.) (.) (.'",
            file_content="a b c",
            log_file=temp_log_file)
        # Should lead to exception
        # example: "re.error: missing ), unterminated subpattern at position 8"
        assert output == ""
        assert "re.error" in system.read_entire_file(temp_log_file)
        # Should have no color spec: <a b c, lightsteelblue>
        assert not my_re.search(r"<a b c, \w+>", output)

    def test_dump_hexnames(self):
        """Verify that DUMP_HEXNAMES covers 100+ unique colors"""
        temp_log_file = self.get_temp_file() + ".log"
        output = self.run_script(
            log_file=temp_log_file,
            options="--verbose",        # dummy arg to bypass usage
            # note: trace level 1 (ERROR) overrides the default of 0 (NONE) for subprocesses;
            # see disable_subcommand_tracing in unittest_wrapper.py and glue_helpers.py.
            env_options="DUMP_HEXNAMES=1 DEBUG_LEVEL=1")
        log_lines = system.read_lines(temp_log_file)
        assert output == ""
        # There should be 100+ entries (currently 138)
        # example: color: thistle=#d8bfd8
        color_info = gh.extract_matches(r"color: (\w+)=(#[0-9a-f]{6})",
                                        log_lines, fields=2)
        color_names, color_codes = unzip(color_info)
        debug.trace_expr(5, color_names, color_codes)
        assert 128 < len(system.unique_items(color_names)) < 256
        assert 128 < len(system.unique_items(color_codes)) < 256
            
#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
