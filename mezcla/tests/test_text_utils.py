#! /usr/bin/env python
#
# Test(s) for ../text_utils.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH="$(realpath .)/..):$PYTHONPATH" python tests/test_text_utils.py
#

"""Tests for text_utils module"""

# Standard packages
import re
import unittest

# Installed packages
## TODO: import pytest

# Local packages
from mezcla.unittest_wrapper import TestWrapper
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
#    TestIt.script_module   string name
import mezcla.text_utils as THE_MODULE

HTML_FILENAME = "simple-window-dimensions.html"

EXPECTED_TEXT = """
   Simple window dimensions

   Simple window dimensions

      Legend:
        Screen dimensions:    ???
        Browser dimensions:   ???

   JavaScript is required
"""
#
# NOTE: Whitespace and punctuation gets normalized
# TODO: restore bullet points (e.g., "* Screen dimensions")

MS_WORD_FILENAME = "spanish-accents.docx"

MS_WORD_TEXT = "Tío Tomás\t\t\t\tUncle Tom\n\n¡Buenos días!\t\t\t\tGood morning\n\nçãêâôöèäàÃëÇÂîòïÔìðÊÅåùÀŠý\t\tcaeaooeaaAeCAioiOioEAauASy"


def normalize_test_text(text):
    """Trim excess whitespace and convert punctuation to <PUNCT>"""
    # EX: normalize_test_text("   h  e y?! ") => "h e y<PUNCT>"
    result = text.strip()
    result = re.sub(r"\s+", " ", result)
    result = re.sub(r"[^\w\s]+", "<PUNCT>", result)
    debug.trace(4, f"normalize_test_text({text}) => {result}")
    return result
    

class TestIt(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__)

    def test_html_to_text(self):
        """Ensure html_to_text works as expected"""
        # TODO: move into test_html_utils.py
        debug.trace(4, "test_html_to_text()")
        html_path = gh.resolve_path(HTML_FILENAME)
        html = system.read_file(html_path)
        text = THE_MODULE.html_to_text(html)
        self.assertEqual(normalize_test_text(text),
                         normalize_test_text(EXPECTED_TEXT))
        return

    def test_document_to_text(self):
        """Ensure document_to_text works as expected"""
        debug.trace(4, "test_document_to_text()")
        doc_path = gh.resolve_path(MS_WORD_FILENAME)
        text = THE_MODULE.document_to_text(doc_path)
        self.assertEqual(normalize_test_text(text),
                         normalize_test_text(MS_WORD_TEXT))
        ## OLD: self.assertEqual(1, 2)
    
#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    unittest.main()
