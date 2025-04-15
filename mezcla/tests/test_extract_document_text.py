#! /usr/bin/env python3
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
## OLD: import re

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper, invoke_tests


# Note: Two references are used for the module to be tested:
#    THE_MODULE:                        global module object
#    TestIt.script_module:              path to file
import mezcla.extract_document_text as THE_MODULE

class TestExtractDocumentText(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_document_to_text(self):
        """Ensure document_to_text() works as expected"""
        debug.trace(4, "test_document_to_text()")
        # NOTE: Output contains \n specifier at the end on the text.
        # - Uses test-specific temp file as per TestWrapper.
        # - Uses file extension for use by underlying textract module (see document_to_text).
        ## OLD: tmp_document = self.get_temp_file()
        tmp_document = self.temp_file + ".txt"

        # DOCUMENT_TEXT = """Lorem Ipsum is simply dummy text of the printing and typesetting industry.
        # Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book.
        # It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged.
        # It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum."""
        
        # Single-line string as INPUT
        DOCUMENT_TEXT = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse porttitor rutrum leo. Nam efficitur justo quis mi ullamcorper consectetur. Aenean posuere nisl dignissim mauris blandit, sed euismod lacus posuere. Morbi ultrices magna eget faucibus ultricies. Praesent in ante nisi. Nulla faucibus sollicitudin sapien in aliquet. Interdum et malesuada fames ac ante ipsum primis in faucibus."
        
        system.write_file(tmp_document, text=DOCUMENT_TEXT)
        output = THE_MODULE.document_to_text(tmp_document)
        ## OLD:
        ## output_case1 = output != DOCUMENT_TEXT
        ## output_case2 = DOCUMENT_TEXT in output
        ## output_case3 = output.endswith("\n")
        ## output_case4 = output.strip() == DOCUMENT_TEXT
        ## assert output_case1 and output_case2 and output_case3 and output_case4
        assert output != DOCUMENT_TEXT
        assert DOCUMENT_TEXT in output
        assert output.endswith("\n")
        assert output.strip() == DOCUMENT_TEXT
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_document_to_text_IO(self):
        """Ensure document_to_text_IO() works as expected"""
        # TODO: Adding tests to check if extract_document_text.py works properly
        debug.trace(4, "test_document_to_text_IO()")
        ## OLD: env_option = "STDOUT"
        # NOTE: Output contains \n specifier at the end on the text.
        ## OLD:
        ## doc_input_temp = self.get_temp_file()
        ## doc_output_temp = self.get_temp_file()
        ## TODO2: carefully review tests/template.py
        doc_input_temp = self.temp_file + ".txt"
        # Single-line string as INPUT
        DOCUMENT_TEXT = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse porttitor rutrum leo. Nam efficitur justo quis mi ullamcorper consectetur. Aenean posuere nisl dignissim mauris blandit, sed euismod lacus posuere. Morbi ultrices magna eget faucibus ultricies. Praesent in ante nisi. Nulla faucibus sollicitudin sapien in aliquet. Interdum et malesuada fames ac ante ipsum primis in faucibus."
        system.write_file(filename=doc_input_temp, text=DOCUMENT_TEXT)
        ## BAD:
        ## test_command_1 = f"../extract_document_text.py {doc_input_temp} {doc_output_temp}"
        ## gh.run(test_command_1)
        ## output = gh.read_file(doc_output_temp)
        output = self.run_script(env_options="STDOUT=1", data_file=doc_input_temp)
        
        ## BAD: assert output == DOCUMENT_TEXT
        assert output.strip() == DOCUMENT_TEXT
        return 
        
    def test_document_to_text_html(self):
        """Ensure document_to_text_html() works as expected"""
        debug.trace(4, "test_document_to_text_html()")
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
    invoke_tests(__file__)
