#! /usr/bin/env python
#
# Simple tests for debug.py, based on following:
#     https://stackoverflow.com/questions/16039463/how-to-access-the-py-test-capsys-from-inside-a-test
#
# Notes:
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

    def test_visible_simple_trace(self, capsys):
        """Make sure level-1 trace outputs to stderr"""
        debug.trace(4, f"test_visible_simple_trace({capsys})")
        self.setup_simple_trace()
        if not __debug__:
            self.expected_stderr_trace = ""
        pre_captured = capsys.readouterr()
        save_trace_level = debug.get_level()
        debug.set_level(4)
        print(self.stdout_text)
        debug.trace(3, self.stderr_text)
        debug.set_level(save_trace_level)
        captured = capsys.readouterr()
        assert(captured.out == self.expected_stdout_trace)
        assert(captured.err == self.expected_stderr_trace)
        debug.trace_expr(6, pre_captured, captured)

    def test_hidden_simple_trace(self, capsys):
        """Make sure level-N+1 trace doesn't output to stderr"""
        debug.trace(4, f"test_hidden_simple_trace({capsys})")
        self.setup_simple_trace()
        ## TEST
        ## capsys.stop_capturing()
        ## capsys.start_capturing()
        pre_captured = capsys.readouterr()
        self.expected_stderr_trace = ""
        save_trace_level = debug.get_level()
        debug.set_level(0)
        print(self.stdout_text)
        debug.trace(1, self.stderr_text)
        captured = capsys.readouterr()
        debug.set_level(save_trace_level)
        assert(captured.out == self.expected_stdout_trace)
        assert(captured.err == self.expected_stderr_trace)
        debug.trace_expr(6, pre_captured, captured)

    def test_debug_val(self):
        """Make sure debug.val only returns value when at specified level"""
        debug.trace(4, f"test_debug_val(): self={self}")
        save_trace_level = debug.get_level()
        test_value = 22
        debug.set_level(5)
        level5_value = debug.val(5, test_value)
        debug.set_level(0)
        level0_value = debug.val(1, test_value)
        debug.set_level(save_trace_level)
        assert(level5_value == test_value)
        assert(level0_value is None)
        
    def test_debug_code(self):
        """Make sure debug code not executed at all"""
        debug.trace(4, f"test_debug_value(): self={self}")
        ## TODO: debug.assertion(debug_level, debug.code(debug_level, lambda: (8 / 0 != 0.0)))
        save_trace_level = debug.get_level()
        count = 0
        def increment():
            """Increase counter"""
            nonlocal count
            count += 1
        debug.set_level(4)
        debug.code(4, lambda: increment)
        debug.set_level(save_trace_level)
        assert(count == 0)
        
#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
