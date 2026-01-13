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
           const unused = 'I am not used';
           print(2 + 2 == 5.0);
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

# HTML with jQuery code
JQUERY_HTML_TEXT = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>jQuery Test</title>
        <script>
           $(document).ready(function() {
               $("#myButton").click(function() {
                   alert("Button clicked!");
               });
           });
        </script>
      </head>
      <body>
         <button id="myButton">Click me</button>
      </body>
    </html>
"""

# HTML with multiple script blocks
MULTI_SCRIPT_HTML_TEXT = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Multiple Scripts</title>
        <script>
           var globalVar = "I am global";
        </script>
        <script>
           function testFunction() {
               console.log(globalVar);
               undefinedVariable = "oops";
           }
           testFunction();
        </script>
      </head>
      <body>
         Test
      </body>
    </html>
"""

# HTML with ES6 features
ES6_HTML_TEXT = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>ES6 Test</title>
        <script>
           const arrow = (x) => x * 2;
           let result = arrow(5);
           console.log(`Result: ${result}`);
           
           class MyClass {
               constructor(name) {
                   this.name = name;
               }
           }
           const obj = new MyClass("test");
        </script>
      </head>
      <body>
         ES6 Features
      </body>
    </html>
"""

# HTML with common linting issues
LINTING_ISSUES_HTML = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Linting Issues</title>
        <script>
           // Missing semicolons
           var x = 5
           var y = 10
           
           // Using == instead of ===
           if (x == "5") {
               console.log("loose equality");
           }
           
           // Undefined variable
           z = x + y;
           
           // Unused variable
           const neverUsed = "I'm never used";
           
           console.log(z);
        </script>
      </head>
      <body>
         Linting Issues
      </body>
    </html>
"""

