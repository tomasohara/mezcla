#! /usr/bin/env python
#
# Common code and settings used in tests.
#

"""Common test module"""

# Standard modules
## TODO: from collections import defaultdict

# Installed modules
## TODO: import pytest

# Local modules
from mezcla import debug
from mezcla import system

# Environment options
# Note: These are just intended for internal options, not for end users.
# It also allows for enabling options in one place.
#
USER = system.getenv_bool(
    "USER", "user",
    description="Current user")
HOME = system.getenv_bool(
    "HOME", "/home/user",
    description="Home directory")
UNDER_RUNNER = system.getenv_bool(
    "UNDER_RUNNER", HOME == "/home/runner",
    description="Whether running under Github actions")
SKIP_SLOW_TESTS = system.getenv_bool(
    "SKIP_SLOW_TESTS",
    (not UNDER_RUNNER),
    description="Omit tests that can a while to run")
RUN_SLOW_TESTS = system.getenv_bool(
    "RUN_SLOW_TESTS", 
    not SKIP_SLOW_TESTS,
    description="Alias for not[-]SKIP_SLOW_TESTS")

if __name__ == "__main__":
    debug.trace_current_context()
    system.print_stderr(f"Warning: {__file__} is not intended to be run standalone\n")
