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
import os

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla.tests.common_module import SKIP_SLOW_TESTS, SKIP_SLOW_REASON

# Constants
LINE_IMPORT_PYDANTIC = "from pydantic import validate_call\n"
## TODO1: don't hardcode /tmp (see below)
## OLD: OUTPUT_PATH_PYDANTIC = "/tmp/temp_"
DECORATOR_VALIDATION_CALL = "@validate_call\ndef"
##
TEST_REGEX = system.getenv_value(
    "TEST_REGEX", None,
    "Regex for tests to include; ex: '^test_c.*' for debugging")
UNDER_UNIX = (os.name == 'posix')


class TestMisc(TestWrapper):
    """Class for test case definitions"""
    script_module= None

    def get_python_module_files(self, include_tests=False, include_archive=False, include_examples=False):
        """Return list of files for python modules.
        Optionally INCLUDE_TESTS unless configuration module like conftest.py.
        Likewise, optionally INCLUDE_EXAMPLES unless commonly used one like hf_stable_diffusion.
        Also, optionally INCLUDE_ARCHIVE."""
        debug.trace_expr(5, include_tests, include_archive, include_examples,
                    prefix="in get_python_module_files: ")
        ## OLD: all_python_modules = gh.run("find . -name '*.py'").splitlines()
        # Get all filenames for python modules in the repo (i.e., at current commit)
        # Note: only includes python files in mezcla subdir (e.g, mezcla/cut.py
        # and mezcla/tests/test_cut.py but not docs/conf.py).
        debug.assertion(system.get_current_directory().endswith("mezcla"))
        all_python_modules = gh.run(r"git ls-tree -r --name-only HEAD | grep '.*\.py$'").splitlines()
        debug.trace_values(6, all_python_modules)
        debug.assertion(system.intersection(["debug.py", "system.py"], all_python_modules))
        debug.assertion(not system.intersection(["setup.py", "conf.py"], all_python_modules))
        ok_python_modules = []

        # Make sure each module adheres to the basic conventions
        for module in all_python_modules:
            dir_path, filename = system.split_path(module)
            _parent_path, dir_proper = system.split_path(dir_path)
            include = True
            reason = "???"
            if TEST_REGEX and not my_re.search(TEST_REGEX, module):
                include = False
                reason = f"not matching test regex {TEST_REGEX!r}"
            if include and (dir_proper == "tests"):
                include = (include_tests and not filename in ["conftest.py"])
                reason = "test script"
            if include and (dir_proper == "archive"):
                include = include_archive
                reason = "archived script"
            if include and (dir_proper == "examples"):
                INCLUDED_EXAMPLES = ["hf_stable_diffusion.py", "hugging_face_translation.py", "youtube_transcript.py"]
                include = include_examples or (filename in INCLUDED_EXAMPLES)
                reason = "example script (not in {INCLUDED_EXAMPLES!r})"
            if include:
                ok_python_modules.append(module)
            else:
                debug.trace(4, f"FYI: Ignoring module {module!r}: {reason}")
        debug.trace_expr(5, ok_python_modules)
        return ok_python_modules
    
    def transform_for_validation(self, file_path):
        """Creates a temporary copy of the script for validation of argument calls (using pydantic)"""
        content = system.read_file(file_path)
        content = my_re.sub(r"^def ", r"@validate_call\n\g<0>", content, flags=my_re.MULTILINE)
        ## Uncomment the line below (and comment the line above) if the decorators are previously used
        ## May not be compatible with scripts in mezcla/tests
        ##
        ## OLD:
        ## # content = my_re.sub(r"^(?:(?!\s*[@'#\']).*?)(\s*)(def )", r'\1@validate_call\n\1\2', content, flags=my_re.MULTILINE)
        ## ## TODO1:  something like the following (so that shebang line kept as first):
        ## ## my_re.sub(r"^((from \S+ )?import)", fr"\1{LINE_IMPORT_PYDANTIC}", content, flags=my_re.MULTILINE, count=1)
        ## content = LINE_IMPORT_PYDANTIC + content
        content = my_re.sub(r"^((from \S+ )?import)", fr"{LINE_IMPORT_PYDANTIC}\n\1", content, flags=my_re.MULTILINE, count=1)
        if LINE_IMPORT_PYDANTIC not in content:
            content = LINE_IMPORT_PYDANTIC + content
        ## OLD:
        ## ## TODO2: use self.get_temp_file(): Lorenzo added new functionality
        ## output_path = OUTPUT_PATH_PYDANTIC + gh.basename(file_path)
        output_path = gh.form_path(self.get_temp_dir(), gh.basename(file_path))
        system.write_file(filename=output_path, text=content)
        return output_path
    
    @pytest.mark.xfail
    def test_01_check_for_tests(self):
        """Make sure test exists for each Python module"""
        debug.trace(4, "test_01_check_for_tests()")
        for module in self.get_python_module_files(include_tests=False):
            dir_name, filename = system.split_path(module)
            debug.trace_expr(5, module, dir_name, filename)
            include = True
            # Check for cases to skip (e.g., __init__.py)
            if filename.startswith("__"):
                include = False
            # Make sure test file exists
            if include:
                test_path = gh.form_path(dir_name, "tests", f"test_{filename}")
                self.do_assert(system.file_exists(test_path),
                               f"module {module} is missing tests")

    @pytest.mark.xfail
    def test_02_check_lib_usages(self):
        """Make sure modules don't use certain standard library calls directly
        Note: The mezcla equivalent should be used for sake of debugging traces"""
        debug.trace(4, "test_02_check_lib_usages()")
        for module in self.get_python_module_files(include_tests=False):
            module_code = system.read_file(module)
            bad_usage = False
            # Direct use of sys.stdin.read()
            # TODO3: use bash AST (e.g., to exclude comments)
            if "import sys" in module_code and "sys.stdin.read" in module_code:
                bad_usage = (module != "main.py")
                debug.trace(4, f"Direct use of sys.stdin.read in {module}")
            self.do_assert(not bad_usage, f"module {module} has bad sys.stdin.read usage")

    @pytest.mark.xfail
    def test_03_check_mezcla_convention(self):
        """Make sure modules follow various mezcla conventions
        - file execute permission, 
        - no tabs"""
        ## TODO3: python-lint alias produces no warning
        debug.trace(4, "test_03_check_permissions()")
        for module in self.get_python_module_files(include_tests=True):
            has_execute_perm = gh.run(f'ls -l "{module}" | grep ^...x..x..x')
            self.do_assert(has_execute_perm, f"module {module} is missing execute permission")
            has_tab_char = "\t" in system.read_file(module)
            self.do_assert(not has_tab_char, f"module {module} should include tab chars")

    @pytest.mark.skipif(SKIP_SLOW_TESTS, reason=SKIP_SLOW_REASON)
    @pytest.mark.xfail
    def test_04_check_transform_for_validation(self):
        """Make sure the transformation is successful when adding decorators for validation of function calls"""
        ## TODO2: have option to run scripts to check for runtime errors
        debug.trace(4, "test_04_check_transform_for_validation()")
        ## OLD: TMP_DIR = system.getenv("TMP")
        for module in self.get_python_module_files(include_tests=False):
            ## OLD:
            ## TODO2: use gh.resolve_path
            ## input_file = "../html_utils.py"
            input_file = module
            result = self.transform_for_validation(input_file)
            ## OLD:
            ## ## TODO1: don't hardcode refs to /tmp 
            ## assert "temp" in result and "/tmp/" in result
            ## OLD: assert "temp" in result and TMP_DIR in result
            content = system.read_file(result)
            ## For debugging: print(content)
            ## OLD: assert content.startswith(LINE_IMPORT_PYDANTIC)
            assert LINE_IMPORT_PYDANTIC in content
            ## OLD: assert content.count(DECORATOR_VALIDATION_CALL) >= 1
            old_content = system.read_file(input_file)
            if "\ndef " in old_content:
                assert content.count(DECORATOR_VALIDATION_CALL) >= 1
            else:
                debug.trace(4, f"FYI: Ignoring validation call check for {input_file}, which has no def's")

    @pytest.mark.skipif(SKIP_SLOW_TESTS, reason=SKIP_SLOW_REASON)
    @pytest.mark.skipif(not UNDER_UNIX, reason="Only applies to Unix")
    @pytest.mark.xfail
    def test_05_usage_statements(self):
        """Make sure usage statments refer to valid arguments"""
        debug.trace(4, "test_05_usage_statements()")
        repo_dir = gh.run("git rev-parse --show-toplevel")
        timeout_script = gh.form_path(repo_dir, "tools", "cmd.sh")
        assert system.file_exists(timeout_script)
        
        # note: checks for incomplete change like --include-header => --header in randomize_lines.py
        #   usage: randomize_lines.py [-h] [--header] [--verbose] [--seed SEED] [--percent PERCENT] [filename]
        #   Sample usage:
        #      randomize_lines.py --include-header --percent 10 ./examples/pima-indians-diabetes.csv
        for module in self.get_python_module_files(include_tests=False):
            debug.trace(4, f"Checking {module} usage")
            module_usage = gh.run(f"echo '' | {timeout_script} {module} --help")
            module_synopsis = my_re.search(r"^\s*usage:.*", module_usage)
            # note: use non-greedy search for perl-like paragraph search
            for usage in my_re.findall(r"^ *(advanced|example|s[ai]mple|typical) +usage:.*+\n\n",
                                       module_usage, flags=my_re.MULTILINE|my_re.DOTALL):
                for option in my_re.findall(r"--[\w-]+", usage):
                    self.do_assert(option in module_synopsis)

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
