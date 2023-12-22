#! /usr/bin/env python
#
# Test(s) for ../examples/hugging_face_translation.py
#
## NOTE: Takes time for initial run and chances of crash (requires specific language models for each tests)

"""Tests for examples/hugging_face_translation module"""

# Standard packages
## NOTE: this is empty for now

# Installed packages
import pytest
import re

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
from mezcla.examples import hugging_face_translation as THE_MODULE

class TestKenlmExample(TestWrapper):
    script_file = TestWrapper.get_module_file_path(__file__)
    script_module = TestWrapper.get_testing_module_name(__file__)
    use_temp_base_dir = True    # treat TEMP_BASE as directory

    """Class for testcase definition"""

    # TEST 1 - DEFAULT TEST (ES -> EN)
    def test_translation_default(self):
        """Ensures that test_translation_default works properly"""
        debug.trace(4, "test_translation_default()")
        source_sentence = "Hay más de cien idiomas oficiales."
        target_sentence = "There are over a hundred official languages."

        temp_file_1 = gh.get_temp_file(delete=True)
        command_1 = f"echo '{source_sentence}' > {temp_file_1}"
        command_2 = f"../examples/hugging_face_translation.py {temp_file_1} > {self.temp_file}"

        gh.run(command_1)
        gh.run(command_2)
        output = gh.read_file(self.temp_file).strip()
        assert(output == target_sentence)
        return
    
    # TEST 2 - SORUCE_LANG to DEFAULT (ENGLISH) (AF -> EN)
    def test_translation_source_lang(self):
        """Ensures that test_translation_source_lang works properly"""
        debug.trace(4, "test_translation_source_lang()")
        
        SOURCE_LANG = "af"
        # TARGET_LANG = "en"
        source_sentence = "Dit was goed."
        target_sentence = "It was good."

        temp_file_1 = gh.get_temp_file(delete=True)
        command_1 = f"echo '{source_sentence}' > {temp_file_1}"
        command_2 = f"SOURCE_LANG='{SOURCE_LANG}' ../examples/hugging_face_translation.py {temp_file_1} > {self.temp_file}"

        gh.run(command_1)
        gh.run(command_2)
        output = gh.read_file(self.temp_file).strip()
        assert(output == target_sentence)
        return
        
    # TEST 3 - DEFAULT (ESPANOL) to TARGET_LANG (ES -> RU)
    def test_translation_target_lang(self):
        """Ensures that test_translation_target_lang works properly"""
        debug.trace(4, "test_translation_target_lang()")
        
        # en = "I am feeling sad."
        # SOURCE_LANG = "es"
        TARGET_LANG = "ru"
        source_sentence = "Me siento triste." 
        target_sentence = "Мне грустно."

        temp_file_1 = gh.get_temp_file(delete=True)
        command_1 = f"echo '{source_sentence}' > {temp_file_1}"
        command_2 = f"TARGET_LANG='{TARGET_LANG}' ../examples/hugging_face_translation.py {temp_file_1} > {self.temp_file}"

        gh.run(command_1)
        gh.run(command_2)
        output = gh.read_file(self.temp_file).strip()
        assert(output == target_sentence)
        return
    
    # TEST 4 - DIFFERENT MT MODEL (EN -> DE)
    def test_translation_mt_model(self):
        """Ensures that test_translation_mt_model works properly"""
        debug.trace(4, "test_translation_mt_model()")
        
        MT_MODEL = "t5-small"
        source_sentence = "My name is Wolfgang and I live in Berlin." 
        target_sentence = "Mein Name ist Wolfgang und ich wohne in Berlin."

        temp_file_1 = gh.get_temp_file(delete=True)
        command_1 = f"echo '{source_sentence}' > {temp_file_1}"
        command_2 = f"MT_MODEL='{MT_MODEL}' ../examples/hugging_face_translation.py {temp_file_1} > {self.temp_file}"

        gh.run(command_1)
        gh.run(command_2)
        output = gh.read_file(self.temp_file).strip()
        assert(output == target_sentence)
        return
    
    # TEST 5 - MASS INPUT TEST (ES -> EN)
    # BUGGY - TAKES LOT OF TIME (Work in Progress)
    def test_translation_default(self):
        """Ensures that test_translation_default works properly"""
        debug.trace(4, "test_translation_default()")
        
        all_sentence = gh.read_file("../examples/translate_txt/100randomen.txt")
        output = []
        
        for sentence in all_sentence:
            source_sentence = sentence

            temp_file_1 = gh.get_temp_file(delete=True)
            command_1 = f"echo '{source_sentence}' > {temp_file_1}"
            command_2 = f"../examples/hugging_face_translation.py {temp_file_1} > {self.temp_file}"

            gh.run(command_1)
            gh.run(command_2)
            output += str(gh.read_file(self.temp_file).strip())

        assert(len(output) == 25)
        return

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])


