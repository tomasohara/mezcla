#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Tests for html_converter.py
#

"""Tests for html_converter module"""

# Standard modules
import os

# Installed modules

# Local modules
from mezcla import debug
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper, invoke_tests

THE_MODULE = None
try:
    import html_converter as THE_MODULE
except Exception:  # pylint: disable=broad-exception-caught
    system.print_exception_info("html_converter import") 

#------------------------------------------------------------------------

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    def test_01_libreoffice_pdf(self):
        """Tests converting a simple HTML to PDF using libreoffice"""
        debug.trace(4, f"TestIt.test_01_libreoffice_pdf(); self={self}")
        
        # Create a simple test HTML
        html_content = ["<html><head><title>Test</title></head><body><h1>Hello LibreOffice PDF</h1></body></html>"]
        in_file = "test_libreoffice.html"
        with open(in_file, "w", encoding="utf-8") as f:
            f.write("\n".join(html_content))
        out_file = in_file.replace(".html", ".pdf")
        
        converter = THE_MODULE.HtmlConverter(engine="libreoffice", out_format="pdf")
        success = converter.process(in_file, out_file)
        
        self.do_assert(success, "Conversion failed")
        self.do_assert(os.path.exists(out_file), "Output file not created")
        if os.path.exists(out_file):
            self.do_assert(os.path.getsize(out_file) > 0, "Output file is empty")
        return

    def test_02_pandoc_docx(self):
        """Tests converting a simple HTML to DOCX using pandoc"""
        debug.trace(4, f"TestIt.test_02_pandoc_docx(); self={self}")
        
        # Create a simple test HTML
        html_content = ["<html><head><title>Test</title></head><body><h1>Hello Pandoc DOCX</h1></body></html>"]
        in_file = "test_pandoc.html"
        with open(in_file, "w", encoding="utf-8") as f:
            f.write("\n".join(html_content))
        out_file = in_file.replace(".html", ".docx")
        
        converter = THE_MODULE.HtmlConverter(engine="pandoc", out_format="docx")
        success = converter.process(in_file, out_file)
        
        self.do_assert(success, "Conversion failed")
        self.do_assert(os.path.exists(out_file), "Output file not created")
        if os.path.exists(out_file):
            self.do_assert(os.path.getsize(out_file) > 0, "Output file is empty")
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
