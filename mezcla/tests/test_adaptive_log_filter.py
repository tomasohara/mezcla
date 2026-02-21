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
DUMMY_UNFILTERED_CONTENTS = """
    Start
    Data files:
        /a/b/c/d/e/f.data
        /a/b/c/d/e/g.data
        /a/b/c/d/e/h.data
        /a/b/c/d.data
        /a/b/c.data
    Progress 0.00%\rProgress 25.00%\rProgress 50.00%\rProgress 75.00%\rProgress 100.00%
    End
"""
DUMMY_FILTERED_CONTENTS = """
    Path substitution legend:
        {path1}: /a/b/c/d/e/
    Start
    Data files:
        {path1}f.data
        {path1}g.data
        {path1}h.data
        /a/b/c/d.data
        /a/b/c.data
    Progress 100.00%
    End
"""

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
        """Verify that tqdm-style \r lines are collapsed correctly."""
        refiner = THE_MODULE.LogRefiner(collapse=True)
        input_data = [
            "Step 1: [==  ]\rStep 1: [====]\rStep 1: Done",
            "Compiling...",
            "Download: 50%\rDownload: 100%"
        ]
        result = refiner.process(input_data)
        
        # Using pytest style assertions
        assert len(result) == 3
        assert result[0] == "Step 1: Done"
        assert result[1] == "Compiling..."
        assert result[2] == "Download: 100%"

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_03_adaptive_paths(self):
        """Verify long nested paths are tokenized."""
        # Note: Path must be > 40 chars and have > 4 levels to match current regex
        p4a_path = "/home/user/project/.buildozer/android/platform/build-arm64-v8a/build/"
        refiner = THE_MODULE.LogRefiner(adaptive=True)
        
        input_data = [
            f"Entering {p4a_path}subdir1",
            f"Leaving {p4a_path}subdir1",
            "A short path /tmp/log"
        ]
        
        result = refiner.process(input_data)
        
        # Verify the adaptive identification worked
        assert p4a_path in refiner.path_map
        assert refiner.path_map[p4a_path] == "{path1}"
        assert "{path1}subdir1" in result[0]
        # Verify short path was NOT tokenized
        assert "/tmp/log" in result[2]

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_04_sampling_fidelity(self):
        """Verify head/tail sampling preserves error messages."""
        refiner = THE_MODULE.LogRefiner(sample=True)
        
        # Create 5000 lines, place an error in the "middle" (which usually gets snipped)
        input_data = [f"Line {i}" for i in range(5000)]
        critical_error = "CRITICAL FAILURE: Build interrupted by signal 9"
        input_data[2500] = critical_error
        
        result = refiner.process(input_data)
        
        # Assertions
        assert len(result) < 5000
        assert any(critical_error in line for line in result)
        assert any("SNIP" in line for line in result)
        assert result[0] == "Line 0"
        assert result[-1] == "Line 4999"
    
#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
