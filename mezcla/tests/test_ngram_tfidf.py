#! /usr/bin/env python3
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
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla.unittest_wrapper import trap_exception
from mezcla.my_regex import my_re
from mezcla import system

# Global settings
# TODO2: only use for run_script test(s): expose API for use in other tests
system.setenv("TFIDF_PRESERVE_CASE", 1)
## TODO3: system.setenv("TFIDF_LANGUAGE", "")
system.setenv("PREPROCESSOR_LANG", "")
system.setenv("SKIP_TFIDF_PREPROCESSOR", "1")
system.setenv("TFIDF_NGRAM_LEN_WEIGHT", "1.1")
system.setenv("TFIDF_BOOST_CAPITALIZED", "1")

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
        ## BAD: data = ["beagle terrier Irish wolfhound lap dog lap dawg"]
        data = ["lap dog", "lap dog", "lap dawg"]
        system.write_lines(self.temp_file, data)
        actual = self.run_script(options="--regular", env_options="MIN_NGRAM_SIZE=2 MAX_NGRAM_SIZE=2",
                                 data_file=self.temp_file)
        debug.trace_expr(5, actual)
        #
        def get_score(doc_id, ngram, output):
            """Get score for NGRAM for DOC_ID in OUTPUT or -1 if not found"""
            # NOTE: Assumes just one ngram per output
            # EX: get_score("2", "lap dawg", "2\tlap dawg: 0.137") => 0.137
            score = -1
            if  my_re.search(fr"{doc_id}\t{ngram}: ([0-9.]+)", output.strip()):
                score = system.to_float(my_re.group(1))
            debug.trace_expr(5, doc_id, ngram, score, prefix="get_score: ")
            return score
        #
        lap_dog_score_doc1 = get_score("0", "lap dog", actual.strip())
        lap_dog_score_doc2 = get_score("1", "lap dog", actual.strip())
        lap_dawg_score_doc3 = get_score("2", "lap dawg", actual.strip())
        self.do_assert(lap_dog_score_doc1 == lap_dog_score_doc2)
        self.do_assert(lap_dog_score_doc1 < lap_dawg_score_doc3)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    ## DEBUG:
    @trap_exception
    def test_simple_ngrams(self):
        """Adds small test with ngrams of size 2 to 4"""
        debug.trace(4, f"TestIt2.test_simple_ngrams(); self={self}")
        tfidf = THE_MODULE.ngram_tfidf_analysis(min_ngram_size=2, max_ngram_size=4)
        docs = [
            "Jul 26, 2022 ... 17 Top-Rated Tourist Attractions in Argentina · 1. Iguazá Falls · 2. Perito Moreno Glacier · 3. Recoleta, La Boca, and Tango in Buenos Aires · 4 ...",
            "Top Attractions in Argentina · 1. Teatro Colon · 2. Puerto Madero · 3. Recoleta · 4. Iguazu Falls · 5. Cementerio de la Recoleta · 6. Garganta del Diablo · 7.",
            ]
        top_terms = [
            ["Tango in Buenos Aires", "Perito Moreno Glacier"],
            ["Teatro Colon", "Cementerio de la Recoleta"],
            ]
        # Populate corpus; done in advance of tests to ensure IDF well defined
        for d, doc in enumerate(docs):
            doc_id = (d + 1)
            tfidf.add_doc(doc, doc_id)
        # Check for expected terms (n.b., all documents need to be added first)
        for d, doc in enumerate(docs):
            doc_id = (d + 1)
            self.do_assert(tfidf.get_doc(doc_id))
            actual_top_terms = [t for (t, _s) in tfidf.get_top_terms(doc_id, limit=10)]
            expected_top_terms = top_terms[d]
            debug.trace_expr(5, actual_top_terms, expected_top_terms, delim="\n")
            self.do_assert(not system.difference(expected_top_terms, actual_top_terms))
        return


if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
