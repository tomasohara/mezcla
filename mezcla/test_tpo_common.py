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

# Local packages
from mezcla import tpo_common as tpo

FUBAR = 101	# sample global for test_format
FOOBAR = 12     # likewise
JOSE = "José"   # UTF-8 encoded string

class TestIt(unittest.TestCase):
    """Class for testcase definition"""

    def test_format(self):
        """Ensure format resolves from local and global namespace, and that local takes precedence"""
        fubar = 202
        self.assertEqual(tpo.format("{F} vs. {f}", F=FUBAR, f=fubar), 
                         ("%s vs. %s" % (FUBAR, fubar)))
        # pylint: disable=redefined-outer-name
        FOOBAR = 21
        self.assertEqual(tpo.format("{FOO}", FOO=FOOBAR), 
                         str(FOOBAR))
        # TODO: self.assertEqual("Hey Jos\xc3\xa9", tpo.format("Hey {j}", j=JOSE))
        return

    def test_get_current_function_name(self):
        """Test(s) for get_current_function_name()"""
        self.assertEqual(tpo.get_current_function_name(), "test_get_current_function_name")
        return

    def test_getenv_functions(self):
        """Ensure that various getenv_xyz functions work as expected"""
        self.assertEqual(tpo.getenv_integer("REALLY FUBAR", 123), 123)
        self.assertEqual(tpo.getenv_number("REALLY FUBAR", 123), 123.0)
        self.assertFalse(isinstance(tpo.getenv_boolean("REALLY FUBAR?", None), 
                                    bool))
        self.assertTrue(isinstance(tpo.getenv_boolean("REALLY FUBAR?", False), 
                                   bool))
        self.assertFalse(isinstance(tpo.getenv_text("REALLY FUBAR?", False), 
                                    bool))
        os.environ["FUBAR"] = "1"
        self.assertEqual(tpo.getenv_text("FUBAR"), "1")
        return

    def test_unicode_functions(self):
        """Esnure that normalize_unicode, encode_unicode, etc. work as expected"""
        UTF8_BOM = "\xEF\xBB\xBF"
        self.assertEqual(tpo.ensure_unicode("ASCII"), u"ASCII")
        self.assertEqual(tpo.normalize_unicode("ASCII"), "ASCII")
        ## TODO: self.assertEqual(tpo.ensure_unicode(UTF8_BOM), u'\ufeff')
        self.assertEqual(tpo.normalize_unicode(UTF8_BOM), UTF8_BOM)
        self.assertEqual(u"Jos\xe9", tpo.ensure_unicode(JOSE))
        ## TODO: self.assertEqual("Jos\xc3\xa9", tpo.normalize_unicode(JOSE))
        return
        
    def test_difference(self):
        """Ensures set difference works as expected"""
        self.assertEqual(tpo.difference([1, 2, 3], [2]), 
                         [1, 3])
        self.assertEqual(tpo.difference([1, 1, 2, 2], [1]), 
                         [2])
        return

if __name__ == '__main__':
    unittest.main()
