#!/usr/bin/env python3

"""Configuration settings"""

# Installed modules
## TEST: from cachetools import LRUCache, cached
from mezcla import debug
from mezcla import system

# Constants
TL = debug.TL
BASE_DEBUG_LEVEL = system.getenv_int(
    "TFIDF_DEBUG_LEVEL", 6,
    description=f"Base level for TF/IDF tracing--lower to TL.USUAL ({TL.USUAL}) for isolated debugging")
BDL = BASE_DEBUG_LEVEL

#-------------------------------------------------------------------------------

def main():
    """Entry point for script"""
    debug.trace(BDL - 2, "Warning: Unimplemented main")

#-------------------------------------------------------------------------------
    
if __name__ == '__main__':
    system.print_stderr(f"Warning: {__file__} is not intended to be run standalone.")
    main()
