#! /usr/bin/env python3
#
# Test(s) for ../hugging_face_speechrec.py
#

"""Tests for hugging_face_speechrec module"""

# Standard modules
## TODO: from collections import defaultdict

# Installed modules
import pytest

# Local modules
from mezcla.unittest_wrapper import TestWrapper
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                        global module object
#    TestIt.script_module:              path to file
import mezcla.examples.hugging_face_speechrec as THE_MODULE
#
# Note: sanity test for customization (TODO: remove if desired)
if not my_re.search(__file__, r"\btemplate.py$"):
    debug.assertion("mezcla.template" not in str(THE_MODULE))

# TEMP FIX: Path specification for mezcla scripts
PATH1 = "$PWD/mezcla/examples/hugging_face_speechrec.py"
PATH2 = "$PWD/examples/hugging_face_speechrec.py"
PATH3 = "$PWD/hugging_face_speechrec.py"
PATH4 = "../hugging_face_speechrec.py"
PWD_COMMAND = "echo $PWD"
echo_pwd = gh.run(PWD_COMMAND)
if echo_pwd.endswith("/mezcla/mezcla/examples"):
    HF_SPEECHREC_PATH = PATH3
elif echo_pwd.endswith("/mezcla/mezcla"):
    HF_SPEECHREC_PATH = PATH2
elif echo_pwd.endswith("/mezcla"):
    HF_SPEECHREC_PATH = PATH1
else:
    HF_SPEECHREC_PATH = PATH4
#------------------------------------------------------------------------

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_data_file(self):
        """Tests run_script w/ data file"""
        debug.trace(4, f"TestIt.test_data_file(); self={self}")
        audio_file = gh.resolve_path("fuzzy-testing-1-2-3.wav")
        output = self.run_script(options="", data_file=audio_file)
        self.do_assert(my_re.search(r"testing|one|two|three", output.strip()))
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_sound_file_default(self):
        """Ensures that test_sound_file_default works properly"""
        ## TEST 1: Test the vanilla script using a soundfile
        debug.trace(4, f"TestIt.test_sound_file_default(); self={self}")
        audio_file = gh.resolve_path("fuzzy-testing-1-2-3.wav")
        output_cmd = f"python3 {HF_SPEECHREC_PATH} {audio_file} 2> /dev/null"
        output = gh.run(output_cmd)
        self.do_assert(my_re.search(r"testing|one|two|three", output.strip()))
        return
    
    @pytest.mark.skip               # TODO: Fix path for audio_file
    def test_sound_file_us1(self):
        """Ensures that test_sound_file_us1 works properly"""
        ## TEST 2: Test the vanilla script using a different soundfile (US English)
        debug.trace(4, f"TestIt.test_sound_file_us1(); self={self}")
        audio_file = gh.resolve_path("examples/resources/speech-wav/us1.wav")
        output_cmd = f"python3 {HF_SPEECHREC_PATH} {audio_file} 2> /dev/null"
        output = gh.run(output_cmd)
        self.do_assert(my_re.search(r"but|we|also|get|to|see|the|whole|thing", output.strip()))
        return
    
    @pytest.mark.skip               # TODO: Fix path for audio_file    
    def test_sound_file_us2(self):
        """Ensures that test_sound_file_us2 works properly"""
        ## TEST 3: Test the vanilla script using a different soundfile (US English)
        debug.trace(4, f"TestIt.test_sound_file_us2(); self={self}")
        audio_file = gh.resolve_path("examples/resources/speech-wav/us10.wav")
        output_cmd = f"python3 {HF_SPEECHREC_PATH} {audio_file} 2> /dev/null"
        output = gh.run(output_cmd)
        self.do_assert(my_re.search(r"we|tend|to|seek|simple|answers", output.strip()))
        return
    
    @pytest.mark.skip 
    def test_sound_file_model(self):
        """Ensures that test_sound_file_model works properly"""
        ## TEST 4: Test the script using a different ASR model
        ## NOTE: Skipped due to use of a different model (i.e. large downloads)   
        audio_file = gh.resolve_path("fuzzy-testing-1-2-3.wav")
        asr_model = "openai/whisper-large-v3"
        output_cmd = f"ASR_MODEL={asr_model} python3 {HF_SPEECHREC_PATH} {audio_file} 2> /dev/null"
        output = gh.run(output_cmd)
        self.do_assert(my_re.search(r"testing|one|two|three", output.strip()))
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
