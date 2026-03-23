#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Convert an HTML dump of a webpage into a PDF or MS Word document.
#
# note:
# - Created via Gemini.
#

"""
Converts HTML files to PDF or DOCX using LibreOffice (high fidelity) or Pandoc (quick & dirty).

Sample usage:
   html_converter.py --format pdf --engine libreoffice input.html output.pdf
"""

# Standard modules
import os
import shutil
import tempfile
import subprocess
from typing import Optional

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main, FILENAME
from mezcla import system

debug.trace(5, f"global __doc__: {__doc__}")
debug.assertion(__doc__)

# Constants
TL = debug.TL
FORMAT_OPT = "format"
ENGINE_OPT = "engine"

#-------------------------------------------------------------------------------

class HtmlConverter:
    """Class for converting HTML to PDF or DOCX"""

    def __init__(self, engine: str = "libreoffice", out_format: str = "pdf", **kwargs) -> None:
        """Initializer"""
        debug.trace_expr(TL.VERBOSE, engine, out_format, kwargs, prefix="in HtmlConverter.__init__: ")
        self.engine = engine.lower()
        self.out_format = out_format.lower()
        debug.assertion(self.engine in ["libreoffice", "pandoc"], "Invalid engine")
        debug.assertion(self.out_format in ["pdf", "docx"], "Invalid format")
        debug.trace_object(5, self, label=f"{self.__class__.__name__} instance")

    def _apply_print_fix(self, html_path: str) -> str:
        """Applies CSS override for single-page printing issue."""
        temp_fd, temp_path = tempfile.mkstemp(suffix=".html", text=True)
        with os.fdopen(temp_fd, "w", encoding="utf-8") as out_f, open(html_path, "r", encoding="utf-8") as in_f:
            for line in in_f:
                if "</head>" in line.lower() or "</HEAD>" in line:
                    out_f.write("<style>@media print { body, html { height: auto !important; overflow: visible !important; position: static !important; } }</style>\n")
                out_f.write(line)
        return temp_path

    def process(self, input_file: str, output_file: Optional[str] = None) -> bool:
        """Converts input_file to PDF or DOCX."""
        if not output_file:
            base, _ = os.path.splitext(input_file)
            output_file = f"{base}.{self.out_format}"

        debug.trace(TL.DETAILED, f"Converting {input_file} to {output_file} using {self.engine}")
        
        temp_html = None
        if self.engine == "libreoffice":
            # Apply CSS fix for LibreOffice print truncation
            temp_html = self._apply_print_fix(input_file)
            work_html = temp_html
        else:
            work_html = input_file

        try:
            if self.engine == "libreoffice":
                filter_arg = "pdf" if self.out_format == "pdf" else 'docx:"MS Word 2007 XML"'
                out_dir = os.path.dirname(os.path.abspath(output_file)) or "."
                cmd = ["libreoffice", "--headless", "--convert-to", filter_arg, "--outdir", out_dir, work_html]
                
                debug.trace(TL.DETAILED, f"Running: {' '.join(cmd)}")
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # LibreOffice derives output name from input file name. We need to rename it to target output_file.
                derived_out = os.path.join(out_dir, os.path.splitext(os.path.basename(work_html))[0] + f".{self.out_format}")
                if derived_out != os.path.abspath(output_file) and os.path.exists(derived_out):
                    shutil.move(derived_out, output_file)

            elif self.engine == "pandoc":
                if self.out_format == "pdf":
                    cmd = ["pandoc", work_html, "-o", output_file]
                else:
                    cmd = ["pandoc", work_html, "--extract-media=./pandoc_media_tmp", "-o", output_file]
                
                debug.trace(TL.DETAILED, f"Running: {' '.join(cmd)}")
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if os.path.exists("./pandoc_media_tmp"):
                    shutil.rmtree("./pandoc_media_tmp", ignore_errors=True)
            return True
        except subprocess.CalledProcessError as e:
            system.print_error(f"Conversion failed: {e.stderr.decode('utf-8')}")
            return False
        finally:
            if temp_html and os.path.exists(temp_html):
                os.remove(temp_html)

#-------------------------------------------------------------------------------

def main() -> None:
    """Entry point"""
    debug.trace(TL.DETAILED, f"main(): script={system.real_path(__file__)}")

    main_app = Main(
        description=__doc__.format(script=gh.basename(__file__)),
        skip_input=True,
        manual_input=True,
        boolean_options=[
            ("pdf", "Output format is PDF (default)"),
            ("docx", "Output format is DOCX"),
            ("libreoffice", "Conversion engine is LibreOffice (default)"),
            ("pandoc", "Conversion engine is Pandoc"),
        ],
        text_options=[
            (FORMAT_OPT, "Output format (pdf or docx). Default: pdf", "pdf"),
            (ENGINE_OPT, "Conversion engine (libreoffice or pandoc). Default: libreoffice", "libreoffice"),
        ],
        positional_arguments=[FILENAME, "output_file"], 
    )
    debug.assertion(main_app.parsed_args)
    
    fmt_opt = main_app.get_parsed_option(FORMAT_OPT)
    if main_app.get_parsed_option("docx"):
        fmt_opt = "docx"
    elif main_app.get_parsed_option("pdf"):
        fmt_opt = "pdf"

    eng_opt = main_app.get_parsed_option(ENGINE_OPT)
    if main_app.get_parsed_option("pandoc"):
        eng_opt = "pandoc"
    elif main_app.get_parsed_option("libreoffice"):
        eng_opt = "libreoffice"
    in_file = main_app.get_parsed_argument(FILENAME)
    out_file = main_app.get_parsed_argument("output_file")

    converter = HtmlConverter(engine=eng_opt, out_format=fmt_opt)
    
    if in_file:
        converter.process(in_file, out_file)
    else:
        system.print_error("Error: Please provide an input HTML file.")

    return

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    main()
