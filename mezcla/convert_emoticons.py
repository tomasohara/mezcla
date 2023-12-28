#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Convert emoticons into names (or just strips them)
#
# Example Input:
#   Nothing to do 😴
#
# Example output:
#   Nothing to do [sleeping face]
#

"""
Replace emoticons with name (or remove entirely)

Sample usage:

   echo 'github-\U0001F634_Transformers' | {script} -
"""                          # 🤗 (HuggingFace logo)

# Standard modules
import unicodedata

# Intalled module
# TODO: import numpy as np

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main
## TODO: from mezcla.my_regex import my_re
from mezcla import system
## TODO2: streamline imports by exposing common functions, etc. in mezcla

# Constants
TL = debug.TL
STRIP_OPT = "strip"

# Environment options
REPLACEMENT_TEXT = system.getenv_value("REPLACEMENT_TEXT", None,
                                       description="Override for empty replacement text")
STRIP_EMOTICONS = system.getenv_value("STRIP_EMOTICONS", False,
                                       description="Make emoticon removal default instead of rename")


#-------------------------------------------------------------------------------

class ConvertEmoticons:
    """Support for stripping those pesky emoticons from text (or replacing with description)"""
    OTHER_SYMBOL = 'So'

    def __init__(self, replace=None, strip=None, replacement=None):
        """Initializer: sets defaults for convert method
        Note: see convert() for argument descriptions
        """
        # TODO3: rework to remove non-standard functional interface for class
        debug.trace_expr(7, replace=None, strip=None, replacement=None, text=None, prefix="in ConvertEmoticons.__init__: ")
        if strip is None:
            strip = STRIP_EMOTICONS
        if replace is None:
            replace = not strip
        if replacement is None:
            replacement = (REPLACEMENT_TEXT or "")        
        self.replace = replace
        self.strip = strip
        self.replacement = replacement
        debug.trace_object(5, self, label=f"{self.__class__.__name__} instance")
    #
    # EX: ce = ConvertEmoticons(); (ce.strip != cs.replace) => True
    # EX: ce.convert()("❌ Failure") => "[cross mark] Failure"

    def convert(self, text=None, replace=None, strip=None, replacement=None):
        """Either REPLACE emotions in TEXT with Unicode name or STRIP them entirely
        Note: REPLACEMENT can be used for subsituted text (e.g., instead of "")
        """
        # EX: ce.convert("✅ Success") => "[checkmark] Success"
        # EX: ce.convert("año") => "año"       # ignore diacritic; Spanish for year
        debug.trace(6, f"ce.convert(_, [r={replace}], [s={strip}])")
        debug.assertion(text is not None)
        debug.assertion(not (replace and strip))
        if strip is None:
            strip = self.strip
        if replace is None:
            replace = self.replace
        if replacement is None:
            replacement = self.replacement
        in_text = text
        text = (text or "")
        #
        chars = []
        for ch in text:
            if unicodedata.category(ch) == self.OTHER_SYMBOL:
                ch = f"[{unicodedata.name(ch).lower()}]" if replace else replacement
            chars.append(ch)
        text = "".join(chars)
        #
        level = (4 if (text != in_text) else 6)
        debug.trace(level, f"ce.convert({in_text!r}) => {text!r}")
        return text
    #
    # EX: ce.convert("✅ Success", strip=True) => " Success"
    # EX: ce.convert("✅ Success", strip=True, replacement="_") => "_ Success"
    # note: ignores common language characters (e.g., CJK and ISO-8859)
    # EX: ce.convert("天気") => "天気"   # Japanese for weather
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
                    skip_input=False)
    debug.assertion(main_app.parsed_args)
    strip_entirely = main_app.get_parsed_option(STRIP_OPT)
    ce = ConvertEmoticons(strip=strip_entirely)

    for line in main_app.read_entire_input().splitlines():
        print(ce.convert(line))
    return

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    main()
