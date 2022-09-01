#! /usr/bin/env python
#
# Test(s) for ../text_processing.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH="$(realpath .)/..):$PYTHONPATH" python tests/test_text_processing.py
#

"""Tests for text_processing module"""

# Standard packages

# Installed packages
import pytest

# Local packages
from mezcla import debug

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
#    TestIt.script_module   string name
import mezcla.text_processing as THE_MODULE

class TestIt:
    """Class for testcase definition"""

    def test_split_sentences(self):
        """Ensure split_sentences works as expected"""
        debug.trace(4, "test_split_sentences()")
        assert THE_MODULE.split_sentences("I came. I saw. I conquered!") == ["I came.", "I saw.", "I conquered!"]
        assert THE_MODULE.split_sentences("Dr. Watson, it's elementary. But why?") == ["Dr. Watson, it's elementary." "But why?"]

    def test_split_word_tokens(self):
        """Ensure split_word_tokens works as expected"""
        debug.trace(4, "test_split_word_tokens()")
        assert THE_MODULE.split_word_tokens("How now, brown cow?") == ['How', 'now', ',', 'brown', 'cow', '?']

    def test_label_for_tag(self):
        """Ensure label_for_tag works as expected"""
        debug.trace(4, "test_label_for_tag()")
        ## TODO: WORK-IN=PROGRESS

    def test_class_for_tag(self):
        """Ensure class_for_tag works as expected"""
        debug.trace(4, "test_class_for_tag()")
        assert THE_MODULE.class_for_tag("NNS") == "noun"
        assert THE_MODULE.class_for_tag("VBG") == "noun"
        assert THE_MODULE.class_for_tag("VBG", previous="MD") == "verb"
        assert THE_MODULE.class_for_tag("NNP", word="(") == "punctuation"

    def test_tag_part_of_speech(self):
        """Ensure tag_part_of_speech works as expected"""
        debug.trace(4, "test_tag_part_of_speech()")
        assert THE_MODULE.tag_part_of_speech(['How', 'now', ',', 'brown', 'cow', '?']) == [('How', 'WRB'), ('now', 'RB'), (',', ','), ('brown', 'JJ'), ('cow', 'NN'), ('?', '.')]

    def test_tokenize_and_tag(self):
        """Ensure tokenize_and_tag works as expected"""
        debug.trace(4, "test_tokenize_and_tag()")
        ## TODO: WORK-IN=PROGRESS

    def test_tokenize_text(self):
        """Ensure tokenize_text works as expected"""
        debug.trace(4, "test_tokenize_text()")
        ## TODO: WORK-IN=PROGRESS

    def test_is_stopword(self):
        """Ensure is_stopword works as expected"""
        debug.trace(4, "test_is_stopword()")
        ## TODO: WORK-IN=PROGRESS

    def test_has_spelling_mistake(self):
        """Ensure has_spelling_mistake works as expected"""
        debug.trace(4, "test_has_spelling_mistake()")
        ## TODO: WORK-IN=PROGRESS

    def test_read_freq_data(self):
        """Ensure read_freq_data works as expected"""
        debug.trace(4, "test_read_freq_data()")
        ## TODO: WORK-IN=PROGRESS

    def test_read_word_POS_data(self):
        """Ensure read_word_POS_data works as expected"""
        debug.trace(4, "test_read_word_POS_data()")
        ## TODO: WORK-IN=PROGRESS

    def test_get_most_common_POS(self):
        """Ensure get_most_common_POS works as expected"""
        debug.trace(4, "test_get_most_common_POS()")
        assert THE_MODULE.get_most_common_POS("can") == "MD"
        assert THE_MODULE.get_most_common_POS("notaword") == "NN"

    def test_is_noun(self):
        """Ensure is_noun works as expected"""
        debug.trace(4, "test_is_noun()")
        ## TODO: WORK-IN=PROGRESS

    def test_is_verb(self):
        """Ensure is_verb works as expected"""
        debug.trace(4, "test_is_verb()")
        assert not THE_MODULE.is_verb('can', 'NN')
        ## TODO: add positive assertion

    def test_is_adverb(self):
        """Ensure is_adverb works as expected"""
        debug.trace(4, "test_is_adverb()")
        assert THE_MODULE.is_adverb('quickly', 'RB')
        ## TODO: add negative assertion

    def test_is_adjective(self):
        """Ensure is_adjective works as expected"""
        debug.trace(4, "test_is_adjective()")
        ## TODO: WORK-IN=PROGRESS

    def test_is_comma(self):
        """Ensure is_comma works as expected"""
        debug.trace(4, "test_is_comma()")
        ## TODO: WORK-IN=PROGRESS

    def test_is_quote(self):
        """Ensure is_quote works as expected"""
        debug.trace(4, "test_is_quote()")
        ## TODO: WORK-IN=PROGRESS

    def test_is_punct(self):
        """Ensure is_punct works as expected"""
        debug.trace(4, "test_is_punct()")
        assert THE_MODULE.is_punct('$', '$')
        ## TODO: WORK-IN=PROGRESS

    def test_usage(self):
        """Ensure usage works as expected"""
        debug.trace(4, "test_usage()")
        ## TODO: WORK-IN=PROGRESS

    ## TODO: test main


if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
