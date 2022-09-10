#! /usr/bin/env python
#
# Simple tests for debug.py, based on following:
#     https://stackoverflow.com/questions/16039463/how-to-access-the-py-test-capsys-from-inside-a-test
#
# Notes:
# - This can be run as follows:
#   $ PYTHONPATH="." python tests/test_debug.py
# - For tests that capture standard error, see
#       https://docs.pytest.org/en/6.2.x/capture.html
# - This uses capsys fixture mentioned in above link.
#................................................................................
# TODO:
# - make sure trace_fmt traps all exceptiona
#   debug.trace_fmt(1, "fu={fu}", fuu=1)
#                           ^^    ^^^
#

"""Tests for debug module"""

# Standard packages
## OLD: import unittest

# Installed packages
import pytest

# Local packages
from mezcla import debug

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
import mezcla.debug as THE_MODULE

class TestDebug:
    """Class for test case definitions"""
    stdout_text = None
    stderr_text = None
    expected_stdout_trace = None
    expected_stderr_trace = None

    def setup_simple_trace(self):
        """Common setup for simple tracing"""
        debug.trace(4, f"setup_common(): self={self}")
        self.stdout_text = "hello"
        self.stderr_text = "world"
        self.expected_stdout_trace = self.stdout_text + "\n"
        self.expected_stderr_trace = self.stderr_text + "\n"

    def test_set_level(self):
        """Ensure set_level works as expected"""
        debug.trace(4, f"test_set_level(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_get_level(self):
        """Ensure get_level works as expected"""
        debug.trace(4, f"test_get_level(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_get_output_timestamps(self):
        """Ensure get_output_timestamps works as expected"""
        debug.trace(4, f"test_get_output_timestamps(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_set_output_timestamps(self):
        """Ensure set_output_timestamps works as expected"""
        debug.trace(4, f"test_set_output_timestamps(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_trace(self):
        """Ensure trace works as expected"""
        debug.trace(4, f"test_trace(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_trace_fmtd(self):
        """Ensure trace_fmtd works as expected"""
        debug.trace(4, f"test_trace_fmtd(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_trace_object(self):
        """Ensure trace_object works as expected"""
        debug.trace(4, f"test_trace_object(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_trace_values(self):
        """Ensure trace_values works as expected"""
        debug.trace(4, f"test_trace_values(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_trace_expr(self):
        """Ensure trace_expr works as expected"""
        debug.trace(4, f"test_trace_expr(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_trace_current_context(self):
        """Ensure trace_current_context works as expected"""
        debug.trace(4, f"test_trace_current_context(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_trace_exception(self):
        """Ensure trace_exception works as expected"""
        debug.trace(4, f"test_trace_exception(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_raise_exception(self):
        """Ensure raise_exception works as expected"""
        debug.trace(4, f"test_raise_exception(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_assertion(self):
        """Ensure assertion works as expected"""
        debug.trace(4, f"test_assertion(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_val(self):
        """Ensure val works as expected"""
        debug.trace(4, f"test_val(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_code(self):
        """Ensure code works as expected"""
        debug.trace(4, f"test_code(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_debug_print(self):
        """Ensure debug_print works as expected"""
        debug.trace(4, f"test_debug_print(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_timestamp(self):
        """Ensure timestamp works as expected"""
        debug.trace(4, f"test_timestamp(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_debugging(self):
        """Ensure debugging works as expected"""
        debug.trace(4, f"test_debugging(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_detailed_debugging(self):
        """Ensure detailed_debugging works as expected"""
        debug.trace(4, f"test_detailed_debugging(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_verbose_debugging(self):
        """Ensure verbose_debugging works as expected"""
        debug.trace(4, f"test_verbose_debugging(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_format_value(self):
        """Ensure format_value works as expected"""
        debug.trace(4, f"test_format_value(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_xor(self):
        """Ensure xor works as expected"""
        debug.trace(4, f"test_xor(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_xor3(self):
        """Ensure xor3 works as expected"""
        debug.trace(4, f"test_xor3(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_init_logging(self):
        """Ensure init_logging works as expected"""
        debug.trace(4, f"test_init_logging(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_profile_function(self):
        """Ensure profile_function works as expected"""
        debug.trace(4, f"test_profile_function(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_reference_var(self):
        """Ensure reference_var works as expected"""
        debug.trace(4, f"test_reference_var(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_clip_value(self):
        """Ensure clip_value works as expected"""
        debug.trace(4, f"test_clip_value(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_read_line(self):
        """Ensure read_line works as expected"""
        debug.trace(4, f"test_read_line(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_debug_init(self):
        """Ensure debug_init works as expected"""
        debug.trace(4, f"test_debug_init(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_display_ending_time_etc(self):
        """Ensure display_ending_time_etc works as expected"""
        debug.trace(4, f"test_display_ending_time_etc(): self={self}")
        ## TODO: WORK-IN-PROGRESS

    def test_visible_simple_trace(self, capsys):
        """Make sure level-1 trace outputs to stderr"""
        debug.trace(4, f"test_visible_simple_trace({capsys})")
        self.setup_simple_trace()
        if not __debug__:
            self.expected_stderr_trace = ""
        pre_captured = capsys.readouterr()
        save_trace_level = THE_MODULE.get_level()
        THE_MODULE.set_level(4)
        print(self.stdout_text)
        THE_MODULE.trace(3, self.stderr_text)
        THE_MODULE.set_level(save_trace_level)
        captured = capsys.readouterr()
        assert(captured.out == self.expected_stdout_trace)
        assert(captured.err == self.expected_stderr_trace)
        THE_MODULE.trace_expr(6, pre_captured, captured)

    def test_hidden_simple_trace(self, capsys):
        """Make sure level-N+1 trace doesn't output to stderr"""
        debug.trace(4, f"test_hidden_simple_trace({capsys})")
        self.setup_simple_trace()
        ## TEST
        ## capsys.stop_capturing()
        ## capsys.start_capturing()
        pre_captured = capsys.readouterr()
        self.expected_stderr_trace = ""
        save_trace_level = THE_MODULE.get_level()
        THE_MODULE.set_level(0)
        print(self.stdout_text)
        THE_MODULE.trace(1, self.stderr_text)
        captured = capsys.readouterr()
        THE_MODULE.set_level(save_trace_level)
        assert captured.out == self.expected_stdout_trace
        assert captured.err == self.expected_stderr_trace
        THE_MODULE.trace_expr(6, pre_captured, captured)

    def test_debug_val(self):
        """Make sure debug.val only returns value when at specified level"""
        debug.trace(4, f"test_debug_val(): self={self}")
        save_trace_level = THE_MODULE.get_level()
        test_value = 22
        THE_MODULE.set_level(5)
        level5_value = THE_MODULE.val(5, test_value)
        THE_MODULE.set_level(0)
        level0_value = THE_MODULE.val(1, test_value)
        THE_MODULE.set_level(save_trace_level)
        assert level5_value == test_value
        assert level0_value is None

    def test_debug_code(self):
        """Make sure debug code not executed at all"""
        debug.trace(4, f"test_debug_value(): self={self}")
        ## TODO: debug.assertion(debug_level, debug.code(debug_level, lambda: (8 / 0 != 0.0)))
        save_trace_level = THE_MODULE.get_level()
        count = 0
        def increment():
            """Increase counter"""
            nonlocal count
            count += 1
        THE_MODULE.set_level(4)
        THE_MODULE.code(4, lambda: increment)
        THE_MODULE.set_level(save_trace_level)
        assert(count == 0)


#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
