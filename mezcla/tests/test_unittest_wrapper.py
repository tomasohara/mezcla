#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Test(s) for ../unittest_wrapper.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_unittest_wrapper.py
#
# Warning:
# - It can be tricky to debug the do_assert and do_assert_equals tests.
# - Temporarily disabling the use of TL.DEFAULT below can help, so that the detailed
#   debugging traces are shown.
# - You might also need to temporarily enable the print-based tracing in resolve_assertion.
#

"""Tests for unittest_wrapper module"""

# Installed packages
import pytest

# Local packages
import os
import unittest
from unittest import mock

## TEST: os.environ["PRESERVE_TEMP_FILE"] = "1"
from mezcla.unittest_wrapper import TestWrapper, invoke_tests, trap_exception
from mezcla import debug
from mezcla.my_regex import my_re
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                  global module object
#    TestTemplate.script_module:  path to file
import mezcla.unittest_wrapper as THE_MODULE


## TODO (use TestWrapper directly):

# Globals
last_self = None                        # Reserved for test_05_check_temp_part1/2

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    last_temp_file = None               # Reserved for test_05_check_temp_part1/2

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

    @pytest.mark.skipif(not __debug__, reason="Must be under __debug__")
    @trap_exception
    def test_02_do_assert(self):
        """Ensure do_assert identifies failing line"""
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
            # Note: see warning with tips on debugging in header comments
            debug.set_level(debug.TL.DEFAULT)
            sti.do_assert(2 + 2 == 5, message)    # Orwell's condition
        except AssertionError:
            pass
        finally:
            debug.set_level(old_debug_level)
        captured_trace = self.get_stderr()
        debug.trace_expr(4, captured_trace, max_len=2048)
        
        #  The condition and message should be displayed
        # example: Test assertion failed: 2 + 2 == 5 (at .../mezcla/tests/test_unittest_wrapper.py:77): Good math
        assert("2 + 2 == 5" in captured_trace)
        assert(message in captured_trace)
        
        # Make sure stuff properly stripped (i.e., message arg and comment)
        assert(not "message" in captured_trace)
        assert(not "Orwell" in captured_trace)
        assert(not "sti.do_assert" in captured_trace)
        return

    @pytest.mark.skipif(not __debug__, reason="Must be under __debug__")
    @trap_exception
    def test_03_do_assert_equals(self):
        """Ensure do_assert_equals shows diff"""
        debug.trace(4, f"TestIt.test_03_do_assert_equals(); self={self}")

        # Get instance for test class
        # TODO3: use TestWrapper() instead of SubTestIt()
        class SubTestIt(TestWrapper):
            """Embedded test suite"""
            pass
        #
        sti = SubTestIt()

        # Make assertion, ensuring debugging level set at minimum required (2)
        captured_trace = ""
        message = "dawg diff"
        # TODO3: use pytest patch support (monkey?)
        old_debug_level = debug.get_level()
        _old_captured_trace = self.get_stderr()   # resets capsys capture
        try:
            # Note: see warning with tips on debugging in header comments
            debug.set_level(debug.TL.DEFAULT)
            sti.do_assert_equals("dog's bark", "dawg's bark", message)
        except AssertionError:
            pass
        finally:
            debug.set_level(old_debug_level)
        captured_trace = self.get_stderr()
        debug.trace_expr(4, captured_trace, max_len=2048)
        
        # The condition and message should be displayed
        # example: Test equality assertion failed: "dog\'s bark", "dawg\'s bark" (at .../mezcla/tests/test_unittest_wrapper.py:118): dawg diff
        assert(my_re.search(r"dog.*dawg", captured_trace))
        assert(message in captured_trace)

        # The value diff should also be displayed
        # example: "diff:\n< dog\'s bark\n…  ^\n> dawg\'s bark\n…  ^^\n\n"
        assert(my_re.search(r" \^\n.* \^\^\n", captured_trace, flags=my_re.DOTALL))
        
        # Make sure stuff properly stripped (i.e., message arg and comment)
        assert(not "sti.do_assert_equals" in captured_trace)
        return

    # XPASS
    @pytest.mark.xfail
    def test_04_get_temp_dir(self):
        """Tests get_temp_dir"""
        debug.trace(4, f"TestIt.test_04_get_temp_dir(); self={self}")
        temp_dir_path = THE_MODULE.get_temp_dir()
        pattern = "/temp/tmp/tmp"
        assert pattern in temp_dir_path
        assert system.is_directory(temp_dir_path) == True

    @pytest.mark.xfail
    def test_05_check_temp_part1(self):
        """Make sure self.temp setup OK"""
        debug.trace(4, f"TestIt.test_05_check_temp_part1(); self={self!r}; id={id(self)}")
        debug.trace_expr(5, self.last_temp_file, self.temp_file)
        assert(self.last_temp_file is None)
        self.last_temp_file = self.temp_file
        global last_self                # TODO4 (use class member)
        debug.assertion(last_self is None)
        last_self = self

    @pytest.mark.xfail
    def test_06_check_temp_part2(self):
        """Make sure self.temp unique"""
        debug.trace(4, f"TestIt.test_06_check_temp_part2(); self={self!r}; id={id(self)}")
        debug.trace_expr(5, self.last_temp_file, self.temp_file)
        assert self.last_temp_file != self.temp_file
        assert(self.last_temp_file is not None)
        global last_self                # TODO4 (use class member)
        # NOTE: The following will fail: apparently each test is run using
        # a separate class instance.
        debug.assertion(last_self == self)

    # XPASS
    @pytest.mark.xfail
    def test_07_trap_exception(self):
        """Make sure trap_exception works as expected"""
        def sum(a, b):
            if a < 0 or b < 0:
                raise AssertionError("Negative numbers not allowed")
            return a + b
        wrapped_func = THE_MODULE.trap_exception(sum)
        output = wrapped_func(17, 10)
        assert output == 27

    # XPASS
    @pytest.mark.xfail
    def test_08_pytest_fixture_wrapper(self):
        """Make sure trap_exception works as expected"""
        
        # pytest_fixture_wrapper designed for unary function
        def square(a:int):
            if a < 0:
                raise AssertionError("Negative numbers not allowed as input")
            return a**2
        
        wrapped_func = THE_MODULE.pytest_fixture_wrapper(square)
        output = wrapped_func(25)
        assert output == 625

    # XPASS
    @pytest.mark.xfail
    @mock.patch('sys.stdout', new_callable=mock.MagicMock)
    @mock.patch('sys.stderr', new_callable=mock.MagicMock)
    def test_09_invoke_tests(self, mock_stderr, mock_stdout):
        """Make sure invoke_tests works as expected"""
        try:
            THE_MODULE.invoke_tests("test_template.py", via_unittest=True)
        except SystemExit:
            pass 
        
        # Extracting the output from the mock objects
        output_stdout = ''.join(call[0][0] for call in mock_stdout.write.call_args_list)
        output_stderr = ''.join(call[0][0] for call in mock_stderr.write.call_args_list)
        
        # Asserting that there's no error output, indicating a successful test run
        assert "usage: pytest" in output_stderr
        assert "\npytest: error: unrecognized arguments: -s\n" in output_stderr
        assert output_stdout == ""

    ## ATTEMPT II: test_09_invoke_tests
    # @pytest.mark.parametrize("via_unittest", [True, False])
    # def test_invoke_tests(via_unittest: bool):
    #     if via_unittest:
    #         import unittest
    #         suite = unittest.TestLoader().discover('test___init__.py', pattern='test_*.py')
    #         unittest.TextTestRunner(verbosity=2).run(suite)
    #     else:
    #         invoke_tests("test_template.py")
    
    # XPASS
    @pytest.mark.xfail
    def test_10_setUpClass(self):
        """Make sure setUpClass works as expected"""
        with mock.patch.dict(os.environ, {"CHECK_COVERAGE": "True", "TEMP_BASE": "/tmp/test_setUpClass"}):
            test_class = THE_MODULE.TestWrapper
            test_class.script_module = "mezcla.template"

            test_class.check_coverage = os.environ.get("CHECK_COVERAGE", "False").lower() in ['true', '1', 't', 'y', 'yes']
            
            test_class.setUpClass(filename="test_template.py")

            assert test_class.class_setup is True
            assert test_class.script_file.endswith("template.py")
            assert test_class.script_module == "mezcla.template"
            assert test_class.check_coverage is True




#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
