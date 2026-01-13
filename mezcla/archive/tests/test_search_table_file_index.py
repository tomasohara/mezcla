#! /usr/bin/env python
#
# Test(s) for search_table_file_index.py
#
# Notes:
# - Fill out the TODO's through the file.
# - This can be run as follows:
#   $ PYTHONPATH="." python tests/test_search_table_file_index.py
#
# Warning:
# - This is basically the version from the repo misc-scripts.
# - This is mainly included for sake of completeness, because
#   analyze_tfidf.py got added to the repo inadvertantly.
# - In addition, it is used in test_format_profile.py because,
#   the script will likely not change much at all.
#

# Standard modules
import re
import sys
import tempfile
import unittest

# Installed modules
import pytest

# Local modules
from mezcla import glue_helpers as gh
from mezcla import tpo_common as tpo
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:               module object (e.g., <module 'mezcla.main' ...>)
#    TestIt.script_module:     dotted module path (e.g., "mezcla.main")
THE_MODULE = None
try:
    import mezcla.archive.search_table_file_index as THE_MODULE
except:
    system.print_exception_info("search_table_file_index import") 


class TestIt(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    def setUp(self):
        """Per-test initializations: disables tracing of scripts invoked via run(); initializes temp file name (With override from environment)."""
        # Note: By default, each test gets its own temp file.
        tpo.debug_print("setUp()", 4)
        gh.disable_subcommand_tracing()
        self.temp_file = tpo.getenv_text("TEMP_FILE", tempfile.NamedTemporaryFile().name)
        # Get rid of any files left from previous run (e.g., with detailed debugging)
        gh.run("rm -rvf {self.temp_file}*")
        return

    ## OLD:
    ## def run_script(self, env_options, index_dir, arguments):
    ##     """Runs the script over the INDEX_DIR, passing ENV_OPTIONS"""
    ##     tpo.debug_format("run_script({env_options}, {index_dir}, {arguments})", 5)
    ##     # Usage: ENVVAR1=VAL1 ... search_table_file_index.py [index_dir [query_word1 ...]
    ##     output = gh.run("{env_options} python  -m {self.script_module_name}   {index_dir}  {arguments}")
    ##     # Make sure no python or bash errors
    ##     # examples: "SyntaxError: invalid syntax", "bash: python: command not found"
    ##     self.assertTrue(not re.search("(\S+Error:)|(no module)|(command not found)", output.lower()))
    ##     return (output)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_data_file(self):
        """Tests results over a known data file"""
        tpo.debug_print("test_data_file()", 4)
        index_dir = self.temp_file + "-index"
        # Index the sample data file
        # note: contents field stored for TF/IDF check but no term vectors included
        data_file = gh.resolve_path("sample-query-log.retrieve_lr_inputs.data")
        output = gh.run("SHOW_TFIDF=0 STORE_CONTENTS=1 python -m index_table_file {data_file} {index_dir}")
        self.assertTrue(re.search("commiting.*done", output))

        # Test different types of queries
        # TODO: fix the query counts (or use ranges to make more robust)
        #
        # All-words search for "windows nt" returns 89 documents
        output = self.run_script("MAX_HITS=100", index_dir, "windows nt")
        self.assertTrue(len(output.split("\n")) == 89)
        # Phrasal search yields one less document
        output = self.run_script("PHRASAL=1 MAX_HITS=100", index_dir, "windows nt")
        self.assertTrue(len(output.split("\n")) == 88)
        # No match in 'name' field
        output = self.run_script("FIELD=name", index_dir, "windows nt")
        self.assertTrue(len(output) == 0)
        # The number 62 should occur 11 times
        output = self.run_script("", index_dir, "62")
        self.assertTrue(len(output.split("\n")) == 11)
        # There should an error in TF/IDF listing (requires stored field).
        # ex: "Error: No term vectors for field contents (docid=62)"
        output = self.run_script("SHOW_TFIDF=1", index_dir, "62")
        self.assertTrue(re.search("No term vectors", output))

        # Re-index the sample data file
        output = gh.run("SHOW_TFIDF=1 STORE_CONTENTS=1 python -m index_table_file {data_file} {index_dir}")
        self.assertTrue(re.search("commiting.*done", output))
        # There should be one TF/IDF result for document 62, with 'crl' having weight 4.9
        # ex "docid=62 tfidf=['clr:4.904', 'net:4.904', 'wzbyukewqfwo7x9neg9ydq:4.522', '0.022744695:3.829', '30.873058:3.829', '37569:3.829', '491868535:3.829', '28:2.912', '5:2.773', '9hq:2.730']"
        output = self.run_script("SHOW_TFIDF=1", index_dir, "62")
        self.assertTrue(len(output.split("\n")) == 1)
        self.assertTrue(re.search("\['clr:4\.9", output))
        return
 
    def tearDown(self):
        """Per-test cleanup: deletes temporary file unless during detailed debugging"""
        tpo.debug_print("tearDown()", 4)
        if (not tpo.detailed_debugging()):
            gh.run("rm -rvf {self.temp_file}*")
        return


#------------------------------------------------------------------------

tpo.debug_format("__name__={__name__} sys.argv={sys.argv}", 6)
if __name__ == '__main__':
    unittest.main()
