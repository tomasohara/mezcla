#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Test(s) for ../spell.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_bing_search.py
#
# TODO1:
# - Rework tests following test_spell_EN
# - Carefully review tests/template.py.
# TODO3:
# - Create test helpers to cut down on all the redundant code.
#   ex: def check_spelling(self, lang, text, bad):
#       """Run spelling over TEXT in TEXT looking for BAD words""
#       output = self.run_script(env_options=f"SPELL_LANG={lang}", data_file=gh.create_temp_file(text))
#       assert(system.intersection(text.split(), bad.split()))
#

"""Tests for spell module"""
# Standard packages
## OLD: import re

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper
from mezcla.unittest_wrapper import trap_exception

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
#    TestIt.script_module:              path to file
try:
    # note: requires enchant-2 library package under Ubuntu (besides pyenchant)
    import mezcla.spell as THE_MODULE
except:
    THE_MODULE = None

# Since importing doesn't work properly, a temporary fix is specifying the path
# import mezcla.spell as THE_MODULE
# *** It works fine: please follow the example in test/template.py better! ***
## BAD
## PATH1 = f'$PWD/mezcla/spell.py'
## PATH2 = f'$PWD/spell.py'
## PATH3 = f'../spell.py'
## PWD_COMMAND = f'echo $PWD'
## echo_PWD = gh.run(PWD_COMMAND)
## if (echo_PWD.endswith('/mezcla/mezcla')):
##     SPELL_PATH = PATH2
## elif (echo_PWD.endswith('/mezcla')):
##     SPELL_PATH = PATH1
## else:
##     SPELL_PATH = PATH3
##
## NOTE: the following is a temporary workaround for the bad tests
## TODO1: use run_script as in the template (and in most other tests elsewhere)!
SPELL_PATH = gh.resolve_path("spell.py")

