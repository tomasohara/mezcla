#! /usr/bin/env python3
#
# Test(s) for ../corpus.py

"""Tests for tfidf corpus submodule"""

# Standard packages
import math

# Installed modules
import pytest

# Local modules
from mezcla.unittest_wrapper import TestWrapper
from mezcla import debug
from mezcla import system
from mezcla.tfidf.preprocess import Preprocessor

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                        global module object
import mezcla.tfidf.corpus as THE_MODULE

# ------------------------------------------------------------------------


class TestPreprocess(TestWrapper):
    """Class for testcase definition"""
    
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    
    THE_MODULE.NGRAM_EPSILON = 0
    corp = THE_MODULE.Corpus(
        preprocessor=Preprocessor(gramsize=1, language='english')
    )
    corp_2 = THE_MODULE.Corpus(
        preprocessor=Preprocessor(gramsize=1, language='english')
    )
    
    text_1 = "The quick brown fox jumps over the lazy dog. The fox is cunning and swift."
    text_2 = "A lazy cat sleeps in the warm sunlight. The cat ignores the playful dog nearby."
    text_3 = "Dogs and foxes are both members of the canine family. Some dogs are as quick as foxes."
    
    corp["doc_1"] = text_1
    corp["doc_2"] = text_2
    corp["doc_3"] = text_3
    
    @classmethod
    def setUpClass(cls, filename=None, module=None):
        """One-time initialization (i.e., for entire class)"""
        debug.trace(6, f"TestPreprocess.setUpClass(); cls={cls}")
        # note: should do parent processing first
        super().setUpClass(filename, module)
        debug.trace_object(5, cls, label=f"{cls.__class__.__name__} instance")

    @pytest.mark.xfail  # TODO: remove xfail
    def test_01_df_freq(self):
        """test document frequency for ngram"""
        assert self.corp.df_freq('dog') == 3
        assert self.corp.df_freq('fox') == 2
            
    @pytest.mark.xfail  # TODO: remove xfail
    def test_02_df_norm(self):
        """Tests the document freq for an ngram normalized
        by the max doc frequency"""
        assert self.corp.df_norm('dog') == 1
        assert self.corp.df_norm('fox') == 2/3
        
    @pytest.mark.xfail  # TODO: remove xfail
    def test_03_idf_basic(self):
        """Test IDF with basic normalization"""
        assert self.corp.idf_basic('dog') == 0
        assert self.corp.idf_basic('fox') == math.log(3/2)
        
    @pytest.mark.xfail  # TODO: remove xfail
    def test_04_idf_freq(self):
        """Test IDF doc freq"""
        assert self.corp.idf_freq('dog') ==  1 / 3
        assert self.corp.idf_freq('fox') ==  1 / 2

    @pytest.mark.xfail  # TODO: remove xfail
    def test_05_idf_smooth(self):
        """Test IDF with simple smoothing"""
        assert self.corp.idf_smooth('dog') == math.log(2)
        assert self.corp.idf_smooth('fox') == math.log(1 + 3/2)
        
    @pytest.mark.xfail  # TODO: remove xfail
    def test_06_idf_max(self):
        """Test IDF with max TF and add-1 smoothing"""
        assert self.corp.idf_max('dog') == math.log(1 + (2/3))
        assert self.corp.idf_max('fox') == math.log(2)
    
    @pytest.mark.xfail  # TODO: remove xfail
    def test_07_idf_probabilistic(self):
        """Test IDF via probabilistic interpretation"""
        ## OLD:
        ## assert self.corp.idf_probabilistic('dog') == math.log(1)
        ## assert self.corp.idf_probabilistic('fox') == math.log(3/2)
        # Note:
        # IDF_prob = log((N - DF)/DF + epsilon) for N docs and DF doc. freq.
        # dog => log((3 - 3) / 3 + epsilon); fox => log((3 - 2) / 2 + epsilon)
        assert system.round3(self.corp.idf_probabilistic('dog')) == -13.816
        assert system.round3(self.corp.idf_probabilistic('fox')) == -0.693
    
    @pytest.mark.xfail  # TODO: remove xfail
    def test_08_tf_idf(self):
        """Test term frequency/inverse document frequency"""
        assert self.corp.tf_idf('dog', 'doc_3', tf_weight='basic').score == 0
        assert self.corp.tf_idf('fox', 'doc_3', tf_weight='basic').score == 0.25 * math.log(3/2)
        
    @pytest.mark.xfail  # TODO: remove xfail
    def test_09_get_keywords(self):
        """Test ngram keywords with scores"""
        keywords = self.corp.get_keywords('doc_1')
        doc = self.corp['doc_1']
        for keyword in keywords:
            assert keyword.ngram in doc
# ------------------------------------------------------------------------

if __name__ == "__main__":

    debug.trace_current_context()
    ## TODO2: here and elsewhere: invoke_tests(__file__)
    pytest.main([__file__])
