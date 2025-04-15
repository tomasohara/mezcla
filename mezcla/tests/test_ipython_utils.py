#! /usr/bin/env python3
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
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
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

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_import_module_globals(self):
        """Test module globals import"""
        debug.trace(4, f"TestIt.test_import_module_globals(); self={self}")
        #
        # Import this module (i.e., "mezcla.ipython_utils")
        globals_dict = {}
        THE_MODULE.import_module_globals(self.script_module, globals_dict=globals_dict)
        assert ("TL" in globals_dict)
        assert ("import_module_globals" in globals_dict)
        #
        # note: following fails because the module argument needs to be text (as above)
        globals_dict = {}
        THE_MODULE.import_module_globals(THE_MODULE, globals_dict=globals_dict, ignore_errors=True)
        assert (not globals_dict)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_pr_dir(self):
        """Makes sure object directory printed"""
        # Sample output:
        #   In [67]: pr_dir(Dummy())
        #   ['__class__', '__delattr__', '__dict__', '__dir__', '__doc__', '__eq__', '__format__', '__ge__', '__getattribute__', '__getstate__', '__gt__', '__hash__', '__init__', '__init_subclass__', '__le__', '__lt__', '__module__', '__ne__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', 'dummy_member']
        #
        class Dummy():
            """Dummy class for testing pr_dir"""
            dummy_member = True
        #
        dummy_instance = Dummy()
        THE_MODULE.pr_dir(dummy_instance)
        stdout = self.get_stdout()
        assert "dummy_member" in stdout
        assert "'__class__'" in stdout

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
