#! /usr/bin/env python3
#
# Test(s) for ../text_processing.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_text_processing.py
#
# TODO1: Combine testes classes into one.
# TODO2: Remove RUN_SLOW_TESTS from test_chunk_noun_phrases.
# TODO3: Remove xfail's.
#

"""Tests for text_processing module"""

# Standard packages
import pytest
import re
# Installed packages

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import system
from mezcla.my_regex import my_re
from mezcla.unittest_wrapper import TestWrapper, UNDER_COVERAGE, RUN_SLOW_TESTS
from mezcla.unittest_wrapper import trap_exception, invoke_tests

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
try:
    import mezcla.text_processing as THE_MODULE
except:
    THE_MODULE = None
    system.print_exception_info("text_processing import")    

# Constants
RESOURCES = gh.form_path(f'{gh.dir_path(__file__)}', 'resources')
TEXT_EXAMPLE = gh.form_path(f'{RESOURCES}', 'example_text.txt')
TEXT_EXAMPLE_TAGS = gh.form_path(f'{RESOURCES}', 'example_text_tags.txt')
WORD_POS_FREQ_FILE = gh.form_path(f'{RESOURCES}', 'word-POS.freq')
WORD_FREQ_FILE = gh.form_path(f'{RESOURCES}', 'word.freq')
NLTK_DIR = system.getenv_text(
    "NLTK_DIR", gh.form_path(gh.HOME_DIR, "nltk_data"),
    desc="Directory for NLTK data")
                             

