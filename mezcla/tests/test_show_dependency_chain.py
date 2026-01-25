#! /usr/bin/env python3
# TODO: # -*- coding: utf-8 -*-
#
# TODO: Test(s) for ../pip_report_dependencies.py
#
# Notes:
# - Fill out TODO's below. Use numbered tests to order (e.g., test_1_usage).
# - * See test_python_ast.py for simple example of customization.
# - TODO: If any of the setup/cleanup methods defined, make sure to invoke base
#   (see examples below for setUp and tearDown).
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by unittest_wrapper.py.
# - This can be run as follows (e.g., from root of repo):
#   $ pytest ./mezcla/examples/tests/test_pip_report_dependencies.py
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

"""TODO: Tests for pip_report_dependencies module"""

# Standard modules
## TODO: from typing import Optional

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
    import mezcla.show_dependency_chain as THE_MODULE
except:
    system.print_exception_info("pip_report_dependencies import")

#------------------------------------------------------------------------

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    # note: script_module used in argument parsing sanity check (e.g., --help)
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_01_basic_yaml_output(self):
        """Verify basic YAML structure is emitted."""
        debug.trace(4, f"TestIt.test_01_basic_yaml_output(); self={self}")

        report = {
            "install": [
                {
                    "metadata": {
                        "name": "example",
                        "requires_dist": ["dep1>=1.0", "dep2"]
                    }
                }
            ]
        }

        helper = THE_MODULE.Helper()
        helper.process(report)
        output = self.get_stdout()

        self.do_assert(output.startswith("---"))
        self.do_assert("- name: example" in output)
        self.do_assert("requires_dist:" in output)
        self.do_assert("- dep1>=1.0" in output)
        self.do_assert("- dep2" in output)
        return

    def test_02_no_requires_dist(self):
        """Ensure packages without requires_dist still emit valid YAML."""
        debug.trace(4, f"TestIt.test_02_no_requires_dist(); self={self}")

        report = {
            "install": [
                {"metadata": {"name": "solo"}}
            ]
        }

        helper = THE_MODULE.Helper()
        helper.process(report)
        output = self.get_stdout()

        self.do_assert("- name: solo" in output)
        self.do_assert("requires_dist" not in output)
        return

    def test_03_empty_install(self):
        """Ensure empty install list still produces YAML header."""
        debug.trace(4, f"TestIt.test_03_empty_install(); self={self}")

        report = {"install": []}
        helper = THE_MODULE.Helper()
        helper.process(report)
        output = self.get_stdout()

        self.do_assert(output.strip() == "---")
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
