#! /usr/bin/env python
#
# Test(s) for ../text_categorizer.py
#
# Notes:
# - This can be run as follows:
#   $ PYTHONPATH="$(realpath .)/..):$PYTHONPATH" python tests/test_<module>.py
#

"""Tests for text_categorizer module"""

# Standard packages
import re
import unittest

# Installed packages
## TODO: import pytest

# Local packages
from mezcla.unittest_wrapper import TestWrapper
from mezcla import debug
## TODO: from mezcla import system
from mezcla import glue_helpers as gh

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
#    TestIt.script_module   string name
import mezcla.text_categorizer as THE_MODULE
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


class TestIt(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__)
    # TODO: use_temp_base_dir = True            # treat TEMP_BASE as directory
    # note: temp_file defined by parent (along with script_module, temp_base, and test_num)

    def test_data_file(self):
        """Makes sure TODO works as expected"""
        debug.trace(4, "TestIt.test_data_file()")
        data = ["TODO1", "TODO2"]
        gh.write_lines(self.temp_file, data)
        output = self.run_script("", self.temp_file)
        self.assertTrue(re.search(r"TODO-pattern", 
                                  output.strip()))
        return

    def test_something_else(self):
        """TODO: flesh out test for something else"""
        debug.trace(4, "test_something_else()")
        self.fail("TODO: code test")
        ## ex: self.assertEqual(THE_MODULE.TODO_function() == TODO_value)
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    unittest.main()
