#! /usr/bin/env python3
#
# Tests for train_language_model module
#
# Notes:
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_train_language_model.py
#
# TODO2:
# - Check for other cases of test classes without tests (due to work-in-progress nature
#   prior to 2025).
# - Likewise check for tests not using tests/template.py, where there are to-do tests with xfail,
#   allowing for easier tracking of tests to be implemeted!
#
#...............................................................................
# Sample output tested (2grams over LICENSE.txt):
#
#   \2-grams:
#   \data\
#   ngram 1=319
#   ngram 2=812
#   
#   \1-grams:
#   ...
#   -2.597798	gnu	-0.76723224
#   ...
#
#   \2-grams:
#   ...
#   -0.05367994	general public
#   ...
#   -0.15376821	combined work
#   ...
#
# Note:
#   $ count_it.perl -i '\w+ \w+' ~/Mezcla/LICENSE.txt | head
#   combined work	13
#   ...
#   general public	6
#   public license	5
#   ...
#
#................................................................................
# Sample usage:
#
# $ train_language_model.py --usage-notes
# /home/tomohara/Mezcla/mezcla/train_language_model.py --usage-notes
# 
# Usage: /home/tomohara/Mezcla/mezcla/train_language_model.py source-file.txt
#
# ...
#
# Notes:
# - The output is put in source-file.Ngram.arpa and source-file.Ngram.mmap.
# 

"""Tests for train_language_model module"""

# Standard modules
## NOTE: this is empty for now

# Installed modules
import pytest

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper, invoke_tests

# Note: Rreference are used for the module to be tested:
#    THE_MODULE:	    global module object
import mezcla.train_language_model as THE_MODULE

class TestTrainLanguageModel(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    license_path = gh.resolve_path("LICENSE.txt", heuristic=True)

    def get_score(self, ngram):
        """Return score for NGRAM from .arpa file"""
        # Note: See format above
        result = system.to_float(gh.run(f"grep '{ngram}' {self.temp_file}.arpa | cut -f1"))
        debug.trace(5, f"get_score({ngram}) => {result}")
        return result
        
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_01_data_file(self):
        """Tests run_script w/ data file"""
        # Warning: see notes above about potential issues with run_script-based tests.
        debug.trace(4, f"TestIt.test_01_data_file(); self={self}")
        self.run_script(
            env_options="MAX_NGRAM=2",
            options=f"--tokenize --output-basename {self.temp_file}",
            data_file=self.license_path)
        #
        combined_work_score = self.get_score("combined work")
        general_public_score = self.get_score("general public")
        self.do_assert(combined_work_score > general_public_score)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_02_something_else(self):
        """Test usage statement"""
        debug.trace(4, f"TestIt.test_02_usage(); self={self}")
        THE_MODULE.usage()
        output = self.get_stdout()
        self.do_assert(my_re.search("output.*source-file.Ngram.arpa", output))
        return


if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
