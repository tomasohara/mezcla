# ! /usr/bin/env python
#
# Test(s) for ../examples/hugging_face_speechrec.py
#
## NOTE: Takes time for initial run and chances of crash (requires specific language models for each tests)

"""Tests for examples/hugging_face_speechrec module"""

# Standard packages
## NOTE: this is empty for now

# Installed packages
import pytest
import re
import json
import ast

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
from mezcla.examples import hugging_face_speechrec as THE_MODULE

class TestKenlmExample(TestWrapper):
    script_file = TestWrapper.get_module_file_path(__file__)
    script_module = TestWrapper.get_testing_module_name(__file__)
    use_temp_base_dir = True    # treat TEMP_BASE as directory

    """Class for testcase definition"""
    
    # TEST - 1 : DEFAULT SPEECHREC (EN)
    def test_speechrec_default(self):
        """Ensures that test_speechrec_default works properly"""
        debug.trace(4, "test_speechrec_default()")

        text_output = "but we also got to see the whole thing"
        SOUND_PATH = "../examples/speech-wav/us1.wav"
        command_1 = f"SOUND_FILE='{SOUND_PATH}' ../examples/hugging_face_speechrec.py {SOUND_PATH} > {self.temp_file}"
        gh.run(command_1)

        output_json = ast.literal_eval(gh.read_file(self.temp_file).strip())
        output = output_json["text"]
        assert (output == text_output)
        return 
    
    # TEST - 2 : SPEECHREC USING DIFFERENT MODEL (EN)
    def test_speechrec_default(self):
        """Ensures that test_speechrec_default works properly"""
        debug.trace(4, "test_speechrec_default()")

        text_output = "but we also got to see the whole thing"
        SOUND_PATH = "../examples/speech-wav/us1.wav"
        command_1 = f"SOUND_FILE='{SOUND_PATH}' ../examples/hugging_face_speechrec.py {SOUND_PATH} > {self.temp_file}"
        gh.run(command_1)

        output_json = ast.literal_eval(gh.read_file(self.temp_file).strip())
        output = output_json["text"]
        assert (output == text_output)
        return 

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])


        

