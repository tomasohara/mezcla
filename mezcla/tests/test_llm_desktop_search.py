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
import atexit
from collections.abc import Iterable

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

def get_last_modified_date(iterable: Iterable) -> float|None:
            """return the newest modification date as a float, 
               or None if iterable is empty or files don't exist"""
            times = map(system.get_file_modification_time, iterable)
            result = None
            for time in times: 
                if time is None:
                    continue
                result = time if result is None or time > result else result
            return result

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    INDEX_STORE_DIR = THE_MODULE.INDEX_STORE_DIR.lstrip().lstrip(system.path_separator())        
    # set a temp dir to test index indexing
    index_temp_dir = gh.form_path(system.TEMP_DIR, INDEX_STORE_DIR)        
    index_parent = gh.form_path(index_temp_dir, "..")
    #
    # TODO: use_temp_base_dir = True            # treat TEMP_BASE as directory
    # note: temp_file defined by parent (along with script_module, temp_base, and test_num)

    @pytest.mark.skipif(not RUN_SLOW_TESTS, reason="Ignoring slow test")
    ## DEBUG: @trap_exception            # TODO: remove when debugged
    def test_01_index_dir(self):
        """Tests run_script to index directory"""
        debug.trace(4, f"TestIt.test_01_index_dir(); self={self}")
        atexit.register(gh.delete_directory(self.index_temp_dir))

        if not system.is_directory(self.index_parent):
            gh.full_mkdir(self.index_parent)
        
        # test if indexing works with with no existing db
        repo_base_dir = gh.form_path(gh.real_path(gh.dirname(__file__)),
                                     "..", "..")
        index_file = self.get_temp_file()
        
        self.run_script(options="--index",
                        data_file=repo_base_dir,
                        log_file=index_file,
                        out_file=index_file,
                        env_options=f"index_STORE_DIR={self.index_temp_dir}")
        
        index_files = system.read_directory(self.index_temp_dir)
        
        # assert INDEX_STORE_DIR is not empty
        self.do_assert(index_files != [])
        # self.do_assert(my_re.search(r"TODO-pattern", output.strip()))
        
        #save modified date for comparing later 
        prev_size = get_last_modified_date(system.get_directory_filenames(self.index_temp_dir, just_regular_files=True))
        
        # test that indexing with an already existing DB works
        resource_dir = gh.form_path(gh.real_path(gh.dirname(__file__)), "resources")
        self.run_script(options="--index",
                        data_file=resource_dir,
                        env_options=f"INDEX_STORE_DIR={self.index_temp_dir}")
        
        # get modification time and check if it changed
        new_size = get_last_modified_date(system.get_directory_filenames(self.index_temp_dir, just_regular_files=True))
        self.do_assert(new_size > prev_size)
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
    

    @pytest.mark.skipif(not RUN_SLOW_TESTS, reason="Ignoring slow test")
    def test_04_show_similar(self):
        ## TODO: WORK-IN-PROGRESS
        """Test run_script to show similar document to QUERY"""
        debug.trace(4,f"test_04_show_similar(): self={self}")
        
        index_parent = gh.form_path(self.index_temp_dir, "..")
        if not system.is_directory(index_parent):
            gh.full_mkdir(index_parent)
            
        
        # index base mezcla dir for LICENSE.txt
        mezcla_base = gh.form_path(gh.dirname(__file__), "..", "..")
        self.run_script(options="--index",
                        data_file= mezcla_base,
                        env_options=f"index_STORE_DIR={self.index_temp_dir}",
                        trace_level=6)
        
        output_file = self.get_temp_file()
        
        self.do_assert(system.is_directory(self.index_temp_dir))
        self.run_script(options="--similar LICENSE",
                                 out_file=output_file,
                                 log_file=output_file,
                                 env_options=f"INDEX_STORE_DIR={self.index_temp_dir}")
        gh.delete_directory(self.index_temp_dir)
        self.do_assert("Lesser General Public License" in system.read_file(output_file))
        




#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
