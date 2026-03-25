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
    import mezcla.html_converter as THE_MODULE
except Exception:  # pylint: disable=broad-exception-caught
    system.print_exception_info("html_converter import") 

#------------------------------------------------------------------------

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    def perform_conversion_test(self, engine: str, out_format: str, title: str) -> None:
        """Helper method to test conversion engines"""
        html_content = f"<html><head><title>Test</title></head><body><h1>Hello {title}</h1></body></html>\n"
        in_file = self.create_temp_file(html_content)
        out_file = in_file + f".{out_format}"
        
        converter = THE_MODULE.HtmlConverter(engine=engine, out_format=out_format)
        success = converter.process(in_file, out_file)
        
        self.do_assert(success, "Conversion failed")
        self.do_assert(os.path.exists(out_file), "Output file not created")
        if os.path.exists(out_file):
            self.do_assert(os.path.getsize(out_file) > 0, "Output file is empty")

    def test_01_libreoffice_pdf(self):
        """Tests converting a simple HTML to PDF using libreoffice"""
        debug.trace(4, f"TestIt.test_01_libreoffice_pdf(); self={self}")
        self.perform_conversion_test("libreoffice", "pdf", "LibreOffice PDF")
        return

    def test_02_pandoc_docx(self):
        """Tests converting a simple HTML to DOCX using pandoc"""
        debug.trace(4, f"TestIt.test_02_pandoc_docx(); self={self}")
        self.perform_conversion_test("pandoc", "docx", "Pandoc DOCX")
        return

    def test_03_selenium_pdf(self):
        """Tests converting a simple HTML to PDF using selenium"""
        debug.trace(4, f"TestIt.test_03_selenium_pdf(); self={self}")
        self.perform_conversion_test("selenium", "pdf", "Selenium PDF")
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
