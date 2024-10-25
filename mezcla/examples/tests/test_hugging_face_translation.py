#! /usr/bin/env python
#
# Test(s) for ../hugging_face_translation.py
#

"""Tests for hugging_face_translation module"""

# Standard modules
## TODO: from collections import defaultdict

# Installed modules
from transformers import pipeline
import pytest

# Local modules
from mezcla.unittest_wrapper import TestWrapper
from mezcla.unittest_wrapper import trap_exception
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                        global module object
#    TestIt.script_module:              path to file
import mezcla.examples.hugging_face_translation as THE_MODULE

## TODO: Use dynamic (conditional) test fixtures for pipeline
#
# Note: sanity test for customization (TODO: remove if desired)
if not my_re.search(__file__, r"\btemplate.py$"):
    debug.assertion("mezcla.template" not in str(THE_MODULE))

# TEMP FIX: Path specification for mezcla scripts
PATH1 = "$PWD/mezcla/examples/hugging_face_translation.py"
PATH2 = "$PWD/examples/hugging_face_translation.py"
PATH3 = "$PWD/hugging_face_translation.py"
PATH4 = "../hugging_face_translation.py"
PWD_COMMAND = "echo $PWD"
echo_pwd = gh.run(PWD_COMMAND)
if echo_pwd.endswith("/mezcla/mezcla/examples"):
    HF_TRANSLATION_PATH = PATH3
elif echo_pwd.endswith("/mezcla/mezcla"):
    HF_TRANSLATION_PATH = PATH2
elif echo_pwd.endswith("/mezcla"):
    HF_TRANSLATION_PATH = PATH1
else:
    HF_TRANSLATION_PATH = PATH4
# ------------------------------------------------------------------------


