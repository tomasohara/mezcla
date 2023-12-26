#! /usr/bin/env python
#
# Test(s) for ../spacy_nlp.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_spacy_nlp.py
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
from mezcla.my_regex import my_re
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper
## DEBUG:
from mezcla.unittest_wrapper import trap_exception

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
try:
    import mezcla.spacy_nlp as THE_MODULE
except:
    THE_MODULE = None
    debug.trace_exception(1, "mezcla.spacy_nlp import")

class TestSentimentAnalyzer:
    """Class for testcase definition"""

    @pytest.mark.xfail
    def test_get_score(self):
        """Ensure SentimentAnalyzer.get_score works as expected"""
        debug.trace(4, "test_get_score()")
        sentiment = THE_MODULE.SentimentAnalyzer()
        assert sentiment.get_score('bad') == -0.5423
        assert sentiment.get_score('good') == 0.4404


class TestSpacyNlpUtils:
    """Class for testcase definition"""

    @pytest.mark.xfail
    ## TODO: @pytest.mark.skipif(not THE_MODULE, reason="Unable to load module")
    def test_get_char_span(self):
        """Ensure get_char_span works as expected"""
        debug.trace(4, "test_get_char_span()")
        assert False, "TODO: code test"

    @pytest.mark.xfail
    ## TODO: @pytest.mark.skipif(not THE_MODULE, reason="Unable to load module")
    def test_pysbd_sentence_boundaries(self):
        """Ensure pysbd_sentence_boundaries works as expected"""
        debug.trace(4, "test_pysbd_sentence_boundaries()")
        assert False, "TODO: code test"

    @pytest.mark.xfail
    ## TODO: @pytest.mark.skipif(not THE_MODULE, reason="Unable to load module")
    def test_nltk_sentence_boundaries(self):
        """Ensure nltk_sentence_boundaries works as expected"""
        debug.trace(4, "test_nltk_sentence_boundaries()")
        assert False, "TODO: code test"


class TestSpacy(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.xfail                   # TODO: remove xfail
    ## DEBUG:
    @trap_exception            # TODO: remove when debugged
    def test_data_file(self):
        """Tests run_script w/ data file"""
        debug.trace(4, f"TestIt.test_data_file(); self={self}")
        data = ["It came, it saw, it conquered. The food", "was bland."]
        system.write_lines(self.temp_file, data)
        output = self.run_script(options="", data_file=self.temp_file)
        actual = output.strip()
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
    ## TODO: @pytest.mark.skipif(not THE_MODULE, reason="Unable to load module")
    def test_whatever(self):
        """TODO: flesh out test for whatever"""
        debug.trace(4, f"TestIt2.test_whatever(); self={self}")
        assert False, "TODO: code test"
        ## ex: assert THE_MODULE.fast_sort() == THE_MODULE.slow_sort()
        return


if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
