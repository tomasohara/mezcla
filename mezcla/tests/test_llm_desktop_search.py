#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Test(s) for ../llm_desktop_search.py
#
# Notes:
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_llm_desktop_search.py
#
# TODO1 By Lroenzo:
# - Remove the old TODO items from template.py.
# - Try to minize usage of run_script to just one or two tests:
#   it is an older style of testing. It is better to use DesktopSearch
#   class directly. More details follow in the warning.
# - See other TODO1's below (i.e., highest priority todo's).
#
# Warning:
# - The use of run_script as in test_01_data_file is an older style of testing.
#   It is better to directly invoke a helper class in the script that is independent
#   of the Script class based on Main, which is mainly for argument parsing.
#   (For an example of this, see python_ast.py and tests/tests_python_ast.py.)
# - Moreover, debugging tests with run_script is complicated because a separate
#   process is involved (e.g., with separate environment variables.)
# - See discussion of SUB_DEBUG_LEVEL in unittest_wrapper.py for more info.
# - TODO: Feel free to delete this warning as well as the related one below.
#

"""Tests for llm_desktop_search module"""

# Standard modules
## TODO: from collections import defaultdict
import atexit
## OLD: from collections.abc import Iterable

# Installed modules
import pytest

# Local modules
from mezcla.unittest_wrapper import TestWrapper, RUN_SLOW_TESTS
from mezcla.unittest_wrapper import trap_exception
from mezcla import debug
from mezcla import glue_helpers as gh
from  mezcla import gpu_utils
from mezcla.main import KEEP_TEMP_FILES
from mezcla.my_regex import my_re
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                        global module object
#    TestIt.script_module:              path to file
import mezcla.llm_desktop_search as THE_MODULE
get_last_modified_date = THE_MODULE.get_last_modified_date

