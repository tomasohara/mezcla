#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Convert emoticons/emoji into names (or just strips them)
#
# Example Input (n.b., U+1f634 is sleeping-face character):
#   Nothing to do 😴
#
# Example output:
#   Nothing to do [sleeping face]
#
# Note:
# - via https://www.dictionary.com/compare-words/emoticon-vs-emoji:
#   emoji comes from a Japanese term meaning “pictograph,” from e, “picture, drawing,” and moji, “(written) character, letter.”
#
# TODO2:
# - Handle variational selectors as in "‼️" (e.g., U+FE0F). See
#   https://stackoverflow.com/questions/38100329/what-does-u-ufe0f-in-an-emoji-mean-is-it-the-same-if-i-delete-it
#

"""
Replace emoticons with name (or remove entirely)

Sample usage:
   echo "some \u24DB\u2009 please" | {script} -
"""
#
# note: uses U+24D8 [Circled Latin Small Letter I] and U+2009 [Thin Space]
#
##
## OLD2:
##    echo "some \U0001F6C8 please" | {script} -
## """                             # 🛈 (Circled Information Source: U+1F6C8)
## TODO3: fix spacing after info icon (wider than default characters)
##
## OLD:
##     echo 'github-\U0001f917_Transformers' | {script} -
## """                          # 🤗 (HuggingFace logo: U+1f917)

# Standard modules
import unicodedata

# Intalled module
# TODO: import numpy as np

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main
from mezcla import system

# Constants
TL = debug.TL
STRIP_OPT = "strip"

# Environment options
REPLACEMENT_TEXT = system.getenv_value(
    "REPLACEMENT_TEXT", None,
    description="Override for empty replacement text")
STRIP_EMOTICONS = system.getenv_bool(
    "STRIP_EMOTICONS", False,
    description="Make emoticon removal default instead of rename/removal")
AUGMENT_EMOTICONS = system.getenv_bool(
    "AUGMENT_EMOTICONS", False,
    description="Make emoticon augmentation default instead of rename/removal")

#-------------------------------------------------------------------------------

class ConvertEmoticons:
    """Support for stripping those pesky emoticons from text (or replacing with description)"""
    OTHER_SYMBOL = 'So'
    BTL = 5                             # base trace level

    def __init__(self, replace=None, strip=None, replacement=None, augment=None, base_trace_level=None):
        """Initializer: sets defaults for convert method
        Note: see convert() for argument descriptions
        """
        # TODO3: rework to remove non-standard functional interface for class
        if base_trace_level is not None:
            self.BTL = base_trace_level
        debug.trace_expr(self.BTL + 3, replace, strip, replacement, augment,
                         prefix="in ConvertEmoticons.__init__: ")
        if strip is None:
            strip = STRIP_EMOTICONS
        if replace is None:
            replace = not strip
        if replacement is None:
            replacement = (REPLACEMENT_TEXT or "")
        if augment is None:
            augment = AUGMENT_EMOTICONS
        self.replace = replace
        self.strip = strip
        self.replacement = replacement
        self.augment = augment
        debug.trace_object(self.BTL + 2, self, label=f"{self.__class__.__name__} instance")
    #
    # EX: ce = ConvertEmoticons(); (ce.strip != cs.replace) => True
    # EX: ce.convert()("❌ Failure") => "[cross mark] Failure"  # U+274c

    def convert(self, text=None, replace=None, strip=None, replacement=None, augment=None):
        """Either REPLACE emotions in TEXT with Unicode name, STRIP them entirely, or AUGMENT
        Note:
        - REPLACEMENT can be used for subsituted text (e.g., instead of "").
        - with AUGMENT the emoticon is still included (a la REPLACE plus STRIP).
        """
        # EX: ce.convert("✅ Success") => "[checkmark] Success"  # U+2705
        # EX: ce.convert("✅ Success", augment=True) => "✅ [checkmark] Success"
        # EX: ce.convert("año") => "año"       # ignore diacritic; Spanish for year
        debug.trace_expr(self.BTL + 1, replace, strip, replacement, augment,
                         prefix="in ce.convert: text=_; ")
        debug.assertion(text is not None)
        debug.assertion(not (replace and strip))
        debug.assertion(not (augment and strip))
        if strip is None:
            strip = self.strip
        if replace is None:
            replace = self.replace
        if replacement is None:
            replacement = self.replacement
        if augment is None:
            augment = self.augment
        debug.trace_expr(self.BTL + 1, replace, strip, replacement, augment,
                         prefix="ce.convert: text=_; ")
        in_text = text
        text = (text or "")
        #
        chars = []
        for ch in text:
            new_ch = ch
            if unicodedata.category(ch) == self.OTHER_SYMBOL:
                new_ch = (f"{ch} " if augment else "")
                new_ch += f"[{unicodedata.name(ch).lower()}]" if replace else replacement
            chars.append(new_ch)
        text = "".join(chars)
        #
        level = (self.BTL if (text != in_text) else self.BTL + 1)
        debug.trace(level, f"ce.convert({in_text!r}) => {text!r}")
        return text
    #
    # EX: ce.convert("✅ Success", strip=True) => " Success"   # U+2705 [White Heavy Check Mark]
    # EX: ce.convert("✅ Success", strip=True, replacement="_") => "_ Success"
    # note: ignores common language characters (e.g., CJK and ISO-8859)
    # EX: ce.convert("天気") => "天気"   # Japanese for weather (U+5929 U+6c17)
    # EX: ce.convert("¿Hablas español?") => "¿Hablas español?"  # Spanish for "Do you speak Spanish"

#-------------------------------------------------------------------------------

def convert_emoticons(text, **kwargs):
    """Convenience wrapper around ConvertEmoticons().convert(TEXT): see argument description there"""
    result = ConvertEmoticons(**kwargs).convert(text)
    debug.trace(7, f"convert_emoticons(); kw={kwargs} => {result!r}")
    return result


def main():
    """Entry point"""
    debug.trace(TL.VERBOSE, f"main(): script={system.real_path(__file__)}")

    # Parse command line options, show usage if --help given
    # TODO: manual_input=True; short_options=True
    main_app = Main(description=__doc__.format(script=gh.basename(__file__)),
                    boolean_options=[(STRIP_OPT, "Strip emoticon entirely, instead of replacing with name")],
                    skip_input=False, input_error='ignore')
    debug.assertion(main_app.parsed_args)
    strip_entirely = main_app.get_parsed_option(STRIP_OPT)
    ce = ConvertEmoticons(strip=strip_entirely)

    # Print the result of conversion, trapping for errors
    # note: awkward construct to avoid BrokenPipeError
    # see https://stackoverflow.com/questions/26692284/how-to-prevent-brokenpipeerror-when-doing-a-flush-in-python
    try:
        for line in main_app.read_entire_input().splitlines():
            print(ce.convert(line))
    except:
        debug.trace_exception(6, "ConvertEmoticons.convert")
    return

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    main()
