#! /usr/bin/env python3
##
## OCR utility based on Tesseract and Pillow.
##..............................................................................
# TODO: # -*- coding: utf-8 -*-
#
# Performs image transformations useful for OCR, including EXIF orientation,
# grayscale conversion, contrast enhancement, denoising, sharpening, scaling,
# thresholding, and inversion.
#
# TODO: Add adaptive thresholding and deskewing when an optional OpenCV backend
# is selected.
#
# Sample usage:
#   printf '%s\n' scan.png | {script} --language eng --

## OLD: Each input line is treated as an image filename and its recognized text is sent
## OLD: to standard output. Pillow and pytesseract remain optional until an image is
## OLD: processed, allowing consumers to import the utility without those packages.
"""Production-oriented OCR image preparation and recognition.

The positional input filename is recognized and its text is sent to standard
output. Pillow and pytesseract remain optional until an image is processed.
"""

# Standard modules
from dataclasses import dataclass
from os import PathLike
from typing import Any, Optional, Union

# Installed modules
## TODO: import PIL.Image directly after Pillow becomes a runtime dependency

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
## OLD: from mezcla.main import Main
from mezcla.main import FILENAME, Main
from mezcla.my_regex import my_re
from mezcla import system
## TODO:
## from mezcla import data_utils as du

debug.trace(5, f"global __doc__: {__doc__}")
debug.assertion(__doc__)

# Constants
TL = debug.TL
LANGUAGE = "language"
PAGE_SEGMENTATION_MODE = "page-segmentation-mode"
#
ImageSource = Union[str, PathLike, Any]

# Environment options
# Notes:
# - These are just intended for internal options, not for end users.
# - They also allow for enabling options in one place rather than four when
#   using main.Main.
#
## TODO: OCR_USE_OPENCV = system.getenv_bool(
##     "OCR_USE_OPENCV", False, description="Use OpenCV preprocessing backend")


@dataclass(frozen=True)
class OCRSettings:
    """Controls transformations applied before invoking the OCR engine."""

    scale: int = 2
    contrast: float = 2.0
    sharpen: bool = True
    denoise: bool = True
    threshold: Optional[int] = None
    invert: bool = False

    def __post_init__(self) -> None:
        """Validate settings before any image processing begins."""
        if self.scale < 1:
            raise ValueError(f"scale must be at least one, not {self.scale}")
        if self.contrast <= 0:
            raise ValueError(f"contrast must be positive, not {self.contrast}")
        if self.threshold is not None and not 0 <= self.threshold <= 255:
            raise ValueError("threshold must be between zero and 255")


def _load_pillow() -> tuple:
    """Load Pillow lazily so importing the module does not require it."""
    try:
        # pylint: disable=import-outside-toplevel
        from PIL import Image, ImageEnhance, ImageFilter, ImageOps
    except ImportError as error:
        raise RuntimeError(
            "Image preprocessing requires Pillow; install it with 'pip install Pillow'."
        ) from error
    return Image, ImageEnhance, ImageFilter, ImageOps


def _load_tesseract() -> Any:
    """Load the optional Python wrapper for the Tesseract executable."""
    try:
        # pylint: disable=import-outside-toplevel
        import pytesseract
    except ImportError as error:
        raise RuntimeError(
            "Text recognition requires pytesseract; install it with "
            "'pip install pytesseract' and install the Tesseract executable."
        ) from error
    return pytesseract


#-------------------------------------------------------------------------------

