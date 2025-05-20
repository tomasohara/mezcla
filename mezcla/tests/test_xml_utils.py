#! /usr/bin/env python3
#
# Test(s) for ../xml_utils.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_xml_utils.py
#
#-------------------------------------------------------------------------------
# Sample input and output:
#
# Input:
#     <?xml version="1.1"?> <xml><a><b>1<c>2<d/>3</c></b>4</a></xml>
#
# XML parse tree
#      xml:
#              a:
#                      b: 1
#                              c: 2
#                                      d:
#                                      3
#                      4
#

"""Tests for xml_utils module"""

# Standard packages
import re

# Installed packages
import pytest

# Local packages
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
import mezcla.xml_utils as THE_MODULE

# Constants
NESTED_XML = """<?xml version="1.1"?>
<xml><a><b>1<c>2<d/>3</c></b>4</a></xml>
"""

class TestXmlUtils(TestWrapper):
    """Class for testcase definition"""
    script_file = TestWrapper.get_module_file_path(__file__)
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)


    @pytest.mark.xfail                   # TODO: remove xfail
    def test_data_file(self):
        """Makes sure simple XML data file parsed OK"""
        debug.trace(4, "TestXmlUtils.test_data_file()")
        data = "<xml><a>A</a><b>B</b></xml>"
        system.write_file(self.temp_file, data)
        output = self.run_script("", self.temp_file)
        assert "a: A" in output
        assert "b: B" in output
        return

    def test_get_xml_text(self):
        """Ensure get_xml_text works as expected"""
        debug.trace(4, "test_get_xml_text()")
        # Example from https://docs.python.org/3/library/xml.etree.elementtree.html.
        parsed_xml_text = THE_MODULE.get_xml_text(THE_MODULE.parse_xml(NESTED_XML))
        assert parsed_xml_text == "xml: \n\ta: \n\t\tb: 1\n\t\t\tc: 2\n\t\t\t\td: \n\t\t\t\t3\n\t\t4"
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
