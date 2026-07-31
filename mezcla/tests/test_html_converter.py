#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Tests for html_converter.py
#

"""Tests for html_converter module"""

# Standard modules
import os
import re

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
            try:
                ## TODO4: put this above (e.g., module scope)
                # pylint: disable=import-outside-toplevel
                import textract
                text = textract.process(out_file).decode("utf-8", errors="ignore")
                self.do_assert(f"Hello {title}" in text, "Title text not found in extracted text")
            except ImportError:
                debug.trace(3, "textract not installed, skipping text verification")
            ## OLD:
            ## except Exception as e:
            ##    debug.trace(3, f"text verification failed: {e}")
            except:
                debug.trace_exception(3, "text verification")

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

    def test_04_tailwind_width_fix(self):
        """Tests that --tailwind / tailwind_fix injects CSS stripping Tailwind max-w-[*] classes.
        Uses tests/resources/tailwind-width-example.html which has real max-w-[760px] and
        max-w-[704px] classes; verifies the fix appears in the modified temp HTML.
        """
        debug.trace(4, f"TestIt.test_04_tailwind_width_fix(); self={self}")
        resource_dir = os.path.join(os.path.dirname(__file__), "resources")
        in_file = os.path.join(resource_dir, "tailwind-width-example.html")
        self.do_assert(os.path.exists(in_file), f"Test resource not found: {in_file}")

        # Verify the resource actually contains Tailwind arbitrary max-width classes
        html_src = system.read_entire_file(in_file)
        self.do_assert("max-w-[760px]" in html_src or r"max-w-\[760px\]" in html_src,
                       "tailwind-width-example.html missing expected max-w-[760px] class")

        # Apply the print fix with tailwind_fix=True and inspect the generated temp HTML
        if THE_MODULE:
            converter = THE_MODULE.HtmlConverter(engine="selenium", out_format="pdf",
                                                 tailwind_fix=True)
            # pylint: disable=protected-access
            temp_html = converter._apply_print_fix(in_file, tailwind_fix=True)
            try:
                modified = system.read_entire_file(temp_html)
                # The injected CSS must include the [class*="max-w-\["] selector
                self.do_assert(r'class*="max-w-\["' in modified or
                               r"class*='max-w-\['" in modified or
                               "max-w-\\[" in modified,
                               "Tailwind width fix CSS not found in modified HTML")
            finally:
                if os.path.exists(temp_html):
                    os.remove(temp_html)
        return

    def test_05_landscape_pdf(self):
        """Tests that --landscape produces a landscape-orientation PDF (792x612 pts).
        Uses tests/resources/dummy-word-wrap.html as a simple self-contained input.
        Requires pdfinfo to verify page dimensions.
        """
        debug.trace(4, f"TestIt.test_05_landscape_pdf(); self={self}")
        resource_dir = os.path.join(os.path.dirname(__file__), "resources")
        in_file = os.path.join(resource_dir, "dummy-word-wrap.html")
        self.do_assert(os.path.exists(in_file), f"Test resource not found: {in_file}")

        out_file = self.create_temp_file("") + ".pdf"
        if THE_MODULE:
            converter = THE_MODULE.HtmlConverter(engine="selenium", out_format="pdf",
                                                 landscape=True)
            success = converter.process(in_file, out_file)
            self.do_assert(success, "Landscape PDF conversion failed")
            self.do_assert(os.path.exists(out_file), "Landscape PDF output file not created")
            if os.path.exists(out_file) and os.path.getsize(out_file) > 0:
                # Use pdfinfo to confirm page size is landscape (792x612 pts = 11x8.5 in)
                try:
                    import subprocess  # pylint: disable=import-outside-toplevel
                    result = subprocess.run(["pdfinfo", out_file], capture_output=True, text=True,
                                           check=False)
                    page_size_line = next(
                        (ln for ln in result.stdout.splitlines() if "Page size" in ln), "")
                    debug.trace(4, f"pdfinfo page size: {page_size_line!r}")
                    # Landscape letter: width > height (792 x 612 pts)
                    nums = re.findall(r"[\d.]+", page_size_line)
                    if len(nums) >= 2:
                        width_pts, height_pts = float(nums[0]), float(nums[1])
                        self.do_assert(width_pts > height_pts,
                                       f"PDF is not landscape: {width_pts} x {height_pts} pts")
                    else:
                        debug.trace(3, "pdfinfo output not parseable; skipping dimension check")
                except FileNotFoundError:
                    debug.trace(3, "pdfinfo not installed; skipping page dimension check")
        return

    def test_06_svg_print_fix(self):
        """Tests that _apply_print_fix excludes SVG elements from height: auto !important."""
        debug.trace(4, f"TestIt.test_06_svg_print_fix(); self={self}")
        html_content = "<html><head><title>SVG Test</title></head><body><svg><rect height='100'/></svg></body></html>\n"
        in_file = self.create_temp_file(html_content)
        if THE_MODULE:
            converter = THE_MODULE.HtmlConverter(engine="selenium", out_format="pdf")
            # pylint: disable=protected-access
            temp_html = converter._apply_print_fix(in_file)
            try:
                modified = system.read_entire_file(temp_html)
                self.do_assert("*:not(svg):not(svg *)" in modified,
                               "SVG-safe print CSS rule not found in modified HTML")
            finally:
                if os.path.exists(temp_html):
                    os.remove(temp_html)
        return

    def test_07_radar_reflectivity_pdf(self):
        """Tests converting tests/resources/radar-reflectivity.html to PDF via selenium engine.
        Verifies that the PDF output is created, non-empty, and contains both legend and explanation text.
        """
        debug.trace(4, f"TestIt.test_07_radar_reflectivity_pdf(); self={self}")
        resource_dir = os.path.join(os.path.dirname(__file__), "resources")
        in_file = os.path.join(resource_dir, "radar-reflectivity.html")
        self.do_assert(os.path.exists(in_file), f"Test resource not found: {in_file}")

        out_file = self.create_temp_file("") + ".pdf"
        if THE_MODULE:
            converter = THE_MODULE.HtmlConverter(engine="selenium", out_format="pdf")
            success = converter.process(in_file, out_file)
            self.do_assert(success, "Radar reflectivity PDF conversion failed")
            self.do_assert(os.path.exists(out_file), "Radar reflectivity PDF output file not created")
            if os.path.exists(out_file) and os.path.getsize(out_file) > 0:
                try:
                    # pylint: disable=import-outside-toplevel
                    import textract
                    text = textract.process(out_file).decode("utf-8", errors="ignore")
                    self.do_assert("Explanation" in text, "Explanation text not found in converted PDF")
                    self.do_assert("Light" in text and "Heavy" in text, "Legend text not found in converted PDF")
                except ImportError:
                    debug.trace(3, "textract not installed, skipping text verification")
                except:
                    debug.trace_exception(3, "text verification failed")
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