@pytest.mark.skipif(not THE_MODULE, reason="Problem loading spell.py: check requirements")
class SpellFiles(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    use_temp_base_dir = True    # treat TEMP_BASE as directory
             
    # NOTE 1: For test_phrase, song lyrics are used
    # NOTE 2: The content in test_phase error MUST be all lowercase
    # TODO 1: Find a method to not create any external filess when test_spell_query_LL functions used
    # TODO 2: A function for test_run_command replacement (optional)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_spell_default(self):
        """Ensure test_spell_default [English] works as expected"""
        debug.trace(4, f"test_spell_default(); self={self}")
        ## OLD: test_lang = "en_EN"
        test_phrase = "One kiss is all it tajkes"
        ## ORGINAL: One kiss is all it takes (from One Kiss by Calvin Harris, Dua Lipa)
        test_run_command = f'echo "{test_phrase}" | {SPELL_PATH} -'
        output = gh.run(test_run_command)
        assert (output != "" and len(output.split())==1)
        return


    @pytest.mark.xfail                   # TODO: remove xfail
    @trap_exception                      # TODO: remove when debugged
    def test_spell_EN(self):
        """Ensure test_spell_EN [English] works as expected"""
        debug.trace(4, f"test_spell_EN(); self={self}")
        
        test_lang = "en_EN"
        test_phrase = "One kiss is all it takesqq"
        test_phrase_error = "takesqq"
        ## BAD: test_run_command = f'echo "{test_phrase}" | SPELL_LANG={test_lang} {SPELL_PATH} - > {self.temp_file}'
        # LITERAL TRANSLATION: N/A  
        system.write_file(self.temp_file, test_phrase)
        output = self.run_script(env_options=f"SPELL_LANG={test_lang}", data_file=self.temp_file)
        debug.trace_expr(5, output, test_phrase_error)
        assert (output == test_phrase_error)
        ## TODO: maldito vs code so awkward to use!
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_spell_ES(self):
        """Ensure test_spell_ES [Spanish] works as expected"""
        debug.trace(4, f"test_spell_ES(); self={self}")

        test_lang = "es_ES"
        test_phrase = "Yo te miro y se me corta la respiraciónqq"
        test_phrase_error = "respiraciónqq"
        ## TODO1: rework using run_script
        test_run_command = f'echo "{test_phrase}" | SPELL_LANG={test_lang} {SPELL_PATH} - > {self.temp_file}'
        # LITERAL TRANSLATION: "I look at you and my breath catches"
        test_run_command = f'echo "{test_phrase}" | SPELL_LANG={test_lang} {SPELL_PATH} -'
        output = gh.run(test_run_command)

        ## TODO2: output = self.run_script(self.temp_file)
        assert (output == test_phrase_error)
        return
    
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_spell_NE(self):
        """Ensure test_spell_NE [Nepali] works as expected"""
        
        test_lang = "ne_NE"
        test_phrase = "थाहा छैन तिमी को हो मेरोqq"
        test_phrase_error = "मेरोqq"
        test_run_command = f'echo "{test_phrase}" | SPELL_LANG={test_lang} {SPELL_PATH} - > {self.temp_file}'
        # LITERAL TRANSLATION: "I don't know who you are"
        # WARN: ne_NE dictionary may not have some words
        output = gh.run(test_run_command)
         
        debug.trace(4, f"test_spell_NE(); self={self}")
        ## TODO2: output = output = self.run_script(self.temp_file)
        assert (output == test_phrase_error)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_spell_AR(self):
        """Ensure test_spell_AR [Arabic] works as expected"""
        debug.trace(4, f"test_spell_AR(); self={self}")
        test_lang = "ar_AR"
        test_phrase = "وإنت معايا بشوفك أحلى النس"
        ## ORIGINAL: وإنت معايا بشوفك أحلى الناس (from Bayen Habeit by Marshmello, Amr Diab)
        ## Literal: When you are with me, I see you as the most beautiful person
        test_run_command = f'echo "{test_phrase}" | SPELL_LANG={test_lang} {SPELL_PATH} -'
        ## TODO2: output = output = self.run_script(self.temp_file)
        output = gh.run(test_run_command)
        assert (output != "" and len(output.split())==2)
        return
    
    @pytest.mark.skip                   # TODO: remove xfail
    def test_spell_RU(self):
        """Ensure test_spell_RU [Russian] works as expected"""
        debug.trace(4, f"test_spell_RU(); self={self}")
        test_lang = "ru_RU"
        test_phrase = "Поплыли туманыны над рекой"
        ## ORIGINAL: Поплыли туманы над рекой (from Катюша by M. Blanter)
        ## Literal: Fogs floated over the river
        test_run_command = f'echo "{test_phrase}" | SPELL_LANG={test_lang} {SPELL_PATH} -'
        ## TODO2: output = output = self.run_script(self.temp_file)
        output = gh.run(test_run_command)
        assert (output != "" and len(output.split())==1)
        return
    
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_spell_query_EN(self):
        """Ensure test_spell_query_EN works as expected"""
        
        test_lang = "en_EN"
        test_phrase = "Because I am lost in the way you moveqq"
        # LITERAL TRANSLATION: N/A
        ## BAD: temp_phrase = None
        temp_phrase = f"{self.temp_file}.phrase"
        test_run_command_1 = f'echo "{test_phrase}" > {temp_phrase}'
        test_run_command_2 = f'SPELL_LANG={test_lang} {SPELL_PATH} {temp_phrase} > {self.temp_file}'

        test_phrase_error = "moveqq"
         
        debug.trace(4, f"test_spell_query_EN(); self={self}")
        gh.issue(test_run_command_1)
        output = gh.run(test_run_command_2)
        ## TODO: output = self.run_script(self.temp_file)
        assert (output == test_phrase_error)
        return
    
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_spell_query_ES(self):
        """Ensure test_spell_query_ES works as expected"""
        
        test_lang = "es_ES"
        test_phrase = "Me dijeron que te estás casandoxx"
        # LITERAL TRANSLATION: "They told me that you are getting married"
        ## BAD: temp_phrase = None
        temp_phrase = f"{self.temp_file}.phrase"
        test_run_command_1 = f'echo "{test_phrase}" > {temp_phrase}'
        test_run_command_2 = f'SPELL_LANG={test_lang} {SPELL_PATH} {temp_phrase} > {self.temp_file}'
        test_phrase_error = "casandoxx"
         
        debug.trace(4, f"test_spell_query_ES(); self={self}")
        gh.issue(test_run_command_1)
        output = gh.run(test_run_command_2)
        output = self.run_script(self.temp_file)
        assert (output == test_phrase_error)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_spell_query_NE(self):
        """Ensure test_spell_query_NE works as expected"""
        
        test_lang = "ne_NE"
        test_phrase = "तिमी नै अब मेरो झुल्केको बिहानीxx"
        # LITERAL TRANSLATION: You are now my rising dawn
        ## BAD: temp_phrase = None
        temp_phrase = f"{self.temp_file}.phrase"
        test_run_command_1 = f'echo "{test_phrase}" > {temp_phrase}'
        test_run_command_2 = f'SPELL_LANG={test_lang} {SPELL_PATH} {temp_phrase} > {self.temp_file}'

        test_phrase_error = "बिहानीxx"
         
        debug.trace(4, f"test_spell_query_NE(); self={self}")
        gh.issue(test_run_command_1)
        output = gh.run(test_run_command_2)
        output = self.run_script(self.temp_file)
        assert (output == test_phrase_error)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_spell_default_batch(self):
        """Ensure test_spell_default_batch [English] works as expected"""
        debug.trace(4, f"test_spell_default_branch(); self={self}")
        testfile_path = gh.resolve_path("./resources/spell-py-en.list")
        test_run_command = f'python3 {SPELL_PATH} {testfile_path}'
        output = gh.run(test_run_command).split("\n")
        ## TODO2: make the tests more flexible (e.g., don't test for specific length)
        assert (output != "" and len(output)==10)    # Error Message contains large amount of characters
        return
    
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_spell_ES_batch(self):
        """Ensure test_spell_ES_batch [Spanish] works as expected"""
        debug.trace(4, f"test_spell_ES_batch(); self={self}")
        test_lang = "es_ES"
        testfile_path = gh.resolve_path("./resources/spell-py-es.list")
        test_run_command = f'SPELL_LANG={test_lang} python3 {SPELL_PATH} {testfile_path}'
        output = gh.run(test_run_command).split("\n")
        assert (output != "" and len(output)==10)    # Error Message contains large amount of characters
        return
    
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_spell_RU_batch(self):
        """Ensure test_spell_RU_batch [Russian] works as expected"""
        debug.trace(4, f"test_spell_RU_batch(); self={self}")
        test_lang = "ru_RU"
        testfile_path = gh.resolve_path("./resources/spell-py-ru.list")
        test_run_command = f'SPELL_LANG={test_lang} python3 {SPELL_PATH} {testfile_path}'
        output = gh.run(test_run_command).split("\n")
        assert (output != "" and len(output)==5)    # Error Message contains large amount of characters
        return
    
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_spell_AR_batch(self):
        """Ensure test_spell_AR_batch [Arabic] works as expected"""
        debug.trace(4, f"test_spell_AR_batch(); self={self}")
        test_lang = "ar_AR"
        testfile_path = gh.resolve_path("./resources/spell-py-ar.list")
        test_run_command = f'SPELL_LANG={test_lang} python3 {SPELL_PATH} {testfile_path}'
        output = gh.run(test_run_command).split("\n")
        assert (output != "" and len(output)==17)    # Error Message contains large amount of characters
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_spell_LANG_suggest(self):
        """Ensure test_spell_LANG_suggest works as expected"""
        debug.trace(4, f"test_suggest_LANG(); self={self}")
        self.do_assert(False, "TODO: code test")

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
