#! /usr/bin/env python3
#
# Test(s) for ../check_html_javascript.py
#
# Notes:
# - Fill out TODO's below. Use numbered tests to order (e.g., test_1_usage).
# - * See test_python_ast.py for simple example of customization.
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by unittest_wrapper.py.
# - This can be run as follows (e.g., from root of repo):
#   $ pytest ./mezcla/tests/test_check_html_javascript.py
#
# Warning:
# - The use of run_script as in test_01_data_file is an older style of testing.
#   It is better to directly invoke a helper class in the script that is independent
#   of the Script class based on Main. (See an example of this, see python_ast.py
#   and tests/tests_python_ast.py.)
# - Moreover, debugging tests with run_script is complicated because a separate
#   process is involved (e.g., with separate environment variables.)
# - See discussion of SUB_DEBUG_LEVEL in unittest_wrapper.py for more info.
# - TODO: Feel free to delete this warning as well as the related one below.
#


"""Tests for check_html_javascript module"""

# Standard modules
## TODO: from collections import defaultdict

# Installed modules
import pytest

# Local modules
from mezcla import debug
from mezcla.my_regex import my_re
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper, invoke_tests

# Note: Two references are used for the module to be tested:
#    THE_MODULE:               module object (e.g., <module 'mezcla.main' ...>)
#    TestIt.script_module:     dotted module path (e.g., "mezcla.main")
THE_MODULE = None
try:
    import mezcla.check_html_javascript as THE_MODULE
except:
    system.print_exception_info("check_html_javascript import") 
#
# Note: sanity test for customization (TODO: remove if desired)
if not my_re.search(r"\btemplate.py$", __file__):
    debug.assertion("mezcla.template" not in str(THE_MODULE))

# Constants
    
SIMPLE_HTML_TEXT = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Dummy HTML file</title>
        <script>
           console.log("in script");
           text = "fubar";
           text -= 666
	   console.log("out script");
        </script>
      </head>
    
      <body>
         Dummy
      </body>
    </html>    
"""

#------------------------------------------------------------------------

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    # note: script_module used in argument parsing sanity check (e.g., --help)
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_01_data_file(self):
        """Tests run_script w/ data file"""
        debug.trace(4, f"TestIt.test_01_data_file(); self={self}")

        # Run script over simple HTML data and get outut
        system.write_file(self.temp_file, SIMPLE_HTML_TEXT)
        output = self.run_script(options="", data_file=self.temp_file)
        output = output.strip()
        
        # Warning from jslint
        # 
        self.do_assert(my_re.search(r"Undeclared.*text", output))
        
        # Warning from jshint
        self.do_assert(my_re.search(r"Missing semicolon", output))
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_02_strict_mode(self):
        """Make sure strict mode used"""
        debug.trace(4, f"TestIt.ttest_02_strict_mode(); self={self}")
        self.do_assert("strict" in THE_MODULE.SAFEMODE_HEADER)
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
