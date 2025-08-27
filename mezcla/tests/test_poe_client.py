#! /usr/bin/env python3
#
# Test(s) for ../poe_client.py
#
# Notes:
# - This can be run as follows (e.g., from root of repo):
#   $ pytest ./mezcla/tests/test_poe_client.py
#

"""Tests for poe_client module"""

# Installed modules
import pytest

# Local modules
from mezcla import debug
## TODO: from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla.tests.common_module import SKIP_TBD_TESTS, SKIP_TBD_REASON

# Note: Two references are used for the module to be tested:
#    THE_MODULE:               module object (e.g., <module 'mezcla.main' ...>)
#    TestIt.script_module:     dotted module path (e.g., "mezcla.main")
THE_MODULE = None
try:
    import mezcla.poe_client as THE_MODULE
except:
    system.print_exception_info("poe_client import") 
## 
## TODO: make sure import above syntactically valid
#
# Note: sanity test for customization (TODO: remove if desired)
if not my_re.search(r"\btemplate.py$", __file__):
    debug.assertion("mezcla.template" not in str(THE_MODULE))

# Constants
NO_POE_API = not THE_MODULE.POE_API
NO_POE_REASON = "POE_API not set"

#------------------------------------------------------------------------

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    # note: script_module used in argument parsing sanity check (e.g., --help)
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    poe_model = THE_MODULE.POE_MODEL or "o4-mini"

    @pytest.mark.skipif(NO_POE_API, reason=NO_POE_REASON)
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_01_list_models(self):
        """Tests run_script w/ --list-models"""
        # Warning: see notes above about potential issues with run_script-based tests.
        debug.trace(4, f"TestIt.test_01_list_models(); self={self}")
        output = self.run_script(options="--list-models").strip().lower()
        self.do_assert(my_re.search(r"gpt-4.1", output))
        return

    @pytest.mark.skipif(NO_POE_API, reason=NO_POE_REASON)
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_02_color_question(self):
        """Test for simple what-is-color questions"""
        debug.trace(4, f"TestIt.test_02_color_question(); self={self}")
        ## OLD: poe = THE_MODULE.POEClient(model="o4-mini")
        poe = THE_MODULE.POEClient(model=self.poe_model)
        self.do_assert("red" in poe.ask("What is the color of blood?").lower())
        return

    @pytest.mark.skipif(NO_POE_API, reason=NO_POE_REASON)
    @pytest.mark.skipif(not SKIP_TBD_TESTS, reason=SKIP_TBD_REASON)
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_03_expression_evaluation(self):
        """Test out expression evaluation via funciton calling"""
        # Note: you might need to disable tracing during setUp (see notes above).
        debug.trace(4, f"TestIt.test_03_expression_evaluation(); self={self}")
        ## OLD: poe = THE_MODULE.POEClient(model="o4-mini")
        poe = THE_MODULE.POEClient(model=self.poe_model)
        poe.call_function("evaluate", {"expression": "2 + 2"},
                           model="fubar")
        captured = self.get_stderr()
        my_re.search("error.*model", captured.lower())
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
