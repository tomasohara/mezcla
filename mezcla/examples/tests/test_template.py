#! /usr/bin/env python3
#
# Test(s) for ../template.py
#
# Notes:
# - Fill out TODO's below. Use numbered tests to order (e.g., test_1_usage).
# - * See test_python_ast.py for simple example of customization.
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by unittest_wrapper.py.
# - This can be run as follows (e.g., from root of repo):
#   $ pytest ./mezcla/examples/tests/test_template.py
#
# Warning:
# - The use of run_script as in test_01_data_file is an older style of testing.
#   It is better to directly invoke a helper class in the script that is independent
#   of the Script class based on Main. (See an example of this, see python_ast.py
#   and tests/tests_python_ast.py.)
#

## TODO1: [Warning] Make sure this template adhered to as much as possible. For,
## example, only delete todo comments not regular code, unless suggested in tip).
## In particular, it is critical that script_module gets initialized properly.

"""Tests for template module"""

# Installed modules
import pytest

# Local modules
from mezcla.unittest_wrapper import TestWrapper
from mezcla import debug
from mezcla.my_regex import my_re
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                        global module object
#    TestIt.script_module:              path to file
import mezcla.examples.template as THE_MODULE   ## TODO: uncomment this line (<<<)
#
# Note: sanity test for customization (TODO: remove if desired)
if not my_re.search(__file__, r"\btemplate.py$"):
    debug.assertion("mezcla.template" not in str(THE_MODULE))

#------------------------------------------------------------------------

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_01_data_file(self):
        """Tests run_script w/ data file"""
        # Warning: see notes above about potential issues with run_script-based tests.
        debug.trace(4, f"TestIt.test_01_data_file(); self={self}")
        data = ["what", "ever"]
        system.write_lines(self.temp_file, data)
        output = self.run_script(options="", data_file=self.temp_file)
        self.do_assert(my_re.search(r"Error.*Implement.me", output.strip()))
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_02_helper(self):
        """Test for helper class"""
        debug.trace(4, f"TestIt.test_02_helper(); self={self}")
        helper = THE_MODULE.Helper()
        self.do_assert(not helper.process("some text"))
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    ## TODO2: here and elsewhere: invoke_tests(__file__)
    pytest.main([__file__])
