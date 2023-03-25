#! /usr/bin/env python
#
# Based on following:
#   TODO: url
#

"""TODO: overview"""

# Standard modules
# TODO: import re

# Intalled module
# TODO: import numpy as np

# Local modules
from mezcla import debug
from mezcla.main import Main
from mezcla import system
## TODO:
## from mezcla import glue_helpers as gh

# Constants
TL = debug.TL

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

    # Show simple usage if --help given
    dummy_main_app = Main(description=__doc__, skip_input=False, manual_input=False)
    debug.assertion(dummy_main_app.parsed_args)

    ## TODO:
    system.print_error("Error: Implement me!")
    return

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_DETAILED)
    main()
