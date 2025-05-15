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

## TODO: Use self.script_output method if possible instead of gh.run()
## TODO: 
# Environment Variables for newer tests
LLM_PATH = system.getenv_text(
    "LLM_PATH", "",
    description="Path for LLM model"
)
RUN_SLOW_TESTS = system.getenv_bool(
    "RUN_SLOW_TESTS", False,
    description="Run tests that takes longer to process"
)

class TestLLMDesktopSearch(TestWrapper):
    """Class for command-line based testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__)
    script_file = TestWrapper.get_module_file_path(__file__)
    INDEX_STORE_DIR = THE_MODULE.INDEX_STORE_DIR.lstrip().lstrip(system.path_separator())
    use_temp_base_dir = True
    mezcla_base = gh.form_path(gh.dirname(__file__), "..", "..")   
    e2e_index_store = gh.get_temp_dir()
    
    ## TODO: Add a helper script for run_script
    # def helper_run_script(allow_unsafe_models=False, index_store_dir="index", llm_path=LLM_PATH)

    def helper_create_sample_files(self):
        """Create a temporary directory consisting of document type files"""
        temp_dir = gh.get_temp_dir()
        doc_content = "You can generate random words or sentences in Python without using any external libraries (like nltk or faker) by using built-in modules like random and defining your own word lists."
        file_extensions = ["txt", "doc", "pdf", "html"]
        for ext in file_extensions[0]:
            filename = "sample_file." + ext
            system.write_file(temp_dir + "/" + filename, doc_content)

        return temp_dir

    @pytest.mark.xfail
    def test_func_get_file_mod_fime(self):
        """Ensures get_file_mod_fime method works as expected"""
        existing_dir = "/etc/passwd"
        non_existing_dir = "/etc/password"
        
        self.assertNotEqual(
            THE_MODULE.get_file_mod_fime(existing_dir), -1
        )
        self.assertEqual(
            THE_MODULE.get_file_mod_fime(non_existing_dir), -1
        )

    @pytest.mark.xfail
    def test_func_get_last_modified_date(self):
        """Ensures get_last_modified_date works as expected"""
        temp_dir = gh.get_temp_dir()
        last_modified_date = THE_MODULE.get_last_modified_date(temp_dir)
        self.assertIsInstance(last_modified_date, float)
    
    # @pytest.mark.skipif(not system.file_exists(LLM_PATH), reason="LLM_PATH does not exist")
    # @pytest.mark.xfail
    def test_preliminary_is_model_loaded(self):
        """Test if test based model is loaded"""

        # Check if QA_LLM_MODEL uses llama by default
        self.assertIn("llama-2-7b-chat", THE_MODULE.QA_LLM_MODEL)

        # script_output = self.run_script(
        #     options=f"--index {self.mezcla_base}",
        #     env_options=f"ALLOW_UNSAFE_MODELS=1"
        # )
        string_allow_unsafe_models = "ALLOW_UNSAFE_MODELS=True "
        string_qa_llm_model = f"QA_LLM_MODEL={LLM_PATH} " 
        command_base = f"python3 {self.mezcla_base}/mezcla/llm_desktop_search.py --index {self.mezcla_base}"
        
        base_output = gh.run(command_base)
        self.assertEqual(base_output, -1)

        command_with_allow_unsafe_models = string_allow_unsafe_models + command_base
        allow_unsafe_models_output = gh.run(command_with_allow_unsafe_models)
        self.assertEqual(allow_unsafe_models_output, -1)

        command_with_llm_loaded = string_qa_llm_model + command_base
        output_with_llm_loaded = gh.run(command_with_llm_loaded)
        self.assertEqual(output_with_llm_loaded, -1)

        final_command = string_allow_unsafe_models + string_qa_llm_model + command_base
        output_all_loaded = gh.run(final_command)
        self.assertEqual(output_all_loaded, -1)

        
    @pytest.mark.xfail
    def test_e2e_generate_index_store(self):
        """End-to-end test to ensure index files (faiss, pkl) is generated"""
        index_store_temp = gh.get_temp_dir()
        ## TODO: Replace gh.run with self.run_script method
        gh.run(f"ALLOW_UNSAFE_MODELS=1 QA_LLM_MODEL={LLM_PATH} INDEX_STORE_DIR={index_store_temp} python3 {self.mezcla_base}/mezcla/llm_desktop_search.py --index {self.mezcla_base}")
        index_store_content = gh.run(f"ls {index_store_temp}")
        self.assertIn("index.faiss", index_store_content)
        self.assertIn("index.pkl", index_store_content)
    
    @pytest.mark.skipif(not system.file_exists(LLM_PATH), reason="LLM_PATH does not exist")
    @pytest.mark.xfail
    def test_scenario_detect_document_file(self):
        """Test to check if document files are detected by THE_MODULE"""
        # temp_file_store = self.helper_create_sample_files()
        ## TODO: Replace .txt in grep with all compatible extensions
        
        doc_files_path = self.mezcla_base
        doc_files_count = gh.run(f"ls {doc_files_path} | grep 'txt' | wc -l")
        
        # If the documents are accepted by script, index is created
        # The output is blank in case of success
        temp_index_store_dir = gh.get_temp_dir()
        llm_command_result = gh.run(
            f"ALLOW_UNSAFE_MODELS=1 QA_LLM_MODEL={LLM_PATH} INDEX_STORE_DIR={temp_index_store_dir} python3 {self.mezcla_base}/mezcla/llm_desktop_search.py --index {doc_files_path}"
        )
        self.assertGreaterEqual(int(doc_files_count), 0)
        self.assertEqual(llm_command_result, "")
        index_store_contents = gh.run(f"ls {temp_index_store_dir}")
        self.assertIn("pkl", index_store_contents)
        self.assertIn("faiss", index_store_contents)

    @pytest.mark.skipif(not system.file_exists(LLM_PATH), reason="LLM_PATH does not exist")
    @pytest.mark.xfail
    def test_scenario_no_document_file(self):
        """Test to check if non document files are not detected by modules"""
        # NOTE: <MEZCLA_BASE>/mezcla is taken as the path as it consists of no documents
        no_docs_path = self.mezcla_base + "/mezcla"
        no_docs_path = gh.run(f"ls {no_docs_path} | grep 'txt' | wc -l")
        
        # If the documents are not accepted by script, no index is created
        # The output consists of Exception messages
        temp_index_store_dir = gh.get_temp_dir()
        llm_command_result = gh.run(
            f"ALLOW_UNSAFE_MODELS=1 QA_LLM_MODEL={LLM_PATH} INDEX_STORE_DIR={temp_index_store_dir} python3 {self.mezcla_base}/mezcla/llm_desktop_search.py --index {no_docs_path}"
        )
        self.assertEqual(int(no_docs_path), 0)
        self.assertNotEqual(llm_command_result, "")
        self.assertIn("IndexError: list index out of range", llm_command_result)
        index_store_contents = gh.run(f"ls {temp_index_store_dir}")
        self.assertEqual(index_store_contents, "")


    ## TODO: Create a helper class for run_script() for multiple cases 
    @pytest.mark.xfail
    def test_e2e_index_option(self):
        """End-to-end tests to check if --index option work as expected"""
        command_output = self.run_script(options=f"--index {self.mezcla_base}",
                        env_options=f"ALLOW_UNSAFE_MODELS=1 QA_LLM_MODEL={LLM_PATH} INDEX_STORE_DIR={self.e2e_index_store}")
        self.assertEqual(command_output, "")
        index_dir_contents = gh.run(f"ls {self.e2e_index_store}")
        self.assertIn("index.faiss", index_dir_contents)
        self.assertIn("index.pkl", index_dir_contents)

    @pytest.mark.xfail
    def test_e2e_search_option(self):
        """End-to-end tests to check if --search option works as expected"""
        ## Create an index at first, and proceed for the search
        ## TODO: Create a helper class or fixture that automates the creation of index
        self.run_script(options=f"--index {self.mezcla_base}",
                        env_options=f"ALLOW_UNSAFE_MODELS=1 QA_LLM_MODEL={LLM_PATH} INDEX_STORE_DIR={self.e2e_index_store}")
        search_term = "explain me the licenses used in this project"
        command_output = self.run_script(options=f"--search {search_term}",
                        env_options=f"ALLOW_UNSAFE_MODELS=1 QA_LLM_MODEL={LLM_PATH} INDEX_STORE_DIR={self.e2e_index_store}")
        ## TODO: Describe proper tests
        self.assertEqual(command_output, "")

    @pytest.mark.xfail
    def test_e2e_similar_option(self):
        """End-to-end tests to check if --similar option works as expected"""
        self.run_script(options=f"--index {self.mezcla_base}",
        env_options=f"ALLOW_UNSAFE_MODELS=1 QA_LLM_MODEL={LLM_PATH} INDEX_STORE_DIR={self.e2e_index_store}")
        similar_term = "GNU"
        command_output = self.run_script(options=f"--similar {similar_term}",
                        env_options=f"ALLOW_UNSAFE_MODELS=1 QA_LLM_MODEL={LLM_PATH} INDEX_STORE_DIR={self.e2e_index_store}")
        ## TODO: Describe proper tests
        self.assertEqual(command_output, "")
        

    @pytest.mark.xfail
    def test_e2e_help_option(self):
        """End-to-end tests to check if --help option works as expected"""
        terms = ["usage", "llm_desktop_search.py", "verbose", "help", "Desktop search utility", "options", THE_MODULE.INDEX_ARG, THE_MODULE.SEARCH_ARG, THE_MODULE.SIMILAR_ARG]
        command_output = self.run_script(options="-h")
        self.assertNotEqual(command_output, "")
        for t in terms:
            self.assertIn(t, command_output)

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
