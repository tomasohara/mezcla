#! /usr/bin/env python
#
# Test(s) for ../ngram_tfidf.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_ngram_tfidf.py
# - To derive ngram test examples, run compute_tfidf.py over text:
#   $ MIN_NGRAM_SIZE=2 MAX_NGRAM_SIZE=4 compute_tfidf.py --text --num-top-terms 3 _argentinian-attraction-snippets-08dec23.list
#

"""Tests for ngram_tfidf module"""

# Standard packages
## NOTE: this is empty for now

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla.unittest_wrapper import TestWrapper
from mezcla.unittest_wrapper import trap_exception
from mezcla.my_regex import my_re
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
## TODO: fix type object 'Preprocessor' has no attribute 'USE_SKLEARN_COUNTER'
import mezcla.ngram_tfidf as THE_MODULE

class TestNgramTfidf(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.xfail                   # TODO: remove xfail
    ## DEBUG: @trap_exception            # TODO: remove when debugged
    def test_data_file(self):
        """Tests run_script w/ data file"""
        debug.trace(4, f"TestIt.test_data_file(); self={self}")
        ## TODO3: extend ngram_tfidf.py to get docs from lines not entire file as in compute_tfidf.py
        ## data = [
        ##     "dog\tbeagle terrier Irish wolfhound lap dog",
        ##     "hound\tbeagle Irish wolfhound ",
        ##     "other\tlap dawg",
        ## ]
        data = "beagle terrier Irish wolfhound lap dog lap dawg"
        system.write_lines(self.temp_file, data)
        output = self.run_script(options="--tsv", env_options="MIN_NGRAM_SIZE=2 MAX_NGRAM_SIZE=2",
                                 data_file=self.temp_file)
        self.do_assert(my_re.search(r"0\tlap dawg: ", output.strip()))
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    ## DEBUG:
    @trap_exception
    def test_simple_ngrams(self):
        """Adds small test with ngrams of size 2 to 4"""
        debug.trace(4, f"TestIt2.test_simple_ngrams(); self={self}")
        tfidf = THE_MODULE.ngram_tfidf_analysis( min_ngram_size=2, max_ngram_size=4)
        docs = [
            "Jul 26, 2022 ... 17 Top-Rated Tourist Attractions in Argentina \u00b7 1. Iguaz\u00fa Falls \u00b7 2. Perito Moreno Glacier \u00b7 3. Recoleta, La Boca, and Tango in Buenos Aires \u00b7 4\u00a0...",
            "Top Attractions in Argentina \u00b7 1. Teatro Colon \u00b7 2. Puerto Madero \u00b7 3. Recoleta \u00b7 4. Iguazu Falls \u00b7 5. Cementerio de la Recoleta \u00b7 6. Garganta del Diablo \u00b7 7."
            ]
        top_terms = [
            ["Tango in Buenos Aires", "Perito Moreno Glacier"],
            ["Teatro Colon", "Cementerio de la Recoleta"],
            ]
        for d, doc in enumerate(docs):
            doc_id = (d + 1)
            tfidf.add_doc(doc, doc_id)
            self.do_assert(tfidf.get_doc(doc_id))
            actual_top_terms = tfidf.get_top_terms(doc_id, limit=10)
            expected_top_terms = top_terms[d]
            debug.trace_expr(5, d, actual_top_terms, expected_top_terms)
            self.do_assert(system.intersection(actual_top_terms, expected_top_terms))
        return


if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