# Empty script tags
EMPTY_SCRIPT_HTML = """
    <!DOCTYPE html>
    <html>
      <head>
        <title>Empty Script</title>
        <script>
        </script>
      </head>
      <body>
         Empty Script
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
        output = self.run_script(options="--use-all", data_file=self.temp_file)
        output = output.strip()
        assert output
        
        # Warning from jslint
        self.do_assert(my_re.search(r"Undeclared.*text", output))
        
        # Warning from jshint
        # TODO: track down intermittent failure
        self.do_assert(my_re.search(r"Missing semicolon", output))

        # Warning from eslint
        self.do_assert(my_re.search(r"warning.*Expected.*===", output))
        
        return
    
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_01a_simple_html(self):
        """Tests run_script with simple HTML data file"""
        debug.trace(4, f"TestIt.test_01a_simple_html(); self={self}")
        # Run script over simple HTML data and get output
        system.write_file(self.temp_file, SIMPLE_HTML_TEXT)
        output = self.run_script(options="", data_file=self.temp_file)
        output = output.strip()
        assert output
        
        # Check that output contains checker results
        self.do_assert(my_re.search(r"Output from", output))
        
        # Should detect undeclared variable 'text'
        self.do_assert(my_re.search(r"(Undeclared|not defined|'text')", output, 
                                   flags=my_re.IGNORECASE))
        
        return
    
    def test_02_strict_mode(self):
        """Make sure strict mode is used by default"""
        debug.trace(4, f"TestIt.test_02_strict_mode(); self={self}")
        self.do_assert("strict" in THE_MODULE.SAFEMODE_HEADER)
        self.do_assert(THE_MODULE.USE_STRICT_MODE)
        return
    
    def test_03_jquery_html(self):
        """Tests jQuery code detection"""
        debug.trace(4, f"TestIt.test_03_jquery_html(); self={self}")
        system.write_file(self.temp_file, JQUERY_HTML_TEXT)
        output = self.run_script(options="--no-use-jslint", data_file=self.temp_file)
        
        # Should not complain about $ being undefined (jQuery is in header)
        self.do_assert(not my_re.search(r"\$.*undefined", output, flags=my_re.IGNORECASE))
        return
    
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_04_multiple_scripts(self):
        """Tests HTML with multiple script blocks"""
        debug.trace(4, f"TestIt.test_04_multiple_scripts(); self={self}")
        system.write_file(self.temp_file, MULTI_SCRIPT_HTML_TEXT)
        output = self.run_script(options="", data_file=self.temp_file)
        
        # Should detect undefined variable
        self.do_assert(my_re.search(r"undefinedVariable", output))
        return
    
    def test_05_es6_features(self):
        """Tests ES6 JavaScript features"""
        debug.trace(4, f"TestIt.test_05_es6_features(); self={self}")
        system.write_file(self.temp_file, ES6_HTML_TEXT)
        output = self.run_script(options="", data_file=self.temp_file)
        
        # Should accept arrow functions, template literals, let/const, classes
        # (No syntax errors expected)
        self.do_assert(my_re.search(r"Output from", output))
        return
    
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_06_linting_issues(self):
        """Tests detection of common linting issues"""
        debug.trace(4, f"TestIt.test_06_linting_issues(); self={self}")
        system.write_file(self.temp_file, LINTING_ISSUES_HTML)
        output = self.run_script(options="--no-use-jslint", data_file=self.temp_file)
        
        # Should detect missing semicolons (jshint)
        self.do_assert(my_re.search(r"(semicolon|;)", output, flags=my_re.IGNORECASE))
        return
    
    def test_07_skip_strict_mode(self):
        """Tests --skip-safe-mode option"""
        debug.trace(4, f"TestIt.test_07_skip_strict_mode(); self={self}")
        system.write_file(self.temp_file, SIMPLE_HTML_TEXT)
        output = self.run_script(options="--skip-safe-mode", data_file=self.temp_file)
        
        # Output should exist even without strict mode
        self.do_assert(my_re.search(r"Output from", output))
        return
    
    def test_08_strip_indent(self):
        """Tests --strip-indent option"""
        debug.trace(4, f"TestIt.test_08_strip_indent(); self={self}")
        system.write_file(self.temp_file, SIMPLE_HTML_TEXT)
        output = self.run_script(options="--strip-indent", data_file=self.temp_file)
        
        # Should process successfully
        self.do_assert(my_re.search(r"Output from", output))
        return
    
    def test_09_only_jshint(self):
        """Tests using only JSHint checker"""
        debug.trace(4, f"TestIt.test_09_only_jshint(); self={self}")
        system.write_file(self.temp_file, SIMPLE_HTML_TEXT)
        output = self.run_script(options="--no-use-jslint", data_file=self.temp_file)
        
        # Should show only jshint output
        self.do_assert(my_re.search(r"Output from jshint", output))
        self.do_assert(not my_re.search(r"Output from jslint", output))
        return
    
    def test_10_only_jslint(self):
        """Tests using only JSLint checker"""
        debug.trace(4, f"TestIt.test_10_only_jslint(); self={self}")
        system.write_file(self.temp_file, SIMPLE_HTML_TEXT)
        output = self.run_script(options="--no-use-jshint", data_file=self.temp_file)
        
        # Should show only jslint output
        self.do_assert(my_re.search(r"Output from jslint", output))
        self.do_assert(not my_re.search(r"Output from jshint", output))
        return
    
    def test_11_ansi_codes_removed(self):
        """Tests that ANSI escape codes are removed from output"""
        debug.trace(4, f"TestIt.test_11_ansi_codes_removed(); self={self}")
        system.write_file(self.temp_file, SIMPLE_HTML_TEXT)
        output = self.run_script(options="", data_file=self.temp_file)
        
        # Should not contain ANSI escape sequences
        self.do_assert(not my_re.search(r"\x1b\[[0-9;]*m", output))
        return
    
    def test_12_empty_script(self):
        """Tests handling of empty script tags"""
        debug.trace(4, f"TestIt.test_12_empty_script(); self={self}")
        system.write_file(self.temp_file, EMPTY_SCRIPT_HTML)
        output = self.run_script(options="", data_file=self.temp_file)
        
        # Should handle gracefully (may show error about no code found)
        self.do_assert(my_re.search(r"(No code found|Output from)", output))
        return
    
    def test_13_es_version_option(self):
        """Tests --es-version option"""
        debug.trace(4, f"TestIt.test_13_es_version_option(); self={self}")
        system.write_file(self.temp_file, ES6_HTML_TEXT)
        output = self.run_script(options="--es-version 6", data_file=self.temp_file)
        
        # Should process ES6 code successfully
        self.do_assert(my_re.search(r"Output from", output))
        return
    
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_14_skip_common_defines(self):
        """Tests --skip-common-defines option"""
        debug.trace(4, f"TestIt.test_14_skip_common_defines(); self={self}")
        system.write_file(self.temp_file, JQUERY_HTML_TEXT)
        output = self.run_script(options="--skip-common-defines", data_file=self.temp_file)
        
        # Should complain about undefined $ since jQuery not defined
        self.do_assert(my_re.search(r"(\$|jQuery).*(undefined|not defined)", 
                                   output, flags=my_re.IGNORECASE))
        return
    
    def test_15_code_checkers_option(self):
        """Tests --code-checkers option"""
        debug.trace(4, f"TestIt.test_15_code_checkers_option(); self={self}")
        system.write_file(self.temp_file, SIMPLE_HTML_TEXT)
        output = self.run_script(options="--code-checkers jshint", data_file=self.temp_file)
        
        # Should only run jshint
        self.do_assert(my_re.search(r"Output from jshint", output))
        self.do_assert(not my_re.search(r"Output from jslint", output))
        return
    
    def test_16_header_constants(self):
        """Tests that header constants are properly defined"""
        debug.trace(4, f"TestIt.test_16_header_constants(); self={self}")
        
        # Check that important constants exist
        self.do_assert(hasattr(THE_MODULE, 'DEFAULT_JAVASCRIPT_HEADER'))
        self.do_assert(hasattr(THE_MODULE, 'SAFEMODE_HEADER'))
        
        # Check header contains necessary definitions
        header = THE_MODULE.DEFAULT_JAVASCRIPT_HEADER
        self.do_assert('document' in header)
        self.do_assert('window' in header)
        self.do_assert('jQuery' in header or '$' in header)
        self.do_assert('console' in header)
        return
    
    def test_17_option_constants(self):
        """Tests that option constants are properly defined"""
        debug.trace(4, f"TestIt.test_17_option_constants(); self={self}")
        
        # Check for main option constants
        self.do_assert(hasattr(THE_MODULE, 'CODE_CHECKERS'))
        self.do_assert(hasattr(THE_MODULE, 'STRIP_INDENT'))
        self.do_assert(hasattr(THE_MODULE, 'SKIP_SAFE_MODE'))
        self.do_assert(hasattr(THE_MODULE, 'USE_JSLINT'))
        self.do_assert(hasattr(THE_MODULE, 'USE_JSHINT'))
        self.do_assert(hasattr(THE_MODULE, 'USE_ESLINT'))
        return
    
    def test_18_default_checkers(self):
        """Tests default checker configuration"""
        debug.trace(4, f"TestIt.test_18_default_checkers(); self={self}")
        
        # Check default checkers string
        default = THE_MODULE.DEFAULT_CODE_CHECKERS
        self.do_assert('jshint' in default.lower() or 'jslint' in default.lower())
        return
    
    def test_19_max_errors_setting(self):
        """Tests MAX_ERRORS configuration"""
        debug.trace(4, f"TestIt.test_19_max_errors_setting(); self={self}")
        
        # Check that MAX_ERRORS is defined and reasonable
        self.do_assert(hasattr(THE_MODULE, 'MAX_ERRORS'))
        self.do_assert(THE_MODULE.MAX_ERRORS > 0)
        return
    
    def test_20_script_class_exists(self):
        """Tests that Script class is properly defined"""
        debug.trace(4, f"TestIt.test_20_script_class_exists(); self={self}")
        
        # Check Script class exists and has required methods
        self.do_assert(hasattr(THE_MODULE, 'Script'))
        script_class = THE_MODULE.Script
        self.do_assert(hasattr(script_class, 'process_line'))
        self.do_assert(hasattr(script_class, 'wrap_up'))
        self.do_assert(hasattr(script_class, 'setup'))
        return

#------------------------------------------------------------------------
if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
