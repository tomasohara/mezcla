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

    ## TODO:
    system.print_error("Error: Implement me!")
    ## ALT TODO:
    ## for line in main_app.read_entire_input().splitlines():
    ##     print(TODO_fn(line))
    return

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    main()
