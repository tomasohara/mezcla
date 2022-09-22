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
## TODO: from mezcla import system
from mezcla import glue_helpers as gh

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
import mezcla.rgb_color_name as THE_MODULE
#
# Note: sanity test for customization (TODO: remove if desired)
if not re.search(__file__, r"\btemplate.py$"):
    debug.assertion("mezcla.template" not in str(THE_MODULE))

## TODO:
## # Environment options
## # Note: These are just intended for internal options, not for end users.
## # It also allows for enabling options in one place.
## #
## FUBAR = system.getenv_bool("FUBAR", False,
##                            description="Fouled Up Beyond All Recognition processing")


class TestRgbColorName(TestWrapper):
    """Class for testcase definition"""
    script_file = TestWrapper.get_module_file_path(__file__)
    script_module = TestWrapper.get_testing_module_name(__file__)
    # TODO: use_temp_base_dir = True            # treat TEMP_BASE as directory
    # note: temp_file defined by parent (along with script_module, temp_base, and test_num)

    def test_data_file(self):
        """Makes sure TODO works as expected"""
        debug.trace(4, "TestRgbColorName.test_data_file()")

        gh.run(f"perl -e 'print(\"\\xFF\\x00\\x00\\x00\\xFF\\x00\\x00\\x00\\xFF\");' | rawtoppm 3 1 | pnmtopng | extcolors > {self.temp_file}")
        #   =>
        #   <(255, 0, 0), red>    :  33.33% (1)
        #   <(0, 255, 0), lime>    :  33.33% (1)
        #   <(0, 0, 255), blue>    :  33.33% (1)        
        output = self.run_script("", self.temp_file)
        assert re.search(
            r"<(0, 255, 0), lime> ",
            output.strip(),
            )
        return

    def test_something_else(self):
        """TODO: flesh out test for something else"""
        debug.trace(4, "test_something_else()")
        self.fail("TODO: code test")
        ## ex: assert THE_MODULE.TODO_function() == TODO_value
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
