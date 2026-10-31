#! /usr/bin/env python3
##
## Tests for ../ocr_utils.py
##..............................................................................
# TODO: # -*- coding: utf-8 -*-
#
# Notes:
# - New OCR tests are xfailed until they are verified with representative scans.
# - Direct helper tests are preferred over run_script because they do not depend
#   on a separate Tesseract installation.

"""Tests for ocr_utils module."""

# Standard modules
import shutil
from unittest.mock import Mock, patch

# Installed modules
import pytest

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
import mezcla.ocr_utils as THE_MODULE

# Note: Two references are used for the module to be tested:
#    THE_MODULE:               module object
#    TestIt.script_module:     dotted module path
PIL = pytest.importorskip("PIL")
pytest.importorskip("pytesseract")
from PIL import Image

# Environment options
## TODO: OCR_TEST_IMAGE = system.getenv_filename(
##     "OCR_TEST_IMAGE", None, description="Representative scanned document")
#
## BAD: EASY_IMAGE = gh.form_path("tests", "resources", "mezcla-1.4.1.1-30oct26.png")
## BAD2: EASY_IMAGE = gh.form_path("mezcla", "tests", "resources", "mezcla-1.4.1.1.png")
EASY_IMAGE = gh.resolve_path("mezcla-1.4.1.1.png", heuristic=True)
## BAD: HARD_IMAGE = gh.form_path("tests", "resources", "blurred-recovery-key.jpg")
## BAD2: HARD_IMAGE = gh.form_path("mezcla", "tests", "resources", "blurred-recovery-key.jpg")
HARD_IMAGE = gh.resolve_path("blurred-recovery-key.jpg", heuristic=True)
TESSERACT_AVILABLE = shutil.which("tesseract")
debug.assertion(TESSERACT_AVILABLE)
SKIP_TESSERACT = not TESSERACT_AVILABLE
SKIP_TESSERACT_REASON = "Tesseract executable is unavailable"


#------------------------------------------------------------------------

class TestIt(TestWrapper):
    """Class for OCR utility test definitions."""

    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    def test_01_prepare_image_normalizes_and_scales(self):
        """Verify grayscale conversion, thresholding, and scaling."""
        debug.trace(4, f"TestIt.test_01_prepare_image_normalizes_and_scales(); self={self}")
        source = Image.new("RGB", (2, 1))
        source.putdata([(20, 20, 20), (240, 240, 240)])
        settings = THE_MODULE.OCRSettings(
            scale=3, contrast=1.0, sharpen=False, denoise=False, threshold=128)

        result = THE_MODULE.prepare_image(source, settings)

        assert result.mode == "L"
        assert result.size == (6, 3)
        assert set(result.getdata()).issubset({0, 255})
        assert source.mode == "RGB"
        return

    def test_02_recognize_uses_tesseract_options(self):
        """Verify recognition supplies normalized input and explicit options."""
        debug.trace(4, f"TestIt.test_02_recognize_uses_tesseract_options(); self={self}")
        tesseract = Mock()
        tesseract.image_to_string.return_value = "recognized text"
        source = Image.new("RGB", (3, 2), "white")
        settings = THE_MODULE.OCRSettings(
            scale=1, contrast=1.0, sharpen=False, denoise=False)

        with patch.object(THE_MODULE, "_load_tesseract", return_value=tesseract):
            result = THE_MODULE.recognize(
                source, settings, language="deu", page_segmentation_mode=11, timeout=5)

        assert result == "recognized text"
        image = tesseract.image_to_string.call_args.args[0]
        assert image.mode == "L"
        tesseract.image_to_string.assert_called_once_with(
            image, lang="deu", config="--psm 11", timeout=5)
        return

    def test_02_cli_uses_positional_filename(self):
        """Verify the command-line path is passed directly to the OCR helper."""
        ## BAD: runtime_args=["input.jpg"], auto_help=False, manual_input=True)
        ## BAD: runtime_args=["input.jpg"], auto_help=False, skip_input=False,
        ## BAD: manual_input=True)
        app = THE_MODULE.Script(
            runtime_args=["input.jpg"], auto_help=False, skip_input=True,
            manual_input=True,
            positional_arguments=[(THE_MODULE.FILENAME, "Image filename to recognize")])
        app.setup()
        app.helper = Mock()
        app.helper.recognize.return_value = "recognized text"

        app.run_main_step()

        app.helper.recognize.assert_called_once_with("input.jpg")
        self.do_assert("recognized text" in self.get_stdout())
        return

    @pytest.mark.skipif(SKIP_TESSERACT, reason=SKIP_TESSERACT_REASON)
    def test_03_release_image_recognition(self):
        """Verify OCR recognizes the package name in the release image."""
        debug.trace(4, f"TestIt.test_03_release_image_recognition(); self={self}")
        text = THE_MODULE.recognize(EASY_IMAGE)
        self.do_assert("mezcla" in text.lower(), f"Unexpected OCR output: {text!r}")
        return

    @pytest.mark.skipif(SKIP_TESSERACT, reason=SKIP_TESSERACT_REASON)
    @pytest.mark.xfail(reason="TODO: improve preprocessing for blurred recovery keys")
    def test_04_blurred_recovery_key_recognition(self):
        """Verify future preprocessing recognizes the blurred recovery key."""
        debug.trace(4, f"TestIt.test_04_blurred_recovery_key_recognition(); self={self}")
        text = THE_MODULE.recognize(HARD_IMAGE)
        self.do_assert("key" in text.lower(), f"Unexpected OCR output: {text!r}")
        return

    @pytest.mark.xfail(reason="TODO: verify settings against representative scans")
    def test_03_representative_scan(self):
        """TODO: Verify OCR accuracy for a real production scan."""
        debug.trace(4, f"TestIt.test_03_representative_scan(); self={self}")
        assert False, "TODO: add a stable fixture and expected transcription"

    @pytest.mark.xfail(reason="TODO: test Tesseract executable error reporting")
    def test_04_tesseract_failure(self):
        """TODO: Verify failures from the OCR executable are actionable."""
        debug.trace(4, f"TestIt.test_04_tesseract_failure(); self={self}")
        assert False, "TODO: mock a Tesseract executable failure"

    @pytest.mark.xfail(reason="TODO: test deskewing with optional OpenCV backend")
    def test_05_deskew(self):
        """TODO: Verify future deskewing support."""
        debug.trace(4, f"TestIt.test_05_deskew(); self={self}")
        assert False, "TODO: implement optional OpenCV deskewing"


#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
