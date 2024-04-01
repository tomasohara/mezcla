#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Test(s) for tpo_common.py
#
# Notes:
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_tpo_common.py
#
# Warning:
# - *** The tpo_common.py module is being phased out. Although there are
#   a bunch of "work-in-progress" tests below, they are low priority because
#   most are addressed by test_system.py or test_debug.py.
#
# TODO1: Make sure all work-in-progress tests issue Assert(False).
#
# TODO:
# - Address commonly used debugging functions (e.g., debug_print) by redirecting output (via remapping sys.stderr to a file) and then checking file contents.
# - add tests for normalize_unicode, ensure_unicode and other problematic functions
#
# Important:
# - Most of the methods on tpo_common was moved to predecessors modules as system.py, debug.py etc.
# - Using the predecessors module tests to these moved methods could be useful to avoid repeated tests but this could create conflicts with modified methods.
#

"""Tests for tpo_common module"""

# Standard modules
import sys
import re
from datetime import datetime

# Installed modules
import pytest
import pickle
import trace

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper
from mezcla.unittest_wrapper import trap_exception

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	                global module object
#    TestIt.script_module:              path to file
import mezcla.tpo_common as THE_MODULE

FUBAR = 101	# sample global for test_format
FOOBAR = 12     # likewise
JOSE = "José"   # UTF-8 encoded string
UTF8_BOM = "\xEF\xBB\xBF"

