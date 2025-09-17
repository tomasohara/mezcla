#! /usr/bin/env python3
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
# - The test.arpa file is based on kenlm repo (https://github.com/kpu/kenlm).
#
#-------------------------------------------------------------------------------
# Sample test and output:
#
#   $ ROUNDING_PRECISION=4 LM=tests/resources/test.arpa python -m  mezcla.kenlm_example  A quick brown fox jumps over a lazy dog.
#   Loading the LM will be faster if you build a binary file.
#   Reading /home/tomohara/Mezcla/mezcla/tests/resources/test.arpa
#   ----5---10---15---20---25---30---35---40---45---50---55---60---65---70---75---80---85---90---95--100
#   ****************************************************************************************************
#   5-gram model
#   sentence: A quick brown fox jumps over a lazy dog.
#   model score: -149.4206
#   normalized score: -16.6023


"""Tests for kenlm_example module"""

## TODO1: revise tests following revision for test_kenlm_example_round below;
## also see recent to revisions bad tests circa Jan 2024.
##
## TODO2: review tests/template.py carefully
## TODO3: check for common patterns from test scripts (i.e., as a whole)

## TODO (IMPORTANT): Rework on the tests (uses old paths for test.arpa and bad code quality)
## TEMP: Run the test script using LM environment variable
## NOTE: All tests passed (as of 2023-12-29 +05:45 GMT 19:41)

# Standard packages
import ast

# Installed packages
## OLD: import re
import pytest

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla.unittest_wrapper import trap_exception

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                        global module object
#    TestIt.script_module:              path to file
try:
    import mezcla.kenlm_example as THE_MODULE
except:
    system.print_exception_info("kenlm_example import")
    THE_MODULE = None

## NEW: Added path for test.arpa (or Language Model)
## TODO2: follow tests/template.py better
lm_path = gh.resolve_path("./resources/test.arpa", heuristic=True)
## TODO2: replace kenlm_example_path w/ run_script as in test_kenlm_example_round
kenlm_example_path = gh.resolve_path("kenlm_example.py", heuristic=True)

## TODO3? Make sure utilities from KenLM installed
## NOTE: lmplz might just be needed for train_language_model.py
HAS_KENLM_UTILS = gh.run("which lmplz")


