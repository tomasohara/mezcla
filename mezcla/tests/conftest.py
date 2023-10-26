#! /usr/bin/env python
#
# TLDR: Attempt at getting maldito pytest not to swallow exceptions.
#
# Note:
# - *** This doesn't work: instead use trap_exception decorator in unittest_wrapper.py.
# - Based on https://stackoverflow.com/questions/62419998/how-can-i-get-pytest-to-not-catch-exceptions.
# - See https://docs.pytest.org/en/7.1.x/reference/reference.html.
#

"""Configuration so that pytest doesn't swallow exceptions"""

# Standard packages
## OLD: import os

# Installed packages
## TODO: import pytest

# Local packages
from mezcla import debug
from mezcla import system

# Have pytest enable exceptions
ENABLE_PYTEST_RAISE = system.getenv_bool('_PYTEST_RAISE', False,
                                         desc="Raise exceptions in test code")
if ENABLE_PYTEST_RAISE:

    ## OLD
    ## @pytest.hookimpl(tryfirst=True)
    ## def pytest_exception_interact(call):
    ##     debug.trace(5, "pytest_exception_interact({call})")
    ##     raise call.excinfo.value
    ##
    ## @pytest.hookimpl(tryfirst=True)
    ## def pytest_internalerror(excinfo):
    ##     debug.trace(5, "pytest_internalerror({excinfo})")
    ##     raise excinfo.value
    
    def pytest_exception_interact(node, call, report):
        """Called when an exception was raised which can potentially be interactively handled"""
        debug.trace(5, f"pytest_exception_interact{((node, call, report))}")
        raise call.excinfo.value

    def pytest_internalerror(excrepr, excinfo):
        """Return True to suppress the fallback handling of printing an INTERNALERROR message directly to sys.stderr"""
        debug.trace(5, f"pytest_internalerror{(excrepr, excinfo)}")
        raise excinfo.value
    

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    system.print_stderr("Error: Not intended to be invoked directly")
