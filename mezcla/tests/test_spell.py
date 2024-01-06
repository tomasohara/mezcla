#! /usr/bin/env python
#
# Test(s) for ../spell.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_bing_search.py

"""Tests for spell module"""
# Standard packages
import re

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object

# Since importing doesn't work properly, a temporary fix is specifying the path
# import mezcla.spell as THE_MODULE 
PATH1 = f'$PWD/mezcla/spell.py'
PATH2 = f'$PWD/spell.py'
PATH3 = f'../spell.py'
PWD_COMMAND = f'echo $PWD'
echo_PWD = gh.run(PWD_COMMAND)
if (echo_PWD.endswith('/mezcla/mezcla')):
    SPELL_PATH = PATH2
elif (echo_PWD.endswith('/mezcla')):
    SPELL_PATH = PATH1
else:
    SPELL_PATH = PATH3

class TestIt(TestWrapper):
    """Class for testcase definition"""
    script_file = TestWrapper.get_module_file_path(__file__)
    script_module = TestWrapper.get_testing_module_name(__file__)
    use_temp_base_dir = True    # treat TEMP_BASE as directory
             
    # NOTE 1: For test_phrase, song lyrics are used
    # NOTE 2: The content in test_phase error MUST be all lowercase
    # TODO 1: Find a method to not create any external filess when test_spell_query_LL functions used
    # TODO 2: A function for test_run_command replacement (optional)  

    @pytest.mark.skip
    # TEST-1: Spell-check in English by default
    def test_spell_default(self):
        """Ensure test_spell_default works as expected"""
        debug.trace(4, f"test_spell_default(); self={self}")
        test_lang = "en_EN"
        test_phrase = "One kiss is all it tajkes"
        ## ORGINAL: One kiss is all it takes (from One Kiss by Calvin Harris, Dua Lipa)
        test_run_command = f'echo "{test_phrase}" | SPELL_LANG={test_lang} {SPELL_PATH} -'
        output = gh.run(test_run_command)
        assert (output != "" and len(output.split())==1)
        return

    @pytest.mark.skip
    # TEST-2: Spell-check in Spanish
    def test_spell_ES(self):
        """Ensure test_spell_ES works as expected"""
        debug.trace(4, f"test_spell_ES(); self={self}")
        test_lang = "es_ES"
        test_phrase = "Yo te miro y se me cortaq la respiración"
        ## ORIGINAL: Yo te miro y se me corta la respiración (from Bailando by Enrique Iglesias)
        ## Literal: I look at you and my breath stops
        test_run_command = f'echo "{test_phrase}" | SPELL_LANG={test_lang} {SPELL_PATH} -'
        output = gh.run(test_run_command)
        assert (output != "" and len(output.split())==1)
        return
    
    @pytest.mark.skip
    # TEST-3: Spell-check in Japanese
    def test_spell_AR(self):
        """Ensure test_spell_JA works as expected"""
        debug.trace(4, f"test_spell_AR(); self={self}")
        test_lang = "ar_AR"
        test_phrase = "وإنت معايا بشوفك أحلى النس"
        ## ORIGINAL: وإنت معايا بشوفك أحلى الناس (from Bayen Habeit by Marshmello, Amr Diab)
        ## Literal: When you are with me, I see you as the most beautiful person
        test_run_command = f'echo "{test_phrase}" | SPELL_LANG={test_lang} {SPELL_PATH} -'
        output = gh.run(test_run_command)
        assert (output != "" and len(output.split())==2)
        return
    
    @pytest.mark.skip
    # TEST-4: Spell-check in Russian
    def test_spell_RU(self):
        """Ensure test_spell_RU works as expected"""
        debug.trace(4, f"test_spell_RU(); self={self}")
        test_lang = "ru_RU"
        test_phrase = "Поплыли туманыны над рекой"
        ## ORIGINAL: Поплыли туманы над рекой (from Катюша by M. Blanter)
        ## Literal: Fogs floated over the river
        test_run_command = f'echo "{test_phrase}" | SPELL_LANG={test_lang} {SPELL_PATH} -'
        output = gh.run(test_run_command)
        assert (output != "" and len(output.split())==1)
        return
    
    @pytest.mark.skip
    # TEST-5: Spell-check in batch for English
    def test_spell_default_batch(self):
        """Ensure test_spell_default_batch works as expected"""
        debug.trace(4, f"test_spell_default_branch(); self={self}")
        testfile_path = gh.resolve_path("./resources/spell-py-en.list")
        test_run_command = f'python3 {SPELL_PATH} {testfile_path}'
        output = gh.run(test_run_command).split("\n")
        assert (output != "" and len(output)==10)    # Error Message contains large amount of characters
        return
    
    @pytest.mark.skip
    # TEST-6: Spell-check in batch for Spanish
    def test_spell_ES_batch(self):
        """Ensure test_spell_ES_batch works as expected"""
        debug.trace(4, f"test_spell_ES_batch(); self={self}")
        test_lang = "es_ES"
        testfile_path = gh.resolve_path("./resources/spell-py-es.list")
        test_run_command = f'SPELL_LANG={test_lang} python3 {SPELL_PATH} {testfile_path}'
        output = gh.run(test_run_command).split("\n")
        assert (output != "" and len(output)==10)    # Error Message contains large amount of characters
        return
    
    @pytest.mark.skip
    # TEST-7: Spell-check in batch for Russian
    def test_spell_RU_batch(self):
        """Ensure test_spell_RU_batch works as expected"""
        debug.trace(4, f"test_spell_RU_batch(); self={self}")
        test_lang = "ru_RU"
        testfile_path = gh.resolve_path("./resources/spell-py-ru.list")
        test_run_command = f'SPELL_LANG={test_lang} python3 {SPELL_PATH} {testfile_path}'
        output = gh.run(test_run_command).split("\n")
        assert (output != "" and len(output)==5)    # Error Message contains large amount of characters
        return
    
    @pytest.mark.skip
    # TEST-8: Spell-check in batch for Arabic
    def test_spell_AR_batch(self):
        """Ensure test_spell_AR_batch works as expected"""
        debug.trace(4, f"test_spell_AR_batch(); self={self}")
        test_lang = "ar_AR"
        testfile_path = gh.resolve_path("./resources/spell-py-ar.list")
        test_run_command = f'SPELL_LANG={test_lang} python3 {SPELL_PATH} {testfile_path}'
        output = gh.run(test_run_command).split("\n")
        assert (output != "" and len(output)==17)    # Error Message contains large amount of characters
        return

    ## TODO: Add suggestion for spell.py
    ## def test_spell_LANG_suggest(self):
    ##     """Ensure test_spell_LANG_suggest works as expected"""
    ##     debug.trace(4, f"test_suggest_LANG(); self={self}")
    ##     assert(re.search)


if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])