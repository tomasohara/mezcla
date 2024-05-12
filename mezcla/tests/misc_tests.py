#! /usr/bin/env python
#
# Miscellaneous tests not tied to particular module.
#
# Note:
# - This is uses to check for enforce some development
#   -- A test exists for each module (e.g., tests/test_fubar.py for ./fubar.py).
#   -- Python files have execute permissions (e.g., chmod ugo+x).
#

"""Miscellaneous/non-module tests"""

# Standard packages
## TODO: from collections import defaultdict

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
## TODO: from mezcla.my_regex import my_re
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper

class TestMisc(TestWrapper):
    """Class for test case definitions"""
    script_module= None

    def get_python_module_files(self, include_tests=False):
        """Return list of files for python modules, optionally with INCLUDE_TESTS"""
        all_python_modules = gh.run("find . -name '*.py'").splitlines()
        ok_python_modules = []
        for module in all_python_modules:
            dir_path, _filename = system.split_path(module)
            _parent_path, dir_proper = system.split_path(dir_path)
            include = True
            if (dir_proper == "tests"):
                include = include_tests
            if include:
                ok_python_modules.append(module)
        debug.trace_expr(5, ok_python_modules)
        return ok_python_modules
    
    @pytest.mark.xfail
    def test_01_check_for_tests(self):
        """Make sure test exists for each Python module"""
        debug.trace(4, "test_01_check_for_tests()")
        for module in self.get_python_module_files():
            dir_name, filename = system.split_path(module)
            include = True
            # Check for cases to skip (e.g., __init__.py)
            if not filename.startswith("__"):
                include = False
            # Make sure test file exists
            if include:
                test_path = gh.form_path(dir_name, f"test_{filename}")
                self.do_assert(system.file_exists(test_path))

    @pytest.mark.xfail
    def test_02_check_lib_usages(self):
        """Make sure modules don't use certain standard library calls directly
        Note: The mezcla equivalent should be used for sake of debugging traces"""
        debug.trace(4, "test_02_check_lib_usages()")
        for module in self.get_python_module_files():
            module_code = system.read_file(module)
            bad_usage = False
            # Direct use of sys.stdin.read()
            # TODO3: use bash AST (e.g., to exclude comments)
            if "import sys" in module_code and "sys.stdin.read" in module_code:
                bad_usage = (module != "main.py")
                debug.trace(4, f"Direct use of sys.stdin.read in {module}")
            self.do_assert(not bad_usage)

    @pytest.mark.xfail
    def test_03_check_permissions(self):
        """Make sure modules don't use certain standard library calls directly
        Note: The mezcla equivalent should be used for sake of debugging traces"""
        debug.trace(4, "test_03_check_permissions()")
        for module in self.get_python_module_files():
            has_execute_perm = gh.run(f'ls -l "{module}" | grep ^...x..x..x')
            self.do_assert(has_execute_perm)

    @pytest.mark.xfail
    def test_04_usage_statements(self):
        """Make sure usage statments refer to valid arguments"""
        debug.trace(4, "test_04_usage_statements()")
        # note: addresses change like --include-header => --header in randomize_lines.py
        #   for module in ...: for usage in module usage: assert (not "test_04_usage_statements" in run_script(usage))
        self.do_assert(False, "TODO: implement")
