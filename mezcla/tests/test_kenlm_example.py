#! /usr/bin/env python
#
# Test(s) for ../kenlm_example.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_kenlm_example.py
# - Alternatively, this can be run as:
#       export LM=./lm/test.arpa
#       ./tests/test_kenlm_example.py

"""Tests for kenlm_example module"""

# Standard packages
## NOTE: this is empty for now

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
## TODO: solve import issue in kenlm_example
import mezcla.kenlm_example as THE_MODULE

class TestKenlmExample:
    """Class for testcase definition"""
    
    ## TODO: TESTS WORK-IN-PROGRESS
    def test_summed_constituent_score(self):
        """Ensures that summed_constituent_score works properly"""
        debug.trace(4, "test_summed_constituent_score()")
        sentence = "language modeling is fun"
        sentence_score = THE_MODULE.summed_constituent_score(sentence)
        assert (abs(sentence_score) - abs(THE_MODULE.model.score(sentence)) < 1e-3)
        ## TODO: Find a method to get sentence score and find the difference < 1e-3

    def test_kenlm_example_1(self):
        """Ensures that kenlm_example_1 works properly"""
        debug.trace(4, "test_kenlm_example()")
        sentences = 'language modeling is fun .'
        test1 = round(THE_MODULE.normaized_score, 2) == -12.92
        test2 = THE_MODULE.model.order == 5
        test3 = round(THE_MODULE.model.score(sentences), 2) == -64.59
        assert(test1 and test2 and test3)
    
    def test_kenlm_example_2(self):
        """Ensures that kenlm_example_2 works properly"""
        debug.trace(4, "test_kenlm_example_2()")
        sentence = "A quick brown fox jumps over a lazy dog."
        
        gh.run(f'')

    ## TODO: Find a way to test the entire output of script

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
