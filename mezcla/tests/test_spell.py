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

class SpellFiles(TestWrapper):
    """Class for testcase definition"""
    script_file = TestWrapper.get_module_file_path(__file__)
    script_module = TestWrapper.get_testing_module_name(__file__)
    use_temp_base_dir = True    # treat TEMP_BASE as directory
             
    # NOTE 1: For test_phrase, song lyrics are used
    # NOTE 2: The content in test_phase error MUST be all lowercase
    # TODO 1: Find a method to not create any external filess when test_spell_query_LL functions used
    # TODO 2: A function for test_run_command replacement (optional)  

    def test_spell_EN(self):
        """Ensure test_spell_EN works as expected"""
        
        test_lang = "en_EN"
        test_phrase = "One kiss is all it takesqq"
        test_phrase_error = "takesqq"
        test_run_command = f'echo "{test_phrase}" | SPELL_LANG={test_lang} {SPELL_PATH} - > {self.temp_file}'
        # LITERAL TRANSLATION: N/A  
        
        debug.trace(4, f"test_spell_EN(); self={self}")
        gh.run(test_run_command)
        output = self.run_script(self.temp_file)
        assert (output == test_phrase_error)
        return

    def test_spell_ES(self):
        """Ensure test_spell_ES works as expected"""

        test_lang = "es_ES"
        test_phrase = "Yo te miro y se me corta la respiraciónqq"
        test_phrase_error = "respiraciónqq"
        test_run_command = f'echo "{test_phrase}" | SPELL_LANG={test_lang} {SPELL_PATH} - > {self.temp_file}'
        # LITERAL TRANSLATION: "I look at you and my breath catches"

        debug.trace(4, f"test_spell_ES(); self={self}")
        gh.run(test_run_command)
        output = self.run_script(self.temp_file)
        assert (output == test_phrase_error)
        return
    
    def test_spell_NE(self):
        """Ensure test_spell_NE works as expected"""
        
        test_lang = "ne_NE"
        test_phrase = "थाहा छैन तिमी को हो मेरोqq"
        test_phrase_error = "मेरोqq"
        test_run_command = f'echo "{test_phrase}" | SPELL_LANG={test_lang} {SPELL_PATH} - > {self.temp_file}'
        # LITERAL TRANSLATION: "I don't know who you are"
        # WARN: ne_NE dictionary may not have some words
         
        debug.trace(4, f"test_spell_NE(); self={self}")
        gh.run(test_run_command)
        output = self.run_script(self.temp_file)
        assert (output == test_phrase_error)
        return

    def test_spell_query_EN(self):
        """Ensure test_spell_query_EN works as expected"""
        
        test_lang = "en_EN"
        test_phrase = "Because I am lost in the way you moveqq"
        # LITERAL TRANSLATION: N/A
        temp_phrase = None
        test_run_command_1 = f'echo "{test_phrase}" > {temp_phrase}'
        test_run_command_2 = f'SPELL_LANG={test_lang} {SPELL_PATH} {temp_phrase} > {self.temp_file}'

        test_phrase_error = "moveqq"
         
        debug.trace(4, f"test_spell_query_EN(); self={self}")
        gh.run(test_run_command_1)
        gh.run(test_run_command_2)
        output = self.run_script(self.temp_file)
        assert (output == test_phrase_error)
        return
    
    def test_spell_query_ES(self):
        """Ensure test_spell_query_ES works as expected"""
        
        test_lang = "es_ES"
        test_phrase = "Me dijeron que te estás casandoxx"
        # LITERAL TRANSLATION: "They told me that you are getting married"
        temp_phrase = None
        test_run_command_1 = f'echo "{test_phrase}" > {temp_phrase}'
        test_run_command_2 = f'SPELL_LANG={test_lang} {SPELL_PATH} {temp_phrase} > {self.temp_file}'
        test_phrase_error = "casandoxx"
         
        debug.trace(4, f"test_spell_query_ES(); self={self}")
        gh.run(test_run_command_1)
        gh.run(test_run_command_2)
        output = self.run_script(self.temp_file)
        assert (output == test_phrase_error)
        return

    def test_spell_query_NE(self):
        """Ensure test_spell_query_NE works as expected"""
        
        test_lang = "ne_NE"
        test_phrase = "तिमी नै अब मेरो झुल्केको बिहानीxx"
        # LITERAL TRANSLATION: You are now my rising dawn
        temp_phrase = None
        test_run_command_1 = f'echo "{test_phrase}" > {temp_phrase}'
        test_run_command_2 = f'SPELL_LANG={test_lang} {SPELL_PATH} {temp_phrase} > {self.temp_file}'

        test_phrase_error = "बिहानीxx"
         
        debug.trace(4, f"test_spell_query_NE(); self={self}")
        gh.run(test_run_command_1)
        gh.run(test_run_command_2)
        output = self.run_script(self.temp_file)
        assert (output == test_phrase_error)
        return

#     # def test_suggest_EN(self):
#     #     """Ensure test_suggest_EN works as expected"""
#     #     debug.trace(4, f"test_suggest_EN(); self={self}")
#     #     assert(re.search)
    
#     # def test_spell_LANG(self):
#     #     """Ensure test_spell_LANG works as expected"""
#     #     debug.trace(4, f"test_spell_LANG(); self={self}")
#     #     assert(re.search)

#     # def test_suggest_LANG(self):
#     #     """Ensure test_suggest_LANG works as expected"""
#     #     debug.trace(4, f"test_suggest_LANG(); self={self}")
#     #     assert(re.search)


if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])