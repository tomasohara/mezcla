#! /usr/bin/env python
#
# Test(s) for ../hugging_face_translation.py
#

"""Tests for hugging_face_translation module"""

# Standard modules
## TODO: from collections import defaultdict

# Installed modules
import pytest

# Local modules
from mezcla.unittest_wrapper import TestWrapper
from mezcla.unittest_wrapper import trap_exception
from mezcla import debug
## TODO: from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                        global module object
#    TestIt.script_module:              path to file
import mezcla.examples.hugging_face_translation as THE_MODULE
#
# Note: sanity test for customization (TODO: remove if desired)
if not my_re.search(__file__, r"\btemplate.py$"):
    debug.assertion("mezcla.template" not in str(THE_MODULE))

#------------------------------------------------------------------------

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.xfail                   # TODO: remove xfail
    ## DEBUG:
    @trap_exception
    def test_data_file(self):
        """Tests run_script w/ data file"""
        debug.trace(4, f"TestIt.test_data_file(); self={self}")
        
        system.write_file(self.temp_file, "Hi, Paul")
        output = self.run_script(options="", env_options="FROM=es TO=en",
                                 data_file=self.temp_file)
        self.do_assert("hola" in output.lower())
        self.do_assert("pablo" in output.lower())
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
