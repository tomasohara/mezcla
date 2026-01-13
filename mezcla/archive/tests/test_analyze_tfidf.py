#! /usr/bin/env python
#
# Test(s) for analyze_tfidf.py. 
#
# The main test automates the following steps:
#
#   $ {
#     base=/tmp/test_analyze_tfidf-$$
#     index_dir="$base-index"
#   
#     cut -f1,12 tests/sample-query-log.retrieve_lr_inputs.data >| $base.data
#   
#     SHOW_TFIDF=1 INCLUSION_FIELDS=2  python  -m index_table_file  $base.data  $index_dir >| $index_dir.index.log
#   
#     SHOW_TFIDF=1 python -m search_table_file_index  $index_dir >| $index_dir.search.log
#   
#     INCLUDE_CONTEXT=1 INDEX_DIR=$index_dir SHOW_TFIDF=1 python -m analyze_tfidf  $index_dir.search.log >| $index_dir.analyze.log
#   }
#   
#   $ grep -c biostatistics $base.data
#   1
#   $ calc "log(92/1)"
#   4.52179
#   
#   $ grep tfidf.*biostatistics $index_dir.analyze.log
#   docid=1 tfidf=['biostatistics:4.522']
#   
#   $ grep -c ONCOLOGY $base.data
#   16
#   
#   $ calc "log(92/16)"
#   1.7492
#   
#   $ grep "tfidf=.*oncology" $index_dir.analyze.log | head -1
#   docid=52 tfidf=['oncology:1.749', 'radiation:1.749']
#------------------------------------------------------------------------
# Sample data (columns 1 and 12 of consolidated data file sample):
#
#   impression	k
#   1aa61096dd9a4126b4ecf6efcfd05605	'biostatistics'
#   d982b02353e441568fd3cd24d4719320	'personal-traveling-assistant'
#   H2P2ChGmSgCv1EjSaXoSUQ	'personal-traveling-assistant'
#   ...
#   0Uu62hBlRomLRzVHJumFuQ	'patent attorney'
#   J6dl5f8xQX-fMC0PFBM4sw	'patent attorney'
#------------------------------------------------------------------------
# Notes:
# - This can be run as follows:
#   $ PYTHONPATH="." python tests/test_analyze_tfidf.py
#
# Warning:
# - This is basically the version from the repo misc-scripts.
# - This is mainly included for sake of completeness, because
#   analyze_tfidf.py got added to the repo inadvertantly.
#

import re
import tempfile
import unittest

import glue_helpers as gh
import tpo_common as tpo


class TestIt(unittest.TestCase):
    """Class for testcase definition"""
    script_module_name = "analyze_tfidf"  # name for invocation via 'python -m ...'

    def setUp(self):
        """Per-test initializations: disables tracing of scripts invoked via run(); initializes temp file name (With override from environment)."""
        # Note: By default, each test gets its own temp file.
        tpo.debug_print("setUp()", 4)
        gh.disable_subcommand_tracing()
        self.base = tpo.getenv_text("TEMP_FILE", tempfile.NamedTemporaryFile().name)
        self.index_dir = self.base + "-index"
        return

    def run_script(self, env_options, arguments):
        """Runs the script setting ENV_OPTIONS and passing ARGUMENTS"""
        tpo.debug_format("run_script({env_options}, {arguments})", 5)
        # Usage: ENVVAR1=VAL1 ... analyze_tfidf.py [-h] [--verbose] [filename]
        output = gh.run("{env_options} python  -m {self.script_module_name}   {arguments}")
        # Make sure no python or bash errors
        # examples: "SyntaxError: invalid syntax", "bash: python: command not found"
        self.assertTrue(not re.search("(\S+Error:)|(no module)|(command not found)", output.lower()))
        return (output)

    def test_data_file(self):
        """Tests results over a known data file"""
        tpo.debug_print("test_data_file()", 4)
        data_file = gh.resolve_path("sample-query-log.retrieve_lr_inputs.data")

        # Extract impresssion IDs and query keywords
        base = self.base
        gh.run("cut -f1,12 {data_file} >| {self.base}.data")
        self.assertTrue(len(gh.read_lines(base + ".data")) == 92)

        # Index the keywords from sample query log
        output = gh.run("SHOW_TFIDF=1 INCLUSION_FIELDS=2  INDEX_DIR={self.index_dir} python  -m index_table_file  {base}.data")
        self.assertTrue(re.search("commiting.*done", output))

        # Create TF/IDF listing for documents
        gh.run("SHOW_TFIDF=1 INDEX_DIR={self.index_dir}  python -m search_table_file_index - >| {base}.search.log")
        output = gh.read_file(base + ".search.log")
        # ex: doc=0 tfidf=['k:3.829']
        self.assertTrue(re.search("docid=0.*tfidf.*'k:", output))
        # ex: doc=91 tfidf=['attorney:2.124', 'patent:2.037']
        self.assertTrue(re.search("docid=91.*tfidf=.*attorney.*patent", output))

        # Perform posthoc TF/IDF analysis
        gh.write_lines(base + ".exclude", [ "attorney" ])
        ## OLD: output = gh.run("INCLUDE_CONTEXT=1 EXCLUSION_FILE={base}.exclude INDEX_DIR={self.index_dir} SHOW_TFIDF=1  python -m analyze_tfidf  {base}.search.log")
        ## BAD: output = self.run_script("INCLUDE_CONTEXT=1 EXCLUSION_FILE={base}.exclude INDEX_DIR={self.index_dir} SHOW_TFIDF=1", "{base}.search.log")
        output = self.run_script(tpo.format("INCLUDE_CONTEXT=1 EXCLUSION_FILE={base}.exclude INDEX_DIR={self.index_dir} SHOW_TFIDF=1"), tpo.format("{base}.search.log"))
        # ex: doc=[assistant, personal, traveling]
        self.assertTrue(re.search("assistant.*personal.*traveling", output))
        # ex: 92 documents
        # ex: 393 keywords; 27 distinct
        # ex: mean mean TF/IDF: 4.268
        self.assertTrue(re.search("92 documents", output))
        self.assertTrue(re.search("[0-9][0-9][0-9] keywords.* [0-9][0-9] distinct", output))
        self.assertTrue(re.search("mean TF/IDF.* [2-6]\.", output))
        return
        
    def tearDown(self):
        """Per-test cleanup: deletes temporary file unless during detailed debugging"""
        tpo.debug_print("tearDown()", 4)
        if (not tpo.detailed_debugging()):
            gh.run("rm -rvf {self.base}*")
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()

