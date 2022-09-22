#! /usr/bin/env python
#
# Test(s) for gensim_test.py
#
# Notes:
# - Fill out the TODO's through the file.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_gensim_test.py
#
#------------------------------------------------------------------------
# TODO: adds tests for following
# $ DEBUG_LEVEL=4  /usr/bin/time python  -u  -m gensim_test  --save  --tfidf  --verbose  random100-titles-descriptions.txt  >| random100-titles-descriptions.log  2>&1
# $ grep food random100-titles-descriptions.verbose.log | less -S
# (3, [('food', 0.5934840534383484), ('accounting', 0.21278874808559092), ('beverage', 0.20959194756482724),
# (53, [('general', 0.3528312412285222), ('manager', 0.3148377686034749), ('food', 0.27899845787097777),
#

"""Tests for gensim_test module"""

# Standard packages
import re

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import tpo_common as tpo
from mezcla.unittest_wrapper import TestWrapper

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
import mezcla.gensim_test as THE_MODULE

class TestGensimTest(TestWrapper):
    """Class for testcase definition"""
    script_file = TestWrapper.get_module_file_path(__file__)
    script_module = TestWrapper.derive_tested_module_name(__file__)

    def test_data_file(self):
        """Tests results over a known data file (LICENSE.txt)"""
        tpo.debug_print("test_data_file()", 4)
        data_file = "LICENSE.txt"
        temp_data_file = self.temp_base + "-" + data_file
        gh.copy_file(gh.resolve_path(data_file), temp_data_file)
        output = self.run_script("--save", temp_data_file)
        ## TODO: assert re.search("storing corpus in Matrix Market format", output)
        assert gh.non_empty_file(temp_data_file.replace(".txt", ".bow.mm"))
        debug.trace_expr(5, output)
        return

    def test_vector_printing(self):
        """Test printing of corpus vector for simple input"""
        tpo.debug_print("test_vector_printing()", 4)
        temp_file = self.temp_base + ".txt"
        gh.write_file(temp_file, "My dog has fleas.\n")
        output = self.run_script("--print --verbose", temp_file)
        assert re.search(r"\(u?'dog', 1\),.*\(u?'has', 1\)", output)
        debug.trace_expr(5, output)
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
