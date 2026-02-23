#! /usr/bin/env python3
# TODO: # -*- coding: utf-8 -*-
#
# Test(s) for ../adaptive_log_filter.py
#
# Notes:
# - This can be run as follows (e.g., from root of repo):
#   $ pytest mezcla/tests/test_adaptive_log_filter.py
# - Initial version produced with Gemini-3-Pro.
#

"""Tests for adaptive_log_filter module"""

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
from mezcla.tests.common_module import fix_indent

# Note: Two references are used for the module to be tested:
#    THE_MODULE:               module object (e.g., <module 'mezcla.main' ...>)
#    TestIt.script_module:     dotted module path (e.g., "mezcla.main")
THE_MODULE = None
try:
    import mezcla.adaptive_log_filter as THE_MODULE
    pass                                ## TODO: delete
except:
    system.print_exception_info("adaptive_log_filter import") 

# Note: sanity test for customization (TODO: remove if desired)
if not my_re.search(r"\btemplate.py$", __file__):
    debug.assertion("mezcla.*template" not in str(THE_MODULE))

## TODO:
## # Environment options
## # Note: These are just intended for internal options, not for end users.
## # It also allows for enabling options in one place.
## #
## FUBAR = system.getenv_bool(
##     "FUBAR", False,
##     description="Fouled Up Beyond All Recognition processing")

# Constants
# Note: modeled after pyside-tools/android_deploy.py buildozer log output
BUILDOZER_BASE = "/home/user/project/.buildozer/android/platform/build-arm64-v8a/build/other_builds/python3/"
DUMMY_UNFILTERED_CONTENTS = """
    \x1b[1m[INFO]\x1b[0m:    python3 has no prebuild_arm64_v8a, skipping
    \x1b[1m\x1b[90m[DEBUG]\x1b[39m\x1b[0m:   \tchecking for sys/time.h... yes
    \x1b[1m\x1b[90m[DEBUG]\x1b[39m\x1b[0m:   \tgcc -c -I{path}Include -o foo.o {path}foo.c
    \x1b[1m\x1b[90m[DEBUG]\x1b[39m\x1b[0m:   \tgcc -c -I{path}Include -o bar.o {path}bar.c
    \x1b[1m[INFO]\x1b[0m:    - copy ./PySide6/Qt/lib/libQt6Sql_arm64-v8a.so
    Compiling '{path}Lib/asyncio/log.py'...
    Progress 0.00%\rProgress 25.00%\rProgress 50.00%\rProgress 75.00%\rProgress 100.00%
    \x1b[1m[INFO]\x1b[0m:    - copy ./PySide6/Qt/translations/qt_zh_TW.qm
""".replace("{path}", BUILDOZER_BASE)
DUMMY_FILTERED_CONTENTS = """
    Substitution legend:
        {{path1}}: {path}
    [INFO]:    python3 has no prebuild_arm64_v8a, skipping
    [DEBUG]:   \tchecking for sys/time.h... yes
    [DEBUG]:   \tgcc -c -I{{path1}}Include -o foo.o {{path1}}foo.c
    [DEBUG]:   \tgcc -c -I{{path1}}Include -o bar.o {{path1}}bar.c
    [INFO]:    - copy ./PySide6/Qt/lib/libQt6Sql_arm64-v8a.so
    Compiling '{{path1}}Lib/asyncio/log.py'...
    Progress 100.00%
    [INFO]:    - copy ./PySide6/Qt/translations/qt_zh_TW.qm
""".replace("{path}", BUILDOZER_BASE).replace("{{path1}}", "{path1}")

