#! /usr/bin/env python
#
# Test(s) for ../hugging_face_translation.py
#

"""Tests for hugging_face_translation module"""

# Standard modules
## TODO: from collections import defaultdict

# Installed modules
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
#------------------------------------------------------------------------

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.xfail                   # TODO: remove xfail
    ## DEBUG:
    @trap_exception
    def test_data_file(self):
        """Tests run_script w/ data file"""
        debug.trace(4, f"TestIt.test_data_file(); self={self}")
        
        system.write_file(self.temp_file, "Hi, Paul")
        output = self.run_script(options="", env_options="FROM=es TO=en",
                                 data_file=self.temp_file)
        self.do_assert("hola" in output.lower())
        self.do_assert("pablo" in output.lower())
        return
    
    ## NEW: Revised tests from mezcla/tests/test_huggingface_translation.py
    
    ## Test 1 - Default Run: ES -> EN
    @pytest.mark.skip
    def test_translation_default(self):
        """Ensures that test_translation_default works properly"""
        debug.trace(4, "test_translation_default()")
        source_sentence = "Hola Soy Dora."
        target_sentence = "Hi, I'm Dora."
        command = f"echo {source_sentence} | python3 {HF_TRANSLATION_PATH} - 2> /dev/null"
        command_output = gh.run(command)
        assert(command_output == target_sentence)
        return
    
    ## Test 2 - Translation I: NOT_EN -> EN (e.g. Japanese)
    @pytest.mark.skip
    def test_translation_ja2en(self):
        """Ensures that test_translation_ja2en works properly"""
        debug.trace(4, "test_translation_ja2en()")
        source_lang, target_lang = "ja", "en"
        source_sentence = "かわいいですね。"
        target_sentence = "It's cute."
        command = f"echo {source_sentence} | FROM={source_lang} TO={target_lang} python3 {HF_TRANSLATION_PATH} - 2> /dev/null"
        command_output = gh.run(command)
        assert(target_sentence in command_output)
        return
    
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
        assert(target_sentence == command_output)
        return
    
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
        assert(target_sentence == command_output)
        return

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
        assert(command_output in target_sentence)
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
