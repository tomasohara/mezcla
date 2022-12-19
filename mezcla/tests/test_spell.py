# test_spell.py TESTS spell.py
# Note: spell.py requires pyenchant

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

# import mezcla.spell as THE_MODULE 

class SpellFiles(TestWrapper):
    """Class for testcase definition"""
    script_file = TestWrapper.get_module_file_path(__file__)
    script_module = TestWrapper.get_testing_module_name(__file__)
    use_temp_base_dir = True    # treat TEMP_BASE as directory            

    # NOTE 1: For test_phrase, song lyrics are used
    # NOTE 2: The content in test_phase error MUST be all lowercase
   
    def test_spell_EN(self):
        """Ensure test_spell_EN works as expected"""

        test_lang = "en_EN"
        test_phrase = "One kiss is all it takesqq"
        # LITERAL TRANSLATION: N/A  
        test_run_command = f'echo "{test_phrase}" | SPELL_LANG="{test_lang}" ../spell.py - > {self.temp_file}'
        test_phrase_error = "takesqq"

        debug.trace(4, f"test_spell_EN(); self={self}")
        gh.run(test_run_command)
        output = self.run_script(self.temp_file)
        assert (output == test_phrase_error)
        return

    def test_spell_ES(self):
        """Ensure test_spell_ES works as expected"""

        test_lang = "es_ES"
        test_phrase = "Yo te miro y se me corta la respiraciónqq"
        # LITERAL TRANSLATION: 
        test_run_command = f'echo "{test_phrase}" | SPELL_LANG="{test_lang}" ../spell.py - > {self.temp_file}'
        test_phrase_error = "respiraciónqq"
        # Note: The content in test_phase error MUST be all lowercase

        debug.trace(4, f"test_spell_ES(); self={self}")
        gh.run(test_run_command)
        output = self.run_script(self.temp_file)
        assert (output == test_phrase_error)
        return
    
    def test_spell_NE(self):
        """Ensure test_spell_NE works as expected"""
        
        test_lang = "ne_NE"
        test_phrase = "थाहा छैन तिमी को हो मेरोqq"
        # LITERAL TRANSLATION: "I don't know who you are"
        test_run_command = f'echo "{test_phrase}" | SPELL_LANG="{test_lang}" ../spell.py - > {self.temp_file}'
        test_phrase_error = "मेरोqq"
        # WARN: ne_NE dictionary may not have some words
         
        debug.trace(4, f"test_spell_NE(); self={self}")
        gh.run(test_run_command)
        output = self.run_script(self.temp_file)
        assert (output == test_phrase_error)
        return

    # def test_suggest_EN(self):
    #     """Ensure test_suggest_EN works as expected"""
    #     debug.trace(4, f"test_suggest_EN(); self={self}")
    #     assert(re.search)
    
    # def test_spell_LANG(self):
    #     """Ensure test_spell_LANG works as expected"""
    #     debug.trace(4, f"test_spell_LANG(); self={self}")
    #     assert(re.search)

    # def test_suggest_LANG(self):
    #     """Ensure test_suggest_LANG works as expected"""
    #     debug.trace(4, f"test_suggest_LANG(); self={self}")
    #     assert(re.search)

    def test_spell_query_EN(self):
        """Ensure test_spell_query_EN works as expected"""
        
        test_lang = "en_EN"
        test_phrase = "Because I am lost in the way you moveqq"
        # LITERAL TRANSLATION: N/A
        temp_phrase = None
        test_run_command_1 = f'echo "{test_phrase}" > {temp_phrase}'
        test_run_command_2 = f'SPELL_LANG={test_lang} ../spell.py {temp_phrase} > {self.temp_file}'

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
        # LITERAL TRANSLATION: N/A
        temp_phrase = None
        test_run_command_1 = f'echo "{test_phrase}" > {temp_phrase}'
        test_run_command_2 = f'SPELL_LANG={test_lang} ../spell.py {temp_phrase} > {self.temp_file}'

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
        test_run_command_2 = f'SPELL_LANG={test_lang} ../spell.py {temp_phrase} > {self.temp_file}'

        test_phrase_error = "बिहानीxx"
         
        debug.trace(4, f"test_spell_query_NE(); self={self}")
        gh.run(test_run_command_1)
        gh.run(test_run_command_2)
        output = self.run_script(self.temp_file)
        assert (output == test_phrase_error)
        return


if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])