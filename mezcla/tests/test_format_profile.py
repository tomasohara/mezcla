#! /usr/bin/env python
#
# Tests for format_profile module
#
# Notes:
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_train_language_model.py 

"""Tests for format_profile module"""

# Standard packages
import re

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper

class TestFormatProfile(TestWrapper):
    """Class for testcase definition"""
    script_file = TestWrapper.get_module_file_path(__file__)
    script_module = TestWrapper.get_testing_module_name(__file__)
    use_temp_base_dir = True    # treat TEMP_BASE as directory
    # For testing, let the dir be ./mezcla/mezcla/tests

    def test_formatprofile_PK_calls(self):
        key_arg = "calls"
        testing_script = "test_glue_helpers.py"
        SAMPLE_OUTPUT = "        1    0.000    0.000    0.000    0.000 <frozen importlib._bootstrap>:881(_find_spec_legacy)"
        
        debug.trace(4, f"test_formatprofile_PK_calls(); self={self}")
        empty_file1 = gh.get_temp_file()
        profile_log  = gh.get_temp_file()
        test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"

        gh.run(test_command_1)
        gh.run(test_command_2)

        output = gh.read_file(empty_file1)
        assert (SAMPLE_OUTPUT in output)
        return
    

    def test_formatprofile_PK_cumulative(self):
        key_arg = "cumulative"
        testing_script = "test_glue_helpers.py"
        SAMPLE_OUTPUT = "        1    0.000    0.000    0.000    0.000 __init__.py:1336(<listcomp>)"
        
        debug.trace(4, f"test_formatprofile_PK_cumulative(); self={self}")
        empty_file1 = gh.get_temp_file()
        profile_log  = gh.get_temp_file()
        test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"

        gh.run(test_command_1)
        gh.run(test_command_2)

        output = gh.read_file(empty_file1)
        assert (SAMPLE_OUTPUT not in output)
        return
    
    def test_formatprofile_PK_cumtime(self):
        key_arg = "cumtime"
        testing_script = "test_glue_helpers.py"
        SAMPLE_OUTPUT = "        1    0.000    0.000    0.000    0.000 main.py:397(<genexpr>)"
        
        debug.trace(4, f"test_formatprofile_PK_cumtime(); self={self}")
        empty_file1 = gh.get_temp_file()
        profile_log  = gh.get_temp_file()
        test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"

        gh.run(test_command_1)
        gh.run(test_command_2)

        output = gh.read_file(empty_file1)
        assert (SAMPLE_OUTPUT in output)
        return

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])