class TestTextProcessing(TestWrapper):
    """Class for testcase definition"""
    script_file = TestWrapper.get_module_file_path(__file__)
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    def test_split_sentences(self):
        """Ensure split_sentences works as expected"""
        debug.trace(4, "test_split_sentences()")
        assert THE_MODULE.split_sentences("I came. I saw. I conquered!") == ["I came.", "I saw.", "I conquered!"]
        assert THE_MODULE.split_sentences("Dr. Watson, it's elementary. But why?") == ["Dr. Watson, it's elementary.", "But why?"]

    def test_split_word_tokens(self):
        """Ensure split_word_tokens works as expected"""
        debug.trace(4, "test_split_word_tokens()")
        assert THE_MODULE.split_word_tokens("How now, brown cow?") == ['How', 'now', ',', 'brown', 'cow', '?']

    def test_nltk_double_quotes(self):
        """Verify double quoting restored with NLTK tokenization"""
        debug.trace(4, "test_nltk_double_quotes()")
        assert (THE_MODULE.split_word_tokens('I said "No!"', undo_nltk_quoting=False)
                == ['I', 'said', '``', 'No', '!', "''"])
        assert (THE_MODULE.split_word_tokens('I said "No!"', undo_nltk_quoting=True)
                == ['I', 'said', '"', 'No', '!', '"'])

    def test_label_for_tag(self):
        """Ensure label_for_tag works as expected"""
        debug.trace(4, "test_label_for_tag()")
        ## OLD: previous_value = THE_MODULE.KEEP_PUNCT
        
        self.monkeypatch.setattr(THE_MODULE, 'KEEP_PUNCT', True)
        assert THE_MODULE.label_for_tag("SYM", ',') == ','
        assert THE_MODULE.label_for_tag("SYM", '?') == '?'
        self.monkeypatch.setattr(THE_MODULE, 'KEEP_PUNCT', False)
        assert THE_MODULE.label_for_tag("SYM", ',') == 'SYM'
        assert THE_MODULE.label_for_tag("SYM", '?') == 'SYM'
        ## OLD: self.monkeypatch.setattr(THE_MODULE, 'KEEP_PUNCT', previous_value)
        

    def test_class_for_tag(self):
        """Ensure class_for_tag works as expected"""
        debug.trace(4, "test_class_for_tag()")
        assert THE_MODULE.class_for_tag("NNS") == "noun"
        assert THE_MODULE.class_for_tag("VBG") == "verb"
        assert THE_MODULE.class_for_tag("VBG", previous="MD") == "verb"
        assert THE_MODULE.class_for_tag("NNP", word="(") == "punctuation"

    def test_tag_part_of_speech(self):
        """Ensure tag_part_of_speech works as expected"""
        debug.trace(4, "test_tag_part_of_speech()")
        # NOTE:
        #   'brown' tagged as IN is wrong, should be JJ, this is a problem related to NLTK
        #   not the module being tested, so we are ignoring it for now.
        #   Related: https://stackoverflow.com/a/30823202
        assert THE_MODULE.tag_part_of_speech(['How', 'now', ',', 'brown', 'cow', '?']) == [('How', 'WRB'), ('now', 'RB'), (',', ','), ('brown', 'IN'), ('cow', 'NN'), ('?', '.')]

    def test_tokenize_and_tag(self):
        """Ensure tokenize_and_tag works as expected"""
        debug.trace(4, "test_tokenize_and_tag()")
        # NOTE:
        #   'brown' tagged as IN is wrong, should be JJ, this is a problem related to NLTK
        #   not the module being tested, so we are ignoring it for now.
        #   Related: https://stackoverflow.com/a/30823202
        assert THE_MODULE.tokenize_and_tag("How now, brown cow ?") == [('How', 'WRB'), ('now', 'RB'), (',', ','), ('brown', 'IN'), ('cow', 'NN'), ('?', '.')]

    def test_tokenize_text(self):
        """Ensure tokenize_text works as expected"""
        debug.trace(4, "test_tokenize_text()")
        assert THE_MODULE.tokenize_text("I came. I saw. I conquered!") == [['I', 'came', '.'], ['I', 'saw', '.'], ['I', 'conquered', '!']]

    def test_is_stopword(self):
        """Ensure is_stopword works as expected"""
        debug.trace(4, "test_is_stopword()")
        assert THE_MODULE.is_stopword('we')
        assert THE_MODULE.is_stopword('i')
        assert not THE_MODULE.is_stopword('cow')

    @pytest.mark.xfail
    def test_has_spelling_mistake(self):
        """Ensure has_spelling_mistake works as expected"""
        debug.trace(4, "test_has_spelling_mistake()")
        # Note: overrides the word frequency file used if Enchant skip;
        # the corresponding hash needs to be reset when changed.
        ## OLD: previous_value = THE_MODULE.SKIP_ENCHANT
        self.monkeypatch.setattr(THE_MODULE, 'SKIP_ENCHANT', True)
        self.monkeypatch.setattr(THE_MODULE, 'WORD_FREQ_FILE', WORD_FREQ_FILE)
        self.monkeypatch.setattr(THE_MODULE, 'word_freq_hash', None)
        assert not THE_MODULE.has_spelling_mistake('the')
        assert THE_MODULE.has_spelling_mistake('ai')
        # HACK: modifies module to ensure enchant loaded (TODO4: add init function)
        import enchant                  # pylint: disable=import-outside-toplevel
        self.monkeypatch.setattr(THE_MODULE, 'enchant', enchant)
        self.monkeypatch.setattr(THE_MODULE, 'SKIP_ENCHANT', False)
        self.monkeypatch.setattr(THE_MODULE, 'word_freq_hash', None)
        assert not THE_MODULE.SKIP_ENCHANT
        assert THE_MODULE.has_spelling_mistake('sneik')
        assert not THE_MODULE.has_spelling_mistake('snake')
        ## OLD: self.monkeypatch.setattr(THE_MODULE, 'SKIP_ENCHANT', previous_value)

    def test_read_freq_data(self):
        """Ensure read_freq_data works as expected"""
        debug.trace(4, "test_read_freq_data()")
        lines = gh.read_lines(WORD_FREQ_FILE)
        freq = THE_MODULE.read_freq_data(WORD_FREQ_FILE)
        for line in lines:
            if line.startswith("#"):
                continue
            token = re.match(r'^.+?(?=\s)', line).group(0).lower()
            self.do_assert(freq[token])


    def test_read_word_POS_data(self): # pylint: disable=invalid-name
        """Ensure read_word_POS_data works as expected"""
        debug.trace(4, "test_read_word_POS_data()")
        lines = gh.read_lines(WORD_POS_FREQ_FILE)
        freq_pos = THE_MODULE.read_word_POS_data(WORD_POS_FREQ_FILE)
        for line in lines:
            if line.startswith("#"):
                continue
            token = re.match(r'^.+?(?=\s)', line).group(0).lower()
            self.do_assert(freq_pos[token])

    def test_get_most_common_POS(self): # pylint: disable=invalid-name
        """Ensure get_most_common_POS works as expected"""
        debug.trace(4, "test_get_most_common_POS()")
        # Testing if word_POS_hash is not none
        THE_MODULE.word_POS_hash = {
            'can': 'MD'
        }
        assert THE_MODULE.get_most_common_POS("notaword") == "NN"
        assert THE_MODULE.get_most_common_POS("can") == "MD"
        # Test reading from freq file
        ## TODO: for some reason this assertion freezes
        ## THE_MODULE.WORD_POS_FREQ_FILE = 'tests/resources/word-POS.freq'
        ## assert THE_MODULE.get_most_common_POS("to") == "TO"

    def test_is_noun(self):
        """Ensure is_noun works as expected"""
        debug.trace(4, "test_is_noun()")
        assert THE_MODULE.is_noun('notaword', 'NN')
        assert not THE_MODULE.is_noun('can', 'MD')

    def test_is_verb(self):
        """Ensure is_verb works as expected"""
        debug.trace(4, "test_is_verb()")
        assert THE_MODULE.is_verb('run', 'VB')
        assert not THE_MODULE.is_verb('can', 'NN')

    def test_is_adverb(self):
        """Ensure is_adverb works as expected"""
        debug.trace(4, "test_is_adverb()")
        assert THE_MODULE.is_adverb('quickly', 'RB')
        assert not THE_MODULE.is_adverb('can', 'MD')

    def test_is_adjective(self):
        """Ensure is_adjective works as expected"""
        debug.trace(4, "test_is_adjective()")
        assert THE_MODULE.is_adjective('quick', 'JJ')
        assert not THE_MODULE.is_adjective('can', 'MD')

    def test_is_comma(self):
        """Ensure is_comma works as expected"""
        debug.trace(4, "test_is_comma()")
        assert THE_MODULE.is_comma('comma', ',')
        assert THE_MODULE.is_comma(',', 'comma')
        assert not THE_MODULE.is_comma('can', 'MD')

    def test_is_quote(self):
        """Ensure is_quote works as expected"""
        debug.trace(4, "test_is_quote()")
        assert THE_MODULE.is_quote('\'', '')
        assert THE_MODULE.is_quote('\"', '')
        assert not THE_MODULE.is_quote('can', 'MD')

    def test_is_punct(self):
        """Ensure is_punct works as expected"""
        debug.trace(4, "test_is_punct()")
        assert THE_MODULE.is_punct('$', '$')
        assert not THE_MODULE.is_punct('can', 'MD')

    def test_usage(self):
        """Ensure usage works as expected"""
        debug.trace(4, "test_usage()")
        THE_MODULE.usage()
        captured = self.get_stderr()
        assert f"Usage: {THE_MODULE.__file__} [--help] [--just-tokenize] [--just-chunk] [--lowercase] file" in captured
        assert f"echo \"My dawg has fleas.\" | {THE_MODULE.__file__} -" in captured
        assert "- Intended more as a library module" in captured
        assert "- In standalone mode it runs the text processing pipeline over the file:" in captured
        assert "sentence splitting, word tokenization, and part-of-speech tagging" in captured
        assert "- Set SKIP_NLTK environment variable to 1 to disable NLTK usage." in captured

