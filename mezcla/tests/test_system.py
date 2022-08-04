#! /usr/bin/env python
#
# Test(s) for ../system.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH="$(realpath .)/..):$PYTHONPATH" python tests/test_system.py
#

"""Tests for system module"""

# Standard packages

# Installed packages
import pytest

# Local packages
from mezcla import debug

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
#    TestIt.script_module   string name
import mezcla.system as THE_MODULE

class TestSystem:
    """Class for test case definitions"""

    def test_maxint(self):
        """Ensure maxint works as expected"""
        debug.trace(4, "test_maxint()")
        ## TODO: WORK-IN=PROGRESS

    def test_register_env_option(self):
        """Ensure register_env_option works as expected"""
        debug.trace(4, "test_register_env_option()")
        ## TODO: WORK-IN=PROGRESS

    def test_get_registered_env_options(self):
        """Ensure get_registered_env_options works as expected"""
        debug.trace(4, "test_get_registered_env_options()")
        ## TODO: WORK-IN=PROGRESS

    def test_get_environment_option_descriptions(self):
        """Ensure get_environment_option_descriptions works as expected"""
        debug.trace(4, "test_get_environment_option_descriptions()")
        ## TODO: WORK-IN=PROGRESS

    def test_formatted_environment_option_descriptions(self):
        """Ensure formatted_environment_option_descriptions works as expected"""
        debug.trace(4, "test_formatted_environment_option_descriptions()")
        ## TODO: WORK-IN=PROGRESS

    def test_getenv(self):
        """Ensure getenv works as expected"""
        debug.trace(4, "test_getenv()")
        ## TODO: WORK-IN=PROGRESS

    def test_getenv_text(self):
        """Ensure getenv_text works as expected"""
        debug.trace(4, "test_getenv_text()")
        ## TODO: WORK-IN=PROGRESS

    def test_getenv_value(self):
        """Ensure getenv_value works as expected"""
        debug.trace(4, "test_getenv_value()")
        ## TODO: WORK-IN=PROGRESS

    def test_getenv_bool(self):
        """Ensure getenv_bool works as expected"""
        debug.trace(4, "test_getenv_bool()")
        ## TODO: WORK-IN=PROGRESS

    def test_getenv_number(self):
        """Ensure getenv_number works as expected"""
        debug.trace(4, "test_getenv_number()")
        ## TODO: WORK-IN=PROGRESS

    def test_getenv_int(self):
        """Ensure getenv_int works as expected"""
        debug.trace(4, "test_getenv_int()")
        ## TODO: WORK-IN=PROGRESS

    def test_get_exception(self):
        """Ensure get_exception works as expected"""
        debug.trace(4, "test_get_exception()")
        ## TODO: WORK-IN=PROGRESS

    def test_print_error(self):
        """Ensure print_error works as expected"""
        debug.trace(4, "test_print_error()")
        ## TODO: WORK-IN=PROGRESS

    def test_print_stderr(self):
        """Ensure print_stderr works as expected"""
        debug.trace(4, "test_print_stderr()")
        ## TODO: WORK-IN=PROGRESS

    def test_print_exception_info(self):
        """Ensure print_exception_info works as expected"""
        debug.trace(4, "test_print_exception_info()")
        ## TODO: WORK-IN=PROGRESS

    def test_exit(self):
        """Ensure exit works as expected"""
        debug.trace(4, "test_exit()")
        ## TODO: WORK-IN=PROGRESS

    def test_setenv(self):
        """Ensure setenv works as expected"""
        debug.trace(4, "test_setenv()")
        ## TODO: WORK-IN=PROGRESS

    def test_print_full_stack(self):
        """Ensure print_full_stack works as expected"""
        debug.trace(4, "test_print_full_stack()")
        ## TODO: WORK-IN=PROGRESS

    def test_trace_stack(self):
        """Ensure trace_stack works as expected"""
        debug.trace(4, "test_trace_stack()")
        ## TODO: WORK-IN=PROGRESS

    def test_get_current_function_name(self):
        """Ensure get_current_function_name works as expected"""
        debug.trace(4, "test_get_current_function_name()")
        ## TODO: WORK-IN=PROGRESS

    def test_open_file(self):
        """Ensure open_file works as expected"""
        debug.trace(4, "test_open_file()")
        ## TODO: WORK-IN=PROGRESS

    def test_save_object(self):
        """Ensure save_object works as expected"""
        debug.trace(4, "test_save_object()")
        ## TODO: WORK-IN=PROGRESS

    def test_load_object(self):
        """Ensure load_object works as expected"""
        debug.trace(4, "test_load_object()")
        ## TODO: WORK-IN=PROGRESS

    def test_quote_url_text(self):
        """Ensure quote_url_text works as expected"""
        debug.trace(4, "test_quote_url_text()")
        ## TODO: WORK-IN=PROGRESS

    def test_unquote_url_text(self):
        """Ensure unquote_url_text works as expected"""
        debug.trace(4, "test_unquote_url_text()")
        ## TODO: WORK-IN=PROGRESS

    def test_escape_html_text(self):
        """Ensure escape_html_text works as expected"""
        debug.trace(4, "test_escape_html_text()")
        ## TODO: WORK-IN=PROGRESS

    def test_unescape_html_text(self):
        """Ensure unescape_html_text works as expected"""
        debug.trace(4, "test_unescape_html_text()")
        ## TODO: WORK-IN=PROGRESS

    def test_stdin_reader(self):
        """Ensure stdin_reader works as expected"""
        debug.trace(4, "test_stdin_reader()")
        ## TODO: WORK-IN=PROGRESS

    def test_stdin_reader(self):
        """Ensure stdin_reader class works as expected"""
        debug.trace(4, "test_stdin_reader()")
        ## TODO: WORK-IN=PROGRESS

    def test_read_all_stdin(self):
        """Ensure read_all_stdin works as expected"""
        debug.trace(4, "test_read_all_stdin()")
        ## TODO: WORK-IN=PROGRESS

    def test_read_entire_file(self):
        """Ensure read_entire_file works as expected"""
        debug.trace(4, "test_read_entire_file()")
        ## TODO: WORK-IN=PROGRESS

    def test_read_lines(self):
        """Ensure read_lines works as expected"""
        debug.trace(4, "test_read_lines()")
        ## TODO: WORK-IN=PROGRESS

    def test_read_binary_file(self):
        """Ensure read_binary_file works as expected"""
        debug.trace(4, "test_read_binary_file()")
        ## TODO: WORK-IN=PROGRESS

    def test_read_directory(self):
        """Ensure read_directory works as expected"""
        debug.trace(4, "test_read_directory()")
        ## TODO: WORK-IN=PROGRESS

    def test_get_directory_filenames(self):
        """Ensure get_directory_filenames works as expected"""
        debug.trace(4, "test_get_directory_filenames()")
        ## TODO: WORK-IN=PROGRESS

    def test_read_lookup_table(self):
        """Ensure read_lookup_table works as expected"""
        debug.trace(4, "test_read_lookup_table()")
        ## TODO: WORK-IN=PROGRESS

    def test_create_boolean_lookup_table(self):
        """Ensure create_boolean_lookup_table works as expected"""
        debug.trace(4, "test_create_boolean_lookup_table()")
        ## TODO: WORK-IN=PROGRESS

    def test_lookup_entry(self):
        """Ensure lookup_entry works as expected"""
        debug.trace(4, "test_lookup_entry()")
        ## TODO: WORK-IN=PROGRESS

    def test_write_file(self):
        """Ensure write_file works as expected"""
        debug.trace(4, "test_write_file()")
        ## TODO: WORK-IN=PROGRESS

    def test_write_binary_file(self):
        """Ensure write_binary_file works as expected"""
        debug.trace(4, "test_write_binary_file()")
        ## TODO: WORK-IN=PROGRESS

    def test_write_lines(self):
        """Ensure write_lines works as expected"""
        debug.trace(4, "test_write_lines()")
        ## TODO: WORK-IN=PROGRESS

    def test_write_temp_file(self):
        """Ensure write_temp_file works as expected"""
        debug.trace(4, "test_write_temp_file()")
        ## TODO: WORK-IN=PROGRESS

    def test_get_file_modification_time(self):
        """Ensure get_file_modification_time works as expected"""
        debug.trace(4, "test_get_file_modification_time()")
        ## TODO: WORK-IN=PROGRESS

    def test_remove_extension(self):
        """Ensure remove_extension works as expected"""
        debug.trace(4, "test_remove_extension()")
        ## TODO: WORK-IN=PROGRESS

    def test_file_exists(self):
        """Ensure file_exists works as expected"""
        debug.trace(4, "test_file_exists()")
        ## TODO: WORK-IN=PROGRESS

    def test_get_file_size(self):
        """Ensure get_file_size works as expected"""
        debug.trace(4, "test_get_file_size()")
        ## TODO: WORK-IN=PROGRESS

    def test_form_path(self):
        """Ensure form_path works as expected"""
        debug.trace(4, "test_form_path()")
        ## TODO: WORK-IN=PROGRESS

    def test_is_directory(self):
        """Ensure is_directory works as expected"""
        debug.trace(4, "test_is_directory()")
        ## TODO: WORK-IN=PROGRESS

    def test_is_regular_file(self):
        """Ensure is_regular_file works as expected"""
        debug.trace(4, "test_is_regular_file()")
        ## TODO: WORK-IN=PROGRESS

    def test_create_directory(self):
        """Ensure create_directory works as expected"""
        debug.trace(4, "test_create_directory()")
        ## TODO: WORK-IN=PROGRESS

    def test_get_current_directory(self):
        """Ensure get_current_directory works as expected"""
        debug.trace(4, "test_get_current_directory()")
        ## TODO: WORK-IN=PROGRESS

    def test_set_current_directory(self):
        """Ensure set_current_directory works as expected"""
        debug.trace(4, "test_set_current_directory()")
        ## TODO: WORK-IN=PROGRESS

    def test_to_utf8(self):
        """Ensure to_utf8 works as expected"""
        debug.trace(4, "test_to_utf8()")
        ## TODO: WORK-IN=PROGRESS

    def test_to_str(self):
        """Ensure to_str works as expected"""
        debug.trace(4, "test_to_str()")
        ## TODO: WORK-IN=PROGRESS

    def test_from_utf8(self):
        """Ensure from_utf8 works as expected"""
        debug.trace(4, "test_from_utf8()")
        ## TODO: WORK-IN=PROGRESS

    def test_to_unicode(self):
        """Ensure to_unicode works as expected"""
        debug.trace(4, "test_to_unicode()")
        ## TODO: WORK-IN=PROGRESS

    def test_from_unicode(self):
        """Ensure from_unicode works as expected"""
        debug.trace(4, "test_from_unicode()")
        ## TODO: WORK-IN=PROGRESS

    def test_to_string(self):
        """Ensure to_string works as expected"""
        debug.trace(4, "test_to_string()")
        ## TODO: WORK-IN=PROGRESS

    def test_chomp(self):
        """Ensure chomp works as expected"""
        debug.trace(4, "test_chomp()")
        ## TODO: WORK-IN=PROGRESS

    def test_normalize_dir(self):
        """Ensure normalize_dir works as expected"""
        debug.trace(4, "test_normalize_dir()")
        ## TODO: WORK-IN=PROGRESS

    def test_non_empty_file(self):
        """Ensure non_empty_file works as expected"""
        debug.trace(4, "test_non_empty_file()")
        ## TODO: WORK-IN=PROGRESS

    def test_absolute_path(self):
        """Ensure absolute_path works as expected"""
        debug.trace(4, "test_absolute_path()")
        ## TODO: WORK-IN=PROGRESS

    def test_absolute_path(self):
        """Ensure absolute_path works as expected"""
        debug.trace(4, "test_absolute_path()")
        ## TODO: WORK-IN=PROGRESS

    def test_real_path(self):
        """Ensure real_path works as expected"""
        debug.trace(4, "test_real_path()")
        ## TODO: WORK-IN=PROGRESS

    def test_get_module_version(self):
        """Ensure get_module_version works as expected"""
        debug.trace(4, "test_get_module_version()")
        ## TODO: WORK-IN=PROGRESS

    def test_intersection(self):
        """Ensure intersection works as expected"""
        debug.trace(4, "test_intersection()")
        ## TODO: WORK-IN=PROGRESS

    def test_union(self):
        """Ensure union works as expected"""
        debug.trace(4, "test_union()")
        ## TODO: WORK-IN=PROGRESS

    def test_difference(self):
        """Ensure difference works as expected"""
        debug.trace(4, "test_difference()")
        ## TODO: WORK-IN=PROGRESS

    def test_append_new(self):
        """Ensure append_new works as expected"""
        debug.trace(4, "test_append_new()")
        ## TODO: WORK-IN=PROGRESS

    def test_just_one_true(self):
        """Ensure just_one_true works as expected"""
        debug.trace(4, "test_just_one_true()")
        ## TODO: WORK-IN=PROGRESS

    def test_just_one_non_null(self):
        """Ensure just_one_non_null works as expected"""
        debug.trace(4, "test_just_one_non_null()")
        ## TODO: WORK-IN=PROGRESS

    def test_unique_items(self):
        """Ensure unique_items works as expected"""
        debug.trace(4, "test_unique_items()")
        ## TODO: WORK-IN=PROGRESS

    def test_to_float(self):
        """Ensure to_float works as expected"""
        debug.trace(4, "test_to_float()")
        ## TODO: WORK-IN=PROGRESS

    def test_to_int(self):
        """Ensure to_int works as expected"""
        debug.trace(4, "test_to_int()")
        ## TODO: WORK-IN=PROGRESS

    def test_to_bool(self):
        """Ensure to_bool works as expected"""
        debug.trace(4, "test_to_bool()")
        ## TODO: WORK-IN=PROGRESS

    def test_round_num(self):
        """Ensure round_num works as expected"""
        debug.trace(4, "test_round_num()")
        ## TODO: WORK-IN=PROGRESS

    def test_round_as_str(self):
        """Ensure round_as_str works as expected"""
        debug.trace(4, "test_round_as_str()")
        ## TODO: WORK-IN=PROGRESS

    def test_sleep(self):
        """Ensure sleep works as expected"""
        debug.trace(4, "test_sleep()")
        ## TODO: WORK-IN=PROGRESS

    def test_current_time(self):
        """Ensure current_time works as expected"""
        debug.trace(4, "test_current_time()")
        ## TODO: WORK-IN=PROGRESS

    def test_time_in_secs(self):
        """Ensure time_in_secs works as expected"""
        debug.trace(4, "test_time_in_secs()")
        ## TODO: WORK-IN=PROGRESS

    def test_python_maj_min_version(self):
        """Ensure python_maj_min_version works as expected"""
        debug.trace(4, "test_python_maj_min_version()")
        ## TODO: WORK-IN=PROGRESS

    def test_get_args(self):
        """Ensure get_args works as expected"""
        debug.trace(4, "test_get_args()")
        ## TODO: WORK-IN=PROGRESS

    def test_get_args(self):
        """Ensure get_args works as expected"""
        debug.trace(4, "test_get_args()")
        ## TODO: WORK-IN=PROGRESS


if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
