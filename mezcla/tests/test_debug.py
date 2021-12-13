#! /usr/bin/env python
#
# Simple tests for debug.py, based on following:
#     https://stackoverflow.com/questions/16039463/how-to-access-the-py-test-capsys-from-inside-a-test
#
# Notes:
# - For tests capture standard error, see
#       https://docs.pytest.org/en/6.2.x/capture.html
# - This uses capsys fixture mentioned in above link.
#

"""Tests for debug module"""

# Standard packages
## OLD: import unittest

# Installed packages
import pytest

# Local packages
import mezcla.debug as debug
## OLD: import mezcla.system as system
## OLD: from mezcla.unittest_wrapper import TestWrapper


class TestDebug:
## OLD: class TestDebug(TestWrapper):
    """Class for test case definitions"""
    ## OLD: script_module = TestWrapper.derive_tested_module_name(__file__)
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

    ## OLD: @pytest.fixture(autouse=True)
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

    ## OLD: @pytest.fixture(autouse=True)
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

    def test_debug_code(self, capsys):
        """Make sure debug code not executed at all"""
        ## TODO: debug.assertion(debug_level, debug.code(debug_level, lambda: (8 / 0 != 0.0)))
        assert(False)
        
#------------------------------------------------------------------------

if __name__ == '__main__':
    pytest.main([__file__])
