#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Test(s) for tpo_common.py
#
# Notes:
# - This can be run as follows:
#   $ PYTHONPATH="." python tests/test_tpo_common.py
# TODO:
# - Address commonly used debugging functions (e.g., debug_print) by redirecting output (via remapping sys.stderr to a file) and then checking file contents.
# - add tests for normalize_unicode, ensure_unicode and other problematic functions
#

"""Tests for tpo_common module"""

# Standard packages
import os
import unittest

# Installed packages
import pytest

# Local packages
from mezcla import debug

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
#    TestIt.script_module   string name
import mezcla.tpo_common as THE_MODULE

FUBAR = 101	# sample global for test_format
FOOBAR = 12     # likewise
JOSE = "José"   # UTF-8 encoded string

class TestIt(unittest.TestCase):
    """Class for testcase definition"""

    def test_set_debug_level(self):
        """Ensure set_debug_level works as expected"""
        debug.trace(4, "test_set_debug_level()")
        ## TODO: WORK-IN=PROGRESS

    def test_debugging_level(self):
        """Ensure debugging_level works as expected"""
        debug.trace(4, "test_debugging_level()")
        ## TODO: WORK-IN=PROGRESS

    def test_debug_trace_without_newline(self):
        """Ensure debug_trace_without_newline works as expected"""
        debug.trace(4, "test_debug_trace_without_newline()")
        ## TODO: WORK-IN=PROGRESS

    def test_debug_trace(self):
        """Ensure debug_trace works as expected"""
        debug.trace(4, "test_debug_trace()")
        ## TODO: WORK-IN=PROGRESS

    def test_debug_print(self):
        """Ensure debug_print works as expected"""
        debug.trace(4, "test_debug_print()")
        ## TODO: WORK-IN=PROGRESS

    def test_debug_format(self):
        """Ensure debug_format works as expected"""
        debug.trace(4, "test_debug_format()")
        ## TODO: WORK-IN=PROGRESS

    def test_debug_timestamp(self):
        """Ensure debug_timestamp works as expected"""
        debug.trace(4, "test_debug_timestamp()")
        ## TODO: WORK-IN=PROGRESS

    def test_debug_raise(self):
        """Ensure debug_raise works as expected"""
        debug.trace(4, "test_debug_raise()")
        ## TODO: WORK-IN=PROGRESS

    def test_trace_array(self):
        """Ensure trace_array works as expected"""
        debug.trace(4, "test_trace_array()")
        ## TODO: WORK-IN=PROGRESS

    def test_trace_object(self):
        """Ensure trace_object works as expected"""
        debug.trace(4, "test_trace_object()")
        ## TODO: WORK-IN=PROGRESS

    def test_trace_value(self):
        """Ensure trace_value works as expected"""
        debug.trace(4, "test_trace_value()")
        ## TODO: WORK-IN=PROGRESS

    def test_trace_current_context(self):
        """Ensure trace_current_context works as expected"""
        debug.trace(4, "test_trace_current_context()")
        ## TODO: WORK-IN=PROGRESS

    def test_during_debugging(self):
        """Ensure during_debugging works as expected"""
        debug.trace(4, "test_during_debugging()")
        ## TODO: WORK-IN=PROGRESS

    def test_debugging(self):
        """Ensure debugging works as expected"""
        debug.trace(4, "test_debugging()")
        ## TODO: WORK-IN=PROGRESS

    def test_detailed_debugging(self):
        """Ensure detailed_debugging works as expected"""
        debug.trace(4, "test_detailed_debugging()")
        ## TODO: WORK-IN=PROGRESS

    def test_verbose_debugging(self):
        """Ensure verbose_debugging works as expected"""
        debug.trace(4, "test_verbose_debugging()")
        ## TODO: WORK-IN=PROGRESS

    def test_to_string(self):
        """Ensure to_string works as expected"""
        debug.trace(4, "test_to_string()")
        ## TODO: WORK-IN=PROGRESS

    def test_normalize_unicode(self):
        """Ensure normalize_unicode works as expected"""
        debug.trace(4, "test_normalize_unicode()")
        ## TODO: WORK-IN=PROGRESS

    def test__normalize_unicode(self):
        """Ensure _normalize_unicode works as expected"""
        debug.trace(4, "test__normalize_unicode()")
        ## TODO: WORK-IN=PROGRESS

    def test_ensure_unicode(self):
        """Ensure ensure_unicode works as expected"""
        debug.trace(4, "test_ensure_unicode()")
        ## TODO: WORK-IN=PROGRESS

    def test_print_stderr(self):
        """Ensure print_stderr works as expected"""
        debug.trace(4, "test_print_stderr()")
        ## TODO: WORK-IN=PROGRESS

    def test_redirect_stderr(self):
        """Ensure redirect_stderr works as expected"""
        debug.trace(4, "test_redirect_stderr()")
        ## TODO: WORK-IN=PROGRESS

    def test_restore_stderr(self):
        """Ensure restore_stderr works as expected"""
        debug.trace(4, "test_restore_stderr()")
        ## TODO: WORK-IN=PROGRESS

    def test_exit(self):
        """Ensure exit works as expected"""
        debug.trace(4, "test_exit()")
        ## TODO: WORK-IN=PROGRESS

    def test_setenv(self):
        """Ensure setenv works as expected"""
        debug.trace(4, "test_setenv()")
        ## TODO: WORK-IN=PROGRESS

    def test_chomp(self):
        """Ensure chomp works as expected"""
        debug.trace(4, "test_chomp()")
        ## TODO: WORK-IN=PROGRESS

    def test_getenv(self):
        """Ensure getenv works as expected"""
        debug.trace(4, "test_getenv()")
        ## TODO: WORK-IN=PROGRESS

    def test_register_env_option(self):
        """Ensure register_env_option works as expected"""
        debug.trace(4, "test_register_env_option()")
        ## TODO: WORK-IN=PROGRESS

    def test_formatted_environment_option_descriptions(self):
        """Ensure formatted_environment_option_descriptions works as expected"""
        debug.trace(4, "test_formatted_environment_option_descriptions()")
        ## TODO: WORK-IN=PROGRESS

    def test_get_registered_env_options(self):
        """Ensure get_registered_env_options works as expected"""
        debug.trace(4, "test_get_registered_env_options()")
        ## TODO: WORK-IN=PROGRESS

    def test_getenv_value(self):
        """Ensure getenv_value works as expected"""
        debug.trace(4, "test_getenv_value()")
        ## TODO: WORK-IN=PROGRESS

    def test_getenv_text(self):
        """Ensure getenv_text works as expected"""
        debug.trace(4, "test_getenv_text()")
        ## TODO: WORK-IN=PROGRESS

    def test_getenv_boolean(self):
        """Ensure getenv_boolean works as expected"""
        debug.trace(4, "test_getenv_boolean()")
        ## TODO: WORK-IN=PROGRESS

    def test_getenv_number(self):
        """Ensure getenv_number works as expected"""
        debug.trace(4, "test_getenv_number()")
        ## TODO: WORK-IN=PROGRESS

    def test_getenv_integer(self):
        """Ensure getenv_integer works as expected"""
        debug.trace(4, "test_getenv_integer()")
        ## TODO: WORK-IN=PROGRESS

    def test_getenv_real(self):
        """Ensure getenv_real works as expected"""
        debug.trace(4, "test_getenv_real()")
        ## TODO: WORK-IN=PROGRESS

    def test_getenv_int(self):
        """Ensure getenv_int works as expected"""
        debug.trace(4, "test_getenv_int()")
        ## TODO: WORK-IN=PROGRESS

    def test_getenv_float(self):
        """Ensure getenv_float works as expected"""
        debug.trace(4, "test_getenv_float()")
        ## TODO: WORK-IN=PROGRESS

    def test_getenv_bool(self):
        """Ensure getenv_bool works as expected"""
        debug.trace(4, "test_getenv_bool()")
        ## TODO: WORK-IN=PROGRESS

    def test_get_current_function_name(self):
        """Test(s) for get_current_function_name()"""
        assert THE_MODULE.get_current_function_name() == "test_get_current_function_name"
        return

    def test_get_property_value(self):
        """Ensure get_property_value works as expected"""
        debug.trace(4, "test_get_property_value()")
        ## TODO: WORK-IN=PROGRESS

    def test_simple_format(self):
        """Ensure simple_format works as expected"""
        debug.trace(4, "test_simple_format()")
        ## TODO: WORK-IN=PROGRESS

    def test_format(self):
        """Ensure format resolves from local and global namespace, and that local takes precedence"""
        fubar = 202
        assert THE_MODULE.format("{F} vs. {f}", F=FUBAR, f=fubar) == ("%s vs. %s" % (FUBAR, fubar))
        # pylint: disable=redefined-outer-name
        FOOBAR = 21
        assert THE_MODULE.format("{FOO}", FOO=FOOBAR) == str(FOOBAR)
        # TODO: assert "Hey Jos\xc3\xa9" == THE_MODULE.format("Hey {j}", j=JOSE)
        return

    def test_init_logging(self):
        """Ensure init_logging works as expected"""
        debug.trace(4, "test_init_logging()")
        ## TODO: WORK-IN=PROGRESS

    def test_load_object(self):
        """Ensure load_object works as expected"""
        debug.trace(4, "test_load_object()")
        ## TODO: WORK-IN=PROGRESS

    def test_store_object(self):
        """Ensure store_object works as expected"""
        debug.trace(4, "test_store_object()")
        ## TODO: WORK-IN=PROGRESS

    def test_dump_stored_object(self):
        """Ensure dump_stored_object works as expected"""
        debug.trace(4, "test_dump_stored_object()")
        ## TODO: WORK-IN=PROGRESS

    def test_create_lookup_table(self):
        """Ensure create_lookup_table works as expected"""
        debug.trace(4, "test_create_lookup_table()")
        ## TODO: WORK-IN=PROGRESS

    def test_lookup_key(self):
        """Ensure lookup_key works as expected"""
        debug.trace(4, "test_lookup_key()")
        ## TODO: WORK-IN=PROGRESS

    def test_create_boolean_lookup_table(self):
        """Ensure create_boolean_lookup_table works as expected"""
        debug.trace(4, "test_create_boolean_lookup_table()")
        ## TODO: WORK-IN=PROGRESS

    def test_normalize_frequencies(self):
        """Ensure normalize_frequencies works as expected"""
        debug.trace(4, "test_normalize_frequencies()")
        ## TODO: WORK-IN=PROGRESS

    def test_sort_frequencies(self):
        """Ensure sort_frequencies works as expected"""
        debug.trace(4, "test_sort_frequencies()")
        ## TODO: WORK-IN=PROGRESS

    def test_sort_weighted_hash(self):
        """Ensure sort_weighted_hash works as expected"""
        debug.trace(4, "test_sort_weighted_hash()")
        ## TODO: WORK-IN=PROGRESS

    def test_format_freq_hash(self):
        """Ensure format_freq_hash works as expected"""
        debug.trace(4, "test_format_freq_hash()")
        ## TODO: WORK-IN=PROGRESS

    def test_union(self):
        """Ensure union works as expected"""
        debug.trace(4, "test_union()")
        ## TODO: WORK-IN=PROGRESS

    def test_intersection(self):
        """Ensure intersection works as expected"""
        debug.trace(4, "test_intersection()")
        ## TODO: WORK-IN=PROGRESS

    def test_is_subset(self):
        """Ensure is_subset works as expected"""
        debug.trace(4, "test_is_subset()")
        ## TODO: WORK-IN=PROGRESS

    def test_difference(self):
        """Ensure difference works as expected"""
        debug.trace(4, "test_difference()")
        ## TODO: WORK-IN=PROGRESS

    def test_remove_all(self):
        """Ensure remove_all works as expected"""
        debug.trace(4, "test_remove_all()")
        ## TODO: WORK-IN=PROGRESS

    def test_equivalent(self):
        """Ensure equivalent works as expected"""
        debug.trace(4, "test_equivalent()")
        ## TODO: WORK-IN=PROGRESS

    def test_append_new(self):
        """Ensure append_new works as expected"""
        debug.trace(4, "test_append_new()")
        ## TODO: WORK-IN=PROGRESS

    def test_extract_list(self):
        """Ensure extract_list works as expected"""
        debug.trace(4, "test_extract_list()")
        ## TODO: WORK-IN=PROGRESS

    def test_is_subsumed(self):
        """Ensure is_subsumed works as expected"""
        debug.trace(4, "test_is_subsumed()")
        ## TODO: WORK-IN=PROGRESS

    def test_round_num(self):
        """Ensure round_num works as expected"""
        debug.trace(4, "test_round_num()")
        ## TODO: WORK-IN=PROGRESS

    def test_round_nums(self):
        """Ensure round_nums works as expected"""
        debug.trace(4, "test_round_nums()")
        ## TODO: WORK-IN=PROGRESS

    def test_round(self):
        """Ensure round works as expected"""
        debug.trace(4, "test_round()")
        ## TODO: WORK-IN=PROGRESS

    def test_normalize(self):
        """Ensure normalize works as expected"""
        debug.trace(4, "test_normalize()")
        ## TODO: WORK-IN=PROGRESS

    def test_is_numeric(self):
        """Ensure is_numeric works as expected"""
        debug.trace(4, "test_is_numeric()")
        ## TODO: WORK-IN=PROGRESS

    def test_safe_int(self):
        """Ensure safe_int works as expected"""
        debug.trace(4, "test_safe_int()")
        ## TODO: WORK-IN=PROGRESS

    def test_safe_float(self):
        """Ensure safe_float works as expected"""
        debug.trace(4, "test_safe_float()")
        ## TODO: WORK-IN=PROGRESS

    def test_reference_variables(self):
        """Ensure reference_variables works as expected"""
        debug.trace(4, "test_reference_variables()")
        ## TODO: WORK-IN=PROGRESS

    def test_memodict(self):
        """Ensure memodict works as expected"""
        debug.trace(4, "test_memodict()")
        ## TODO: WORK-IN=PROGRESS

    def test_dummy_main(self):
        """Ensure dummy_main works as expected"""
        debug.trace(4, "test_dummy_main()")
        ## TODO: WORK-IN=PROGRESS

    ## TODO: test main

    def test_getenv_functions(self):
        """Ensure that various getenv_xyz functions work as expected"""
        assert THE_MODULE.getenv_integer("REALLY FUBAR", 123) == 123
        assert THE_MODULE.getenv_number("REALLY FUBAR", 123) == 123.0
        assert not isinstance(THE_MODULE.getenv_boolean("REALLY FUBAR?", None), bool)
        assert isinstance(THE_MODULE.getenv_boolean("REALLY FUBAR?", False), bool)
        assert not isinstance(THE_MODULE.getenv_text("REALLY FUBAR?", False), bool)
        os.environ["FUBAR"] = "1"
        assert THE_MODULE.getenv_text("FUBAR") == "1"
        return

    def test_unicode_functions(self):
        """Esnure that normalize_unicode, encode_unicode, etc. work as expected"""
        UTF8_BOM = "\xEF\xBB\xBF"
        assert THE_MODULE.ensure_unicode("ASCII") == u"ASCII"
        assert THE_MODULE.normalize_unicode("ASCII") == "ASCII"
        ## TODO: assert THE_MODULE.ensure_unicode(UTF8_BOM) == u'\ufeff'
        assert THE_MODULE.normalize_unicode(UTF8_BOM) == UTF8_BOM
        assert u"Jos\xe9" == THE_MODULE.ensure_unicode(JOSE)
        ## TODO: assert "Jos\xc3\xa9", THE_MODULE.normalize_unicode(JOSE)
        return

    def test_difference(self):
        """Ensures set difference works as expected"""
        assert THE_MODULE.difference([1, 2, 3], [2]) == [1, 3]
        assert THE_MODULE.difference([1, 1, 2, 2], [1]) == [2]
        return

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
