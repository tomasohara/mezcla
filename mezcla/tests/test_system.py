#! /usr/bin/env python3
#
# Test(s) for ../system.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_system.py
#
# TODO3: Remove xfail's
#

"""Tests for system module"""

# Standard packages
import io
from math import pi
import time
import sys
import re
import pickle
import os

# Installed packages
import pytest

# Local packages
from mezcla.unittest_wrapper import TestWrapper, invoke_tests, get_temp_dir
from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla import debug

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
#    TestIt.script_module:              path to file
import mezcla.system as THE_MODULE
# note: 'system.function' used for functions not being tested (out of habit)
system = THE_MODULE

class TestSystem(TestWrapper):
    """Class for test case definitions"""
    script_module = None

    def test_maxint(self):
        """Ensure maxint works as expected"""
        debug.trace(4, "test_maxint()")

        assert THE_MODULE.maxint() is not None
        assert THE_MODULE.maxint() == sys.maxsize

    def test_register_env_option(self):
        """Ensure register_env_option works as expected"""
        debug.trace(4, "test_register_env_option()")

        THE_MODULE.env_options = {}
        THE_MODULE.env_defaults = {}

        THE_MODULE.register_env_option(
            var='VAR_STRING',
            description='this is a string variable',
            default='empty'
        )

        assert THE_MODULE.env_options['VAR_STRING'], 'this is a string variable'
        assert THE_MODULE.env_defaults['VAR_STRING'], 'empty'
        assert len(THE_MODULE.env_options) == 1
        assert len(THE_MODULE.env_defaults) == 1

    def test_get_registered_env_options(self):
        """Ensure get_registered_env_options works as expected"""
        debug.trace(4, "test_get_registered_env_options()")

        set_test_env_var()

        assert isinstance(THE_MODULE.get_registered_env_options(), list)
        assert 'VAR_STRING' in THE_MODULE.get_registered_env_options()
        assert len(THE_MODULE.get_registered_env_options()) == 2

    def test_get_environment_option_descriptions(self):
        """Ensure get_environment_option_descriptions works as expected"""
        debug.trace(4, "test_get_environment_option_descriptions()")

        set_test_env_var()

        ## TODO: Test include_all option
        ## assert ('VAR_STRING', "this is a string variable") in THE_MODULE.get_environment_option_descriptions(include_all=False)

        # Test include_default option
        assert ('VAR_STRING', "this is a string variable") in THE_MODULE.get_environment_option_descriptions(include_default=False)
        assert ('VAR_STRING', "this is a string variable ('empty')") in THE_MODULE.get_environment_option_descriptions(include_default=True)

        # Test indent option
        assert ('VAR_STRING', "this is a string variable, default=('empty')") in THE_MODULE.get_environment_option_descriptions(indent=', default=')
        assert ('VAR_STRING', "this is a string variable => ('empty')") in THE_MODULE.get_environment_option_descriptions(indent=' => ')

        # Test get N enviroments vars descriptions
        assert len(THE_MODULE.get_environment_option_descriptions()) == 2

    def test_formatted_environment_option_descriptions(self):
        """Ensure formatted_environment_option_descriptions works as expected"""
        debug.trace(4, "test_formatted_environment_option_descriptions()")

        set_test_env_var()

        # Test sort
        expected = (
            'VAR_STRING\tthis is a string variable (\'empty\')\n'
            '\tANOTHER_VAR\tthis is another env. var. (\'2022\')'
        )
        assert THE_MODULE.formatted_environment_option_descriptions(sort=False) == expected
        expected = (
            'ANOTHER_VAR\tthis is another env. var. (\'2022\')\n'
            '\tVAR_STRING\tthis is a string variable (\'empty\')'
        )
        assert THE_MODULE.formatted_environment_option_descriptions(sort=True) == expected

        # Test include_all
        # NOTE: this is being tested on test_system.test_get_environment_option_descriptions()

        # Test indent
        expected = (
            'VAR_STRING + this is a string variable (\'empty\')\n'
            ' + ANOTHER_VAR + this is another env. var. (\'2022\')'
        )
        assert THE_MODULE.formatted_environment_option_descriptions(indent=' + ') == expected

    def test_getenv(self):
        """Ensure getenv works as expected"""
        debug.trace(4, "test_getenv()")
        self.monkeypatch.setenv('TEST_ENV_VAR', 'some value', prepend=False)
        assert THE_MODULE.getenv('TEST_ENV_VAR') == 'some value'
        assert THE_MODULE.getenv('INT_ENV_VAR', default_value=5) == 5

    @pytest.mark.xfail
    def test_getenv_text_etc_bookkeeping(self):
        """Check getenv_text, etc. used of env. option registration"""
        debug.trace(4, "test_getenv_bookkeeping()")
        self.patch_trace_level(4)
        THE_MODULE.getenv_bool("TEST_ENV_VAR", default=False, desc="desc1")
        THE_MODULE.getenv_bool("TEST_ENV_VAR", default=True, desc="desc2")
        stderr = self.get_stderr()
        assert "redefining env option description" in stderr
        assert "redefining env option default" in stderr

    def test_getenv_text(self):
        """Ensure getenv_text works as expected"""
        debug.trace(4, "test_getenv_text()")
        self.monkeypatch.setenv('TEST_ENV_VAR', 'some value', prepend=False)
        assert THE_MODULE.getenv_text('TEST_ENV_VAR') == 'some value'
        assert not THE_MODULE.getenv_text("REALLY FUBAR?", False)

    def test_getenv_value(self):
        """Ensure getenv_value works as expected"""
        debug.trace(4, "test_getenv_value()")
        set_test_env_var()
        self.monkeypatch.setenv('NEW_ENV_VAR', 'some value', prepend=False)
        assert THE_MODULE.getenv_value('NEW_ENV_VAR', default='empty', description='another test env var') == 'some value'
        assert THE_MODULE.env_defaults['NEW_ENV_VAR'] == 'empty'
        assert THE_MODULE.env_options['NEW_ENV_VAR'] == 'another test env var'

    def test_getenv_normalization(self):
        """Verify getenv_value/text env var normalization"""
        self.monkeypatch.setenv("MY_VAR", "my value")
        assert THE_MODULE.getenv_value("my-var") is None
        assert THE_MODULE.getenv_text("my-var") == ""
        assert THE_MODULE.getenv_value("my-var", normalize=True) == "my value"
        assert THE_MODULE.getenv_text("my-var", normalize=True) == "my value"
        
    def test_getenv_missing(self):
        """Verify getenv_xyz with mising env"""
        var = "NULL_VAR"
        self.monkeypatch.delenv(var, raising=False)
        assert THE_MODULE.getenv_value(var) is None
        assert THE_MODULE.getenv_text(var) == ""
        assert THE_MODULE.getenv_int(var) == -1
        assert THE_MODULE.getenv_int(var, default=666) == 666
        assert THE_MODULE.getenv_float(var) == -1.0
        assert THE_MODULE.getenv_float(var, default=1.5) == 1.5
        assert THE_MODULE.getenv_float(var, default=1, update=True) == 1
        assert THE_MODULE.getenv_value(var) == "1"
        
    def test_getenv_bool(self):
        """Ensure getenv_bool works as expected"""
        debug.trace(4, "test_getenv_bool()")
        # note: whitespaces is not a typo, is to test strip condition
        self.monkeypatch.setenv('TEST_BOOL', 'FALSE', prepend=False)
        assert not THE_MODULE.getenv_bool('TEST_BOOL', None)
        self.monkeypatch.setenv('TEST_BOOL', '  true   ', prepend=False)
        assert THE_MODULE.getenv_bool('TEST_BOOL', None)
        assert isinstance(THE_MODULE.getenv_bool('TEST_BOOL', None), bool)

    def test_getenv_number(self):
        """Ensure getenv_number works as expected"""
        debug.trace(4, "test_getenv_number()")
        # note: whitespaces is not a typo, is to test strip condition
        self.monkeypatch.setenv('TEST_NUMBER', ' 9.81    ', prepend=False)
        assert THE_MODULE.getenv_number('TEST_NUMBER', default=10) == 9.81
        assert THE_MODULE.getenv_number('BAD_TEST_NUMBER', default=10) == 10
        assert THE_MODULE.getenv_number('BAD VAR', default=None, allow_none=True) is None
        assert THE_MODULE.getenv_number('BAD VAR', default=None, allow_none=False) == 0.0
        ## TODO: test helper argument

    def test_getenv_int(self):
        """Ensure getenv_int works as expected"""
        debug.trace(4, "test_getenv_int()")
        self.monkeypatch.setenv('TEST_NUMBER', '9.81', prepend=False)
        assert THE_MODULE.getenv_int('TEST_NUMBER', default=20) == 9
        assert THE_MODULE.getenv_int("REALLY FUBAR", 123) == 123
        assert THE_MODULE.getenv_int('BAD VAR', default=None, allow_none=True) is None
        assert THE_MODULE.getenv_int('BAD VAR', default=None, allow_none=False) == 0

    def test_get_exception(self):
        """Ensure get_exception works as expected"""
        debug.trace(4, "test_get_exception()")
        exception = None
        try:
            raise RuntimeError("testing")
        except RuntimeError:
            exception = THE_MODULE.get_exception()
        assert str(exception[1]) == "testing"

    def test_print_error(self):
        """Ensure print_error works as expected"""
        debug.trace(4, "test_print_error()")
        THE_MODULE.print_error("this is an test error message")
        captured = self.get_stderr()
        assert "error" in captured

    def test_print_stderr(self):
        """Ensure print_stderr works as expected"""
        debug.trace(4, "test_print_stderr()")
        THE_MODULE.print_stderr("Error: F{oo}bar!", oo='OO')
        captured = self.get_stderr()
        assert "Error: FOObar!" in captured

    def test_print_exception_info(self):
        """Ensure print_exception_info works as expected"""
        debug.trace(4, "test_print_exception_info()")
        THE_MODULE.print_exception_info("Foobar")
        captured = self.get_stderr()
        assert "Foobar" in captured

    @pytest.mark.xfail
    def test_exit(self):
        """Ensure exit works as expected"""
        # Note: This modifies sys.exit so that system.exit doesn't really exit.
        debug.trace(4, "test_exit()")
        #
        EXIT = 'exit'
        def sys_exit_mock(_status=None):
            """Stub for sys.exit that just returns 'exit' text"""
            debug.trace(4, "sys_exit_mock()")
            return EXIT
        #
        self.monkeypatch.setattr(sys, "exit", sys_exit_mock)
        MESSAGE = "test_exit method"
        ## NOTE: system.exit returns None
        ## BAD: self.do_assert(THE_MODULE.exit(MESSAGE) == EXIT)
        self.do_assert(sys.exit(MESSAGE) == EXIT)
        # pylint: disable=unreachable
        THE_MODULE.exit(MESSAGE)
        # Exit is mocked, ignore code editor hidding [TODO4: hidden?]
        captured = self.get_stderr()
        debug.trace_expr(5, captured)
        self.do_assert(MESSAGE in captured)

    def test_setenv(self):
        """Ensure setenv works as expected"""
        debug.trace(4, "test_setenv()")
        THE_MODULE.setenv('NEW_TEST_ENV_VAR', 'the gravity is 10, pi is 3')
        assert THE_MODULE.getenv('NEW_TEST_ENV_VAR') == 'the gravity is 10, pi is 3'

    def test_print_full_stack(self):
        """Ensure print_full_stack works as expected"""
        debug.trace(4, "test_print_full_stack()")
        try:
            raise RuntimeError('test')
        except RuntimeError:
            THE_MODULE.print_full_stack(sys.stderr)
        captured_error = self.get_stderr()
        assert 'RuntimeError' in captured_error

    def test_trace_stack(self):
        """Ensure trace_stack works as expected"""
        debug.trace(4, "test_trace_stack()")
        try:
            raise RuntimeError('test')
        except RuntimeError:
            THE_MODULE.trace_stack(1, sys.stderr)
        captured_error = self.get_stderr()
        assert 'RuntimeError' in captured_error

    def test_get_current_function_name(self):
        """Ensure get_current_function_name works as expected"""
        debug.trace(4, "test_get_current_function_name()")
        assert THE_MODULE.get_current_function_name() == "test_get_current_function_name"

    def test_open_file(self):
        """Ensure open_file works as expected with existent files"""
        debug.trace(4, "test_open_file()")
        #test file exists and can be open
        test_filename = self.create_temp_file("open file")
        assert THE_MODULE.open_file(test_filename).read() == "open file\n"

        # assert opening a nonexistent file returns none
        assert THE_MODULE.open_file("empty") is None

    def test_save_object(self):
        """Ensure save_object works as expected"""
        debug.trace(4, "test_save_object()")
        test_dict = {
            1: 'first',
            2: 'second',
        }
        test_filename = self.get_temp_file()

        THE_MODULE.save_object(test_filename, test_dict)

        with open(test_filename, 'rb') as test_file:
            actual_object = pickle.load(test_file)
        assert actual_object == test_dict
        test_file.close()

    def test_load_object(self):
        """Ensure load_object works as expected"""
        debug.trace(4, "test_load_object()")

        # Test valid file
        test_dict = {
            1: 'first',
            2: 'second',
        }
        test_filename = self.get_temp_file()
        with open(test_filename, 'wb') as test_file :
            pickle.dump(test_dict, test_file)
            test_file.close()
        assert THE_MODULE.load_object(test_filename) == test_dict

        # Test invalid file
        THE_MODULE.load_object('bad_file_name')
        captured = self.get_stderr()
        assert "Error:" in captured

    def test_quote_url_text(self):
        """Ensure quote_url_text works as expected"""
        debug.trace(4, "test_quote_url_text()")

        ## TODO: set fixed sys.version_info.major > 2.
        ## TODO1: please explain the issue here and below

        # Test quoting
        assert THE_MODULE.quote_url_text("<2/") == "%3C2%2F"
        assert THE_MODULE.quote_url_text("Joe's hat") == "Joe%27s+hat"
        assert THE_MODULE.quote_url_text("Joe%27s+hat") == "Joe%2527s%2Bhat"

        # Test unquoting
        assert THE_MODULE.quote_url_text("%3C2%2f", unquote=True) == "<2/"
        assert THE_MODULE.quote_url_text("Joe%27s+hat", unquote=True) == "Joe's hat"
        assert THE_MODULE.quote_url_text("Joe%2527s%2Bhat", unquote=True) == "Joe%27s+hat"

        ## TEMP: Test workaround for handling null text
        ## NOTE: -1 traicng blocks assertions
        self.patch_trace_level(-1)
        assert THE_MODULE.quote_url_text(None) == ""
        assert THE_MODULE.quote_url_text(None, unquote=True) == ""

        ## TODO: Test sys.version_info.major < 2

    def test_unquote_url_text(self):
        """Ensure unquote_url_text works as expected"""
        debug.trace(4, "test_unquote_url_text()")
        assert THE_MODULE.unquote_url_text("%3C2%2f") == "<2/"
        assert THE_MODULE.unquote_url_text("Joe%27s+hat") == "Joe's hat"
        assert THE_MODULE.unquote_url_text("Joe%2527s%2Bhat") == "Joe%27s+hat"

    def test_escape_html_text(self):
        """Ensure escape_html_text works as expected"""
        debug.trace(4, "test_escape_html_text()")

        ## TODO: set fixed sys.version_info.major > 2.

        assert THE_MODULE.escape_html_text("<2/") == "&lt;2/"
        assert THE_MODULE.escape_html_text("Joe's hat") == "Joe&#x27;s hat"

        ## TODO: test with sys.version_info.major < 2

    def test_unescape_html_text(self):
        """Ensure unescape_html_text works as expected"""
        debug.trace(4, "test_unescape_html_text()")

        ## TODO: set fixed sys.version_info.major > 2.

        assert THE_MODULE.unescape_html_text("&lt;2/") == "<2/"
        assert THE_MODULE.unescape_html_text("Joe&#x27;s hat") == "Joe's hat"

        ## TODO: test with sys.version_info.major < 2

    def test_stdin_reader(self):
        """Ensure stdin_reader works as expected"""
        debug.trace(4, "test_stdin_reader()")
        self.monkeypatch.setattr('sys.stdin', io.StringIO('my input\nsome line\n'))
        test_iter = THE_MODULE.stdin_reader()
        assert next(test_iter) == 'my\tinput'
        assert next(test_iter) == 'some\tline'
        assert next(test_iter) == ''

    def test_read_all_stdin(self):
        """Ensure read_all_stdin works as expected"""
        debug.trace(4, "test_read_all_stdin()")
        self.monkeypatch.setattr('sys.stdin', io.StringIO('my input\nsome line'))
        assert THE_MODULE.read_all_stdin() == 'my input\nsome line'

    def test_read_entire_file(self):
        """Ensure read_entire_file works as expected"""
        debug.trace(4, "test_read_entire_file()")

        # Test valid file
        temp_file = self.get_temp_file()
        system.write_file(temp_file, 'file\nwith\nmultiple\nlines\n')
        assert THE_MODULE.read_entire_file(temp_file) == 'file\nwith\nmultiple\nlines\n'

        # Test invalid file
        debug.set_level(3)
        THE_MODULE.read_entire_file('invalid_file', errors='ignore')
        captured = self.get_stderr()
        assert "Unable to read file" not in captured
        THE_MODULE.read_entire_file('invalid_file')
        captured = self.get_stderr()
        assert "Unable to read file" in captured

    def test_read_lines(self):
        """Ensure read_lines works as expected"""
        debug.trace(4, "test_read_lines()")
        temp_file = self.get_temp_file()
        THE_MODULE.write_file(temp_file, 'file\nwith\nmultiple\nlines\n')
        assert THE_MODULE.read_lines(temp_file) == ['file', 'with', 'multiple', 'lines']

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_read_binary_file(self):
        """Ensure read_binary_file works as expected"""
        debug.trace(4, "test_read_binary_file()")
        test_filename = self.create_temp_file("open binary")
        assert THE_MODULE.read_binary_file(test_filename) == bytes("open binary"+os.linesep, "UTF-8")

    def test_read_directory(self):
        """Ensure read_directory works as expected"""
        debug.trace(4, "test_read_directory()")
        split = self.create_temp_file('').split(THE_MODULE.path_separator())
        path = THE_MODULE.path_separator().join(split[:-1])
        filename = split[-1]
        assert filename in THE_MODULE.read_directory(path)

    def test_get_directory_filenames(self):
        """Ensure get_directory_filenames works as expected"""
        debug.trace(4, "test_get_directory_filenames()")
        path = gh.dir_path(__file__)
        assert gh.form_path(path, "README.md") in THE_MODULE.get_directory_filenames(path)
        assert gh.form_path(path, "resources") not in THE_MODULE.get_directory_filenames(path, just_regular_files=True)

    @pytest.mark.xfail
    def test_read_lookup_table(self):
        """Ensure read_lookup_table works as expected"""
        debug.trace(4, "test_read_lookup_table()")

        content = (
            'COUNTRY -> CAPITAL\n'
            'United States -> Washington D. C.\n'
            'France -> Paris\n'
            'Canada -> Ottawa\n'
        )
        expected_uppercase = {
            'COUNTRY': 'CAPITAL',
            'United States': 'Washington D. C.',
            'France':'Paris',
            'Canada': 'Ottawa'
        }
        expected_lowercase = {
            'country': 'capital',
            'united states': 'washington d. c.',
            'france':'paris',
            'canada': 'ottawa'
        }

        # Test normal usage parameters
        temp_file = self.get_temp_file()
        system.write_file(temp_file, content)
        assert THE_MODULE.read_lookup_table(temp_file, skip_header=False, delim=' -> ', retain_case=False) == expected_lowercase
        assert THE_MODULE.read_lookup_table(temp_file, skip_header=False, delim=' -> ', retain_case=True) == expected_uppercase
        assert THE_MODULE.read_lookup_table(temp_file, skip_header=True, retain_case=False)['country'] == ''

        # Tests default delim
        content_with_tabs = content.replace(' -> ', '\t')
        temp_file = self.get_temp_file()
        system.write_file(temp_file, content_with_tabs)
        assert THE_MODULE.read_lookup_table(temp_file) == expected_lowercase

        # Test without delim
        without_delim_content = (
            'line without delim\n'
            'France -> Paris\n'
        )
        temp_file = self.get_temp_file()
        system.write_file(temp_file, without_delim_content)
        THE_MODULE.read_lookup_table(temp_file)
        captured = self.get_stderr()
        assert 'Warning: Ignoring line' in captured

        # Test invalid filename
        ## Note: AssertionError now trapped by read_lookup_table
        ## OLD:
        ## with pytest.raises(AssertionError):
        ##     THE_MODULE.read_lookup_table('bad_filename')
        ##     captured = self.get_stderr()
        ##     assert 'Error' in captured
        THE_MODULE.read_lookup_table('bad_filename')
        captured = self.get_stderr()
        assert 'Error' in captured

    @pytest.mark.xfail
    def test_create_boolean_lookup_table(self):
        """Ensure create_boolean_lookup_table works as expected"""
        debug.trace(4, "test_create_boolean_lookup_table()")

        content_with_custom_delim = (
            'EmailEntered - someemail@hotmail.com\n'
            'PasswdEntered - 12345\n'
            'IsBusiness - True\n'
        )
        content_tab_delim = content_with_custom_delim.replace(' - ', '\t')
        expected_lowercase = {
            'emailentered': True,
            'passwdentered': True,
            'isbusiness': True
        }
        expected_uppercase = {
            'EmailEntered': True,
            'PasswdEntered': True,
            'IsBusiness': True
        }

        temp_file = self.get_temp_file()
        system.write_file(temp_file, content_with_custom_delim)
        assert THE_MODULE.create_boolean_lookup_table(temp_file, delim=' - ', retain_case=False) == expected_lowercase
        assert THE_MODULE.create_boolean_lookup_table(temp_file, delim=' - ', retain_case=True) == expected_uppercase

        # Test default delim tab
        temp_file = self.get_temp_file()
        system.write_file(temp_file, content_tab_delim)
        assert THE_MODULE.create_boolean_lookup_table(temp_file, retain_case=True) == expected_uppercase

        # Test invalid file
        ## Note: AssertionError now trapped by create_boolean_lookup_table
        ## OLD
        ## with pytest.raises(AssertionError):
        ##     THE_MODULE.create_boolean_lookup_table('/tmp/bad_filename')
        ##     captured = self.get_stderr()
        ##     assert 'Error:' in captured
        THE_MODULE.create_boolean_lookup_table('/tmp/bad_filename')
        captured = self.get_stderr()
        assert 'Error:' in captured
    
    def test_lookup_entry(self):
        """Ensure lookup_entry works as expected"""
        debug.trace(4, "test_lookup_entry()")
        hash_map = {
            'description': 'this is a TEST',
            'passwdentered': '12345',
            'IsBusiness': 'True',
        }
        assert THE_MODULE.lookup_entry(hash_map, 'PasswdEntered') == '12345'
        assert THE_MODULE.lookup_entry(hash_map, 'description', retain_case=True) == 'this is a TEST'

    def test_write_file(self):
        """Ensure write_file works as expected"""
        debug.trace(4, "test_write_file()")

        # Test normal usage
        filename = self.get_temp_file()
        THE_MODULE.write_file(filename, "it")
        assert THE_MODULE.read_file(filename) == "it\n"

        # Test skip newline argument
        filename = self.get_temp_file()
        THE_MODULE.write_file(filename, "it", skip_newline=True)
        assert THE_MODULE.read_file(filename) == "it"
        assert THE_MODULE.read_file(filename) != "it\n"

    def test_write_binary_file(self):
        """Ensure write_binary_file works as expected"""
        debug.trace(4, "test_write_binary_file()")
        filename = self.get_temp_file()
        THE_MODULE.write_binary_file(filename, bytes("binary", "UTF-8"))
        assert THE_MODULE.read_binary_file(filename) == b'binary'

    def test_write_lines(self):
        """Ensure write_lines works as expected"""
        debug.trace(4, "test_write_lines()")

        content = (
            'this is\n'
            'a multiline\n'
            'text used\n'
        )
        content_in_lines = [
            'this is',
            'a multiline',
            'text used',
        ]

        # Test normal usage
        filename = self.get_temp_file()
        THE_MODULE.write_lines(filename, content_in_lines)
        assert THE_MODULE.read_file(filename) == content

        # Test append
        THE_MODULE.write_lines(filename, ['for testing'], append=True)
        assert THE_MODULE.read_file(filename) == content + 'for testing\n'

    def test_write_temp_file(self):
        """Ensure write_temp_file works as expected"""
        debug.trace(4, "test_write_temp_file()")
        temp_file = self.get_temp_file()
        THE_MODULE.write_temp_file(temp_file, 'some content')
        assert THE_MODULE.read_file(temp_file) == 'some content\n'

    def test_get_file_modification_time(self):
        """Ensure get_file_modification_time works as expected"""
        debug.trace(4, "test_get_file_modification_time()")

        # create two temp files at the same time
        filedir1 = self.create_temp_file('test modified time')
        filedir2 = self.create_temp_file('test modified time2')
        # get the modification time of the files
        timestamp1 = THE_MODULE.get_file_modification_time(filedir1)[:19]
        timestamp2 = THE_MODULE.get_file_modification_time(filedir2)[:19]
        # get and format local time
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        # test timestamps are equal
        assert timestamp1 == timestamp2

        # test timestamp is equal to actual time (ignoring miliseconds)
        assert timestamp1 == now

    def test_remove_extension(self):
        """Ensure remove_extension works as expected"""
        debug.trace(4, "test_remove_extension()")
        assert THE_MODULE.remove_extension("/tmp/document.pdf") == "/tmp/document"
        assert THE_MODULE.remove_extension("it.abc.def") == "it.abc"
        assert THE_MODULE.remove_extension("it.abc.def", "abc.def") == "it"
        assert THE_MODULE.remove_extension("it.abc.def", ".abc.def") == "it"
        assert THE_MODULE.remove_extension(".coveragerc") == ".coveragerc"

        ## TODO: Check if this is a valid test case and if the returned value is correct
        assert THE_MODULE.remove_extension("it.abc.def", "abc.dtf") == "it.abc.def"

    def test_get_extension(self):
        """Verify test_get_extension over simple filenames"""
        assert THE_MODULE.get_extension("it.py") == "py"
        assert THE_MODULE.get_extension("it.py", keep_period=True) == ".py"
        assert THE_MODULE.get_extension("it") == ""        

    def test_file_exists(self):
        """Ensure file_exists works as expected"""
        debug.trace(4, "test_file_exists()")
        existent_file = self.get_temp_file()
        system.write_file(existent_file, 'content')
        assert THE_MODULE.file_exists(existent_file)
        assert not THE_MODULE.file_exists('bad_file_name')

    def test_get_file_size(self):
        """Ensure get_file_size works as expected"""
        debug.trace(4, "test_get_file_size()")
        temp_file = self.get_temp_file()
        system.write_file(temp_file, 'content')
        if os.name == 'nt':
            # CRLF line-end occupies 1 byte more than LF
            assert THE_MODULE.get_file_size(temp_file) == 9
        elif os.name == 'posix':
            assert THE_MODULE.get_file_size(temp_file) == 8
        else:
            assert False, "unsupported OS"
        assert THE_MODULE.get_file_size('non-existent-file.txt') == -1

    def test_form_path(self):
        """Ensure form_path works as expected"""
        debug.trace(4, "test_form_path()")
        assert THE_MODULE.form_path('usr', 'bin', 'cat') == 'usr' + THE_MODULE.path_separator() + 'bin' + THE_MODULE.path_separator() + 'cat'
        THE_MODULE.path_separator()

    def test_is_directory(self):
        """Ensure is_directory works as expected"""
        debug.trace(4, "test_is_directory()")
        assert THE_MODULE.is_directory(THE_MODULE.get_current_directory())

    def test_is_regular_file(self):
        """Ensure is_regular_file works as expected"""
        debug.trace(4, "test_is_regular_file()")
        filename = self.get_temp_file()
        system.write_file(filename, 'content')
        assert THE_MODULE.is_regular_file(filename)
        assert not THE_MODULE.is_regular_file('/etc')

    @pytest.mark.xfail
    def test_create_directory(self):
        """Ensure create_directory works as expected"""
        debug.trace(4, "test_create_directory()")
        ## OLD: temp_dir = THE_MODULE.getenv('TEMP')
        temp_dir = get_temp_dir()
        path = THE_MODULE.form_path(temp_dir, 'mezcla_test')
        THE_MODULE.create_directory(path)
        assert THE_MODULE.is_directory(path)

    def test_get_current_directory(self):
        """Ensure get_current_directory works as expected"""
        debug.trace(4, "test_get_current_directory()")
        ## BAD: assert '/home/' in THE_MODULE.get_current_directory()
        assert 'mezcla' in THE_MODULE.get_current_directory()

    @pytest.mark.xfail
    def test_set_current_directory(self):
        """Ensure set_current_directory works as expected"""
        debug.trace(4, "test_set_current_directory()")
        ## OLD: past_dir = THE_MODULE.get_current_directory()
        test_dir = gh.dir_path(__file__)
        assert THE_MODULE.set_current_directory(gh.form_path(test_dir, '..')) is None
        assert not THE_MODULE.get_current_directory().endswith('tests')
        THE_MODULE.set_current_directory(test_dir)
        assert THE_MODULE.get_current_directory().endswith('tests')
        ## OLD: assert THE_MODULE.get_current_directory() is not past_dir

    def test_to_utf8(self):
        """Ensure to_utf8 works as expected"""
        debug.trace(4, "test_to_utf8()")
        assert THE_MODULE.to_utf8("\ufeff") == "\ufeff"
        ## TODO: add tests for sys.version_info.major < 3
        ## assert THE_MODULE.to_utf8("\ufeff") == "\xEF\xBB\xBF"

    def test_to_str(self):
        """Ensure to_str works as expected"""
        debug.trace(4, "test_to_str()")
        assert THE_MODULE.to_str(pi).startswith('3.141592653589793')

    def test_from_utf8(self):
        """Ensure from_utf8 works as expected"""
        debug.trace(4, "test_from_utf8()")
        assert THE_MODULE.from_utf8("\xBF") == "\u00BF"
        # assert THE_MODULE.to_unicode("\xEF\xBB\xBF") == "\ufeff"
        # Lorenzo: can't convert "\ufeff" to BOM, but can convert "\xEF\xBB\xBF"

    def test_to_unicode(self):
        """Ensure to_unicode works as expected"""
        debug.trace(4, "test_to_unicode()")
        assert THE_MODULE.to_unicode("\xEF\xBB\xBF") == "\xEF\xBB\xBF"
        ## TODO: add tests for sys.version_info.major < 3
        # assert THE_MODULE.to_unicode("\xEF\xBB\xBF") == "\ufeff"

    def test_from_unicode(self):
        """Ensure from_unicode works as expected"""
        debug.trace(4, "test_from_unicode()")
        assert THE_MODULE.from_unicode("\u00BF") == "¿"

    def test_to_string(self):
        """Ensure to_string works as expected"""
        debug.trace(4, "test_to_string()")
        assert THE_MODULE.to_string(123) == "123"
        assert THE_MODULE.to_string("\u1234") ==  "\u1234"
        assert THE_MODULE.to_string(None) == "None"

    def test_chomp(self):
        """Ensure chomp works as expected"""
        debug.trace(4, "test_chomp()")
        assert THE_MODULE.chomp("some"+os.linesep) == "some"
        assert THE_MODULE.chomp("abc"+os.linesep+os.linesep) == "abc"+os.linesep
        assert THE_MODULE.chomp("http://localhost/", "/") == "http://localhost"

    def test_normalize_dir(self):
        """Ensure normalize_dir works as expected"""
        debug.trace(4, "test_normalize_dir()")
        assert THE_MODULE.normalize_dir(__file__ + THE_MODULE.path_separator()) == __file__

    def test_non_empty_file(self):
        """Ensure non_empty_file works as expected"""
        debug.trace(4, "test_non_empty_file()")

        # Test valid file
        file_with_content = self.get_temp_file()
        system.write_file(file_with_content, 'content')
        assert THE_MODULE.non_empty_file(file_with_content)

        # Test non existent file
        assert not THE_MODULE.non_empty_file('bad_file_name')

        # Test empty file
        empty_file = self.get_temp_file()
        with open(empty_file, 'wb') as _:
            pass # system.write_file cant be used because appends a newline
        assert not THE_MODULE.non_empty_file(empty_file)

    def test_absolute_path(self):
        """Ensure absolute_path works as expected"""
        debug.trace(4, "test_absolute_path()")
        temp_file = self.create_temp_file('abc')
        if os.name == 'nt':
            assert my_re.search(r"[A-Z]:\\", THE_MODULE.absolute_path(temp_file))
            ## TODO3: .absolute_path(".").startswith(USER_HOME)
        elif os.name == 'posix':
            assert "/" in THE_MODULE.absolute_path(temp_file)
            assert THE_MODULE.absolute_path("/etc/mtab").startswith("/etc")
        else:
            assert False, "unsupported OS"

    def test_real_path(self):
        """Ensure real_path works as expected"""
        debug.trace(4, "test_real_path()")
        temp_file = self.create_temp_file('abc')
        if os.name == 'nt':
            assert my_re.search(r"[A-Z]:\\", THE_MODULE.absolute_path(temp_file))
            ## TODO3: .absolute_path(".").startswith(USER_HOME)
        if os.name == 'posix':
            assert "/" in THE_MODULE.real_path("/etc/mtab")
            assert THE_MODULE.real_path("/etc/mtab").startswith("/proc")

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_get_module_version(self):
        """Ensure get_module_version works as expected"""
        debug.trace(4, "test_get_module_version()")
        num_good = 0
        num_total = 0
        for line in gh.run("pip freeze").splitlines():
            if my_re.search(r"(\S+)==(\S+)", line):
                num_total += 1
                module, version = my_re.groups()
                if version == THE_MODULE.get_module_version(module):
                    num_good += 1
            else:
                debug.trace(4, f"Ignoring pip freeze line: {line}")
        percent = (num_good / num_total * 100) if num_total else 0
        debug.trace_expr(5, num_good, num_total, percent)
        assert percent >= 90

    def test_intersection(self):
        """Ensure intersection works as expected"""
        debug.trace(4, "test_intersection()")
        assert THE_MODULE.intersection([1, 2], [5, 7, 8]) == []
        assert THE_MODULE.intersection([1, 2, 3, 4, 5], [2, 4]) == [2, 4]
        assert THE_MODULE.intersection([1, 2], [5, 7, 8], as_set=True) == set()
        assert THE_MODULE.intersection([1, 2, 3, 4, 5], [2, 4], as_set=True) == {2, 4}

    def test_union(self):
        """Ensure union works as expected"""
        debug.trace(4, "test_union()")
        assert THE_MODULE.union([1, 2, 3], [2, 3, 4, 5]) == [1, 2, 3, 4, 5]
        assert THE_MODULE.union([1, 2, 3], [2, 3, 4, 5], as_set=True) == {1, 2, 3, 4, 5}

    def test_difference(self):
        """Ensure difference works as expected"""
        debug.trace(4, "test_difference()")
        assert THE_MODULE.difference([5, 4, 3, 2, 1], [4, 2]) == [5, 3, 1]
        assert THE_MODULE.difference([1, 2, 3], [2]) == [1, 3]
        assert THE_MODULE.difference([1, 1, 2, 2], [1]) == [2, 2]

    def test_append_new(self):
        """Ensure append_new works as expected"""
        debug.trace(4, "test_append_new()")
        assert THE_MODULE.append_new([1, 2], 3) == [1, 2, 3]
        assert THE_MODULE.append_new([1, 2, 3], 3) == [1, 2, 3]

    def test_just_one_true(self):
        """Ensure just_one_true works as expected"""
        debug.trace(4, "test_just_one_true()")

        assert THE_MODULE.just_one_true(['yes', '', '', ''], strict=True)
        assert not THE_MODULE.just_one_true(['', '', '', ''], strict=True)

        # all nones should return always True unless strict
        assert THE_MODULE.just_one_true(['', '', '', ''], strict=False)
        assert not THE_MODULE.just_one_true(['', '', '', ''], strict=True)

    def test_just_one_non_null(self):
        """Ensure just_one_non_null works as expected"""
        debug.trace(4, "test_just_one_non_null()")

        assert THE_MODULE.just_one_non_null(['yes', None, None, None], strict=True)
        assert not THE_MODULE.just_one_non_null([None, None, None, None], strict=True)

        # all nones should return always True unless strict
        assert THE_MODULE.just_one_non_null([None, None, None, None], strict=False)
        assert not THE_MODULE.just_one_non_null([None, None, None, None], strict=True)

    def test_unique_items(self):
        """Ensure unique_items works as expected"""
        debug.trace(4, "test_unique_items()")

        # Test normal usage
        assert THE_MODULE.unique_items([1, 2, 3, 2, 1], prune_empty=False) == [1, 2, 3]

        # Test prune_empty
        assert THE_MODULE.unique_items(['cars', 'cars', 'plane', 'train', ''], prune_empty=False) == ['cars', 'plane', 'train', '']
        assert THE_MODULE.unique_items(['cars', 'cars', 'plane', 'train', ''], prune_empty=True) == ['cars', 'plane', 'train']
        assert THE_MODULE.unique_items(['Cars', 'cars', 'plane', 'train', ''], prune_empty=True) == ['Cars', 'cars', 'plane', 'train']
        assert THE_MODULE.unique_items(['Cars', 'cars', 'plane', 'train', ''], prune_empty=True, ignore_case=True) == ['Cars', 'plane', 'train']

    def test_to_float(self):
        """Ensure to_float works as expected"""
        debug.trace(4, "test_to_float()")

        # Test normal usage
        assert THE_MODULE.to_float('9.81', default_value=10.0) == 9.81

        # Test default_value
        assert THE_MODULE.to_float('3,14', default_value=4.0) == 4.0 # comma raises the exception.

    def test_to_int(self):
        """Ensure to_int works as expected"""
        debug.trace(4, "test_to_int()")

        # Test normal usage
        assert THE_MODULE.to_int('45', default_value=5, base=10) == 45

        # Test default_value
        assert THE_MODULE.to_int('foo', default_value=5, base=10) == 5

        # Test base
        assert THE_MODULE.to_int('10011', default_value=5, base=2) == 19

    def test_to_bool(self):
        """Ensure to_bool works as expected"""
        debug.trace(4, "test_to_bool()")
        assert THE_MODULE.to_bool(True)
        assert THE_MODULE.to_bool("True")
        assert THE_MODULE.to_bool("Foobar")
        assert THE_MODULE.to_bool(333)
        assert not THE_MODULE.to_bool(False)
        assert not THE_MODULE.to_bool("false")
        assert not THE_MODULE.to_bool("none")
        assert not THE_MODULE.to_bool("off")
        assert not THE_MODULE.to_bool("0")
        assert not THE_MODULE.to_bool("")

    def test_round_num(self):
        """Ensure round_num works as expected"""
        debug.trace(4, "test_round_num()")
        assert THE_MODULE.round_num(3.15914, 3) == 3.159
        THE_MODULE.PRECISION = 5
        assert THE_MODULE.round_num(3.15914311312) == 3.15914

    def test_round_as_str(self):
        """Ensure round_as_str works as expected"""
        debug.trace(4, "test_round_as_str()")
        assert THE_MODULE.round_as_str(3.15914, 3) == "3.159"
        assert isinstance(THE_MODULE.round_as_str(3.15914, 3), str)

    def test_sleep(self):
        """Ensure sleep works as expected"""
        debug.trace(4, "test_sleep()")
        def sleep_mock(secs):
            return f'sleeping {secs}'
        self.monkeypatch.setattr(time, "sleep", sleep_mock)
        THE_MODULE.sleep(123123, trace_level=-1)
        captured = self.get_stderr()
        assert '123123' in captured

    def test_current_time(self):
        """Ensure current_time works as expected"""
        debug.trace(4, "test_current_time()")
        def time_mock():
            return 12345.6789
        self.monkeypatch.setattr(time, "time", time_mock)
        assert THE_MODULE.current_time() == 12345.6789
        assert THE_MODULE.current_time(integral=True) == 12346

    def test_time_in_secs(self):
        """Ensure time_in_secs works as expected"""
        debug.trace(4, "test_time_in_secs()")
        # This method is most covered on test_current_time
        assert isinstance(THE_MODULE.time_in_secs(), int)

    def test_python_maj_min_version(self):
        """Ensure python_maj_min_version works as expected"""
        debug.trace(4, "test_python_maj_min_version()")
        assert re.search(r'\d+\.\d+', str(THE_MODULE.python_maj_min_version()))

    def test_get_args(self):
        """Ensure get_args works as expected"""
        debug.trace(4, "test_get_args()")
        args = [
            "pytest",
            "--name",
            "logfilename.log",
        ]
        self.monkeypatch.setattr("sys.argv", args)
        assert THE_MODULE.get_args() == args

    def test_main(self):
        """Ensure main works as expected"""
        THE_MODULE.main('some-arg')
        captured = self.get_stderr()
        # ex: Warning, tomohara: system.py not intended for direct invocation!
        assert "not intended" in captured.lower()


def set_test_env_var():
    """Set enviroment vars to run tests"""
    THE_MODULE.env_options = {
        'VAR_STRING': 'this is a string variable',
        'ANOTHER_VAR': 'this is another env. var.'
    }
    THE_MODULE.env_defaults = {
        'VAR_STRING': 'empty',
        'ANOTHER_VAR': '2022'
    }


if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
