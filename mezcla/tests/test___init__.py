#! /usr/bin/env python3
#
# Test(s) for ../__init__.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test___init__.py
#

"""Tests for __init__ module"""

# Standard packages
import re

# Installed packages
import pytest

# Local packages
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla import debug
from mezcla.my_regex import my_re

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                  global module object
#    TestTemplate.script_module:  path to file
import mezcla.__init__ as THE_MODULE

class TestIt(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_data_file(self):
        """Makes sure TODO works as expected"""
        debug.trace(4, f"TestIt.test_data_file(); self={self}")
        output = self.run_script("", self.temp_file)
        assert(not output.strip())
        return

class TestIt2:
    """Another class for testcase definition
    Note: Needed to avoid error with pytest due to inheritance with unittest.TestCase via TestWrapper"""

    def test_version(self):
        """Test version string"""
        debug.trace(5, f"test_version(); self={self}")
        assert(hasattr(THE_MODULE, "__VERSION__"))
        assert(my_re.match(r"^\d+.\d+\.\d+.*", THE_MODULE.__VERSION__))


#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
