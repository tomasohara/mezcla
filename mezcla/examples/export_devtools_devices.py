#! /usr/bin/env python3
# TODO: # -*- coding: utf-8 -*-
## TODO: handle case when env installed elsewhere (e.g., maldito mac)
## #! env python
#
# TODO what the script does (detailed)
# -or-
# Based on following:
#   TODO: url
#

"""
Export Chrome DevTools emulated devices (vertical dimensions) as CSV.

Extracted fields:
    title,width,height,device-pixel-ratio,user-agent

Example:
    curl --remote-name --silent 'https://raw.githubusercontent.com/ChromeDevTools/devtools-frontend/refs/heads/main/front_end/models/emulation/EmulatedDevices.ts'
    python {script} EmulatedDevices.ts > devices.csv
"""

# Standard modules
from typing import Optional

# Installed modules
## TODO: import numpy as np

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main, FILENAME
from mezcla.my_regex import my_re
from mezcla import system
## TODO:
## from mezcla import data_utils as du
## TODO2: streamline imports by exposing common functions, etc. in mezcla
##
## Optional:
## # Increase trace level for regex searching, etc. (e.g., from 6 to 7)
## my_re.TRACE_LEVEL = debug.QUITE_VERBOSE
debug.trace(5, f"global __doc__: {__doc__}")
debug.assertion(__doc__)

# Constants
TL = debug.TL
## TODO: Constants for switches omitting leading dashes (e.g., DEBUG_MODE = "debug-mode")
## Note: Run following in Emacs to interactively replace TODO_ARG with option label
##    M-: (query-replace-regexp "todo\\([-_]\\)arg" "arg\\1name")
## where M-: is the emacs keystroke short-cut for eval-expression.
##
## TODO: TODO_BOOL_OPT = "todo-bool-option"
## TODO: TODO_TEXT_OPT = "todo-text-option"

# Environment options
# Notes:
# - These are just intended for internal options, not for end users.
# - They also allow for enabling options in one place rather than four
#   when using main.Main (e.g., [Main member] initialization, run-time
#   value, and argument spec., along with string constant definition).
# WARNING: To minimize environment comflicts with other programs make the names
# longer such as two or more tokens (e.g., "FUBAR" => "FUBAR_LEVEL").
#
## TODO_FUBAR = system.getenv_bool(
##     "TODO_FUBAR", False,
##     description="TODO:Fouled Up Beyond All Recognition processing")

#-------------------------------------------------------------------------------

class Helper:
    """TODO: class for doing DevTools device export"""

    def __init__(self, _arg=None, **kwargs) -> None:
        """Initializer: TODO_arg desc"""
        debug.trace_expr(TL.VERBOSE, _arg, kwargs, prefix="in Helper.__init__: ")
        self._arg = _arg                # TODO: revise
        self.TODO: Optional[bool] = None
        debug.trace_object(5, self, label=f"{self.__class__.__name__} instance")

    # -------------------------------------------------------------------------

    def _extract_device_block(self, text: str) -> str:
        debug.trace(TL.DETAILED, "_extract_device_block()")
        match = my_re.search(
            r"// DEVICE-LIST-BEGIN(.*?)// DEVICE-LIST-END",
            text,
            my_re.DOTALL,
        )
        return match.group(1) if match else ""

    # -------------------------------------------------------------------------

    def _extract_field(self, pattern: str, text: str, default: str = "") -> str:
        match = my_re.search(pattern, text, my_re.DOTALL)
        return match.group(1).strip() if match else default

    # -------------------------------------------------------------------------

    def process(self, _arg) -> bool:
        """TODO: Process _ARG to generate CSV"""
        debug.trace_expr(TL.DETAILED, _arg)

        text = _arg
        block = self._extract_device_block(text)

        if not block:
            print("Error: DEVICE-LIST block not found")
            return False

        print("title,width,height,device-pixel-ratio,user-agent")

        devices = my_re.split(r"\n\s*\{\s*\n", block)

        for dev in devices:
            if "'title':" not in dev:
                continue

            title = self._extract_field(r"'title':\s*(?:i18nLazyString\([^)]*\)|'([^']*)')", dev)
            if not title:
                title = self._extract_field(r"'title':\s*i18nLazyString\([^)]*'([^']*)'\)", dev)

            width = self._extract_field(
                r"'vertical':\s*\{[^}]*'width':\s*([0-9.]+)", dev
            )
            height = self._extract_field(
                r"'vertical':\s*\{[^}]*'height':\s*([0-9.]+)", dev
            )
            dpr = self._extract_field(
                r"'device-pixel-ratio':\s*([0-9.]+)", dev
            )
            ua = self._extract_field(
                r"'user-agent':\s*'([^']*)'", dev
            )

            print(f"{title},{width},{height},{dpr},\"{ua}\"")

        return True


#-------------------------------------------------------------------------------

def main() -> None:
    """Entry point"""
    debug.trace(TL.DETAILED, f"main(): script={system.real_path(__file__)}")

    main_app = Main(
        skip_input=False,
        manual_input=True,
        description=__doc__.format(script=gh.basename(__file__)),
        # FILENAME is default positional argument
    )

    debug.reference_var(FILENAME)
    debug.assertion(main_app.parsed_args)

    helper = Helper()

    input_text = main_app.read_entire_input()
    helper.process(input_text)

    debug.assertion(not any(my_re.search(r"^TODO_", m, my_re.IGNORECASE)
                            for m in dir(main_app)))
    return

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    debug.trace(5, f"module __doc__: {__doc__}")
    debug.assertion("TODO:" not in __doc__)
    main()
