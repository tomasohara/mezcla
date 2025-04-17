#! /usr/bin/env python3
#
# Test(s) for ../document.py

"""Tests for tfidf document submodule"""

# Standard packages
import math

# Installed modules
import pytest

# Local modules
from mezcla.unittest_wrapper import TestWrapper
from mezcla import debug
from mezcla.tfidf.preprocess import Preprocessor

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                        global module object
import mezcla.tfidf.document as THE_MODULE

# ------------------------------------------------------------------------


class TestPreprocess(TestWrapper):
    """Class for testcase definition"""

    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    text = "my man fran is not a man"
    doc = THE_MODULE.Document(text, Preprocessor(gramsize=1, stemmer=lambda x: x))

    @classmethod
    def setUpClass(cls, filename=None, module=None):
        """One-time initialization (i.e., for entire class)"""
        debug.trace(6, f"TestPreprocess.setUpClass(); cls={cls}")
        # note: should do parent processing first
        super().setUpClass(filename, module)
        debug.trace_object(5, cls, label=f"{cls.__class__.__name__} instance")

    @pytest.mark.xfail  # TODO: remove xfail
    def test_01_tf_freq(self):
        """test frequency of ngram in document"""
        # count appareances of different ngrams in document
        man_freq = self.doc.tf_freq("man")
        fran_freq = self.doc.tf_freq("fran")
        peter_freq = self.doc.tf_freq("peter")
        # assert the reported amount is correct
        assert man_freq == 2
        assert fran_freq == 1
        assert peter_freq == 0

    @pytest.mark.xfail  # TODO: remove xfail
    def test_02_tf_raw(self):
        """Tests relative frequency of ngram in document"""
        old_pensalize_singletons = THE_MODULE.PENALIZE_SINGLETONS
        self.monkeypatch.setattr(THE_MODULE, "PENALIZE_SINGLETONS", True)
        assert self.doc.tf_raw("fran") == 0
        assert self.doc.tf_raw("man") == 2 / 7
        self.monkeypatch.setattr(THE_MODULE, "PENALIZE_SINGLETONS", False)
        new_tf_fran = self.doc.tf_raw("fran")
        self.monkeypatch.setattr(
            THE_MODULE, "PENALIZE_SINGLETONS", old_pensalize_singletons
        )
        assert new_tf_fran == 1 / 7

    @pytest.mark.xfail  # TODO: remove xfail
    def test_03_tf_log(self):
        """Tests log frequency of ngram in document"""
        # TODO: point out relation between tf_raw and tf_freq
        old_pensalize_singletons = THE_MODULE.PENALIZE_SINGLETONS
        self.monkeypatch.setattr(THE_MODULE, "PENALIZE_SINGLETONS", True)
        man_log_freq = self.doc.tf_log("man")
        self.monkeypatch.setattr(
            THE_MODULE, "PENALIZE_SINGLETONS", old_pensalize_singletons
        )
        assert man_log_freq == (1 + math.log(2 / 7))

    @pytest.mark.xfail  # TODO: remove xfail
    def test_04_tf_binary(self):
        """Tests binary term frequency"""
        assert self.doc.tf_binary("man") == 1
        assert self.doc.tf_binary("dog") == 0

    @pytest.mark.xfail  # TODO: remove xfail
    def test_04_tf_norm_50(self):
        """Tests double normalized ngram frequency"""
        old_pensalize_singletons = THE_MODULE.PENALIZE_SINGLETONS
        self.monkeypatch.setattr(THE_MODULE, "PENALIZE_SINGLETONS", False)
        man_norm_freq = self.doc.tf_norm_50("man")
        fran_norm_freq = self.doc.tf_norm_50("fran")
        self.monkeypatch.setattr(
            THE_MODULE, "PENALIZE_SINGLETONS", old_pensalize_singletons
        )
        assert man_norm_freq == 0.5 + (0.5 * (2/7) / 2)
        assert fran_norm_freq == 0.5 + (0.5 * (1/7) / 2)

    @pytest.mark.xfail  # TODO: remove xfail
    def test_05_max_raw_frequency(self):
        """Tests doc's max raw frequency"""
        assert self.doc.max_raw_frequency == self.doc.tf_freq("man")

    @pytest.mark.xfail  # TODO: remove xfail
    def test_06_keywordset(self):
        """Tests the set of keywords in the document and their location"""
        keywords = self.doc.keywordset
        text = self.doc.text
        for word, keyword in keywords.items():
            for location_set in keyword.locations:
                location = list(location_set)
                start = location[1]
                end = location[2]
                assert word == text[start:end]
    
    @pytest.mark.xfail # TODO: remove xfail
    def test_07_len(self):
        """Tests the length of the document is calculated correctly"""
        assert len(self.doc) == 7
        
    
    


# ------------------------------------------------------------------------

if __name__ == "__main__":

    debug.trace_current_context()
    ## TODO2: here and elsewhere: invoke_tests(__file__)
    pytest.main([__file__])
