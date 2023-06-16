#! /usr/bin/env python
#
# Test(s) for Hugging Face (HF) Stable Diffulion (SD) module: ../hf_stable_diffusion.py
#
# Notes:
# - Fill out TODO's below. Use numbered tests to order (e.g., test_1_usage).
# - TODO: If any of the setup/cleanup methods defined, make sure to invoke base
#   (see examples below for setUp and tearDown).
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_hf_stable_diffusion.py
#
# TODO3: check image attributes (e.g., backgfround color) and work in image classification (e.g., box)
#

"""Tests for hf_stable_diffusion module"""

# Standard packages
import re

# Installed packages
import pytest
try:
    import diffusers
except:
    diffusers = None

# Local packages
from mezcla.unittest_wrapper import TestWrapper
from mezcla import debug
from mezcla import system
from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                  global module object
#    TestTemplate.script_module:  path to file
import mezcla.examples.hf_stable_diffusion as THE_MODULE
#
# Note: sanity test for customization (TODO: remove if desired)
if not re.search(__file__, r"\btemplate.py$"):
    debug.assertion("mezcla.template" not in str(THE_MODULE))

class TestIt(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    # -or- non-mezcla: script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    #
    use_temp_base_dir = True            # treat TEMP_BASE as directory
    # note: temp_file defined by parent (along with script_module, temp_base, and test_num)

    @pytest.mark.skipif(not diffusers, reason="SD diffusers package missing")
    def test_simple_generation(self):
        """Makes sure simple image generation works as expected"""
        debug.trace(4, f"TestIt.test_data_file(); self={self}")
        # ex: See sd-app-image-1.png
        output = self.run_script(
            options="--batch --prompt 'orange ball' --negative 'green blue red yellow purple pink brown'",
            env_options=f"BASENAME='{self.temp_base}'", uses_stdin=True)
        debug.trace_expr(5, output)
        assert (my_re.search(r"See (\S+.png) for output image(s).", output.strip()))
        image_file = my_re.group(1)
        # ex: sd-app-image-3.png: PNG image data, 512 x 512, 8-bit/color RGB, non-interlaced
        file_info = gh.run(f"file {image_file}")
        debug.trace_expr(5, file_info)
        assert (my_re.search("PNG image data, 512 x 512, 8-bit/color RGB", file_info))
        # TODO2: orange in rgb-color profile for image
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    @pytest.mark.skipif(not diffusers, reason="SD diffusers package missing")
    def test_something_else(self):
        """TODO: flesh out test for something else"""
        debug.trace(4, f"TestIt.test_something_else(); self={self}")
        self.fail("TODO: code test")
        # ex: extcolors sd-app-image-1.png | rgb_color_name.py - | grep -i orange
        return

#...............................................................................

class TestIt2:
    """Another class for testcase definition
    Note: Needed to avoid error with pytest due to inheritance with unittest.TestCase via TestWrapper"""
    
    @pytest.mark.skipif(not diffusers, reason="SD diffusers package missing")
    def test_pipeline(self):
        """Make sure valid SD pipeline created"""
        debug.trace(4, f"TestIt.test_something_else(); self={self}")
        sd = THE_MODULE.StableDiffusion(use_hf_api=True)
        pipe = sd.init_pipeline()
        actual = my_re.split(r"\W+", str(pipe))
        expect = "CLIPImageProcessor CLIPTextModel StableDiffusionSafetyChecker text_encoder".split()
        debug.trace_expr(5, actual, expect, delim="\n")
        assert (len(system.intersection(actual, expect)) > 2)
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
