#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Test(s) for ../master_test.py
#
# Notes:
# - Fill out TODO's below. Use numbered tests to order (e.g., test_1_usage).
# - * See test_python_ast.py for simple example of customization.
# - TODO: If any of the setup/cleanup methods defined, make sure to invoke base
#   (see examples below for setUp and tearDown).
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by unittest_wrapper.py.
# - This can be run as follows (e.g., from root of repo):
#   $ pytest ./mezcla/tests/test_master_test.py
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
# Tip:
# - Make sure the tests differ from any EX-based comments in the source file:
#   they tend to be simple for sake of illustration. Moreover, they get tested
#   via evaluate_example_tests.py, leading to redundancy.
#

## TODO1: [Warning] Make sure this template adhered to as much as possible. For,
## example, only delete todo comments not regular code, unless suggested in tip.
## In particular, it is critical that script_module gets initialized properly.

"""TODO: Tests for master_test module"""

# Standard modules
## TODO: from typing import Optional

# Installed modules
import pytest

# Local modules
from mezcla import debug
## TODO: from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
## TODO: import mezcla.tests.common_module as cm ... @skipif(cm.SKIP_SLOW_TESTS, cm.SKIP_SLOW_REASON)

# Note: Two references are used for the module to be tested:
#    THE_MODULE:               module object (e.g., <module 'mezcla.main' ...>)
#    TestIt.script_module:     dotted module path (e.g., "mezcla.main")
THE_MODULE = None
try:
    import mezcla.master_test as THE_MODULE
except:
    system.print_exception_info("master_test import") 

# Note: sanity test for customization (TODO: remove if desired)
if not my_re.search(r"\btemplate.py$", __file__):
    debug.assertion("mezcla.*template" not in str(THE_MODULE))

#------------------------------------------------------------------------

class TestIt(TestWrapper):
    """Class for testcase definition"""
    # note: script_module used in argument parsing sanity check (e.g., --help)
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    #
    # TODO: use_temp_base_dir = True    # treat TEMP_BASE as dir (e.g., for simpler organization with many tests)
    # note: temp_file defined by parent (along with script_module, temp_base, and test_num)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_01_data_file(self):
        """Tests run_script w/ data file"""
        # Warning: see notes above about potential issues with run_script-based tests.
        debug.trace(4, f"TestIt.test_01_data_file(); self={self}")
        ## TODO: add uses_stdin=True to following if no file argument
        output = self.run_script(options="--run", env_options="TEST_REGEX=merge_")
        assert my_re.search(r"merge_notes.py", output.strip())
        assert my_re.search(r"merge_files.py", output.strip())
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_02_resolve_tools_file(self):
        """Test for resolve_tools_file"""
        debug.trace(4, f"TestIt.test_02_resolve_tools_file(); self={self}")
        assert THE_MODULE.resolve_tools_file("mypy.ini") == "../tools/mypy.ini"
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_03_run_tests(self):
        """Test for run_tests"""
        # Note: you might need to disable tracing during setUp (see notes above).
        debug.trace(4, f"TestIt.test_03_run_tests(); self={self}")
        failed = THE_MODULE.run_tests({"simple_main_example.py": 0.5})
        assert failed == 0
        captured = self.get_stderr()
        assert "Ignoring non-python test" in captured
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
