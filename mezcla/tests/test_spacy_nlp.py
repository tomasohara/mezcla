#! /usr/bin/env python
#
# Test(s) for ../spacy_nlp.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH="$(realpath .)/..):$PYTHONPATH" python tests/test_spacy_nlp.py
#

"""Tests for spacy_nlp module"""

# Standard packages

# Installed packages
import pytest

# Local packages
from mezcla import debug

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
#    TestIt.script_module   string name
import mezcla.spacy_nlp as THE_MODULE


class TestSentimentAnalyzer:
    """Class for testcase definition"""

    def test_get_score(self):
        """Ensure SentimentAnalyzer.get_score works as expected"""
        debug.trace(4, "test_get_score()")
        sentiment = THE_MODULE.SentimentAnalyzer()
        assert sentiment.get_score('bad') == -0.5423
        assert sentiment.get_score('good') == 0.4404


class TestIt:
    """Class for testcase definition"""

    def test_get_char_span(self):
        """Ensure get_char_span works as expected"""
        debug.trace(4, "test_get_char_span()")
        ## TODO: WORK-IN=PROGRESS

    def test_pysbd_sentence_boundaries(self):
        """Ensure pysbd_sentence_boundaries works as expected"""
        debug.trace(4, "test_pysbd_sentence_boundaries()")
        ## TODO: WORK-IN=PROGRESS

    def test_nltk_sentence_boundaries(self):
        """Ensure nltk_sentence_boundaries works as expected"""
        debug.trace(4, "test_nltk_sentence_boundaries()")
        ## TODO: WORK-IN=PROGRESS


class TestScript:
    """Class for testcase definition"""

    def test_get_entity_spec(self):
        """Ensure script.get_entity_spec works as expected"""
        debug.trace(4, "test_get_entity_spec()")
        ## TODO: WORK-IN=PROGRESS

    def test_get_sentiment_score(self):
        """Ensure script.get_sentiment_score works as expected"""
        debug.trace(4, "test_get_sentiment_score()")
        ## TODO: WORK-IN=PROGRESS

    def test_process_line(self):
        """Ensure script.process_line works as expected"""
        debug.trace(4, "test_process_line()")
        ## TODO: WORK-IN=PROGRESS

    def test_process_sentence(self):
        """Ensure script.process_sentence works as expected"""
        debug.trace(4, "test_process_sentence()")
        ## TODO: WORK-IN=PROGRESS


if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
