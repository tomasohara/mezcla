#! /usr/bin/env python3
#
# Test(s) for ../spacy_nlp.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_spacy_nlp.py
#
# Warning:
# - Maldito Spacy has some issues under Python 3.8 and 3.9, so the tests are
#   currently marked xfail until it stabilizes.
#
#...............................................................................
# Output from sample test:
#
# $ spacy_nlp.py - <<<$'I came, I saw, I conquered. The food\nwas bland.'
# text  is_oov  is_stop sentiment       is_sent_start
# It    False   True    0.0     True
# came  False   False   0.0     False
# ,     False   False   0.0     False
# it    False   True    0.0     False
# saw   False   False   0.0     False
# ,     False   False   0.0     False
# it    False   True    0.0     False
# conquered     False   False   0.0     False
# .     False   False   0.0     False
# text  is_oov  is_stop sentiment       is_sent_start
# The   False   True    0.0     True
# food  False   False   0.0     False
# was   False   True    0.0     False
# bland False   False   0.0     False
# .	False	False	0.0	False
#

"""Tests for spacy_nlp module"""

# Standard packages
## NOTE: this is empty for now

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.misc_utils import is_close
from mezcla.my_regex import my_re
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
## DEBUG: from mezcla.unittest_wrapper import trap_exception

# Environment manpulation
# note: needed to be done prior to loading Spacy (see THE_MODULE below)
# TODO2: rework to modification as part of test case (e.g., a la monkey patch)
system.setenv("SPACY_MODEL", "en_core_web_md")

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
try:
    import mezcla.spacy_nlp as THE_MODULE
except:
    THE_MODULE = None
    debug.trace_exception(1, "mezcla.spacy_nlp import")

class TestSentimentAnalyzer(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.xfail
    def test_get_score(self):
        """Ensure SentimentAnalyzer.get_score works as expected"""
        debug.trace(4, "test_get_score()")
        sentiment = THE_MODULE.SentimentAnalyzer()
        self.do_assert(is_close(sentiment.get_score('bad'), -0.542))
        self.do_assert(is_close(sentiment.get_score('good'), 0.440))


class TestSpacyNlpUtils(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.xfail
    ## TODO: @pytest.mark.skipif(not THE_MODULE, reason="Unable to load module")
    def test_get_char_span(self):
        """Ensure get_char_span works as expected"""
        debug.trace(4, "test_get_char_span()")
        doc = THE_MODULE.SpacyHelper().nlp("the quick brown fox")
        # contract mode
        assert THE_MODULE.get_char_span(doc, 4, 19).text == "quick brown fox"
        assert THE_MODULE.get_char_span(doc, 4, 18).text == "quick brown"
        assert THE_MODULE.get_char_span(doc, 4, 20) is None

        # expand mode
        assert THE_MODULE.get_char_span(doc, 16, 16).text == "fox"
        assert THE_MODULE.get_char_span(doc, 14, 17).text == "brown fox"

        # adjusted span
        assert doc.text[15] == ' ' # make sure we're starting at a space
        assert THE_MODULE.get_char_span(doc, 15, 16).text == "fox"
        assert THE_MODULE.get_char_span(doc, 15, 15).text == "brown"


    @pytest.mark.xfail
    ## TODO: @pytest.mark.skipif(not THE_MODULE, reason="Unable to load module")
    def test_pysbd_sentence_boundaries(self):
        """Ensure pysbd_sentence_boundaries works as expected"""
        debug.trace(4, "test_pysbd_sentence_boundaries()")
        self.do_assert(False, "TODO: code test")

    @pytest.mark.xfail
    ## TODO: @pytest.mark.skipif(not THE_MODULE, reason="Unable to load module")
    def test_nltk_sentence_boundaries(self):
        """Ensure nltk_sentence_boundaries works as expected"""
        debug.trace(4, "test_nltk_sentence_boundaries()")
        self.do_assert(False, "TODO: code test")


class TestSpacy(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.xfail
    def test_data_file(self):
        """Tests run_script w/ data file"""
        debug.trace(4, f"TestIt.test_data_file(); self={self}")
        data = ["It came, it saw, it conquered. The food", "was bland."]
        system.write_lines(self.temp_file, data)
        output = self.run_script(options="", data_file=self.temp_file)
        actual = output.strip()
        debug.trace_expr(5, actual, max_len=1024)
        # Check for header
        self.do_assert(my_re.search(r"text\tis_oov\tis_stop\tsentiment\tis_sent_start", actual))
        # Check for start of sentences
        self.do_assert(my_re.search(r"It\tFalse\tTrue\t0.0\tTrue", actual))
        self.do_assert(my_re.search(r"The\tFalse\tTrue\t0.0\tTrue", actual))
        # Check that no other sentence starts (n.b., "was" doesn't even though new line)
        self.do_assert(my_re.search(r"was\tFalse\tTrue\t0.0\tFalse", actual))
        sent_start_info = sorted(gh.extract_matches(r"\t(\S+)$", actual.splitlines()))
        self.do_assert(sent_start_info[-5:] == ["False", "True", "True", "is_sent_start", "is_sent_start"])
        return

    @pytest.mark.xfail
    def test_chunker(self):
        """Test NP chunking"""
        debug.trace(4, f"TestIt2.test_chunker(); self={self}")
        chunker = THE_MODULE.Chunker()
        text = "my dog has fleas"
        expected_NPs = ["my dog", "fleas"]
        actual_NPs = chunker.noun_phrases(text)
        self.do_assert(expected_NPs == actual_NPs)
        return


if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
