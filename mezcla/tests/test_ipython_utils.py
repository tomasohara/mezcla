#! /usr/bin/env python
#
# Test(s) for ../ipython_utils.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_ipython_utils.py
#

"""Tests for ipython_utils module"""

# Standard packages
## TODO: from collections import defaultdict

# Installed packages
import pytest

# Local packages
from mezcla.unittest_wrapper import TestWrapper
from mezcla import debug
import mezcla.ipython_utils as THE_MODULE

#------------------------------------------------------------------------

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    def test_grep_obj_methods(self):
        """Test (module) object grepping"""
        debug.trace(4, f"TestIt.test_grep_obj_methods(); self={self}")
        import_functions = THE_MODULE.grep_obj_methods(THE_MODULE, "import_*")
        assert ("import_module_globals" in import_functions)
        leading_space_names = THE_MODULE.grep_obj_methods(THE_MODULE, "^ +")
        assert (not leading_space_names)
        return

    def test_import_module_globals(self):
        """Test module globals import"""
        debug.trace(4, f"TestIt.test_import_module_globals(); self={self}")
        #
        globals_dict = {}
        THE_MODULE.import_module_globals(self.script_module, globals_dict=globals_dict)
        assert ("TL" in globals_dict)
        #
        # note: following fails because the module argument needs to be text
        globals_dict = {}
        THE_MODULE.import_module_globals(THE_MODULE, globals_dict=globals_dict, ignore_errors=True)
        assert (not globals_dict)
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
