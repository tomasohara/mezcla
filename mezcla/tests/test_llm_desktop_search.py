#! /usr/bin/env python
# TODO: # -*- coding: utf-8 -*-
#
# TODO: Test(s) for ../llm_desktop_search.py
#
# Notes:
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_llm_desktop_search.py
#

"""Tests for llm_desktop_search module"""

# Standard modules
## TODO: from collections import defaultdict

# Installed modules
import pytest

# Local modules
from mezcla.unittest_wrapper import TestWrapper
## TODO: from mezcla.unittest_wrapper import trap_exception
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                        global module object
#    TestIt.script_module:              path to file
import mezcla.llm_desktop_search as THE_MODULE
#
# Note: sanity test for customization (TODO: remove if desired)
if not my_re.search(__file__, r"\btemplate.py$"):
    debug.assertion("mezcla.template" not in str(THE_MODULE))

## TODO:
## # Environment options
## # Note: These are just intended for internal options, not for end users.
## # It also allows for enabling options in one place.
## #
## FUBAR = system.getenv_bool("FUBAR", False,
##                            description="Fouled Up Beyond All Recognition processing")

#------------------------------------------------------------------------

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    #
    # TODO: use_temp_base_dir = True            # treat TEMP_BASE as directory
    # note: temp_file defined by parent (along with script_module, temp_base, and test_num)

    @pytest.mark.xfail                   # TODO: remove xfail
    ## DEBUG: @trap_exception            # TODO: remove when debugged
    def test_01_index_dir(self):
        """Tests run_script to index directory"""
        debug.trace(4, f"TestIt.test_01_index_dir(); self={self}")
        system.write_lines(self.temp_file, data)
        repo_base_dir = gh.form_path(gh.real_path(gh.dirname(__file__)),
                                     "..", "..")
        output = self.run_script(options=f"--index {repo_base_dir}")
        self.do_assert(my_re.search(r"TODO-pattern", output.strip()))
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    ## DEBUG: @trap_exception            # TODO: remove when debugged
    def test_02_search_docs(self):
        """Test for something_else: TODO..."""
        debug.trace(4, f"TestIt.test_02_search_docs(); self={self}")
        output = self.run_script(options=f"--search 'What license is used?'")
        self.do_assert(my_re.search(r"GNU", output.strip()))
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_02_whatever(self):
        """TODO: flesh out test for whatever (capsys-like)"""
        debug.trace(4, f"TestIt2.test_02_whatever(); self={self}")
        THE_MODULE.TODO_whatever()
        captured = self.get_stderr()
        self.do_assert("whatever" in captured, "TODO_whatever trace")
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
