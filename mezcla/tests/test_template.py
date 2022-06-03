#! /usr/bin/env python
#
# Test(s) for ../template.py
#
# Notes:
# - This is simple test of module not the test template (see ./template.py).
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python tests/test_template.py
#

"""Tests for template module"""

# Standard packages
import re
import unittest

# Installed packages
## TODO: import pytest

# Local packages
from mezcla.unittest_wrapper import TestWrapper
from mezcla import debug
from mezcla import glue_helpers as gh

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
#    TestIt.script_module   string name
## TODO: template => new name
import mezcla.template as THE_MODULE
#
# Note: sanity test for customization (TODO: remove if desired)
if not re.search(__file__, r"\btemplate.py$"):
    debug.assertion("mezcla.template" not in str(THE_MODULE))


class TestIt(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__)

    def test_data_file(self):
        """Makes sure to-do grep works as expected"""
        debug.trace(4, "TestIt.test_data_file()")
        data = ["TEMP", "TODO", "DONE"]
        gh.write_lines(self.temp_file, data)
        output = self.run_script("--TODO-arg", self.temp_file)
        self.assertTrue(re.search(r"arg1 line \(2\): TODO", 
                                  output.strip()))
        return

    def test_something_else(self):
        """Make sure arg value reflects to-do nature"""
        debug.trace(4, "test_something_else()")
        self.assertTrue("todo" in THE_MODULE.TODO_ARG.lower())
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    unittest.main()
