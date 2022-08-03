#! /usr/bin/env python
#
# Test(s) for ../misc_utils.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH="$(realpath .)/..):$PYTHONPATH" python tests/test_misc_utils.py
#

"""Tests for misc_utils module"""

# Standard packages
import re
import os

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
#    TestIt.script_module   string name
import mezcla.misc_utils as THE_MODULE

class TestMiscUtils:
    """Class for test case definitions"""

    def test_transitive_closure(self):
        """Ensure transitive_closure works as expected"""
        debug.trace(4, "test_transitive_closure()")
        ## TODO: WORK-IN-PROGRESS

    def test_read_tabular_data(self):
        """Ensure read_tabular_data works as expected"""
        debug.trace(4, "test_read_tabular_data()")
        ## TODO: WORK-IN-PROGRESS

    def test_extract_string_list(self):
        """Ensure extract_string_list works as expected"""
        debug.trace(4, "test_extract_string_list()")
        ## TODO: WORK-IN-PROGRESS

    def test_is_prime(self):
        """Ensure is_prime works as expected"""
        debug.trace(4, "test_is_prime()")
        ## TODO: WORK-IN-PROGRESS

    def test_fibonacci(self):
        """Ensure fibonacci works as expected"""
        debug.trace(4, "test_fibonacci()")
        ## TODO: WORK-IN-PROGRESS

    def test_sort_weighted_hash(self):
        """Ensure sort_weighted_hash works as expected"""
        debug.trace(4, "test_sort_weighted_hash()")
        ## TODO: WORK-IN-PROGRESS

    def test_unzip(self):
        """Ensure unzip works as expected"""
        debug.trace(4, "test_unzip()")
        ## TODO: WORK-IN-PROGRESS

    def test_get_current_frame(self):
        """Ensure get_current_frame works as expected"""
        debug.trace(4, "test_get_current_frame()")
        ## TODO: WORK-IN-PROGRESS

    def test_eval_expression(self):
        """Ensure eval_expression works as expected"""
        debug.trace(4, "test_eval_expression()")
        ## TODO: WORK-IN-PROGRESS

    def test_trace_named_object(self):
        """Ensure trace_named_object works as expected"""
        debug.trace(4, "test_trace_named_object()")
        ## TODO: WORK-IN-PROGRESS

    def test_trace_named_objects(self):
        """Ensure trace_named_objects works as expected"""
        debug.trace(4, "test_trace_named_objects()")
        ## TODO: WORK-IN-PROGRESS

    def test_exactly1(self):
        """Ensure exactly1 works as expected"""
        debug.trace(4, "test_exactly1()")
        ## TODO: WORK-IN-PROGRESS

    def test_string_diff(self):
        """Ensure string_diff works as expected"""
        debug.trace(4, "test_string_diff()")
        ## TODO: WORK-IN-PROGRESS

    def test_elide_string_values(self):
        """Ensure elide_string_values works as expected"""
        debug.trace(4, "test_elide_string_values()")
        ## TODO: WORK-IN-PROGRESS


if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
