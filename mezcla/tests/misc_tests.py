#! /usr/bin/env python3
#
# Miscellaneous tests not tied to particular module.
#
# Note:
# - This is uses to check for enforce some development
#   -- A test exists for each module (e.g., tests/test_fubar.py for ./fubar.py).
#   -- Python files have execute permissions (e.g., chmod ugo+x).
#
# TODO2: Run once a week or so (e.g., to help catch poor test stubs like
# test_train_language_model.py)!
#
# TODO3:
# - Check for common pylint issues (n.b., not nitpicking ones like spacing).
#

"""Miscellaneous/non-module tests"""

# Standard packages
## TODO: from collections import defaultdict

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper, invoke_tests

# Constants
LINE_IMPORT_PYDANTIC = "from pydantic import validate_call\n"
## TODO1: don't hardcode /tmp (see below)
OUTPUT_PATH_PYDANTIC = "/tmp/temp_"
DECORATOR_VALIDATION_CALL = "@validate_call\ndef"

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
    
    def transform_for_validation(self, file_path):
        """Creates a temporary copy of the script for validation of argument calls (using pydantic)"""
        content = system.read_file(file_path)
        content = my_re.sub(r"^def", r"@validate_call\n\g<0>", content, flags=my_re.MULTILINE)
        ## Uncomment the line below (and comment the line above) if the decorators are previously used
        ## May not be compatible with scripts in mezcla/tests
        # content = my_re.sub(r"^(?:(?!\s*[@'#\']).*?)(\s*)(def )", r'\1@validate_call\n\1\2', content, flags=my_re.MULTILINE)
        ## TODO1:  something like the following (so that shebang line kept as first):
        ## my_re.sub(r"^((from \S+ )?import)", fr"\1{LINE_IMPORT_PYDANTIC}", content, flags=my_re.MULTILINE, count=1)
        content = LINE_IMPORT_PYDANTIC + content
        ## TODO2: use self.get_temp_file(): Lorenzo added new functionality
        output_path = OUTPUT_PATH_PYDANTIC + gh.basename(file_path)
        system.write_file(filename=output_path, text=content)
        return output_path
    
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
                self.do_assert(system.file_exists(test_path),
                               f"module {module} is missing tests")

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
            self.do_assert(not bad_usage, f"module {module} has bad sys.stdin.read usage")

    @pytest.mark.xfail
    def test_03_check_permissions(self):
        """Make sure modules don't use certain standard library calls directly
        Note: The mezcla equivalent should be used for sake of debugging traces"""
        debug.trace(4, "test_03_check_permissions()")
        for module in self.get_python_module_files():
            has_execute_perm = gh.run(f'ls -l "{module}" | grep ^...x..x..x')
            self.do_assert(has_execute_perm, f"module {module} is missing execute permission")

    @pytest.mark.xfail
    def test_04_check_transform_for_validation(self):
        """Make sure the transformation is successful when adding decorators for validation of function calls"""
        debug.trace(4, "test_04_check_transform_for_validation()")

        ## TODO2: use gh.resolve_path
        input_file = "../html_utils.py"
        result = self.transform_for_validation(input_file)
        ## TODO1: don't hardcode refs to /tmp 
        assert "temp" in result and "/tmp/" in result
        content = system.read_file(result)
        ## For debugging: print(content)
        assert content.startswith(LINE_IMPORT_PYDANTIC)
        assert content.count(DECORATOR_VALIDATION_CALL) >= 1

    @pytest.mark.xfail
    def test_05_usage_statements(self):
        """Make sure usage statments refer to valid arguments"""
        debug.trace(4, "test_05_usage_statements()")
        # note: addresses change like --include-header => --header in randomize_lines.py
        #   for module in ...: for usage in module usage: assert (not "test_04_usage_statements" in run_script(usage))
        self.do_assert(False, "TODO: implement")
    
#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
