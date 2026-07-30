#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Convert an HTML dump of a webpage into a PDF or MS Word document.
#
# note:
# - Created via Gemini.
# - revised via Claude Sonnet 4.6
# - applies following CSS
#    @media print {
#        body, html {
#            height: auto !important;
#            overflow: visible !important;
#            position: static !important;
#            display: block !important;
#        }
#        * {
#            overflow: visible !important;
#            height: auto !important;
#          }
#        /* Omit SavePage-WE header */
#        #savepage-pageinfo-bar-container, #savepage-pageinfo-bar, [id^=\"savepage-pageinfo-bar\"] {
#            display: none !important;
#        }
#    }
# - includes optional styling:
#        /* Use wide sections in Tailwind websites */
#        .max-w-\[704px\], .max-w-\[760px\] {
#            max-width: none !important;
#        }
#

"""
Converts HTML files to PDF or DOCX using LibreOffice (high fidelity), Pandoc (quick & dirty), or Selenium (browser rendering).

Sample usage:
   html_converter.py --format pdf --engine libreoffice input.html output.pdf
"""

# Standard modules
import os
import shutil
## OLD: import tempfile
import subprocess
import base64
import time
from typing import Optional

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main, FILENAME
from mezcla.my_regex import my_re
from mezcla import system

debug.trace(5, f"global __doc__: {__doc__}")
debug.assertion(__doc__)

# Constants
TL = debug.TL
FORMAT_OPT = "format"
ENGINE_OPT = "engine"
WEBDRIVER_OPTIONS = system.getenv_value(
    "WEBDRIVER_OPTIONS", None,
    description="Space delimited options for the web driver (chromium)")
USE_LANDSCAPE = system.getenv_bool(
    "USE_LANDSCAPE", False,
    description="Use landscape orientation when converting to PDF")
TAILWIND_WIDTH_HACK = system.getenv_bool(
    "TAILWIND_WIDTH_HACK", False,
    description="Apply fixup for specific Tailwind quirks")

#-------------------------------------------------------------------------------

