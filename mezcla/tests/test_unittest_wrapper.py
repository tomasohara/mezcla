#! /usr/bin/env python
#
# Test(s) for ../unittest_wrapper.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_unittest_wrapper.py
#

"""Tests for unittest_wrapper module"""

# Installed packages
import pytest

# Local packages
## TODO (effing pytest): from mezcla.unittest_wrapper import TestWrapper, trap_exception, pytest_fixture_wrapper
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla import debug
from mezcla.my_regex import my_re
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                  global module object
#    TestTemplate.script_module:  path to file
import mezcla.unittest_wrapper as THE_MODULE


## TODO (use TestWrapper directly):

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    def test_01_usage(self):
        """Make sure usage warns that not intended for command line and that no stdout"""
        debug.trace(4, f"TestIt.test_01_usage(); self={self}")
        log_file = self.temp_file + ".log"
        ## BAD: output = self.run_script(log_file=log_file)
        output = self.run_script(env_options="DEBUG_LEVEL=4", log_file=log_file)
        self.do_assert(not output.strip())
        log_contents = system.read_file(log_file)
        debug.trace_expr(5, log_contents)
        self.do_assert(my_re.search(r"Warning: not intended.*command-line", log_contents))
        return

    ## OLD:
    ## class TestIt2:
    ## """Class for API usage"""

    @pytest.mark.skipif(not __debug__, reason="Must be under __debug__")
    ## TODO:
    ## @pytest_fixture_wrapper
    ## @trap_exception
    ## OLD: def test_02_do_assert(self, capsys):
    def test_02_do_assert(self):
        """Ensure do_assert identifies failing line"""
        ## OLD: debug.trace(4, f"TestIt.test_02_do_assert({capsys}); self={self}")
        debug.trace(4, f"TestIt.test_02_do_assert(); self={self}")

        # Get instance for test class
        # TODO3: use TestWrapper() instead of SubTestIt()
        class SubTestIt(TestWrapper):
            """Embedded test suite"""
            pass
        #
        sti = SubTestIt()

        # Make assertion, ensuring debugging level set at minimum required (2)
        captured_trace = ""
        message = "Good math"
        # TODO3: use pytest patch support (monkey?)
        old_debug_level = debug.get_level()
        _old_captured_trace = self.get_stderr()   # resets capsys capture
        try:
            debug.set_level(debug.TL.DEFAULT)
            sti.do_assert(2 + 2 == 5, message)    # Orwell's condition
        except AssertionError:
            pass
        finally:
            debug.set_level(old_debug_level)
        ## OLD: captured_trace = capsys.readouterr().err
        captured_trace = self.get_stderr()
        debug.trace_expr(4, captured_trace, max_len=2048)
        
        #  The condition and message should be displayed
        assert("2 + 2 == 5" in captured_trace)
        assert(message in captured_trace)
        
        # Make sure stuff properly stripped (i.e., message arg and comment)
        assert(not "message" in captured_trace)
        assert(not "Orwell" in captured_trace)
        assert(not "sti.do_assert" in captured_trace)
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests([__file__])
