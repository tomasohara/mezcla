#! /usr/bin/env python3
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
from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla import system

# Constants and environment options
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
##
## TODO3: remove alias RUN_SLOW_TESTS
RUN_SLOW_TESTS = system.getenv_bool(
    "RUN_SLOW_TESTS", 
    description="Alias for not[-]SKIP_SLOW_TESTS")
SKIP_SLOW_TESTS = system.getenv_bool(
    "SKIP_SLOW_TESTS",
    (not (UNDER_RUNNER or RUN_SLOW_TESTS)),
    description="Omit tests that can a while to run")
SKIP_SLOW_REASON="Ignoring slow test"
##
SKIP_UNIMPLEMENTED_TESTS = system.getenv_bool(
    # Note: used to avoid clutter due to (so many) unimplemented tests, such as
    # when using --runxfail for better test failure diagnostics.
    "SKIP_UNIMPLEMENTED_TESTS", 
    False,
    description="Skip tests not yet implemented")
SKIP_UNIMPLEMENTED_REASON = "Ignoring unimplemented test"
SKIP_EXPECTED_REASON = "Skipping cases that should never pass (e.g., intentional error)"
SKIP_EXPECTED_ERRORS = system.getenv_bool(
    # Note: this helps filter known errors before running error checking script,
    # (e.g., check_errors.py in companion repo tomasohara/shell-scripts).
    # It is different from xfail in that the tests are not likely to ever pass.
    "SKIP_EXPECTED_ERRORS",
    False,
    description="Skip cases intentionally causing conversion errors, etc.")
#
SKIP_TBD_REASON="Ignore test to be designed"
SKIP_TBD_TESTS = system.getenv_bool(
    "SKIP_TBD_TESTS", False,
    description=SKIP_TBD_REASON)

# Globals
mezcla_root_dir = None

#-------------------------------------------------------------------------------

def fix_indent(code):
    """Make sure CODE indented proper if it is a string;
    however, list input is returned as is.
    Note: this accounts for code defined with indented triple-quoted strings
    
    >>> fix_indent('''
                   print("ok")
                   ''')
    'print("ok")'
    """
    result = code
    if isinstance(result, str) and my_re.search(r"^\n( +)", result):
        indentation = my_re.group(1)
        result = my_re.sub(fr"^{indentation}", "", result, flags=my_re.MULTILINE)
    debug.trace(8, f"fix_indent{code!r} => {result!r}")
    return result


def get_mezcla_root_dir():
    """Get the base directory for the mezcla distribution"""
    test_dir = gh.dir_path(__file__)
    root_dir = system.real_path(gh.form_path(test_dir, "..", ".."))
    debug.assertion(system.file_exists(gh.form_path(root_dir, "LICENSE.txt")))
    debug.trace(5, f"get_mezcla_root_dir() => {root_dir!r}")
    return root_dir      

mezcla_root_dir = get_mezcla_root_dir()

#-------------------------------------------------------------------------------

if __name__ == "__main__":
    debug.trace_current_context()
    system.print_stderr(f"Warning: {__file__} is not intended to be run standalone\n")