class HtmlConverter:
    """Class for converting HTML to PDF or DOCX"""

    def __init__(self, engine: str = "libreoffice", out_format: str = "pdf", landscape: bool = False, **kwargs) -> None:
        """Initializer"""
        debug.trace_expr(TL.VERBOSE, engine, out_format, landscape, kwargs, prefix="in HtmlConverter.__init__: ")
        self.engine = engine.lower()
        self.out_format = out_format.lower()
        self.landscape = landscape or USE_LANDSCAPE
        debug.assertion(self.engine in ["libreoffice", "pandoc", "selenium"], "Invalid engine")
        debug.assertion(self.out_format in ["pdf", "docx"], "Invalid format")
        if self.engine == "selenium" and self.out_format != "pdf":
            system.print_error("Warning: Selenium engine only supports PDF output. Format will be forced to PDF.")
            self.out_format = "pdf"
        debug.trace_object(5, self, label=f"{self.__class__.__name__} instance")

    def _apply_print_fix(self, html_path: str, landscape: bool = False) -> str:
        """Applies CSS override for single-page printing issue and hides Save Page WE info bar.
        Also injects @page landscape rule when landscape=True (honoured by LibreOffice and Pandoc).
        When landscape=True also removes max-width constraints so content fills the full page width.
        """
        debug.trace_expr(TL.VERBOSE, html_path, landscape, prefix="in _apply_print_fix: ")
        ## OLD: temp_fd, temp_path = tempfile.mkstemp(suffix=".html", text=True)

        # Build the @page orientation rule (empty string when portrait so no extra CSS is emitted)
        page_orientation_css = "@page { size: landscape; } " if landscape else ""
        # In landscape mode, strip max-width from common layout containers so content
        # reflows across the full page width rather than staying in a narrow column.
        # Also keep the legacy TAILWIND_WIDTH_HACK selectors for backward-compat.
        tailwind_css = "" if not TAILWIND_WIDTH_HACK else r"""
            /* Use wide sections in Tailwind websites (TODO: generalize) */
            .max-w-\[704px\], .max-w-\[760px\] {
                 max-width: none !important;
            }
        """
        landscape_width_css = "" if not landscape else """
            body, html, main, article, section, aside, nav,
            div[class*="max-w"], div[class*="container"], div[class*="wrapper"],
            div[class*="content"], div[class*="layout"], div[class*="page"] {
                max-width: none !important;
                width: auto !important;
            }
        """

        ## OLD:
        ## with os.fdopen(temp_fd, "w", encoding="utf-8") as out_f, open(html_path, "r", encoding="utf-8") as in_f:
        ##    for line in in_f:
        ##         if "</head>" in line.lower() or "</HEAD>" in line:    ## TODO2: wth?
        ##             out_f.write(f"<style>{page_orientation_css}@media print {{ body, html {{ height: auto !important; overflow: visible !important; position: static !important; display: block !important; }} * {{ overflow: visible !important; height: auto !important; }} #savepage-pageinfo-bar-container, #savepage-pageinfo-bar, [id^=\"savepage-pageinfo-bar\"] {{ display: none !important; }} {tailwind_css}{landscape_width_css} }}</style>\n")
        ##         out_f.write(line)
        ##
        new_style = (f"<style>{page_orientation_css}@media print {{ body, html {{ height: auto !important; overflow: visible !important; position: static !important; display: block !important; }} * {{ overflow: visible !important; height: auto !important; }} #savepage-pageinfo-bar-container, #savepage-pageinfo-bar, [id^=\"savepage-pageinfo-bar\"] {{ display: none !important; }} {tailwind_css}{landscape_width_css} }}</style>\n")
        ##
        original_html = system.read_entire_file(html_path)
        ## TODO4: get one-liner to work w/ sub (b.b., hanging on latge file)
        ## modified_html = my_re.sub(r"(.*?)(</head>)", rf"\1{new_style}\2", original_html,
        ##                           count=1, flags=my_re.IGNORECASE)
        end_head = r"</head>"
        if my_re.search(end_head, original_html, flags=my_re.IGNORECASE):
            modified_html = my_re.pre_match() + new_style + my_re.group(0) + my_re.post_match()
        else:
            debug.trace(TL.WARNING, "_apply_print_fix: no </head> tag found; appending style")          
            modified_html = original_html + new_style
        debug.assertion(modified_html != original_html)
        debug.assertion("overflow: visible !important" in modified_html)
        temp_path = gh.write_temp_file("apply_print_fix.html", modified_html)
        
        return temp_path

    def process(self, input_file: str, output_file: Optional[str] = None) -> bool:
        """Converts input_file to PDF or DOCX."""
        if not output_file:
            base, _ = os.path.splitext(input_file)
            output_file = f"{base}.{self.out_format}"

        debug.trace(TL.DETAILED, f"Converting {input_file} to {output_file} using {self.engine}")
        
        temp_html = None
        work_html = ""
        if self.engine in ["libreoffice", "selenium", "pandoc"]:
            # Apply CSS fix for print truncation; also inject landscape @page rule if requested
            temp_html = self._apply_print_fix(input_file, landscape=self.landscape)
            work_html = temp_html
        ## OLD:
        ## else:
        ##     work_html = input_file

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
                    ## OLD: cmd = ["pandoc", work_html, "-o", output_file]
                    cmd = ["pandoc", work_html, "-o", output_file]
                else:
                    cmd = ["pandoc", work_html, "--extract-media=./pandoc_media_tmp", "-o", output_file]
                
                debug.trace(TL.DETAILED, f"Running: {' '.join(cmd)}")
                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if os.path.exists("./pandoc_media_tmp") and not debug.verbose_debugging():
                    shutil.rmtree("./pandoc_media_tmp", ignore_errors=True)

            elif self.engine == "selenium":
                try:
                    ## TODO4: put this above (e.g., module scope)
                    # pylint: disable=import-outside-toplevel
                    from selenium import webdriver
                    from selenium.webdriver.chrome.options import Options
                    from selenium.webdriver.chrome.service import Service
                except ImportError:
                    system.print_error("Error: Selenium engine requires selenium to be installed (pip install selenium).")
                    return False
                
                options = Options()
                if WEBDRIVER_OPTIONS:
                    for option in WEBDRIVER_OPTIONS.split():
                        options.add_argument(option)
                else:
                    options.add_argument('--headless')
                    options.add_argument('--disable-gpu')
                    options.add_argument('--no-sandbox')
                    # note: uses /tmp instead of system's shared memory partition (/dev/shm)
                    options.add_argument('--disable-dev-shm-usage')
                
                debug.trace(TL.DETAILED, "Starting Selenium Chrome WebDriver")
                debug.trace(TL.VERBOSE, f"\toptions={options.arguments}")
                service = None
                if debug.debugging(6):
                    ## TODO3: add argument to enable low-level webdriver logs; also refine gh.create_temp_file to take filename
                    log_path = gh.write_temp_file("chromedriver-verbose.log", "")
                    service = Service(log_output=log_path, service_args=["--verbose"])
                driver = webdriver.Chrome(service=service, options=options)
                try:
                    file_url = f"file://{os.path.abspath(work_html)}"
                    debug.trace(TL.DETAILED, f"Loading {file_url}")
                    driver.get(file_url)
                    time.sleep(1) # wait for rendering
                    
                    # Remove "Save Page WE" info bar
                    driver.execute_script('''
                        var container = document.getElementById("savepage-pageinfo-bar-container");
                        if (container) container.remove();
                        var bar = document.getElementById("savepage-pageinfo-bar");
                        if (bar) bar.remove();
                        var dt = document.getElementById("savepage-pageinfo-bar-datetime");
                        if (dt) dt.remove();
                    ''')

                    print_options = {
                        'landscape': self.landscape,
                        'displayHeaderFooter': False,
                        'printBackground': True,
                        ## OLD: 'preferCSSPageSize': True,
                        # note: preferCSSPageSize must be False when landscape=True so that
                        # CSS @page rules in the saved HTML cannot override the orientation
                        'preferCSSPageSize': not self.landscape,
                    }
                    # Chrome's CDP landscape flag internally swaps width/height, so supply
                    # portrait dimensions (8.5×11) and let landscape=True flip them to 11×8.5
                    if self.landscape:
                        print_options['paperWidth'] = 8.5
                        print_options['paperHeight'] = 11.0
                    debug.trace(TL.DETAILED, "Executing Page.printToPDF")
                    debug.trace(TL.VERBOSE, f"\toptions={print_options}")
                    result = driver.execute_cdp_cmd("Page.printToPDF", print_options)
                    
                    with open(output_file, 'wb') as f:
                        f.write(base64.b64decode(result['data']))
                finally:
                    driver.quit()

            return True
        ## OLD:
        ## except subprocess.CalledProcessError as e:
        ##     system.print_error(f"Conversion failed: {e.stderr.decode('utf-8')}")
        ##     return False
        ## except Exception as e:
        ##     system.print_error(f"Conversion failed: {e}")
        ##     return False
        except:
            system.print_exception_info("conversion-process")
            return False
        finally:
            if temp_html and os.path.exists(temp_html) and not debug.verbose_debugging():
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
            ("selenium", "Conversion engine is Selenium (PDF only)"),
            ("landscape", "Use landscape orientation (default: portrait)"),
        ],
        text_options=[
            (FORMAT_OPT, "Output format (pdf or docx). Default: pdf", "pdf"),
            (ENGINE_OPT, "Conversion engine (libreoffice, pandoc, or selenium). Default: libreoffice", "libreoffice"),
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
    if main_app.get_parsed_option("selenium"):
        eng_opt = "selenium"
    elif main_app.get_parsed_option("pandoc"):
        eng_opt = "pandoc"
    elif main_app.get_parsed_option("libreoffice"):
        eng_opt = "libreoffice"
    in_file = main_app.get_parsed_argument(FILENAME)
    out_file = main_app.get_parsed_argument("output_file")
    landscape_opt = main_app.get_parsed_option("landscape", default=False)

    converter = HtmlConverter(engine=eng_opt, out_format=fmt_opt, landscape=landscape_opt)
    
    if in_file:
        converter.process(in_file, out_file)
    else:
        system.print_error("Error: Please provide an input HTML file.")

    return

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    main()
