#! /usr/bin/env python3
#
# Miscellaneous tests not tied to particular module.
#

"""Miscellaneous/non-module tests"""

# Standard packages
## TODO: from collections import defaultdict

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla import system
from mezcla import glue_helpers as gh
from mezcla.unittest_wrapper import TestWrapper
from mezcla.unittest_wrapper import trap_exception
from mezcla.tfidf.corpus import Corpus
from mezcla.tfidf.dockeyword import DocKeyword

# Constants
DOCUMENT_DATA = [
    "0",
    "1 2 3 4 5",
    "2 4",
    "3 4 5",
    ""
    ]
# note: order is lexicographic in case of ties
TOP_BIGRAMS =  ["",  "1 2",  "2 4",  "3 4",  ""]
TOP_UNIGRAMS = ["0",  "1",    "2",    "3",    ""]

# Environment settings
## OLD:
## HOME = system.getenv_text(
##     "HOME", "~",
##     description="Home directory for user")
## USING_GITHUB_RUNNER = ("/home/runner" in HOME)
USING_GITHUB_RUNNER_DEFAULT = ("/home/runner" in gh.HOME_DIR)
USING_GITHUB_RUNNER = system.getenv_bool(
    "USING_GITHUB_RUNNER", USING_GITHUB_RUNNER_DEFAULT,
    desc="Whether likely using the Github Actions runner VM")

class TestMisc(TestWrapper):
    """Class for test case definitions"""
    script_module= None
    use_temp_base_dir = True

    def setUp(self):
        """Performs test setup with capsys disabled
           Note: This works around quirk with pytest stderr capturing"""
        with self.capsys.disabled():
            super().setUp()
    
    ## OLD:
    ## @pytest.fixture(autouse=True)
    ## def capsys(self, capsys):
    ##     """Gets capsys"""
    ##     self.capsys = capsys

    @pytest.mark.xfail                   # TODO: remove xfail
    @trap_exception
    def test_01_simple_tfidf(self):
        """Verify top term for each document by TF/IDF using unigrams and bigrams"""
        debug.trace(4, "test_01_simple_tfidf()")
        uni_corpus = Corpus(min_ngram_size=1, max_ngram_size=1)
        bi_corpus = Corpus(min_ngram_size=2, max_ngram_size=2)

        # Add text to collections
        for d, doc_text in enumerate(DOCUMENT_DATA):
            uni_corpus[d + 1] = doc_text
            bi_corpus[d + 1] = doc_text

        # Make sure top term is expected (n.b., sorted in case of ties)
        debug.assertion(len(DOCUMENT_DATA) == len(uni_corpus.keys()))
        for d, docid in enumerate(uni_corpus.keys()):
            #
            def is_top_term(top_term, corpus_info):
                """Whether TOP_TERM is top for CORPUS_INFO document D"""
                ## OLD: corpus_terms = [term for (term, _score) in list(corpus_info)]
                corpus_terms = [keyword.ngram for keyword in list(corpus_info)]
                ok = False
                if not top_term:
                    ok = not corpus_terms
                else:
                    ok = (top_term == sorted(corpus_terms)[0])
                debug.trace_expr(5, top_term, corpus_terms)
                return ok
            #
            self.do_assert(is_top_term(TOP_UNIGRAMS[d], uni_corpus.get_keywords(docid)))
            self.do_assert(is_top_term(TOP_BIGRAMS[d], bi_corpus.get_keywords(docid)))
        debug.trace(5, "out test_01_simple_tfidf()")

    @pytest.mark.xfail                   # TODO: remove xfail
    @pytest.mark.skipif(not USING_GITHUB_RUNNER,
                        reason="The following is only for the Github runner VM")
    def test_02_no_dockeyword_tracing(self):
        """Make sure no debug calls in DocKeyword class
           Note: This is intended as a sanity check to ensure the debug calls aren't
           checked in by accident. That is, the '## DEBUG:' prefix should only be
           removed in a local version."""
        # Set the highest-possible debugging level
        ## TODO2: use monkey patch
        save_debug_level = debug.get_level()
        debug.set_level(system.MAX_INT)
        # note: make sure stderr empty by capturing it before initializer (DocKeyword).
        # In addition, the setup method ensures that capsys is disabed beforehand.
        ## OLD: pre_init_stderr_text = self.capsys.readouterr().err
        self.clear_stdout_stderr()
        pre_init_stderr_text = self.get_stderr()

        # Perform the test proper
        dummy_word = "dummy"
        dk = DocKeyword(dummy_word)
        ## OLD: init_stderr_text = self.capsys.readouterr().err
        init_stderr_text = self.get_stderr()
        debug.trace_expr(5, pre_init_stderr_text, init_stderr_text, dk)
        self.do_assert(not init_stderr_text.strip())
        self.do_assert(dk.text == dummy_word)

        # Post-test sanity checks
        debug.assertion(isinstance(pre_init_stderr_text, str))
        debug.assertion(isinstance(init_stderr_text, str))
        debug.set_level(save_debug_level)
