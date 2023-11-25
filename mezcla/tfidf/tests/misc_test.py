#! /usr/bin/env python
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
from mezcla.unittest_wrapper import TestWrapper
from mezcla.unittest_wrapper import trap_exception
from mezcla.tfidf.corpus import Corpus

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


class TestMisc(TestWrapper):
    """Class for test case definitions"""
    script_module= None
    use_temp_base_dir = True

    @pytest.mark.xfail                   # TODO: remove xfail
    @trap_exception
    def test_01_simple_tfidf(self):
        """Verify top term for each document by TF/IDF using unigrams and bigrams"""
        debug.trace(4, "test_01_simple_tfidf()")
        uni_corpus = Corpus(min_ngram_size=1, max_ngram_size=1)
        bi_corpus = Corpus(min_ngram_size=2, max_ngram_size=2)

        # Add text to collections
        for d, doc_text in enumerate(DOCUMENT_DATA):
            uni_corpus[d] = doc_text
            bi_corpus[d] = doc_text

        # Make sure top term is expected (n.b., sorted in case of ties)
        for d in uni_corpus.keys():
            self.do_assert(TOP_UNIGRAMS[d] in uni_corpus.get_keywords(d)[0: 1])
            self.do_assert(TOP_BIGRAMS[d] in bi_corpus.get_keywords(d)[0: 1])
