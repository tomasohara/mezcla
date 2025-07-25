#! /usr/bin/env python3
# TODO: # -*- coding: utf-8 -*-
#
# Based on following:
#   TODO: url
#

"""
TODO: what module does (brief)

Sample usage:
   echo $'TODO:task1\\nDONE:task2' | {script} --TODO-arg --
"""

# Standard modules
## TODO: import json

# Installed modules
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
## TODO: TODO_BOOL_OPT = "todo-bool-option"
## TODO: TODO_TEXT_OPT = "todo-text-option"

## TODO:
## # Environment options
## # Notes:
## # - These are just intended for internal options, not for end users.
## # - They also allow for enabling options in one place rather than four
## #   when using main.Main (e.g., [Main member] initialization, run-time
## #   value, and argument spec., along with string constant definition).
## #
## ENABLE_FUBAR = system.getenv_bool("ENABLE_FUBAR", False,
##                                   description="Enable fouled up beyond all recognition processing")

#-------------------------------------------------------------------------------

class Helper:
    """TODO: class for doing ..."""

    def __init__(self, _arg=None) -> None:
        """Initializer: TODO: ..."""
        debug.trace(TL.VERBOSE, f"Helper.__init__({_arg}): self={self}")
        self.TODO = None
        debug.trace_object(5, self, label=f"{self.__class__.__name__} instance")

    def process(self, _arg) -> bool:
        """TODO: ..."""
        # TODO: flesh out
        ## TODO3: system.print_error("Error: Implement me!")
        ## NOTE: print used for sake of unit test (see examples/tests/test_template.py)
        print("Error: Implement me!")
        return False

#-------------------------------------------------------------------------------

def main():
    """Entry point"""
    debug.trace(TL.USUAL, f"main(): script={system.real_path(__file__)}")

    # Parse command line options, show usage if --help given
    # TODO: manual_input=True; short_options=True
    # Note: Uses Main without subclassing, so some methods are stubs (e.g., run_main_step).
    main_app = Main(
        description=__doc__.format(script=gh.basename(__file__)),
        ## TODO: boolean_options=[(TODO_BOOL_OPT, "TODO desc1")],
        ## TODO: text_options=[(TODO_TEXT_OPT, "TODO desc2")],
    )
    debug.assertion(main_app.parsed_args)
    ## TODO_opt1 = main_app.get_parsed_option(TODO_BOOL_OPT)

    helper = Helper()
    helper.process("TODO: some argument")
    
    ## TODO:
    ## ALT TODO:
    ## for line in main_app.read_entire_input().splitlines():
    ##     helper.process(TODO_fn(line))
    ## -or-
    ## helper.process( main_app.read_entire_input())
    return

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    main()