class Helper:
    """Prepare images and submit them to Tesseract."""

    def __init__(
            self, settings: Optional[OCRSettings] = None, language: str = "eng",
            page_segmentation_mode: Optional[int] = 6,
            timeout: Optional[float] = 30.0) -> None:
        """Initialize recognition settings shared by every image."""
        debug.trace_expr(
            TL.VERBOSE, settings, language, page_segmentation_mode, timeout,
            prefix="in Helper.__init__: ")
        if not language:
            raise ValueError("language must not be empty")
        if page_segmentation_mode is not None and page_segmentation_mode < 0:
            raise ValueError("page_segmentation_mode must not be negative")
        if timeout is not None and timeout <= 0:
            raise ValueError("timeout must be positive")
        self.settings = settings or OCRSettings()
        self.language = language
        self.page_segmentation_mode = page_segmentation_mode
        self.timeout = timeout
        debug.trace_object(5, self, label=f"{self.__class__.__name__} instance")

    def prepare_image(self, source: ImageSource) -> Any:
        """Return a normalized, grayscale image suitable for OCR."""
        image_module, enhancer, image_filter, image_ops = _load_pillow()
        if isinstance(source, (str, PathLike)):
            with image_module.open(source) as source_image:
                image = source_image.copy()
        elif isinstance(source, image_module.Image):
            image = source.copy()
        else:
            raise TypeError("source must be a Pillow image or image filename")

        # Apply the camera orientation before changing image coordinates.
        image = image_ops.exif_transpose(image).convert("L")
        image = image_ops.autocontrast(image)
        if self.settings.contrast != 1.0:
            image = enhancer.Contrast(image).enhance(self.settings.contrast)
        if self.settings.denoise:
            image = image.filter(image_filter.MedianFilter(size=3))
        if self.settings.sharpen:
            image = image.filter(
                image_filter.UnsharpMask(radius=2, percent=150, threshold=3))
        if self.settings.scale > 1:
            image = image.resize(
                (image.width * self.settings.scale, image.height * self.settings.scale),
                resample=image_module.Resampling.LANCZOS)
        if self.settings.threshold is not None:
            image = image.point(
                lambda value: 255 if value >= self.settings.threshold else 0)
        if self.settings.invert:
            image = image_ops.invert(image)
        debug.trace(
            TL.DETAILED,
            f"Helper.prepare_image(): size={image.size}; settings={self.settings}")
        return image

    def recognize(self, source: ImageSource) -> str:
        """Recognize text in SOURCE using the configured Tesseract options."""
        tesseract = _load_tesseract()
        config = (f"--psm {self.page_segmentation_mode}"
                  if self.page_segmentation_mode is not None else "")
        try:
            text = tesseract.image_to_string(
                self.prepare_image(source), lang=self.language, config=config,
                timeout=self.timeout)
        except (RuntimeError, OSError) as error:
            raise RuntimeError(f"Tesseract OCR failed: {error}") from error
        debug.trace(TL.DETAILED, f"Helper.recognize(): {len(text)} characters recognized")
        return text


def prepare_image(source: ImageSource, settings: Optional[OCRSettings] = None) -> Any:
    """Return OCR-ready SOURCE using SETTINGS or the production defaults."""
    return Helper(settings=settings).prepare_image(source)


def recognize(
        source: ImageSource, settings: Optional[OCRSettings] = None,
        language: str = "eng", page_segmentation_mode: Optional[int] = 6,
        timeout: Optional[float] = 30.0) -> str:
    """Recognize SOURCE text after applying the selected transformations."""
    return Helper(
        settings=settings, language=language,
        page_segmentation_mode=page_segmentation_mode, timeout=timeout).recognize(source)


class Script(Main):
    """Command-line processor for one positional image filename."""

    language: str = "eng"
    page_segmentation_mode: Optional[int] = 6
    filename: str = ""
    helper: Optional[Helper] = None

    def setup(self) -> None:
        """Extract command-line options and initialize the OCR helper."""
        debug.trace(TL.VERBOSE, f"Script.setup(): self={self}")
        self.language = self.get_parsed_option(LANGUAGE, self.language)
        self.page_segmentation_mode = self.get_parsed_option(
            PAGE_SEGMENTATION_MODE, self.page_segmentation_mode)
        self.filename = self.get_parsed_argument(FILENAME, self.filename)
        self.helper = Helper(
            language=self.language,
            page_segmentation_mode=self.page_segmentation_mode)
        debug.trace_object(5, self, label=f"{self.__class__.__name__} instance")

    def process_line(self, line: str) -> None:
        """Recognize text from the image filename in LINE."""
        debug.trace_fmtd(TL.QUITE_DETAILED, "Script.process_line({l})", l=line)
        debug.assertion(self.helper)
        print(self.helper.recognize(line.strip()))

    def run_main_step(self) -> None:
        """Recognize text from the positional image filename."""
        debug.trace(TL.DETAILED, f"Script.run_main_step(): filename={self.filename!r}")
        debug.assertion(self.helper)
        print(self.helper.recognize(self.filename))

    ## TODO: Add a mode accepting newline-delimited image filenames from standard input.


#-------------------------------------------------------------------------------

def main() -> None:
    """Run the OCR command-line processor."""
    debug.trace(TL.DETAILED, f"main(): script={system.real_path(__file__)}")
    app = Script(
        description=__doc__.format(script=gh.basename(__file__)),
        ## BAD: skip_input=False,
        skip_input=True,
        ## OLD: manual_input=False,
        manual_input=True,
        positional_arguments=[
            (FILENAME, "Image filename to recognize")],
        text_options=[
            (LANGUAGE, "Tesseract language code (default: eng)")],
        ## BAD: (PAGE_SEGMENTATION_MODE, "Tesseract page segmentation mode (default: 6)")])
        int_options=[
            (PAGE_SEGMENTATION_MODE, "Tesseract page segmentation mode (default: 6)")])
    app.run()
    debug.assertion(
        not any(my_re.search(r"^TODO_", member, my_re.IGNORECASE)
                for member in dir(app)))
    return


if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    debug.trace(5, f"module __doc__: {__doc__}")
    main()
