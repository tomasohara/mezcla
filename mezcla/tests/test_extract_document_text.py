#! /usr/bin/env python
#
# Test(s) for ../extract_document_text.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_extract_document_text.py
#

"""Tests for extract_document_text module"""

# Standard packages
## NOTE: this is empty for now

# Installed packages
import pytest

# Local packages
from mezcla.unittest_wrapper import TestWrapper
from mezcla import debug
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
import mezcla.extract_document_text as THE_MODULE

class TestExtractDocumentText(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    
    @pytest.mark.xfail
    def test_document_to_text(self):
        """Ensure document_to_text() works as expected"""
        debug.trace(4, "test_document_to_text()")
        data = [
            "<HTML lang='en'>",
            "  <BODY>",
            "    <H3>Hey</H3>"
            "  </BODY>",
            "</HTML>",
            ]
        temp_file = self.temp_file + ".html"
        system.write_lines(temp_file, data)
        output = self.run_script(options="", env_options="STDOUT=1", data_file=temp_file)
        self.do_assert("Hey" == output.strip())
        return

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
