#! /usr/bin/env python3
#
# Test(s) for ../__init__.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test___init__.py
#
## UPDATE 09/23/2026: adds test for ipython-specific exports

"""Tests for __init__ module"""

# Standard packages
## OLD: import re
import shlex

# Installed packages
import pytest

# Local packages
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
import mezcla.tests.common_module as cm

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                  global module object
#    TestTemplate.script_module:  path to file
import mezcla.__init__ as THE_MODULE

class TestIt(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_data_file(self):
        """Makes sure no output"""
        debug.trace(4, f"TestIt.test_data_file(); self={self}")
        output = self.run_script("", self.temp_file)
        assert(not output.strip())
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_convenience_exports(self):
        """Verify ipython includes convenience exports but not regular python"""
        debug.trace(4, f"TestIt.test_convenience_exports(); self={self}")

        pytest.importorskip("IPython")
        mezcla_root = shlex.quote(cm.get_mezcla_root_dir())
        pythonpath = f"PYTHONPATH={mezcla_root}"
        import_snippet = cm.fix_indent(
            """
            from mezcla import *;
            print(dummy_app);
            """)
        undefined_regex = "Error.*dummy_app.*not.defined"

        # Only valid for ipython with flag set (others raise expeption)
        output = gh.run(f"{pythonpath} ADD_COMMON_EXPORT=0 python -c '{import_snippet}' 2>&1")
        assert(my_re.search(undefined_regex, output))
        #
        output = gh.run(f"{pythonpath} ADD_COMMON_EXPORT=0 ipython -c '{import_snippet}' 2>&1")
        assert(my_re.search(undefined_regex, output))
        #
        output = gh.run(f"{pythonpath} ADD_COMMON_EXPORT=1 ipython -c '{import_snippet}' 2>&1")
        assert(not my_re.search(undefined_regex, output))

        return

    def test_common_exports(self):
        """Verify the regular package export contract"""
        debug.trace(4, f"TestIt.test_common_exports(); self={self}")
        assert(THE_MODULE.__all__ == ["__VERSION__"])
        return

    ## OLD:
    ## class TestIt2:
    ##     """Another class for testcase definition
    ##     Note: Needed to avoid error with pytest due to inheritance with unittest.TestCase via TestWrapper"""
    ##

    def test_version(self):
        """Test version string"""
        debug.trace(5, f"test_version(); self={self}")
        assert(hasattr(THE_MODULE, "__VERSION__"))
        assert(my_re.match(r"^\d+.\d+\.\d+.*", THE_MODULE.__VERSION__))

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
