#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Test(s) for tpo_common.py
#
# Notes:
# - This can be run as follows:
#   $ PYTHONPATH="." python tests/test_tpo_common.py
# TODO:
# - Address commonly used debugging functions (e.g., debug_print) by redirecting output (via remapping sys.stderr to a file) and then checking file contents.
# - add tests for normalize_unicode, ensure_unicode and other problematic functions
#

"""Tests for tpo_common module"""

# Standard packages
import os
import unittest

# Installed packages
import pytest

# Local packages
from mezcla import debug

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
#    TestIt.script_module   string name
import mezcla.tpo_common as THE_MODULE

FUBAR = 101	# sample global for test_format
FOOBAR = 12     # likewise
JOSE = "José"   # UTF-8 encoded string

class TestIt(unittest.TestCase):
    """Class for testcase definition"""

    def test_format(self):
        """Ensure format resolves from local and global namespace, and that local takes precedence"""
        fubar = 202
        assert THE_MODULE.format("{F} vs. {f}", F=FUBAR, f=fubar) == ("%s vs. %s" % (FUBAR, fubar))
        # pylint: disable=redefined-outer-name
        FOOBAR = 21
        assert THE_MODULE.format("{FOO}", FOO=FOOBAR) == str(FOOBAR)
        # TODO: assert "Hey Jos\xc3\xa9" == THE_MODULE.format("Hey {j}", j=JOSE)
        return

    def test_get_current_function_name(self):
        """Test(s) for get_current_function_name()"""
        assert THE_MODULE.get_current_function_name() == "test_get_current_function_name"
        return

    def test_getenv_functions(self):
        """Ensure that various getenv_xyz functions work as expected"""
        assert THE_MODULE.getenv_integer("REALLY FUBAR", 123) == 123
        assert THE_MODULE.getenv_number("REALLY FUBAR", 123) == 123.0
        assert not isinstance(THE_MODULE.getenv_boolean("REALLY FUBAR?", None), bool)
        assert isinstance(THE_MODULE.getenv_boolean("REALLY FUBAR?", False), bool)
        assert not isinstance(THE_MODULE.getenv_text("REALLY FUBAR?", False), bool)
        os.environ["FUBAR"] = "1"
        assert THE_MODULE.getenv_text("FUBAR") == "1"
        return

    def test_unicode_functions(self):
        """Esnure that normalize_unicode, encode_unicode, etc. work as expected"""
        UTF8_BOM = "\xEF\xBB\xBF"
        assert THE_MODULE.ensure_unicode("ASCII") == u"ASCII"
        assert THE_MODULE.normalize_unicode("ASCII") == "ASCII"
        ## TODO: assert THE_MODULE.ensure_unicode(UTF8_BOM) == u'\ufeff'
        assert THE_MODULE.normalize_unicode(UTF8_BOM) == UTF8_BOM
        assert u"Jos\xe9" == THE_MODULE.ensure_unicode(JOSE)
        ## TODO: assert "Jos\xc3\xa9", THE_MODULE.normalize_unicode(JOSE)
        return

    def test_difference(self):
        """Ensures set difference works as expected"""
        assert THE_MODULE.difference([1, 2, 3], [2]) == [1, 3]
        assert THE_MODULE.difference([1, 1, 2, 2], [1]) == [2]
        return

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
