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
#   $ pytest ./mezclatests/test_template.py
# - TODO: Remove TODO notes when stable.
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


"""TODO: Tests for template module"""

# Standard modules
from typing import Optional

# Installed modules
import pytest

# Local modules
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla import debug
## TODO: from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:               module object (e.g., <module 'mezcla.main' ...>)
#    TestIt.script_module:     dotted module path (e.g., "mezcla.main")
THE_MODULE = None
try:
    ## TODO: import mezcla.<module> as THE_MODULE
    pass                                ## TODO: delete
except:
    system.print_exception_info("<module> import") 
#
# Note: sanity test for customization (TODO: remove if desired)
if not my_re.search(__file__, r"\btemplate.py$"):
    debug.assertion("mezcla.template" not in str(THE_MODULE))



class TestTemplate(TestWrapper):
    """Class for testcase definition"""
    script_file = TestWrapper.get_module_file_path(__file__)
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_01_data_file(self):
        """Makes sure to-do grep works as expected"""
        debug.trace(4, "TestTemplate.test_01_data_file()")
        data = ["TEMP", "TODO", "DONE"]
        system.write_lines(self.temp_file, data)
        output = self.run_script(options="--TODO-arg", env_options="TODO_ENV=VAL",
                                 data_file=self.temp_file)
        self.do_assert(my_re.search(r"Error.*Implement.me", output.strip()))
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_02_helper(self):
        """Test for helper class"""
        debug.trace(4, f"TestIt.test_02_helper(); self={self}")
        TODO_var: Optional[bool] = None
        helper = THE_MODULE.Helper(TODO_var)
        self.do_assert(not helper.process("TODO: some arg"))
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_03_captured_stdout(self):
        """Ensure that stdout and/or stderr captured properly"""
        debug.trace(4, "test_03_captured_IO()")
        helper = THE_MODULE.Helper()
        self.do_assert(not helper.process("TODO: some arg"))
        stdout = self.get_stdout()
        self.do_assert(my_re.search(r"Error.*Implement.me", stdout.strip()))
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_04_captured_stderr(self):
        """Ensure that stderr captured properly"""
        debug.trace(4, "test_04_captured_stderr()")
        self.patch_trace_level(5)
        THE_MODULE.Helper()
        stderr = self.get_stderr()
        self.do_assert(my_re.search(r"Helper.*instance", stderr.strip()))
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
