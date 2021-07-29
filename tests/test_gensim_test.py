#! /usr/bin/env python
#
# Test(s) for gensim_test.py
#
# Notes:
# - Fill out the TODO's through the file.
# - This can be run as follows:
#   $ PYTHONPATH="." python tests/test_gensim_test.py
#
#------------------------------------------------------------------------
# TODO: adds tests for following
# $ DEBUG_LEVEL=4  /usr/bin/time python  -u  -m gensim_test  --save  --tfidf  --verbose  random100-titles-descriptions.txt  >| random100-titles-descriptions.log  2>&1
# $ grep food random100-titles-descriptions.verbose.log | less -S
# (3, [('food', 0.5934840534383484), ('accounting', 0.21278874808559092), ('beverage', 0.20959194756482724),
# (53, [('general', 0.3528312412285222), ('manager', 0.3148377686034749), ('food', 0.27899845787097777),
#

"""Tests for gensim_test module"""

import re
## OLD: import sys
import tempfile
import unittest

import tomas_misc.glue_helpers as gh
import tomas_misc.tpo_common as tpo


class TestIt(unittest.TestCase):
    """Class for testcase definition"""
    script_module_name = "gensim_test"  # name for invocation via 'python -m ...'

    def setUp(self):
        """Per-test initializations: disables tracing of scripts invoked via run(); initializes temp file name (With override from environment)."""
        # Note: By default, each test gets its own temp file.
        tpo.debug_print("setUp()", 4)
        gh.disable_subcommand_tracing()
        self.temp_base = tpo.getenv_text("TEMP_FILE", tempfile.NamedTemporaryFile().name)
        return

    def run_script(self, options, data_file):
        """Runs the script over the DATA_FILE, passing OPTIONS"""
        tpo.debug_format("run_script({options}, {data_file})", 5)
        output = gh.run("python  -m {self.script_module_name}  {options}  {data_file}")
        # examples: "SyntaxError: invalid syntax", "bash: python: command not found"
        ## OLD: self.assertTrue(not re.search("(\S+Error:)|(no module)|(command not found)", output.lower()))
        self.assertTrue(not re.search(r"(\S+Error:)|(no module)|(command not found)", output.lower()))
        return (output)

    def test_data_file(self):
        """Tests results over a known data file (LICENSE.txt)"""
        tpo.debug_print("test_data_file()", 4)
        data_file = "LICENSE.txt"
        temp_data_file = self.temp_base + "-" + data_file
        gh.copy_file(gh.resolve_path(data_file), temp_data_file)
        output = self.run_script("--save", temp_data_file)
        ## TODO: self.assertTrue(re.search("storing corpus in Matrix Market format", output))
        self.assertTrue(gh.non_empty_file(temp_data_file.replace(".txt", ".bow.mm")))
        return
        
    def test_vector_printing(self):
        """Test printing of corpus vector for simple input"""
        tpo.debug_print("test_vector_printing()", 4)
        temp_file = self.temp_base + ".txt"
        gh.write_file(temp_file, "My dog has fleas.\n")
        output = self.run_script("--print --verbose", temp_file)
        self.assertTrue(re.search(r"\(u?'dog', 1\),.*\(u?'has', 1\)", output))
        return

    def tearDown(self):
        """Per-test cleanup: deletes temporary file unless during detailed debugging"""
        tpo.debug_print("tearDown()", 4)
        if (tpo.debugging_level() < 4):
            gh.run("rm -vf {self.temp_base}*")
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    unittest.main()
