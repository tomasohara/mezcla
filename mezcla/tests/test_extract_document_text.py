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
import re

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper


# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
import mezcla.extract_document_text as THE_MODULE

class TestExtractDocumentText:
    """Class for testcase definition"""
    
    def test_document_to_text(self):
        """Ensure document_to_text() works as expected"""
        debug.trace(4, "test_document_to_text()")
        # NOTE: Output contains \n specifier at the end on the text.
        tmp_document = gh.get_temp_file()

        # DOCUMENT_TEXT = """Lorem Ipsum is simply dummy text of the printing and typesetting industry.
        # Lorem Ipsum has been the industry's standard dummy text ever since the 1500s, when an unknown printer took a galley of type and scrambled it to make a type specimen book.
        # It has survived not only five centuries, but also the leap into electronic typesetting, remaining essentially unchanged.
        # It was popularised in the 1960s with the release of Letraset sheets containing Lorem Ipsum passages, and more recently with desktop publishing software like Aldus PageMaker including versions of Lorem Ipsum."""
        
        # Single-line string as INPUT
        DOCUMENT_TEXT = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse porttitor rutrum leo. Nam efficitur justo quis mi ullamcorper consectetur. Aenean posuere nisl dignissim mauris blandit, sed euismod lacus posuere. Morbi ultrices magna eget faucibus ultricies. Praesent in ante nisi. Nulla faucibus sollicitudin sapien in aliquet. Interdum et malesuada fames ac ante ipsum primis in faucibus."
        
        gh.write_file(tmp_document, text=DOCUMENT_TEXT)
        output = THE_MODULE.document_to_text(tmp_document)
        output_case1 = output != DOCUMENT_TEXT
        output_case2 = DOCUMENT_TEXT in output
        output_case3 = output.endswith("\n")
        output_case4 = output.strip() == DOCUMENT_TEXT
        assert output_case1 and output_case2 and output_case3 and output_case4
        return

    # TODO: Adding tests to check if extract_document_text.py works properly
    def test_document_to_text_IO(self):
        """Ensure document_to_text_IO() works as expected"""
        debug.trace(4, "test_document_to_text_IO()")
        env_option = "STDOUT"
        # NOTE: Output contains \n specifier at the end on the text.
        doc_input_temp = gh.get_temp_file()
        doc_output_temp = gh.get_temp_file()
        # Single-line string as INPUT
        DOCUMENT_TEXT = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse porttitor rutrum leo. Nam efficitur justo quis mi ullamcorper consectetur. Aenean posuere nisl dignissim mauris blandit, sed euismod lacus posuere. Morbi ultrices magna eget faucibus ultricies. Praesent in ante nisi. Nulla faucibus sollicitudin sapien in aliquet. Interdum et malesuada fames ac ante ipsum primis in faucibus."
        gh.write_file(filename=doc_input_temp, text=DOCUMENT_TEXT)
        test_command_1 = f"../extract_document_text.py {doc_input_temp} {doc_output_temp}"
        gh.run(test_command_1)

        output = gh.read_file(doc_output_temp)
        assert output == DOCUMENT_TEXT
        return 

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
