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
from mezcla.unittest_wrapper import TestWrapper, RUN_SLOW_TESTS
## TODO: from mezcla.unittest_wrapper import trap_exception
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                        global module object
#    TestIt.script_module:              path to file
import mezcla.llm_desktop_search as THE_MODULE

#------------------------------------------------------------------------

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    #
    # TODO: use_temp_base_dir = True            # treat TEMP_BASE as directory
    # note: temp_file defined by parent (along with script_module, temp_base, and test_num)

    @pytest.mark.skipif(not RUN_SLOW_TESTS, reason="Ignoring slow test")
    ## DEBUG: @trap_exception            # TODO: remove when debugged
    def test_01_index_dir(self):
        """Tests run_script to index directory"""
        debug.trace(4, f"TestIt.test_01_index_dir(); self={self}")
        # set a temp dir to test faiss indexing
        faiss_temp_dir = gh.form_path(system.TEMP_DIR,THE_MODULE.FAISS_STORE_DIR)        
        faiss_parent = gh.form_path(faiss_temp_dir, "..")
        if not system.is_directory(faiss_parent):
            gh.full_mkdir(faiss_parent)
        
        # test if indexing works with with no existing db
        repo_base_dir = gh.form_path(gh.real_path(gh.dirname(__file__)),
                                     "..", "..")
        
        output = self.run_script(options=f"--index {repo_base_dir}")
        self.do_assert(system.is_directory(faiss_temp_dir))
        # self.do_assert(my_re.search(r"TODO-pattern", output.strip()))
        
        # test that indexing with an already existing DB works
        prev_size = map(system.get_directory_filenames())
        resource_dir = gh.form_path(gh.real_path(gh.dirname(__file__)), "resources")
        output = self.run_script(options=f"--index {resource_dir}")
        
        
        # self.do_assert(my_re.search(r"TODO-pattern", output.strip()))
        
        
    @pytest.mark.skipif(not RUN_SLOW_TESTS, reason="Ignoring slow test")
    @pytest.mark.xfail                   # TODO: remove xfail
    ## DEBUG: @trap_exception            # TODO: remove when debugged
    def test_02_search_docs(self):
        """Test for something_else: TODO..."""
        debug.trace(4, f"TestIt.test_02_search_docs(); self={self}")
        output = self.run_script(options="--search 'What license is used?'")
        self.do_assert(my_re.search(r"GNU", output.strip()))
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_03_gpu_usage(self):
        """Test for GPU libs being used"""
        debug.trace(4, f"TestIt.test_03_gpu_usage(); self={self}")
        ds = THE_MODULE.DesktopSearch()
        ds.show_similar("license")
        stdout, stderr = self.get_stdout_stderr()
        self.do_assert("GNU" in stdout) 
        self.do_assert("tensorflow" in stderr)
        return
    
    def test_04_show_similar(self):
        """Test run_script to show similar document to QUERY"""
        debug.trace(4,f"test_04_show_similar(): self={self}")
        
        # index base mezcla dir for LICENSE.txt
        mezcla_base = gh.form_path(gh.dirname(__file__), "..", "..")
        self.run_script(options=f"--index {mezcla_base}")
        
        output = self.run_script(options=f"--similar LICENSE")
        assert output == ''
        
        
        

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