#------------------------------------------------------------------------

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
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
        contents = fix_indent(DUMMY_UNFILTERED_CONTENTS)
        expected = fix_indent(DUMMY_FILTERED_CONTENTS)
        temp_file = self.create_temp_file(contents)
        ## TODO: add uses_stdin=True to following if no file argument
        actual = self.run_script(options="--collapse --adaptive", env_options="TODO_ENV=VAL",
                                 data_file=temp_file)
        assert(expected.strip() == actual.strip())
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_02_collapse_logic(self):
        """Verify that tqdm-style \\r lines are collapsed and ANSI codes stripped."""
        refiner = THE_MODULE.LogRefiner(collapse=True)
        input_data = [
            "Step 1: [==  ]\rStep 1: [====]\rStep 1: Done",
            "\x1b[1m\x1b[90m[DEBUG]\x1b[39m\x1b[0m:   \tCompiling...",
            "Download: 50%\rDownload: 100%"
        ]
        result = refiner.process(input_data)
        
        # Using pytest style assertions
        assert len(result) == 3
        assert result[0] == "Step 1: Done"
        assert result[1] == "[DEBUG]:   \tCompiling..."
        assert result[2] == "Download: 100%"

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_03_adaptive_paths(self):
        """Verify long nested buildozer paths are tokenized."""
        # Note: Path must be > 40 chars and have > 4 levels to match current regex
        # Note: regex finds all sub-paths; sorted longest first for substitution
        p4a_base = "/home/user/project/.buildozer/android/platform/build-arm64-v8a/build/other_builds/python3/"
        refiner = THE_MODULE.LogRefiner(adaptive=True)
        
        input_data = [
            f"[DEBUG]:   \tgcc -I{p4a_base}Include -o foo.o {p4a_base}foo.c",
            f"[DEBUG]:   \tgcc -I{p4a_base}Include -o bar.o {p4a_base}bar.c",
            "[INFO]:    - copy ./PySide6/Qt/lib/libQt6Sql.so"
        ]
        
        result = refiner.process(input_data)
        
        # Verify the adaptive identification worked
        assert p4a_base in refiner.path_map
        token = refiner.path_map[p4a_base]
        assert token in result[0]
        # Verify short relative path was NOT tokenized
        assert "./PySide6/Qt/lib/libQt6Sql.so" in result[2]

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_04_sampling_fidelity(self):
        """Verify head/tail sampling preserves error messages but not [DEBUG] lines."""
        refiner = THE_MODULE.LogRefiner(sample=True)
        
        # Create 5000 lines of [DEBUG] output (like real buildozer log), place error in middle
        input_data = [f"[DEBUG]:   \tLine {i}" for i in range(5000)]
        critical_error = "SyntaxError: unknown encoding: uft-8"
        input_data[2500] = critical_error
        
        result = refiner.process(input_data)
        
        # Assertions
        assert len(result) < 5000
        assert any(critical_error in line for line in result)
        assert any("SNIP" in line for line in result)
        assert result[0] == "[DEBUG]:   \tLine 0"
        assert result[-1] == "[DEBUG]:   \tLine 4999"

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_05_substr_detection(self):
        """Verify that frequent substrings are detected and substituted."""
        refiner = THE_MODULE.LogRefiner(substr=True)

        # Simulate compiler flags with long repeated substrings
        flag_prefix = "-I/home/user/project/build/arm64-v8a"
        input_data = [
            f"gcc -c {flag_prefix}/include1 -o foo.o {flag_prefix}/src1/foo.c",
            f"gcc -c {flag_prefix}/include2 -o bar.o {flag_prefix}/src2/bar.c",
            f"gcc -c {flag_prefix}/include3 -o baz.o {flag_prefix}/src3/baz.c",
            f"gcc -c {flag_prefix}/include1 -o qux.o {flag_prefix}/src1/qux.c",
            f"gcc -c {flag_prefix}/include2 -o abc.o {flag_prefix}/src2/abc.c",
            "[INFO]:    - copy ./PySide6/Qt/lib/libQt6Sql.so"
        ]

        result = refiner.process(input_data)

        # Verify a substitution was made for the common prefix
        assert len(refiner.substr_map) > 0
        # At least one token should appear in the output
        tokens = list(refiner.substr_map.values())
        assert any(tok in line for line in result for tok in tokens)
        # Short unrelated line should NOT be affected
        assert "./PySide6/Qt/lib/libQt6Sql.so" in result[-1]
    
#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