@pytest.mark.skipif(not THE_MODULE, reason="Problem loading kenlm_example.py: check requirements")
class TestKenlmExample(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    use_temp_base_dir = True    # treat TEMP_BASE as directory
    
    @pytest.mark.xfail                   # TODO: remove xfail
    @trap_exception                      # TODO: remove when debugged
    def test_summed_constituent_score(self):
        """Ensures that summed_constituent_score works properly"""
        debug.trace(4, "test_summed_constituent_score()")
        sentence = "language modeling is fun"
        sentence_score = THE_MODULE.summed_constituent_score(sentence)
        assert (abs(sentence_score) - abs(THE_MODULE.model.score(sentence)) < 1e-3)
        return
    
    @pytest.mark.xfail                   # TODO: remove xfail
    @trap_exception                      # TODO: remove when debugged
    def test_kenlm_example_default(self):
        """Ensures that kenlm_example_default works properly"""
        debug.trace(4, f"test_kenlm_example_default(); self={self}")
        sentence = 'language modeling is fun'
        ## OLD: 
        # command_export_LM = 'export LM=../lm/test.arpa'
        # test1 = round(THE_MODULE.normaized_score, 2) == -12.9
        # test3 = round(round(THE_MODULE.model.score(sentence), 2) == -64.59
        # gh.run(command_export_LM)
        test1 = 12 < abs(round(THE_MODULE.normaized_score, 2)) < 13
        test2 = THE_MODULE.model.order == 5
        test3 = 64 < abs(round(THE_MODULE.model.score(sentence), 2)) < 65
        assert(test1 and test2 and test3)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_kenlm_example_round(self):
        """Ensures that kenlm_example_round works properly"""
        debug.trace(4, f"test_kenlm_example_round(); self={self}")
        
        ## OLD: Bad piece of code
        # command_export_LM = 'export LM=../lm/test.arpa'
        # command_kenlm = f'ROUNDING_PRECISION=4 ../kenlm_example.py {sentence} > {self.temp_file}'
        
        ## OLD: Didn't work, returned tmp path as sentence
        # output = self.run_script(self.temp_file)
        # output = gh.read_file(self.temp_file)

        sentence = "A quick brown fox jumps over a lazy dog."
        round_val = 4
        ## BAD:
        ## command = f"ROUNDING_PRECISION={round_val} LM={lm_path} python3 {kenlm_example_path} {sentence} 2> /dev/null"
        ## command = f"ROUNDING_PRECISION={round_val} LM={lm_path} python3 {kenlm_example_path} {sentence} 2> /dev/null"
        ## output = gh.run(command).split("\n")
        output = self.run_script(env_options=f"ROUNDING_PRECISION={round_val} LM={lm_path}", options=sentence,
                                 uses_stdin=False)
        output = output.split("\n")

        test_model_order = 5
        test_model_score = -149.4206
        test_normalized_score = -16.6023

        ## OLD:
        ## test0 = str(test_model_order) in output[0] # n-gram model
        ## test1 = sentence in output[1]
        ## test2 = (str(test_model_score) in output[2]) and (-150 <= test_model_score <= -149)
        ## test3 = (str(test_normalized_score) in output[3]) and (-17 <= test_normalized_score <= -16)
        ##
        ## assert all([test0, test1, test2, test3])
        
        self.do_assert(str(test_model_order) in output[0])  # n-gram model
        self.do_assert(sentence in output[1])
        self.do_assert((str(test_model_score) in output[2]) and (-150 <= test_model_score <= -149))
        self.do_assert((str(test_normalized_score) in output[3]) and (-17 <= test_normalized_score <= -16))

        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_kenlm_example_verbose(self):
        """Ensures that kenlm_example_verbose works properly"""
        debug.trace(4, f"test_kenlm_example_VERBOSE(); self={self}")

        ## OLD: Improved command used
        # command_export_LM = 'export LM=../lm/test.arpa'
        # command_kenlm = f'VERBOSE=True ../kenlm_example.py {sentence} > {self.temp_file}'
        # gh.run(command_export_LM)
        # gh.run(command_kenlm)
        sentence = "One kiss is all it takes."
        command = f"VERBOSE=1 LM={lm_path} python3 {kenlm_example_path} {sentence} 2> /dev/null"
        output = gh.run(command)
        prob_values = [-2.411, -15.000, -23.688, -2.297, -15.000, -17.000, -23.029]

        ## [OLD]: Didn't work, returned tmp path as sentence
        # output = self.run_script(self.temp_file)
        ## OLD: Using gh.run instead of temp_file 
        # output = gh.read_file(self.temp_file)

        # TEST 1 - For checking the values in verbose list
        def is_prob_values_true():
            return_bool = True
            for value in prob_values:
                if str(value) not in output:
                    return_bool = False
            return return_bool

        assert (is_prob_values_true())
        return 


    @pytest.mark.xfail
    def test_kenlm_example_outofvocab(self):
        """Ensures that kenlm_example_outofvocab works properly"""
        debug.trace(4, f"test_kenlm_example_outofvocab(); self={self}")

        ## OLD: Improved command used
        # command_export_LM = 'export LM=../lm/test.arpa'
        # command_kenlm = f'VERBOSE=True ../kenlm_example.py {sentence} | tail -n 1 | cut -c 26- > {self.temp_file}'
        # gh.run(command_export_LM)
        # gh.run(command_kenlm)

        ## [OLD]: Didn't work, returned tmp path as sentence
        # output = self.run_script(self.temp_file)
        # output = gh.read_file(self.temp_file)

        ## OLD: Replaced by another method
        # ## [TODO]: WORK IN PROGRESS
        # ## TEST 2 - Checking for seen words in out-of-vocabs dict (VERBOSE)
        # def return_words(gow):
        #     x = []
        #     for word in gow.split():
        #         x += [word]
        #     return str(x)
        
        # def uncommon_words(a, b):
        #     # count will contain all the word counts
        #     count = {}
        
        #     for word in a.split():
        #         count[word] = count.get(word, 0) + 1

        #     for word in b.split():
        #         count[word] = count.get(word, 0) + 1

        #     return [word for word in count if count[word] == 1]

        # uncommon_str = str(uncommon_words(return_words(sentence), out_of_vocab_arr))
        # ## [WARNING]: Use of regex shows warning in pytest       
        # # uncommon_filter = re.sub('[\W_]+', '', uncommon_str)
        # uncommon_filter = "".join(list([val for val in uncommon_str if val.isalnum()]))
        
        # assert ("is" == uncommon_filter)
        # return

        # NOTE: Requires approval 
        sentence = "I just died in your arms tonight."
        known_seen_character = "in"
        command = f"LM={lm_path} VERBOSE=True python3 {kenlm_example_path} {sentence} 2> /dev/null | tail -n 1"
        output = gh.run(command).split(": ")
        out_of_vocab_arr = ast.literal_eval(output[-1])
        unseen_vocab = list(set(sentence.split(" ")) - set(out_of_vocab_arr))[0]
        assert(unseen_vocab == known_seen_character)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_kenlm_example_precision(self):
        """Ensures that kenlm_example_precision works properly"""
        debug.trace(4, f"test_kenlm_example_precision(); self={self}")
        PRECISION_VALUE = 7
        sentence = "I just died in your arms tonight"
        command = f"LM={lm_path} ROUNDING_PRECISION={PRECISION_VALUE} python3 {kenlm_example_path} {sentence} 2> /dev/null"
        output = gh.run(command).split("\n")
        normalized_score = (output[-1].split(": "))[-1]

        ## OLD: BAD PIECE OF CODE
        # command_export_LM = 'export LM=../lm/test.arpa'
        # command_kenlm = f'ROUNDING_PRECISION={PRECISION_VALUE} ../kenlm_example.py {sentence} | tail -n 1 | cut -c 19- > {self.temp_file}'
        # output = gh.read_file(self.temp_file)
        # gh.run(command_export_LM)
        # gh.run(command_kenlm)

        ## assert (normalized_score is None)
        ## [OLD]: Didn't work, returned tmp path as sentence
        # output = self.run_script(self.temp_file)
        
        def count_precision(num_string):
            before_decimal, after_decimal = num_string.split(".")
            debug.trace_expr(5, num_string, before_decimal, after_decimal)
            return len(after_decimal)

        assert (count_precision(normalized_score) == PRECISION_VALUE)
        return

    @pytest.mark.xfail
    @pytest.mark.skipif(not HAS_KENLM_UTILS, reason="KenLM utilities needed")
    def test_kenlm_utils(self):
        """Make sure KenLM utilities installed (e.g., lmplz)"""
        lmplz_usage = gh.run("lmplz")
        self.do_assert("Builds unpruned language models" in lmplz_usage)
        self.do_assert("Kenneth Heafield" in lmplz_usage)
    
if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
