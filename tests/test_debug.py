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
import unittest

# Installed packages
import pytest

# Local packages
import tomas_misc.debug as debug

class TestDebug(unittest.TestCase):
    """Class for test case definitions"""
    stdout_text = None
    stderr_text = None
    expected_stdout_trace = None
    expected_stderr_trace = None

    def setup_simple_trace(self):
        """Common setup for simple tracing"""
        self.stdout_text = "hello"
        self.stderr_text = "world"
        self.expected_stdout_trace = self.stdout_text + "\n"
        self.expected_stderr_trace = self.stderr_text + "\n"

    @pytest.fixture(autouse=True)
    def test_visible_simple_trace(self, capsys):
        """Make sure level-1 trace outputs to stderr"""
        self.setup_simple_trace()
        self.expected_stderr_trace = self.stderr_text + "\n"
        if not __debug__:
            self.expected_stderr_trace = ""
        debug.set_level(4)
        print(self.stdout_text)
        debug.trace(3, self.stderr_text)
        captured = capsys.readouterr()
        assert(captured.out == self.expected_stdout_trace)
        assert(captured.err == self.expected_stderr_trace)

    @pytest.fixture(autouse=True)
    def test_hidden_simple_trace(self, capsys):
        """Make sure level-N+1 trace doesn't output to stderr"""
        self.setup_simple_trace()
        self.expected_stderr_trace = self.stderr_text + "\n"
        debug.set_level(0)
        print(self.stdout_text)
        debug.trace(1, self.stderr_text)
        captured = capsys.readouterr()
        assert(captured.out == self.expected_stdout_trace)
        assert(captured.err == self.expected_stderr_trace)
