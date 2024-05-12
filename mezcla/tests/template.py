#! /usr/bin/env python
# TODO: # -*- coding: utf-8 -*-
#
# TODO: Test(s) for ../<module>.py
#
# Notes:
# - Fill out TODO's below. Use numbered tests to order (e.g., test_1_usage).
# - * See test_python_ast.py for simple example of customization.
# - TODO: If any of the setup/cleanup methods defined, make sure to invoke base
#   (see examples below for setUp and tearDown).
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by unittest_wrapper.py.
# - This can be run as follows (e.g., from root of repo):
#   $ pytest ./mezcla/tests/test_<module>.py
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


## TODO1: [Warning] Make sure this template adhered to as much as possible. For,
## example, only delete todo comments not regular code, unless suggested in tip).
## In particular, it is critical that script_module gets initialized properly.

"""TODO: Tests for <module> module"""

# Standard modules
## TODO: from collections import defaultdict

# Installed modules
import pytest

# Local modules
from mezcla.unittest_wrapper import TestWrapper
## TODO: from mezcla.unittest_wrapper import trap_exception
from mezcla import debug
## TODO: from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                        global module object
#    TestIt.script_module:              path to file
## TODO (vvv): insert new module name in commented out template teo lines below
THE_MODULE = None         ## TODO: remove this line: avoids <module> syntax error in next)
## import mezcla.<module> as THE_MODULE   ## TODO: uncomment this line (<<<)
## TODO (^^^): use modified line above
#
# Note: sanity test for customization (TODO: remove if desired)
if not my_re.search(__file__, r"\btemplate.py$"):
    debug.assertion("mezcla.template" not in str(THE_MODULE))

## TODO:
## # Environment options
## # Note: These are just intended for internal options, not for end users.
## # It also allows for enabling options in one place.
## #
## FUBAR = system.getenv_bool(
##     "FUBAR", False,
##     description="Fouled Up Beyond All Recognition processing")

#------------------------------------------------------------------------

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    #
    # TODO: use_temp_base_dir = True            # treat TEMP_BASE as directory
    # note: temp_file defined by parent (along with script_module, temp_base, and test_num)

    ## TODO: optional setup methods
    ##
    ## @classmethod
    ## def setUpClass(cls, filename=None, module=None):
    ##     """One-time initialization (i.e., for entire class)"""
    ##     debug.trace(6, f"TestIt.setUpClass(); cls={cls}")
    ##     # note: should do parent processing first
    ##     super().setUpClass(filename, module)
    ##     ...
    ##     debug.trace_object(5, cls, label=f"{cls.__class__.__name__} instance")
    ##     return
    ##
    ## def setUp(self):
    ##     """Per-test setup"""
    ##     debug.trace(6, f"TestIt.setUp(); self={self}")
    ##     # note: must do parent processing first (e.g., for temp file support)
    ##     super().setUp()
    ##     ...
    ##     # TODO: debug.trace_current_context(level=debug.QUITE_DETAILED)
    ##     return

    @pytest.mark.xfail                   # TODO: remove xfail
    ## DEBUG: @trap_exception            # TODO: remove when debugged
    def test_01_data_file(self):
        """Tests run_script w/ data file"""
        # Warning: see notes above about potential issues with run_script-based tests.
        debug.trace(4, f"TestIt.test_01_data_file(); self={self}")
        data = ["TODO1", "TODO2"]
        system.write_lines(self.temp_file, data)
        ## TODO: add use_stdin=True to following if no file argument
        output = self.run_script(options="", data_file=self.temp_file)
        self.do_assert(my_re.search(r"TODO-pattern", output.strip()))
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    ## DEBUG: @trap_exception            # TODO: remove when debugged
    def test_02_something_else(self):
        """Test for something_else: TODO..."""
        debug.trace(4, f"TestIt.test_02_something_else(); self={self}")
        self.do_assert(False, "TODO: implement")
        ## ex: self.do_assert(THE_MODULE.TODO_function() == TODO_value)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_03_whatever(self):
        """TODO: flesh out test for whatever (capsys-like)"""
        debug.trace(4, f"TestIt.test_03_whatever(); self={self}")
        THE_MODULE.TODO_whatever()
        captured = self.get_stderr()
        self.do_assert("whatever" in captured, "TODO_whatever trace")
        return

    ## TODO: optional cleanup methods
    ##
    ## def tearDown(self):
    ##     debug.trace(6, f"TestIt.tearDown(); self={self}")
    ##     super().tearDownClass()
    ##     ...
    ##     return
    ##
    ## @classmethod
    ## def tearDownClass(cls):
    ##     debug.trace(6, f"TestIt.tearDownClass(); cls={cls}")
    ##     super().tearDown()
    ##     ...
    ##     return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    ## TODO2: here and elsewhere: invoke_tests(__file__)
    pytest.main([__file__])