class TestTextProcessingScript(TestWrapper):
    """Class for testcase definition"""
    script_file = TestWrapper.get_module_file_path(__file__)
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.xfail
    def test_all(self):
        """Ensure text_processing without argument works as expected"""
        debug.trace(4, "test_all()")
        output = [tag.strip() for tag in self.run_script(data_file=TEXT_EXAMPLE).split(',')]
        expected_tags = [tag.strip() for tag in gh.read_file(TEXT_EXAMPLE_TAGS)[:-1].split(',')]
        for output_tag, expected_tag in zip(output, expected_tags):
            assert output_tag == expected_tag

    @pytest.mark.xfail
    def test_just_tokenize(self):
        """Ensure just_tokenize argument works as expected"""
        debug.trace(4, "test_just_tokenize()")
        tokenized_text = self.run_script(data_file=TEXT_EXAMPLE,options="--just-tokenize")
        non_tokenized_text = gh.read_file(TEXT_EXAMPLE)
        # match every token except whitespaces, 
        # that way tokenized and non-tokenized texts are equals 
        matches_tokenized = my_re.match(r'\S', tokenized_text).groups()
        matches_normal = my_re.match(r'\S', non_tokenized_text).groups()
        assert matches_tokenized == matches_normal
        assert not tokenized_text == non_tokenized_text
        # self.do_assert(output == '', "TODO: code test")

    def test_make_lowercase(self):
        """Ensure make_lowercase argument works as expected"""
        debug.trace(4, "test_make_lowercase()")
        output_normal = self.run_script(data_file=TEXT_EXAMPLE,options="--just-tokenize")
        output_lower = self.run_script(data_file=TEXT_EXAMPLE,options="--just-tokenize --lowercase")
        self.do_assert(output_lower == output_normal.lower(), "TODO: code test")

    @pytest.mark.skipif(not RUN_SLOW_TESTS, reason="Ignoring slow test")
    @pytest.mark.xfail
    def test_download_nltk_resources(self):
        """Makes sure download_nltk_resources actually does so"""
        THE_MODULE.download_nltk_resources()
        resource_info = [
            ("tokenizers", ["punkt", "punkt_tab"]),
            ("taggers", ["averaged_perceptron_tagger", "averaged_perceptron_tagger_eng"]),
            ("corpora", ["stopwords"])]
        for subdir, resource_names in resource_info:
            for resource in resource_names:
                assert system.is_directory(
                    gh.form_path(NLTK_DIR, subdir, resource))
        return


class TestTextProc(TestWrapper):
    """Test TextProc classes"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.xfail
    @pytest.mark.skipif(not RUN_SLOW_TESTS, reason="Ignoring slow test")
    ## DEBUG:
    @pytest.mark.skipif(UNDER_COVERAGE,reason="skipped because crashes when run under coverage")
    @trap_exception            # TODO: remove when debugged
    def test_chunk_noun_phrases(self):
        """Make sure sentences split into NPs properly"""
        sentence = "The cat is on the mat by the door"
        expected = ["The cat", "the mat", "the door"]
        min_overlap = 2
        stp = THE_MODULE.SpacyTextProc()
        stp_nps = stp.noun_phrases(sentence)
        self.do_assert(len(system.intersection(stp_nps, expected)) >= min_overlap)
        ftp = THE_MODULE.FlairTextProc()
        ftp_nps = ftp.noun_phrases(sentence)
        self.do_assert(len(system.intersection(stp_nps, ftp_nps)) >= min_overlap)
    

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
