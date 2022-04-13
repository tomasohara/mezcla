#! /usr/bin/env python
#
# Test(s) for ../html_utils.py
#
# Notes:
# - Fill out TODO's below. Use numbered tests to order (e.g., test_1_usage).
# - TODO: If any of the setup/cleanup methods defined, make sure to invoke base
#   (see examples below for setUp and tearDown).
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python tests/test_html_utils.py
#

"""Tests for html_utils module"""

# Standard packages
import re
import unittest

# Installed packages
## TODO: import pytest

# Local packages
from mezcla.unittest_wrapper import TestWrapper
from mezcla import debug
from mezcla import system
from mezcla import glue_helpers as gh

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
#    TestIt.script_module   string name
## TODO: template => new name
import mezcla.html_utils as THE_MODULE
#
# Note: sanity test for customization (TODO: remove if desired)
if not re.search(__file__, r"\btemplate.py$"):
    debug.assertion("mezcla.template" not in str(THE_MODULE))

# 
TEST_SELENIUM = system.getenv_bool("TEST_SELENIUM", False,
                                   "Include tests requiring selenium")

class TestIt(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__)
    # TODO: use_temp_base_dir = True            # treat TEMP_BASE as directory
    # note: temp_file defined by parent (along with script_module, temp_base, and test_num)


    def test_get_url_parameter_value(self):
        """Ensure get_url_parameter_value works as expected"""
        debug.trace(4, "test_get_url_parameter_value()")
        save_user_parameters = THE_MODULE.user_parameters
        THE_MODULE.user_parameters = {}
        self.assertEqual(THE_MODULE.get_url_parameter_value("fubar", None), None)
        self.assertEqual(THE_MODULE.get_url_parameter_value("fubar", None, {"fubar": "fu"}), "fu")
        THE_MODULE.user_parameters = {"fubar": "bar"}
        self.assertEqual(THE_MODULE.get_url_parameter_value("fubar", None), "bar")
        self.assertEqual(THE_MODULE.get_url_parameter_value("fubar", None, {"fubar": "fu"}), "fu")
        THE_MODULE.user_parameters = save_user_parameters
        return

    def test_get_inner_text(self):
        """Verify that JavaScript fills in window dimensions
        Note: requires selenium"""
        debug.trace(4, "test_get_inner_text()")
        if not TEST_SELENIUM:
            debug.trace(4, "Ignoring test_get_inner_text as selenium required")
            return
        html_filename = "simple-window-dimensions.html"
        html_path = gh.resolve_path(html_filename)
        url = ("file:" + system.absolute_path(html_path))
        # TODO: use direct API call to return unrendered text
        unrendered_text = gh.run(f"lynx -dump {url}")
        debug.trace_expr(5, unrendered_text)
        self.assertTrue(re.search(r"Browser dimensions: \?", unrendered_text))
        rendered_text = THE_MODULE.get_inner_text(url)
        debug.trace_expr(5, rendered_text)
        self.assertTrue(re.search(r"Browser dimensions: \d+x\d+", rendered_text))
    
    def test_get_inner_html(self):
        """Verify that JavaScript fills in window dimensions
        Note: requires selenium"""
        debug.trace(4, "test_get_inner_html()")
        if not TEST_SELENIUM:
            debug.trace(4, "Ignoring test_get_inner_html as selenium required")
            return
        html_filename = "simple-window-dimensions.html"
        html_path = gh.resolve_path(html_filename)
        url = ("file:" + system.absolute_path(html_path))
        # TODO: use direct API call to return unrendered text
        unrendered_html = gh.run(f"lynx -source {url}")
        debug.trace_expr(5, unrendered_html)
        self.assertTrue(re.search(r"<li>Browser dimensions:\s*<span.*>\?\?\?</span></li>",
                                  unrendered_html))
        rendered_html = THE_MODULE.get_inner_html(url)
        debug.trace_expr(5, rendered_html)
        self.assertTrue(re.search(r"<li>Browser dimensions:\s*<span.*>\d+x\d+</span></li>",
                                  rendered_html))
    
#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    unittest.main()
