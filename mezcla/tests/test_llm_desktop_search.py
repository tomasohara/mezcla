#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Test(s) for ../llm_desktop_search.py
#
# Notes:
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_llm_desktop_search.py
#
# TODO3:
# - Try to minize usage of run_script to just one or two tests:
#   it is an older style of testing. It is better to use DesktopSearch
#   class directly. More details follow in the warning.
#
# Warning:
# - The use of run_script as in test_01_data_file is an older style of testing.
#   It is better to directly invoke a helper class in the script that is independent
#   of the Script class based on Main, which is mainly for argument parsing.
#   (For an example of this, see python_ast.py and tests/tests_python_ast.py.)
# - Moreover, debugging tests with run_script is complicated because a separate
#   process is involved (e.g., with separate environment variables).
# - See discussion of SUB_DEBUG_LEVEL in unittest_wrapper.py for more info.
#

"""Tests for llm_desktop_search module"""

# Standard modules
import atexit

# Installed modules
import pytest

# Local modules
from mezcla.unittest_wrapper import TestWrapper, RUN_SLOW_TESTS, invoke_tests
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import gpu_utils
from mezcla.main import KEEP_TEMP_FILES
from mezcla.my_regex import my_re
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                        module instance (e.g,, <module 'mezcla.main' from '/home/testuser/Mezcla/mezcla/main.py'>
#    TestIt.script_module:              dotted module path (e.g., "mezcla.main")
try:
    import mezcla.llm_desktop_search as THE_MODULE
    get_last_modified_date = THE_MODULE.get_last_modified_date
except:
    THE_MODULE = None
    get_last_modified_date = None
    debug.trace_exception(3, "llm_desktop_search import")

#------------------------------------------------------------------------


@pytest.mark.skipif(not THE_MODULE, reason="Unable to load module")
class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    INDEX_STORE_DIR = (THE_MODULE.INDEX_STORE_DIR.lstrip().lstrip(system.path_separator())
                       if THE_MODULE else None)
    use_temp_base_dir = True            # needed for self.temp_base to be a dir
    
    # set a temp dir to test index indexing setUpClass
    # Note: index_temp_dir needs to be unique
    index_temp_dir = None
    index_parent = None

    @classmethod
    def setUpClass(cls, filename=None, module=None):
        """One-time initialization (i.e., for entire class)"""
        # note: creates default FAISS index shared by tests (unless overriden)
        debug.trace(6, f"TestIt.setUpClass(); cls={cls}")
        # note: should do parent processing first
        super().setUpClass(filename, module)
        cls.index_parent = cls.temp_base
        cls.index_temp_dir = gh.form_path(cls.index_parent, cls.INDEX_STORE_DIR)
        if not system.is_directory(cls.index_temp_dir):
            gh.full_mkdir(cls.index_temp_dir)
        if THE_MODULE.INDEX_ONLY_RECENT:
            THE_MODULE.INDEX_ONLY_RECENT = False
        debug.trace_object(5, cls, label=f"{cls.__class__.__name__} instance")
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    @pytest.mark.skipif(not RUN_SLOW_TESTS, reason="Ignoring slow test")
    def test_01_index_dir(self):
        """Tests run_script to index directory"""
        # Warning: see notes above about potential issues with run_script-based tests.
        debug.trace(4, f"TestIt.test_01_index_dir(); self={self}")
        if not KEEP_TEMP_FILES:
            atexit.register(gh.delete_directory, self.index_temp_dir)
            
        if not system.is_directory(self.index_parent):
           debug.assertion(False)
           gh.full_mkdir(self.index_parent)
        
        # test if indexing works with with no existing db
        file_dir = gh.real_path(gh.dirname(__file__))
        repo_base_dir = gh.form_path(file_dir, "..", "..")
        
        init_output = self.run_script(options=f"--index {repo_base_dir}",
                                      env_options=f"INDEX_STORE_DIR={self.index_temp_dir}")
        self.do_assert(my_re.search(r"(\d\d+) chunks indexed", init_output))
        num_initial_chunks = int(my_re.group(1))
        index_files = system.read_directory(self.index_temp_dir)
        
        # assert INDEX_STORE_DIR is not empty
        self.do_assert(index_files != [])
        
        # save modified date for comparing later 
        prev_date = get_last_modified_date(system.get_directory_filenames(self.index_temp_dir, just_regular_files=True))
        
        # test that indexing with an already existing DB works
        resource_dir = gh.form_path(file_dir, "resources")
        revised_output = self.run_script(options=f"--index {resource_dir}",
                                         env_options=f"INDEX_STORE_DIR={self.index_temp_dir}")
        self.do_assert(my_re.search(r"(\d\d+) chunks indexed", init_output))
        num_final_chunks = int(my_re.group(1))
        self.do_assert(num_final_chunks > num_initial_chunks)
       
        # get modification time and check if it changed
        new_date = get_last_modified_date(system.get_directory_filenames(self.index_temp_dir, just_regular_files=True))
        self.do_assert(new_date > prev_date)
        

    @pytest.mark.skipif(not RUN_SLOW_TESTS, reason="Ignoring slow test")
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_02_search_docs(self):
        """Test for something_else: TODO..."""
        debug.trace(4, f"TestIt.test_02_search_docs(); self={self}")
        desktop = THE_MODULE.DesktopSearch(self.index_temp_dir)
        desktop.search_to_answer('What license is used?')
        output = self.get_stdout()
        
        self.do_assert(my_re.search(r"GNU", output.strip()))
        

    @pytest.mark.xfail                   # TODO: remove xfail
    @pytest.mark.skipif(gpu_utils.TORCH_DEVICE != "cuda", reason="Ignoring non-CUDA device")
    @pytest.mark.skipif(not RUN_SLOW_TESTS, reason="Ignoring slow test")
    def test_03_gpu_usage(self):
        """Test for GPU libs being used"""
        # Note: verifies process using GPU via nvida-smi
        #  |  GPU   GI   CI        PID   Type   Process name            GPU Memory |
        #  ...
        #  |    0   N/A  N/A   1111609      C   python                      366MiB |
        debug.trace(4, f"TestIt.test_03_gpu_usage(); self={self}")
        ds = THE_MODULE.DesktopSearch(self.index_temp_dir)
        ds.show_similar("license")
        trace_level = max(1, debug.get_level())
        gpu_utils.trace_gpu_usage(level=trace_level)
        stdout, stderr = self.get_stdout_stderr()
        self.do_assert("GNU" in stdout) 
        pid = system.get_process_id()
        self.do_assert(my_re.search(fr"\b{pid}\b.*python", stderr))
        return
    

    @pytest.mark.xfail                   # TODO: remove xfail
    @pytest.mark.skipif(not RUN_SLOW_TESTS, reason="Ignoring slow test")
    def test_04_show_similar(self):
        """Test run_script to show similar document to QUERY"""
        debug.trace(4, f"test_04_show_similar(): self={self}")
        desktop = THE_MODULE.DesktopSearch(index_store_dir=self.index_temp_dir)
        
        desktop.show_similar(query="LICENSE", num=1)
        output = self.get_stdout()
        if not KEEP_TEMP_FILES:
            gh.delete_directory(self.index_temp_dir)
        self.do_assert("Lesser General Public License" in output)
        

    @pytest.mark.xfail                   # TODO: remove xfail
    @pytest.mark.skipif(not RUN_SLOW_TESTS, reason="Ignoring slow test")
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
    invoke_tests(__file__)