class TestTpoCommon(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    def test_set_debug_level(self):
        """Ensure set_debug_level works as expected"""
        debug.trace(4, "test_set_debug_level()")
        THE_MODULE.set_debug_level(5)
        assert THE_MODULE.debugging_level() == 5

    def test_debugging_level(self):
        """Ensure debugging_level works as expected"""
        debug.trace(4, "test_debugging_level()")
        THE_MODULE.set_debug_level(5)
        assert THE_MODULE.debugging_level() == 5

    def test_debug_trace_without_newline(self):
        """Ensure debug_trace_without_newline works as expected"""
        debug.trace(4, "test_debug_trace_without_newline()")
        text = 'test debug trace withouht newline'
        
        # test underlying function is being called
        tracer = trace.Trace(countfuncs=1)
        tracer.runfunc(THE_MODULE.debug_trace_without_newline, (text))
        
        # redirect write_results to temp file
        temp = self.get_temp_file()
        tracer.results().write_results(coverdir=temp)
        
        out, error = self.get_stdout_stderr()
        assert re.search(r'modulename: debug, funcname: trace', out)

        # test behaviour of functions
        assert text in error
        assert f'{text}\n' not in error


    @pytest.mark.xfail
    def test_debug_trace(self):
        """Ensure debug_trace works as expected"""
        debug.trace(4, "test_debug_trace()")
        ## TODO: WORK-IN-PROGRESS
        assert(False)

    @pytest.mark.xfail
    def test_debug_print(self):
        """Ensure debug_print works as expected"""
        debug.trace(4, "test_debug_print()")
        ## TODO: WORK-IN-PROGRESS
        assert(False)

    @pytest.mark.xfail
    def test_debug_format(self):
        """Ensure debug_format works as expected"""
        debug.trace(4, "test_debug_format()")
        ## TODO: WORK-IN-PROGRESS
        assert(False)

    def test_debug_timestamp(self):
        """Ensure debug_timestamp works as expected"""
        debug.trace(4, "test_debug_timestamp()")
        tracer = trace.Trace(countfuncs=1)
        tracer.runfunc(THE_MODULE.debug_timestamp)
        
        # redirect write_results to temp file
        temp = self.get_temp_file()
        tracer.results().write_results(coverdir=temp)
        
        captured = self.get_stdout()
        assert re.search(r'modulename: debug, funcname: timestamp', captured)
        
        # test behaviour of function
        actual, expected = THE_MODULE.debug_timestamp(), str(datetime.now())
        # truncating the timestamp to eliminate milisecond difference in calculation
        assert actual[:22] == expected[:22]

    def test_debug_raise(self):
        """Ensure debug_raise works as expected"""
        debug.trace(4, "test_debug_raise()")
        
        tracer = trace.Trace(countfuncs=1)
        with pytest.raises(RuntimeError):
            tracer.runfunc(THE_MODULE.debug_raise)
                
        # redirect write_results to temp file
        temp = self.get_temp_file()
        tracer.results().write_results(coverdir=temp)
        
        captured = self.get_stdout()
        assert re.search(r'modulename: debug, funcname: raise_exception', captured)


    def test_trace_array(self):
        """Ensure trace_array works as expected"""
        debug.trace(4, "test_trace_array()")
        array = ['test', 'trace', 'array']
        tracer = trace.Trace(countfuncs=1)
        tracer.runfunc(THE_MODULE.trace_array, (array))
        
        # redirect write_results to temp file
        temp = self.get_temp_file()
        tracer.results().write_results(coverdir=temp)
        
        out, error = self.get_stdout_stderr()
        assert re.search(r'modulename: debug, funcname: trace_values', out)
        
        for i, item in enumerate(array):
            assert f"{i}: {item}" in error

    def test_trace_object(self):
        """Ensure trace_object works as expected"""
        debug.trace(4, "test_trace_object()")
        
        class TestObj:
            __var__ = 1
            
            def test_method():
                pass
        
        obj = TestObj()
        tracer = trace.Trace(countfuncs=1)
        tracer.runfunc(THE_MODULE.trace_object, obj, show_methods_etc=True, show_private=True)
        
        # redirect write_results to temp file
        temp = self.get_temp_file()
        tracer.results().write_results(coverdir=temp)
        
        out, error = self.get_stdout_stderr()
        assert re.search(r'modulename: debug, funcname: trace_object', out)
        
        assert '__var__: 1' in error
        assert 'test_method' in error
        

    @pytest.mark.xfail
    def test_trace_value(self):
        """Ensure trace_value works as expected"""
        debug.trace(4, "test_trace_value()")
        ## TODO: WORK-IN-PROGRESS
        assert(False)

    @pytest.mark.xfail
    def test_trace_current_context(self):
        """Ensure trace_current_context works as expected"""
        debug.trace(4, "test_trace_current_context()")
        
        test_var = 1
        #assert local and global variables are traced
        THE_MODULE.trace_current_context(level=8, label='TPO', show_methods_etc=True)
        error = self.get_stderr()
        assert 'TPO' in error
        assert 'test_var' in error
        assert 'FOOBAR' in error
        
        # assert debug function is being called
        tracer = trace.Trace(countfuncs=1)
        tracer.runfunc(THE_MODULE.trace_current_context, show_methods_etc=True, label='TPO')
        
        # redirect write_results to temp file
        temp = self.get_temp_file()
        tracer.results().write_results(coverdir=temp)
        
        stdout = self.get_stdout()
        assert re.search(r'modulename: debug, funcname: trace_current_context', stdout)

    @pytest.mark.xfail
    def test_during_debugging(self):
        """Ensure during_debugging works as expected"""
        debug.trace(4, "test_during_debugging()")
        ## TODO: WORK-IN-PROGRESS
        assert(False)

    def test_debugging(self):
        """Ensure debugging works as expected"""
        debug.trace(4, "test_debugging()")
        THE_MODULE.set_debug_level(4)
        assert THE_MODULE.debugging(2)
        assert THE_MODULE.debugging(4)
        assert not THE_MODULE.debugging(6)

    def test_detailed_debugging(self):
        """Ensure detailed_debugging works as expected"""
        debug.trace(4, "test_detailed_debugging()")
        THE_MODULE.set_debug_level(2)
        assert not THE_MODULE.detailed_debugging()
        THE_MODULE.set_debug_level(4)
        assert THE_MODULE.detailed_debugging()
        THE_MODULE.set_debug_level(6)
        assert THE_MODULE.detailed_debugging()

    def test_verbose_debugging(self):
        """Ensure verbose_debugging works as expected"""
        debug.trace(4, "test_verbose_debugging()")
        THE_MODULE.set_debug_level(2)
        assert not THE_MODULE.verbose_debugging()
        THE_MODULE.set_debug_level(5)
        assert THE_MODULE.verbose_debugging()
        THE_MODULE.set_debug_level(7)
        assert THE_MODULE.verbose_debugging()

    def test_to_string(self):
        """Ensure to_string works as expected"""
        debug.trace(4, "test_to_string()")
        assert THE_MODULE.to_string(123) == "123"
        assert THE_MODULE.to_string("\u1234") == "\u1234"
        assert THE_MODULE.to_string(None) == "None"

    def test_normalize_unicode(self):
        """Ensure normalize_unicode works as expected"""
        debug.trace(4, "test_normalize_unicode()")
        assert THE_MODULE.normalize_unicode("ASCII") == "ASCII"
        assert THE_MODULE.normalize_unicode(UTF8_BOM) == UTF8_BOM
        ## TODO: assert "Jos\xc3\xa9", THE_MODULE.normalize_unicode(JOSE)
        ## TODO: add tests for sys.version_info.major < 3
        ## assert THE_MODULE.normalize_unicode('\u1234') == '\xe1\x88\xb4'

    def test_ensure_unicode(self):
        """Ensure ensure_unicode works as expected"""
        debug.trace(4, "test_ensure_unicode()")
        assert THE_MODULE.ensure_unicode("ASCII") == "ASCII"
        assert "Jos\xe9" == THE_MODULE.ensure_unicode(JOSE)
        ## TODO: assert THE_MODULE.ensure_unicode(UTF8_BOM) == '\ufeff'
        ## TODO: add tests for sys.version_info.major < 3
        ## assert THE_MODULE.ensure_unicode('\xe1\x88\xb4') == '\u1234'

    def test_print_stderr(self):
        """Ensure print_stderr works as expected"""
        debug.trace(4, "test_print_stderr()")
        # ensure stderr is not being redirected
        self.monkeypatch.setattr(THE_MODULE, 'stderr', sys.stderr)

        message = "this is error"
        THE_MODULE.print_stderr(message)
        error = self.get_stderr()
        assert message in error

    # @pytest.mark.xfail
    def test_redirect_stderr(self):
        """Ensure redirect_stderr works as expected"""
        debug.trace(4, "test_redirect_stderr()")
        # ensure stderr is not being redirected
        self.monkeypatch.setattr(THE_MODULE, 'stderr', sys.stderr)
        
        temp = self.get_temp_file()
        THE_MODULE.redirect_stderr(temp)
        THE_MODULE.print_stderr("stderr redirected")
        THE_MODULE.restore_stderr()
        assert "stderr redirected" in gh.read_file(temp)

    @pytest.mark.xfail
    def test_restore_stderr(self):
        """Ensure restore_stderr works as expected"""
        debug.trace(4, "test_restore_stderr()")
        # ensure stderr is already being redirected
        self.monkeypatch.setattr(THE_MODULE, 'stderr', system.open_file(self.get_temp_file()))
        THE_MODULE.restore_stderr()
        assert sys.stderr == THE_MODULE.stderr

    def test_setenv(self):
        """Ensure setenv works as expected"""
        debug.trace(4, "test_setenv()")
        THE_MODULE.setenv('NEW_TEST_ENV_VAR', 'the gravity is 10, pi is 3')
        assert THE_MODULE.getenv('NEW_TEST_ENV_VAR') == 'the gravity is 10, pi is 3'

    def test_chomp(self):
        """Ensure chomp works as expected"""
        debug.trace(4, "test_chomp()")
        assert THE_MODULE.chomp("abc\n") == "abc"
        assert THE_MODULE.chomp("http://localhost/", "/") == "http://localhost"

    @trap_exception
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

        self.do_assert(THE_MODULE.env_options['VAR_STRING'], 'this is a string variable')
        self.do_assert(THE_MODULE.env_defaults['VAR_STRING'], 'empty')
        self.do_assert(len(THE_MODULE.env_options) == 1)
        self.do_assert(len(THE_MODULE.env_defaults) == 1)

    @pytest.mark.xfail                   # TODO: remove xfail
    @trap_exception
    def test_formatted_environment_option_descriptions(self):
        """Ensure formatted_environment_option_descriptions works as expected"""
        debug.trace(4, "test_formatted_environment_option_descriptions()")

        set_test_env_var()

        # Test sort
        expected = (
            'VAR_STRING\tthis is a string variable (empty)\n'
            '\tANOTHER_VAR\tthis is another env. var. n/a'
        )
        self.do_assert(THE_MODULE.formatted_environment_option_descriptions(sort=False) == expected)
        expected = (
            'ANOTHER_VAR\tthis is another env. var. n/a\n'
            '\tVAR_STRING\tthis is a string variable (empty)'
        )
        self.do_assert(THE_MODULE.formatted_environment_option_descriptions(sort=True) == expected)

        # Test include_all
        # NOTE: this is being tested on test_system.test_get_environment_option_descriptions()

        # Test indent
        expected = (
            'VAR_STRING + this is a string variable (empty)\n'
            ' + ANOTHER_VAR + this is another env. var. n/a'
        )
        self.do_assert(THE_MODULE.formatted_environment_option_descriptions(indent=' + ') == expected)

    def test_get_registered_env_options(self):
        """Ensure get_registered_env_options works as expected"""
        debug.trace(4, "test_get_registered_env_options()")
        set_test_env_var()
        result = THE_MODULE.get_registered_env_options()
        assert isinstance(result, list)
        assert 'VAR_STRING' in result
        assert len(result) == 2

    @trap_exception
    def test_get_environment_option_descriptions(self):
        """Test get_environment_option_descriptions"""
        debug.trace(4, "test_get_environment_option_descriptions()")
        set_test_env_var()
        result = THE_MODULE.get_environment_option_descriptions(include_default=True)
        self.do_assert(isinstance(result, list))
        self.do_assert("(2022)" in str(result), "default added")
        self.do_assert(len(result) == 2)
        
    @pytest.mark.xfail
    def test_getenv_real(self):
        """Ensure getenv_real works as expected"""
        debug.trace(4, "test_getenv_real()")
        ## TODO: WORK-IN-PROGRESS
        assert(False)

    @pytest.mark.xfail
    def test_getenv_float(self):
        """Ensure getenv_float works as expected"""
        debug.trace(4, "test_getenv_float()")
        ## TODO: WORK-IN-PROGRESS
        assert(False)

    def test_get_current_function_name(self):
        """Test(s) for get_current_function_name()"""
        assert THE_MODULE.get_current_function_name() == "test_get_current_function_name"
        return

    @pytest.mark.xfail
    def test_get_property_value(self):
        """Ensure get_property_value works as expected"""
        debug.trace(4, "test_get_property_value()")
        ## TODO: WORK-IN-PROGRESS
        assert(False)

    @pytest.mark.xfail
    def test_simple_format(self):
        """Ensure simple_format works as expected"""
        debug.trace(4, "test_simple_format()")
        ## TODO: WORK-IN-PROGRESS
        assert(False)

    def test_format(self):
        """Ensure format resolves from local and global namespace, and that local takes precedence"""
        fubar = 202
        assert THE_MODULE.format("{F} vs. {f}", F=FUBAR, f=fubar) == ("%s vs. %s" % (FUBAR, fubar))
        # pylint: disable=redefined-outer-name
        FOOBAR = 21
        assert THE_MODULE.format("{FOO}", FOO=FOOBAR) == str(FOOBAR)
        ## TODO: assert "Hey Jos\xc3\xa9" == THE_MODULE.format("Hey {j}", j=JOSE)
        return

    @pytest.mark.xfail
    def test_init_logging(self):
        """Ensure init_logging works as expected"""
        debug.trace(4, "test_init_logging()")
        ## TODO: WORK-IN-PROGRESS
        assert(False)

    def test_load_object(self):
        """Ensure load_object works as expected"""
        debug.trace(4, "test_load_object()")
        test_dict = {
            1: 'first',
            2: 'second',
        }
        test_filename = self.get_temp_file()
        test_file = open(test_filename, 'wb')
        pickle.dump(test_dict, test_file)
        test_file.close()

        assert THE_MODULE.load_object(test_filename) == test_dict

    def test_store_object(self):
        """Ensure store_object works as expected"""
        debug.trace(4, "test_store_object()")
        test_dict = {
            1: 'first',
            2: 'second',
        }
        test_filename = self.get_temp_file()

        THE_MODULE.store_object(test_filename, test_dict)

        test_file = open(test_filename, 'rb')
        actual_object = pickle.load(test_file)
        assert actual_object == test_dict
        test_file.close()

    def test_dump_stored_object(self):
        """Ensure dump_stored_object works as expected"""
        debug.trace(4, "test_dump_stored_object()")

        ## TODO: add tests related to redirect_stderr and restore_stderr

        test_dict = {
            1: 'first',
            2: 'second',
        }
        test_filename = self.get_temp_file()

        THE_MODULE.store_object(test_filename, test_dict)

        test_file = open(test_filename, 'rb')
        actual_object = pickle.load(test_file)
        assert actual_object == test_dict
        test_file.close()

    @pytest.mark.xfail
    def test_create_lookup_table(self):
        """Ensure create_lookup_table works as expected"""
        debug.trace(4, "test_create_lookup_table()")
        ## TODO: WORK-IN-PROGRESS
        assert(False)

    def test_lookup_key(self):
        """Ensure lookup_key works as expected"""
        debug.trace(4, "test_lookup_key()")
        test_table = {
            'first': '1st',
            'second': '2nd',
        }
        assert THE_MODULE.lookup_key(test_table, 'second', 'two-nd') == '2nd'
        assert THE_MODULE.lookup_key(test_table, 'third', '3rd') == '3rd'

    def test_create_boolean_lookup_table(self):
        """Ensure create_boolean_lookup_table works as expected"""
        debug.trace(4, "test_create_boolean_lookup_table()")

        content = (
            'EmailEntered - someemail@hotmail.com\n'
            'PasswdEntered - 12345\n'
            'IsBusiness - True\n'
        )
        expected = {
            'emailentered - someemail@hotmail.com': True,
            'passwdentered - 12345': True,
            'isbusiness - true': True,
        }

        temp_file = self.get_temp_file()
        gh.write_file(temp_file, content)
        assert THE_MODULE.create_boolean_lookup_table(temp_file) == expected

    @pytest.mark.xfail
    def test_normalize_frequencies(self):
        """Ensure normalize_frequencies works as expected"""
        debug.trace(4, "test_normalize_frequencies()")
        ## TODO: WORK-IN-PROGRESS
        assert(False)

    @pytest.mark.xfail
    def test_sort_frequencies(self):
        """Ensure sort_frequencies works as expected"""
        debug.trace(4, "test_sort_frequencies()")
        ## TODO: WORK-IN-PROGRESS
        assert(False)

    def test_sort_weighted_hash(self):
        """Ensure sort_weighted_hash works as expected"""
        debug.trace(4, "test_sort_weighted_hash()")
        test_hash = {
            'bananas': 3,
            'apples': 1411,
            'peach': 43,
        }
        sorted_hash = [
            ('bananas', 3),
            ('peach', 43),
            ('apples', 1411),
        ]
        reversed_hash = [
            ('apples', 1411),
            ('peach', 43),
            ('bananas', 3),
        ]
        assert THE_MODULE.sort_weighted_hash(test_hash) == reversed_hash
        assert THE_MODULE.sort_weighted_hash(test_hash, reverse=False) == sorted_hash
        assert len(THE_MODULE.sort_weighted_hash(test_hash, max_num=2)) == 2

    @pytest.mark.xfail
    def test_format_freq_hash(self):
        """Ensure format_freq_hash works as expected"""
        debug.trace(4, "test_format_freq_hash()")
        ## TODO: WORK-IN-PROGRESS
        assert(False)

    def test_union(self):
        """Ensure union works as expected"""
        debug.trace(4, "test_union()")
        assert THE_MODULE.union([1, 2, 3], [2, 3, 4, 5]) == [1, 2, 3, 4, 5]

    def test_intersection(self):
        """Ensure intersection works as expected"""
        debug.trace(4, "test_intersection()")
        assert THE_MODULE.intersection([1, 2, 3, 4, 5], [2, 4]) == [2, 4]

    def test_is_subset(self):
        """Ensure is_subset works as expected"""
        debug.trace(4, "test_is_subset()")
        assert THE_MODULE.is_subset(['mouse', 'dog'], ['dog', 'cat', 'mouse'])

    def test_difference(self):
        """Ensures set difference works as expected"""
        assert THE_MODULE.difference([5, 4, 3, 2, 1], [4, 2]) == [1, 3, 5]
        assert THE_MODULE.difference([1, 2, 3], [2]) == [1, 3]
        assert THE_MODULE.difference([1, 1, 2, 2], [1]) == [2]

    def test_remove_all(self):
        """Ensure remove_all works as expected"""
        debug.trace(4, "test_remove_all()")
        assert THE_MODULE.remove_all([5, 4, 3, 2, 1], [4, 2, 0]) == [5, 3, 1]
        assert THE_MODULE.remove_all(['A', 'B', 'C', 'D'], ['A', 'B', 'D']) == ['C']
        assert THE_MODULE.remove_all(['a', 'B', 'c', 'D'], ['A', 'b', 'd'], ignore_case=True) == ['c']

    def test_equivalent(self):
        """Ensure equivalent works as expected"""
        debug.trace(4, "test_equivalent()")
        assert THE_MODULE.equivalent([1, 2, 3], [1, 2, 3])
        assert not THE_MODULE.equivalent([1, 2, 3, 4], [1, 2, 3])
        assert not THE_MODULE.equivalent([1, 3], [1, 2])

    def test_append_new(self):
        """Ensure append_new works as expected"""
        debug.trace(4, "test_append_new()")
        assert THE_MODULE.append_new([1, 2], 3) == [1, 2, 3]
        assert THE_MODULE.append_new([1, 2, 3], 3) == [1, 2, 3]

    def test_extract_list(self):
        """Ensure extract_list works as expected"""
        debug.trace(4, "test_extract_list()")
        assert THE_MODULE.extract_list('a,b,c') == ['a', 'b', 'c']

    def test_is_subsumed(self):
        """Ensure is_subsumed works as expected"""
        debug.trace(4, "test_is_subsumed()")
        assert THE_MODULE.is_subsumed("dog", ["dog house", "catnip"])
        assert not THE_MODULE.is_subsumed("cat", ["dog house", "catnip"])

    def test_round_num(self):
        """Ensure round_num works as expected"""
        debug.trace(4, "test_round_num()")
        assert THE_MODULE.round_num(15000, 3) == "15000.000"
        assert THE_MODULE.round_num(15000, 3, False) == "15000"

    def test_round_nums(self):
        """Ensure round_nums works as expected"""
        debug.trace(4, "test_round_nums()")
        assert THE_MODULE.round_nums([0.333333, 0.666666, 0.99999]) == ['0.333', '0.667', '1.000']

    def test_round(self):
        """Ensure round works as expected"""
        debug.trace(4, "test_round()")
        assert THE_MODULE.round(15000) == 15000.0
        assert THE_MODULE.round([0.333333, 0.666666, 0.99999]) == [0.333, 0.667, 1.0]

    def test_normalize(self):
        """Ensure normalize works as expected"""
        debug.trace(4, "test_normalize()")
        assert THE_MODULE.normalize([1, 2, 3]) == [0.0, 0.5, 1.0]

    def test_is_numeric(self):
        """Ensure is_numeric works as expected"""
        debug.trace(4, "test_is_numeric()")
        assert THE_MODULE.is_numeric("123")
        assert not THE_MODULE.is_numeric("one")

    def test_safe_int(self):
        """Ensure safe_int works as expected"""
        debug.trace(4, "test_safe_int()")
        THE_MODULE.safe_int('1') == 1
        THE_MODULE.safe_int(2.0) == 2
        THE_MODULE.safe_int("F", base=16) == 16
        THE_MODULE.safe_int("82", base=8) == 10
        THE_MODULE.safe_int("four") == 0

    # @pytest.mark.xfail
    def test_safe_float(self):
        """Ensure safe_float works as expected"""
        debug.trace(4, "test_safe_float()")
        assert THE_MODULE.safe_float(5) == 5.0
        assert THE_MODULE.safe_float("3") == 3.0
        assert THE_MODULE.safe_float("three") == 0.0
        
        
    @pytest.mark.xfail
    def test_reference_variables(self):
        """Ensure reference_variables works as expected"""
        debug.trace(4, "test_reference_variables()")
        ## TODO: WORK-IN-PROGRESS
        assert(False)

    @pytest.mark.xfail
    def test_memodict(self):
        """Ensure memodict works as expected"""
        debug.trace(4, "test_memodict()")
        ## TODO: WORK-IN-PROGRESS
        assert(False)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_exit(self):
        """Ensure exit works as expected"""
        debug.trace(4, "test_exit()")
        def sys_exit_mock():
            return 'exit'
        self.monkeypatch.setattr(sys, "exit", sys_exit_mock)
        assert THE_MODULE.exit('test exit method') == 'exit'
        # Exit is mocked, ignore code editor hiding
        ## TODO: for some reason (probably the debug level) the message is not being printed
        captured = self.get_stdout_stderr()
        debug.trace_object(5, captured)
        ## TODO: assert "test exit method" in captured.err
        debug.assertion("test exit method" in captured[1])

    def test_dummy_main(self):
        """Ensure dummy_main works as expected"""
        debug.trace(4, "test_dummy_main()")
        THE_MODULE.dummy_main()
        captured = self.get_stdout()
        assert 'Environment options' in captured

    @trap_exception
    def test_getenv(self):
        """Ensure getenv works as expected"""
        debug.trace(4, "test_getenv()")
        self.monkeypatch.setenv('TEST_ENV_VAR', 'some value', prepend=False)
        assert THE_MODULE.getenv('TEST_ENV_VAR') == 'some value'

    def test_getenv_value(self):
        """Ensure getenv_value works as expected"""
        debug.trace(4, "test_getenv_value()")
        self.monkeypatch.setenv('NEW_ENV_VAR', 'some value', prepend=False)
        assert THE_MODULE.getenv_value('NEW_ENV_VAR', default='empty', description='another test env var') == 'some value'
        assert THE_MODULE.env_defaults['NEW_ENV_VAR'] == 'empty'
        assert THE_MODULE.env_options['NEW_ENV_VAR'] == 'another test env var'

    def test_getenv_text(self):
        """Ensure getenv_text works as expected"""
        debug.trace(4, "test_getenv_text()")
        self.monkeypatch.setenv('TEST_ENV_VAR', 'some value', prepend=False)
        assert THE_MODULE.getenv_text('TEST_ENV_VAR') == 'some value'
        assert THE_MODULE.getenv_text("REALLY FUBAR?", False) == 'False'

    def test_getenv_number(self):
        """Ensure getenv_number works as expected"""
        debug.trace(4, "test_getenv_number()")
        self.monkeypatch.setenv('TEST_NUMBER', '9.81', prepend=False)
        assert THE_MODULE.getenv_number('TEST_NUMBER', default=20) == 9.81
        assert THE_MODULE.getenv_number("REALLY FUBAR", 123) == 123.0

    def test_getenv_int(self):
        """Ensure getenv_int works as expected"""
        debug.trace(4, "test_getenv_int()")
        self.monkeypatch.setenv('TEST_NUMBER', '34', prepend=False)
        assert THE_MODULE.getenv_int('TEST_NUMBER', default=20) == 34
        assert THE_MODULE.getenv_int("REALLY FUBAR", 123) == 123

    def test_getenv_bool(self):
        """Ensure getenv_bool works as expected"""
        debug.trace(4, "test_getenv_bool()")
        self.monkeypatch.setenv('TEST_BOOL', 'FALSE', prepend=False)
        assert not THE_MODULE.getenv_bool('TEST_BOOL', None)
        self.monkeypatch.setenv('TEST_BOOL', '  true   ', prepend=False)
        assert THE_MODULE.getenv_bool('TEST_BOOL', None)
        assert not isinstance(THE_MODULE.getenv_boolean("REALLY FUBAR?", None), bool)
        assert isinstance(THE_MODULE.getenv_boolean("REALLY FUBAR?", False), bool)


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
    pytest.main([__file__])
