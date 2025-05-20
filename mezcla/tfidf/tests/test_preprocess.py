#! /usr/bin/env python3
#
# Test(s) for ../preprocess.py

"""Tests for tfidf preprocess submodule"""

# Standard packages
import html

# Installed modules
import pytest

# Local modules
from mezcla.unittest_wrapper import TestWrapper
from mezcla import debug

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                        global module object
import mezcla.tfidf.preprocess as THE_MODULE

# ------------------------------------------------------------------------

# TODO: add variety to tests
# TODO: review monkey patching on undoing modifications
class TestPreprocess(TestWrapper):
    """Class for testcase definition"""

    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @classmethod
    def setUpClass(cls, filename=None, module=None):
        """One-time initialization (i.e., for entire class)"""
        debug.trace(6, f"TestPreprocess.setUpClass(); cls={cls}")
        # note: should do parent processing first
        super().setUpClass(filename, module)
        debug.trace_object(5, cls, label=f"{cls.__class__.__name__} instance")

    @pytest.mark.xfail  # TODO: remove xfail
    def test_01_full_yield_keywords(self):
        """Tests yield_keywords"""
        ## TODO2: remove monkeypatch since the prep class can be re-instantiated
        text = "my man fran is not a man"
        prep = THE_MODULE.Preprocessor(gramsize=2)
        debug.trace_object(5, prep)
        old_env = THE_MODULE.USE_SKLEARN_COUNTER
        # run yield_keywords with USE_SKLEARN_COUNTER = False
        # so it uses full_yield_keywords
        ## BAD: self.monkeypatch.setattr(THE_MODULE, "USE_SKLEARN_COUNTER", False)
        prep.use_sklearn_counter = False
        full_ngrams = list(p.text for p in prep.yield_keywords(text))
        # set the env var back to previous state
        self.monkeypatch.setattr(THE_MODULE, "USE_SKLEARN_COUNTER", old_env)
        assert "my man" in full_ngrams
        assert "not a" in full_ngrams
        assert "my man fran" not in full_ngrams
        assert "fran man" not in full_ngrams

        #  run yield_keywords with USE_SKLEARN_COUNTER = True
        #  so it uses quick_yield_keywords
        ## BAD: self.monkeypatch.setattr(THE_MODULE, "USE_SKLEARN_COUNTER", True)
        prep.use_sklearn_counter = True
        quick_ngrams = list(p.text for p in prep.yield_keywords(text))
        assert "my man" in quick_ngrams
        assert "not a" not in quick_ngrams
        assert "my man fran" not in quick_ngrams
        assert "fran man" not in quick_ngrams

        # since full_ngrams has offsets, it should have more ngrams
        assert len(full_ngrams) > len(quick_ngrams)

    @pytest.mark.xfail  # TODO: remove xfail
    def test_02_preprocessor_normalize_term(self):
        """tests Preprocessor.normalize_term"""
        prep = THE_MODULE.Preprocessor(language="english")
        text = "<body>\u00a1MY FLYING MAN- FRAN IS NOT A LYING MAN !\n </body>"
        escaped_text = html.escape(text)
        assert (
            prep.normalize_term(escaped_text)
            == "<body> ¡ fli man; fran lie man ! </body>"
        )

    @pytest.mark.xfail  # TODO: remove xfail
    def test_03_clean_text(self):
        """Tests clean_text"""
        text = html.escape("<body>\u00a1MY MAN- FRAN IS NOT A MAN !\n </body>")
        old_skip_cleaning = THE_MODULE.SKIP_WORD_CLEANING
        old_preserve_case = THE_MODULE.TFIDF_PRESERVE_CASE

        # first test no-op if SKIP_WORD_CLEANING
        self.monkeypatch.setattr(THE_MODULE, "SKIP_WORD_CLEANING", True)
        text_skip_cleaning = THE_MODULE.clean_text(text)
        assert text_skip_cleaning == text

        # cleaning with no SKIP_WORD_CLEANING and TFIDF_PRESERVE_CASE
        self.monkeypatch.setattr(THE_MODULE, "SKIP_WORD_CLEANING", False)
        self.monkeypatch.setattr(THE_MODULE, "TFIDF_PRESERVE_CASE", True)
        text_clean_preserve_case = THE_MODULE.clean_text(text)
        assert (
            text_clean_preserve_case == "<body> ¡ MY MAN; FRAN IS NOT A MAN ! </body>"
        )

        # cleaning with no SKIP_WORD_CLEANING and no TFIDF_PRESERVE_CASE
        self.monkeypatch.setattr(THE_MODULE, "TFIDF_PRESERVE_CASE", False)
        text_clean_no_preserve_case = THE_MODULE.clean_text(text)

        # restore previous env vars
        self.monkeypatch.setattr(THE_MODULE, "TFIDF_PRESERVE_CASE", old_preserve_case)
        self.monkeypatch.setattr(THE_MODULE, "SKIP_WORD_CLEANING", old_skip_cleaning)

        assert text_clean_no_preserve_case == text_clean_preserve_case.lower()

    @pytest.mark.xfail  # TODO: remove xfail
    def test_04_handle_unicode(self):
        """Tests handle_unicode"""
        text1 = "handle unicode\u00A9"
        assert THE_MODULE.handle_unicode(text1) == "handle unicode \u00A9"

        text2 = "handle unicode\u0100"
        assert THE_MODULE.handle_unicode(text2) != "handle unicode \u0100"

    @pytest.mark.xfail  # TODO: remove xfail
    def test_05_handle_html_unquote(self):
        """Tests handle_html_unquote"""
        text = "<body> handle html </body>"
        escaped_text = html.escape(text)
        assert escaped_text == "&lt;body&gt; handle html &lt;/body&gt;"
        assert THE_MODULE.handle_html_unquote(escaped_text) == text

    @pytest.mark.xfail  # TODO: remove xfail
    def test_06_handle_mac_quotes(self):
        """Tests handle_mac_quotes"""
        text_double_quoted = "my man fran is not a “man”"
        text_single_quotes = "my man fran is not a ‘man’"
        assert (
            THE_MODULE.handle_mac_quotes(text_double_quoted)
            == 'my man fran is not a "man"'
        )
        assert (
            THE_MODULE.handle_mac_quotes(text_single_quotes)
            == "my man fran is not a 'man'"
        )

    @pytest.mark.xfail  # TODO: remove xfail
    def test_07_handle_text_break_dash(self):
        """Tests handle_text_break_dash"""
        text_dash_break = "my man fran- is not a man"
        text_no_dask_break = "my man fran is not a 27-year-old man"

        assert (
            THE_MODULE.handle_text_break_dash(text_dash_break)
            == "my man fran; is not a man"
        )
        assert (
            THE_MODULE.handle_text_break_dash(text_no_dask_break)
            == text_no_dask_break
        )

    @pytest.mark.xfail  # TODO: remove xfail
    def test_08_preprocessor_handle_stopwords(self):
        """tests Preprocessor.handle_stopwords"""
        prep = THE_MODULE.Preprocessor(language="english")
        text = "my man fran is not a man"

        assert prep.handle_stopwords(text) == "man fran man"

    @pytest.mark.xfail  # TODO: remove xfail
    def test_09_preprocessor_stem_term_english(self):
        """tests Preprocessor.stem_term with english language"""
        prep = THE_MODULE.Preprocessor(language="english")
        text = "my flying man fran is not a lying man"
        assert prep.stem_term(text) == "my fli man fran is not a lie man"



# ------------------------------------------------------------------------

if __name__ == "__main__":

    debug.trace_current_context()
    ## TODO2: here and elsewhere: invoke_tests(__file__)
    pytest.main([__file__])
