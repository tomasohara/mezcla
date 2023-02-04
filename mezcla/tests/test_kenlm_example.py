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
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
## TODO: solve import issue in kenlm_example
import mezcla.kenlm_example as THE_MODULE

class TestKenlmExample(TestWrapper):
    script_file = TestWrapper.get_module_file_path(__file__)
    script_module = TestWrapper.get_testing_module_name(__file__)
    use_temp_base_dir = True    # treat TEMP_BASE as directory

    """Class for testcase definition"""
    
    def test_summed_constituent_score(self):
        """Ensures that summed_constituent_score works properly"""
        debug.trace(4, "test_summed_constituent_score()")
        sentence = "language modeling is fun"
        sentence_score = THE_MODULE.summed_constituent_score(sentence)
        assert (abs(sentence_score) - abs(THE_MODULE.model.score(sentence)) < 1e-3)
        return

    def test_kenlm_example_DEFAULT(self):
        """Ensures that kenlm_example_DEFAULT works properly"""

        command_export_LM = 'export LM=../lm/test.arpa'
        debug.trace(4, f"test_kenlm_example(); self={self}")
        sentences = 'language modeling is fun .'
        test1 = round(THE_MODULE.normaized_score, 2) == -12.92
        test2 = THE_MODULE.model.order == 5
        test3 = round(THE_MODULE.model.score(sentences), 2) == -64.59
        gh.run(command_export_LM)
        assert(test1 and test2 and test3)
        return
    
    def test_kenlm_example_ROUND(self):
        """Ensures that kenlm_example_ROUND works properly"""

        sentence = "A quick brown fox jumps over a lazy dog."
        command_export_LM = 'export LM=../lm/test.arpa'
        command_kenlm = f'ROUNDING_PRECISION=4 ../kenlm_example.py {sentence} > {self.temp_file}'
        test_model_score = "-149.4206"
        test_normalized_score = "-16.6023"

        debug.trace(4, f"test_kenlm_example_ROUND(); self={self}")
        gh.run(command_export_LM)
        gh.run(command_kenlm)
        
        ## [OLD]: Didn't work, returned tmp path as sentence
        # output = self.run_script(self.temp_file)
        output = gh.read_file(self.temp_file)
        test1 = test_model_score in output
        test2 = test_normalized_score in output
        test3 = sentence in output

        assert (test1 and test2 and test3)
        return 

    def test_kenlm_example_VERBOSE(self):
        """Ensures that kenlm_example_VERBOSE works properly"""

        sentence = "One kiss is all it takes."
        command_export_LM = 'export LM=../lm/test.arpa'
        command_kenlm = f'VERBOSE=True ../kenlm_example.py {sentence} > {self.temp_file}'

        debug.trace(4, f"test_kenlm_example_VERBOSE(); self={self}")
        gh.run(command_export_LM)
        gh.run(command_kenlm)
        
        prob_values = [-2.411, -15.000, -23.688, -2.297, -15.000, -17.000, -23.029]

        ## [OLD]: Didn't work, returned tmp path as sentence
        # output = self.run_script(self.temp_file)
        output = gh.read_file(self.temp_file)

        # TEST 1 - For checking the values in verbose list
        def is_prob_values_true(array=prob_values):
            return_bool = True
            for value in prob_values:
                if str(value) not in output:
                    return_bool = False
            return return_bool

        assert (is_prob_values_true)
        return 

    def test_kenlm_example_OUTOFVOCAB(self):
        """Ensures that kenlm_example_OUTOFVOCAB works properly"""

        sentence = "One kiss is all it takes."
        known_seen_character = "is"
        command_export_LM = 'export LM=../lm/test.arpa'
        command_kenlm = f'VERBOSE=True ../kenlm_example.py {sentence} > {self.temp_file} | tail -n 1 | cut -c 26-'

        debug.trace(4, f"test_kenlm_example_OUTOFVOCAB(); self={self}")
        gh.run(command_export_LM)
        gh.run(command_kenlm)

        ## [OLD]: Didn't work, returned tmp path as sentence
        # output = self.run_script(self.temp_file)
        output = gh.read_file(self.temp_file)

        ## [TODO]: WORK IN PROGRESS
        # TEST 2 - Checking for seen words in out-of-vocabs dict (VERBOSE)
        def return_seen_character(gow):
            for word in gow.split():
                if word in output:
                    return word

        seen_words = return_seen_character(sentence)

        assert ("is" in seen_words)
        return 

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