#------------------------------------------------------------------------

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    INDEX_STORE_DIR = THE_MODULE.INDEX_STORE_DIR.lstrip().lstrip(system.path_separator())
    use_temp_base_dir = True            # needed for self.temp_base to be a dir
    
    # set a temp dir to test index indexingL setUpClass
    # Note: index_temp_dir needs to be unique
    ## OLD: index_temp_dir = gh.form_path(system.TEMP_DIR, INDEX_STORE_DIR)
    index_temp_dir = None
    index_parent = None

    @classmethod
    def setUpClass(cls, filename=None, module=None):
        """One-time initialization (i.e., for entire class)"""
        # note: creates default FAISS index shared by tests (unless overriden)
        debug.trace(6, f"TestIt.setUpClass(); cls={cls}")
        # note: should do parent processing first
        super().setUpClass(filename, module)
        cls.index_temp_dir = gh.form_path(cls.temp_base, "llm-desktop-index")
        cls.index_parent = gh.form_path(cls.index_temp_dir, "..")
        debug.trace_object(5, cls, label=f"{cls.__class__.__name__} instance")
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    @pytest.mark.skipif(not RUN_SLOW_TESTS, reason="Ignoring slow test")
    ## DEBUG: @trap_exception            # TODO: remove when debugged
    def test_01_index_dir(self):
        """Tests run_script to index directory"""
        # Warning: see notes above about potential issues with run_script-based tests.
        debug.trace(4, f"TestIt.test_01_index_dir(); self={self}")
        if not KEEP_TEMP_FILES:
            atexit.register(gh.delete_directory(self.index_temp_dir))

        if not system.is_directory(self.index_parent):
           debug.assertion(False)
           gh.full_mkdir(self.index_parent)
        
        # test if indexing works with with no existing db
        repo_base_dir = gh.form_path(gh.real_path(gh.dirname(__file__)),
                                     "..", "..")
        # TODO1: clarify what this should get (made stderr below)
        ## OLD: index_file = self.get_temp_file()
        
        self.run_script(options=f"--index {repo_base_dir}",
                        ## TODO1: note: files shouldn't be the same (stdout and stderr)
                        ## likewise below; output usually gotten from result
                        ## OLD: log_file=index_file,
                        ## OLD: out_file=index_file,
                        env_options=f"INDEX_STORE_DIR={self.index_temp_dir}")
        
        index_files = system.read_directory(self.index_temp_dir)
        
        # assert INDEX_STORE_DIR is not empty
        self.do_assert(index_files != [])
        # self.do_assert(my_re.search(r"TODO-pattern", output.strip()))
        
        #save modified date for comparing later 
        prev_size = get_last_modified_date(system.get_directory_filenames(self.index_temp_dir, just_regular_files=True))
        
        # test that indexing with an already existing DB works
        resource_dir = gh.form_path(gh.real_path(gh.dirname(__file__)), "resources")
        self.run_script(options=f"--index {resource_dir}",
                        env_options=f"INDEX_STORE_DIR={self.index_temp_dir}")
        
        # get modification time and check if it changed
        # TODO1: new_size to new_time; likewise for prev_time
        new_size = get_last_modified_date(system.get_directory_filenames(self.index_temp_dir, just_regular_files=True))
        self.do_assert(new_size > prev_size)
        

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
    @pytest.mark.skipif(gpu_utils.TORCH_DEVICE != "cuda", reason="Ignoring non-CUDA device")
    @pytest.mark.skipif(not RUN_SLOW_TESTS, reason="Ignoring slow test")
    def test_03_gpu_usage(self):
        """Test for GPU libs being used"""
        # Note: verifies process using GPU via nvida-smi
        #  |  GPU   GI   CI        PID   Type   Process name                            GPU Memory |
        #  ...
        #  |    0   N/A  N/A   1111609      C   python                                      366MiB |
        debug.trace(4, f"TestIt.test_03_gpu_usage(); self={self}")
        ds = THE_MODULE.DesktopSearch()
        ds.show_similar("license")
        trace_level = max(1, debug.get_level())
        gpu_utils.trace_gpu_usage(level=trace_level)
        stdout, stderr = self.get_stdout_stderr()
        self.do_assert("GNU" in stdout) 
        ## OLD: self.do_assert("tensorflow" in stderr)
        pid = system.get_process_id()
        self.do_assert(my_re.search(fr"\b{pid}\b.*python", stderr))
        return
    

    @pytest.mark.xfail                   # TODO: remove xfail
    @pytest.mark.skipif(not RUN_SLOW_TESTS, reason="Ignoring slow test")
    def test_04_show_similar(self):
        """Test run_script to show similar document to QUERY"""
        debug.trace(4, f"test_04_show_similar(): self={self}")
        
        index_parent = gh.form_path(self.index_temp_dir, "..")
        if not system.is_directory(index_parent):
           debug.assertion(False)
           gh.full_mkdir(index_parent)
   
        # index base mezcla dir for LICENSE.txt
        mezcla_base = gh.form_path(gh.dirname(__file__), "..", "..")
        self.run_script(options=f"--index {mezcla_base}",
                        env_options=f"INDEX_STORE_DIR={self.index_temp_dir}",
                        trace_level=6)
        
        self.do_assert(system.is_directory(self.index_temp_dir))
        output = self.run_script(options="--similar LICENSE",
                                 env_options=f"INDEX_STORE_DIR={self.index_temp_dir}")
        if not KEEP_TEMP_FILES:
            gh.delete_directory(self.index_temp_dir)
        self.do_assert("Lesser General Public License" in system.read_file(output))
        

    @pytest.mark.xfail                   # TODO: remove xfail
    @pytest.mark.skipif(not RUN_SLOW_TESTS, reason="Ignoring slow test")
    @trap_exception                      # TODO: remove when debugged
    def test_05_index_via_API(self):
        """Run indexing via class-based API"""
        debug.trace(4, f"test_05_index_via_API(): self={self}")
        
        # Index the files
        # note: index is specific to this test case
        temp_index_dir = gh.form_path(self.temp_base, "index")
        test_dir = gh.dirname(__file__)
        doc_dir = gh.resolve_path("resources", base_dir=test_dir)
        ds = THE_MODULE.DesktopSearch(index_store_dir=temp_index_dir)
        ds.index_dir(doc_dir)

        # Make sure most of expected content got indexed included (e.g., 75%)
        #
        # Note: document contents check as follows
        # In [67]: docid = db.index_to_docstore_id[0];  db.docstore.search(docid).page_content
        # Out[67]: 'Tío Tomás\t\t\t\tUncle Tom\n\n¡Buenos días!\t\t\t\tGood morning\n\nçãêâôöèäàÃëÇÂîòïÔìðÊÅåùÀŠý\t\tcaeaooeaaAeCAioiOioEAauASy'
        #
        expected_text = ["Tío Tomás", "Library", "validation", "Iris", "Argentina"]
        num_total = len(expected_text)
        num_found = 0
        for text in expected_text:
           for docid in ds.db.index_to_docstore_id.values():
              if text in ds.db.docstore.search(docid).page_content:
                 num_found += 1
                 break
        pct_75 = (3 * num_total // 4)
        debug.trace_expr(5, num_found, num_total, pct_75)
        assert(num_found >= pct_75)

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