class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""

    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    # Helper functions to return models
    def helper_return_models(self, source_lang="en", target_lang="es"):
        """Returns translation models according to the pipelines"""
        debug.trace(5, f"helper_return_models({source_lang}, {target_lang})")
        model = pipeline(
            task=f"translation_{source_lang}_to_{target_lang}",
            model=f"Helsinki-NLP/opus-mt-{source_lang}-{target_lang}",
        )
        model_reverse = pipeline(
            task=f"translation_{target_lang}_to_{source_lang}",
            model=f"Helsinki-NLP/opus-mt-{target_lang}-{source_lang}",
        )
        return model, model_reverse

    def helper_filter_text(self, input_str):
        """Returns the sentence with all characters removed except alphabets"""
        debug.trace(5, f"helper_return_models({input_str})")
        result = my_re.sub(r"[^a-zA-Z]", "", input_str)
        return result.lower()

    @pytest.mark.xfail  # TODO: remove xfail
    @trap_exception
    def test_data_file(self):
        """Tests run_script w/ data file"""
        debug.trace(4, f"TestIt.test_data_file(); self={self}")

        system.write_file(self.temp_file, "Hi, Paul")
        output = self.run_script(
            options="", env_options="FROM=es TO=en", data_file=self.temp_file
        )
        self.do_assert("hola" in output.lower())
        self.do_assert("pablo" in output.lower())

    ## NEW: Revised tests from mezcla/tests/test_huggingface_translation.py

    ## Test 1 - Default Run: ES -> EN
    @pytest.mark.skip
    def test_translation_default(self):
        """Ensures that test_translation_default works properly"""
        debug.trace(4, "test_translation_default()")
        source_sentence = "Hola Soy Dora."
        target_sentence = "Hi, I'm Dora."
        command = (
            f"echo {source_sentence} | python3 {HF_TRANSLATION_PATH} - 2> /dev/null"
        )
        command_output = gh.run(command)
        assert command_output == target_sentence

    ## Test 2 - Translation I: NON_EN -> EN (e.g. Japanese)
    @pytest.mark.skip
    def test_translation_ja2en(self):
        """Ensures that test_translation_ja2en works properly"""
        debug.trace(4, "test_translation_ja2en()")
        source_lang, target_lang = "ja", "en"
        source_sentence = "かわいいですね。"
        target_sentence = "It's cute."
        command = f"echo {source_sentence} | FROM={source_lang} TO={target_lang} python3 {HF_TRANSLATION_PATH} - 2> /dev/null"
        command_output = gh.run(command)
        assert target_sentence in command_output

    ## Test 3 - Translation II: EN -> NON_EN (e.g. French)
    @pytest.mark.skip
    def test_translation_en2fr(self):
        """Ensures that test_translation_en2fr works properly"""
        debug.trace(4, "test_translation_en2fr()")
        source_lang, target_lang = "en", "fr"
        ## OLD: Use of string with quotes halts the test
        # source_sentence = "It's cute."
        # target_sentence = "C'est mignon."
        source_sentence = "The people love croissant."
        target_sentence = "Les gens aiment les croissants."
        command = f"echo {source_sentence} | FROM={source_lang} TO={target_lang} python3 {HF_TRANSLATION_PATH} - 2> /dev/null"
        command_output = gh.run(command)
        assert target_sentence == command_output

    ## Test 4 - Translation III: NON_EN -> NON_EN (e.g. Russian to Arabic)
    @pytest.mark.skip
    def test_translation_ru2ar(self):
        """Ensures that test_translation_ru2ar works properly"""
        debug.trace(4, "test_translation_ru2ar()")
        source_lang, target_lang = "ru", "ar"
        # Literal Translation: I love potato juice.
        source_sentence = "Я люблю картофельный сок."
        target_sentence = "أنا أحب عصير البطاطس."
        command = f"echo {source_sentence} | FROM={source_lang} TO={target_lang} python3 {HF_TRANSLATION_PATH} - 2> /dev/null"
        command_output = gh.run(command)
        assert target_sentence == command_output

    ## Test 5 - Translation IV: Using a different model (e.g. t5-small)
    ## NOTE: Default Translation: EN (English) -> DE (German)
    @pytest.mark.skip
    def test_translation_t5small(self):
        """Ensures that test_translation_t5small works properly"""
        debug.trace(4, "test_translation_t5small()")
        mt_model = "t5-small"
        source_sentence = "Dortmund is black and yellow."
        target_sentence = "Dortmund ist Schwarz und yellow."
        command = f"echo {source_sentence} | python3 {HF_TRANSLATION_PATH} --model {mt_model} - 2> /dev/null"
        command_output = gh.run(command)
        assert command_output in target_sentence

    ## Test 6 - Tests for Dynamic Word Chunking
    @pytest.mark.xfail
    def test_dynamic_chunking(self):
        """Ensures that dynamic_chunking function works as expected"""
        debug.trace(4, "test_dynamic_chunking()")
        source_sentence = "Please just get it to run and shift focus to gradio. Do add a test case though."
        chunks = THE_MODULE.dynamic_chunking(text=source_sentence, max_len=10)
        for chunk in chunks:
            assert isinstance(chunk, str)
        assert chunks[0] == ""
        # By default, chunking is performed on the basis of sentences
        assert len(chunks) == len(source_sentence.split("."))

    ## Test 6.5 - Tests for Dynamic Chunking with Dynamic Word Chunking enabled
    @pytest.mark.xfail
    def test_dynamic_chunking_dwc_1(self):
        """Ensures that dynamic_chunking function works as expected when DYNAMIC_WORD_CHUNKING is enabled"""
        debug.trace(4, "test_dynamic_chunking_dwc_1()")
        self.monkeypatch.setattr(THE_MODULE, "DYNAMIC_WORD_CHUNKING", True)
        max_len = 5
        source_sentence = "Please just get it to run and shift focus to gradio. Do add a test case though."
        chunks = THE_MODULE.dynamic_chunking(text=source_sentence, max_len=max_len)

        # Test if last chunk is less than or equal to given max_len
        assert (len(chunks[-1].split())) <= max_len
        # Test if all other chunks are of max_size
        for chunk in chunks[:-1]:
            assert (len(chunk.split())) == max_len

    ## Test 7 - Tests for Similarity Scores
    @pytest.mark.xfail
    def test_calculate_similarity(self):
        """Ensures that calculate_similarity function works as expected"""
        debug.trace(4, "test_calculate_similarity()")

        def is_desc(arr):
            return all(arr[i] >= arr[i + 1] for i in range(len(arr) - 1))

        sentence_pairs = [
            (
                "The quick brown dog jumps over the lazy fox.",
                "The quick brown fox jumps over the lazy dog.",
            ),
            (
                "A quick brown fox jumps over the lazy dog.",
                "The quick brown fox jumps over the lazy dog.",
            ),
            (
                "The quick brown fox jumps over a lazy dog.",
                "The quick brown fox jumps over the lazy dog.",
            ),
            (
                "The quick fox jumps over the lazy dog.",
                "The quick brown fox jumps over the lazy dog.",
            ),
            (
                "The quick brown fox leaps over the lazy dog.",
                "The quick brown fox jumps over the lazy dog.",
            ),
            (
                "The quick brown fox jumps over the lazy cat.",
                "The quick brown fox jumps over the lazy dog.",
            ),
            (
                "A fast brown fox jumps over the lazy dog.",
                "The quick brown fox jumps over the lazy dog.",
            ),
            (
                "The lazy dog is jumped over by the quick brown fox.",
                "The quick brown fox jumps over the lazy dog.",
            ),
            (
                "The fox jumped over the dog.",
                "The quick brown fox jumps over the lazy dog.",
            ),
        ]

        scores = []
        for sentence in sentence_pairs:
            score = THE_MODULE.calculate_similarity(sentence[0], sentence[1])
            scores.append(round(score, 4))

        assert is_desc(scores)

    ## Test 8 - Tests for gradio_translation_input
    @pytest.mark.xfail
    def test_gradio_translation_input(self):
        """Ensures that gradio_translation_input works as expected"""
        debug.trace(4, "test_gradio_translation_input()")

        model, model_reverse = self.helper_return_models()
        source_words = ("Hello", "World")
        output = THE_MODULE.gradio_translation_input(
            source_words[0],
            source_words[1],
            is_round_trip=False,
            model=model,
            model_reverse=model_reverse,
        )

        assert output[0] == "Hola Mundo"

    ## Test 9 - Tests for round trip translation
    @pytest.mark.xfail
    def test_round_trip_translation(self):
        """Ensures that round trip translation works as expected"""
        debug.trace(4, "test_round_trip_translation()")
        model, model_reverse = self.helper_return_models()
        source_words = ("Hi", "Dora")
        translated = "Hola, Dora"
        output = THE_MODULE.gradio_translation_input(
            source_words[0],
            source_words[1],
            is_round_trip=True,
            model=model,
            model_reverse=model_reverse,
        )
        assert self.helper_filter_text(output[0]) == self.helper_filter_text(translated)
        assert self.helper_filter_text(output[1]) == self.helper_filter_text(
            " ".join(source_words)
        )
        assert output[2] > 0.75

    ## Test 10 - Tests for translated_text
    @pytest.mark.xfail
    def test_translated_text(self):
        """Ensures that translated_text works as expected"""
        debug.trace(4, "test_translated_text()")
        source_text = "Hello World"
        translated_text = "Hola Mundo"
        model, model_rev = self.helper_return_models()
        translation = model(source_text)
        output = THE_MODULE.translated_text(translation)

        assert output == translated_text

    ## Test 11 - Tests for get_split_regex()
    @pytest.mark.xfail
    def test_get_split_regex(self):
        """Ensures that get_split_regex works as expected"""
        debug.trace(4, "test_get_split_regex()")

        ## When dynamic chunking is True, no split regex is used (word by word split)
        self.monkeypatch.setattr(THE_MODULE, "DYNAMIC_WORD_CHUNKING", True)
        output = THE_MODULE.get_split_regex()
        assert output is None

        ## When dynamic chunking is False, split is performed sentence wise
        self.monkeypatch.setattr(THE_MODULE, "DYNAMIC_WORD_CHUNKING", False)
        output = THE_MODULE.get_split_regex()
        assert output == r"(?<=[.!?]) +"

        ## When paragraph mode is set, split is performed according to new line
        self.monkeypatch.setattr(THE_MODULE, "USE_PARAGRAPH_MODE", True)
        output = THE_MODULE.get_split_regex()
        assert output == r"\n\s*\n"

    ## Test 12 - Tests for show_gpu_usage
    @pytest.mark.skip
    def test_show_gpu_usage(self):
        """Ensures that show_gpu_usage works as expected"""
        debug.trace(4, "test_show_gpu_usage()")

        ## TODO: Find more test cases (function returns None so test case passes)
        assert THE_MODULE.show_gpu_usage() is None

        ## For USE_GPU enabled
        self.monkeypatch.setattr(THE_MODULE, "USE_GPU", True)
        assert THE_MODULE.show_gpu_usage() is None

    ## Test 13 - Test Methods in Translation UI (fn_machine_translation)
    @pytest.mark.xfail
    def test_ui_fn_machine_translation(self):
        """Ensures that fn_machine_translation of TranslationUI class works as expected"""
        debug.trace(4, "test_ui_fn_machine_translation()")

        model, model_rev = self.helper_return_models()
        source_text = "Hello World"
        target_text = "Hola Mundo"
        ui = THE_MODULE.TranslationUI(model=model)
        result = ui.fn_machine_translation(input=source_text)
        assert result == target_text

    ## Test 14 - Test Methods in Translation UI (fn_round_trip_translation)
    @pytest.mark.xfail
    def test_ui_fn_round_trip_translation(self):
        """Ensures that fn_machine_translation of TranslationUI class works as expected"""
        debug.trace(4, "test_ui_fn_round_trip_translation()")
        model, model_rev = self.helper_return_models()

        # TODO: Create helper function for returning models and filtering translated sentences
        source_text = "Hello World"
        target_text = "Hola Mundo"
        ui = THE_MODULE.TranslationUI(model=model, model_rev=model_rev)
        result = ui.fn_round_trip_translation(input=source_text)
        assert isinstance(result, tuple)
        assert result[0] == target_text
        assert self.helper_filter_text(result[1]) == self.helper_filter_text(
            source_text
        )
        assert isinstance(result[2], float)

    ## Test 15 - Test Methods in Translation UI (fn_alternative_ui)
    @pytest.mark.xfail
    def test_ui_fn_alternative_ui(self):
        """Ensures that fn_alternative_ui of TranslationUI class works as expected"""
        debug.trace(4, "test_ui_fn_alternative_ui()")
        model, model_rev = self.helper_return_models()

        source_text = ["Hello World", "I like", "apple"]
        target_text = "Hola Mundo Me gusta la manzana"
        is_round_trip = True

        ui = THE_MODULE.TranslationUI(model=model, model_rev=model_rev)
        result = ui.fn_alternative_ui(*source_text, is_round_trip)

        assert isinstance(result, tuple)
        assert self.helper_filter_text(result[0]) == self.helper_filter_text(
            target_text
        )
        assert self.helper_filter_text(result[1]) == self.helper_filter_text(
            " ".join(source_text)
        )
        assert isinstance(result[2], float)


# ------------------------------------------------------------------------

if __name__ == "__main__":
    debug.trace_current_context()
    pytest.main([__file__])
