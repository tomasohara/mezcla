#! /usr/bin/env python3
#
# Test(s) for ../misc_utils.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_misc_utils.py
#

"""Tests for misc_utils module"""

# Standard packages
import math
import datetime
import time
import os 

# Installed packages
import pytest
from unittest_parametrize import ParametrizedTestCase, parametrize

# Local packages
from mezcla import glue_helpers as gh
from mezcla import debug
from mezcla.my_regex import my_re
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla.tests.common_module import SKIP_EXPECTED_ERRORS, SKIP_EXPECTED_REASON
## OLD: from mezcla.mezcla_to_standard import EqCall, Features
# note: mezcla_to_standard uses packages not installed by default (e.g., libcst)
try:
    from mezcla import mezcla_to_standard
    EqCall = mezcla_to_standard.EqCall
except:
    mezcla_to_standard = None
    class Path:
        """Dummy path"""
        path = "n/a"
    class EqCall:
        """Dummy equivalent call"""
        ## TODO3: use mock package
        dests = targets = [Path()]
        def __init__(self, *_args, **_kwargs):
            pass
    debug.trace_exception(4, "mezcla.mezcla_to_standard import")

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
import mezcla.misc_utils as THE_MODULE

# Make sure more_itertools available
more_itertools = None
try:
    import more_itertools
except ImportError:
    system.print_exception_info("more_itertools import")

# Constants
ONE_MB = 1024 ** 2


class TestMiscUtils(TestWrapper, ParametrizedTestCase):
    """Class for test case definitions"""
    # note: script_module used in argument parsing sanity check (e.g., --help)
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    def test_transitive_closure(self):
        """Ensure transitive_closure works as expected"""
        debug.trace(4, "test_transitive_closure()")

        actual = THE_MODULE.transitive_closure([(1, 2), (2, 3), (3, 4)])
        expected = set([(1, 2), (1, 3), (1, 4), (2, 3), (3, 4), (2, 4)])
        assert actual == expected

    def test_read_tabular_data(self):
        """Ensure read_tabular_data works as expected"""
        debug.trace(4, "test_read_tabular_data()")
        string_table = (
            'language\tPython\n' +
            'framework\tPytest\n'
        )
        dict_table = {
            'language': 'Python\n',
            'framework': 'Pytest\n',
        }
        temp_file = self.get_temp_file()
        system.write_file(temp_file, string_table)
        assert THE_MODULE.read_tabular_data(temp_file) == dict_table

    def test_extract_string_list(self):
        """Ensure extract_string_list works as expected"""
        debug.trace(4, "test_extract_string_list()")

        # Check typical cases
        assert THE_MODULE.extract_string_list("  a  b,c") == ['a', 'b', 'c']
        assert THE_MODULE.extract_string_list("a\nb\tc") == ['a', 'b', 'c']
        assert THE_MODULE.extract_string_list("a, b c") == ['a', 'b', 'c']

        # Check special cases
        assert THE_MODULE.extract_string_list("") == []
        assert THE_MODULE.extract_string_list(",") == ['', '']
        assert THE_MODULE.extract_string_list(",", strip_empty=True) == []

    def test_extract_numeric_string_list(self):
        """Verify extract_string_list with numericranges"""
        debug.trace(4, "test_extract_numeric_string_list()")

        # Check typical cases
        self.do_assert(THE_MODULE.extract_string_list("1-4", allow_numeric_ranges=True)
                       == ['1', '2', '3', '4'])
        self.do_assert(THE_MODULE.extract_string_list("a b-c d", allow_numeric_ranges=True)
                       == ['a', 'b-c', 'd'])
        
    def test_is_prime(self):
        """Ensure is_prime works as expected"""
        debug.trace(4, "test_is_prime()")

        first_100_primes = [
            2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37,
            41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83,
            89, 97, 101, 103, 107, 109, 113, 127, 131,
            137, 139, 149, 151, 157, 163, 167, 173, 179,
            181, 191, 193, 197, 199, 211, 223, 227, 229,
            233, 239, 241, 251, 257, 263, 269, 271, 277,
            281, 283, 293, 307, 311, 313, 317, 331, 337,
            347, 349, 353, 359, 367, 373, 379, 383, 389,
            397, 401, 409, 419, 421, 431, 433, 439, 443,
            449, 457, 461, 463, 467, 479, 487, 491, 499,
            503, 509, 521, 523, 541,
        ]

        assert all(THE_MODULE.is_prime(n) for n in first_100_primes)
        assert all((not THE_MODULE.is_prime(n)) for n in range(first_100_primes[-1]) if n not in first_100_primes)

    def test_fibonacci(self):
        """Ensure fibonacci works as expected"""
        debug.trace(4, "test_fibonacci()")
        assert not THE_MODULE.fibonacci(-5)
        assert THE_MODULE.fibonacci(1) == [0]
        assert THE_MODULE.fibonacci(10) == [0, 1, 1, 2, 3, 5, 8]

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

    def test_unzip(self):
        """Ensure unzip works as expected"""
        debug.trace(4, "test_unzip()")
        assert THE_MODULE.unzip(zip([1, 2, 3], ['a', 'b', 'c'])) == [[1, 2, 3], ['a', 'b', 'c']]
        assert THE_MODULE.unzip(zip([], []), 2) == [[], []]
        assert THE_MODULE.unzip(zip(), 4) == [[], [], [], []]
        assert THE_MODULE.unzip(zip(), 4) != [[], []]

    def test_get_current_frame(self):
        """Ensure get_current_frame works as expected"""
        debug.trace(4, "test_get_current_frame()")
        stack = str(THE_MODULE.get_current_frame())
        test_name = system.get_current_function_name()
        assert f'code {test_name}' in stack
        assert repr(__file__) in stack

    def test_eval_expression(self):
        """Ensure eval_expression works as expected"""
        debug.trace(4, "test_eval_expression()")
        assert THE_MODULE.eval_expression("len([123, 321]) == 2")
        assert not THE_MODULE.eval_expression("'helloworld' == 2")

    def test_trace_named_object(self):
        """Ensure trace_named_object works as expected"""
        debug.trace(4, "test_trace_named_object()")
        # With level -1 we ensure that the trace will be printed
        THE_MODULE.trace_named_object(-1, "sys.argv")
        captured = self.get_stderr()
        assert "sys.argv" in captured

    def test_trace_named_objects(self):
        """Ensure trace_named_objects works as expected"""
        debug.trace(4, "test_trace_named_objects()")
        # With level -1 we ensure that the trace will be printed
        THE_MODULE.trace_named_objects(-1, "[len(sys.argv), sys.argv]")
        captured = self.get_stderr()
        assert "len(sys.argv)" in captured
        assert "sys.argv" in captured

    @pytest.mark.skipif(not more_itertools, reason="Unable to load more_itertools")
    def test_exactly1(self):
        """Ensure exactly1 works as expected"""
        debug.trace(4, "test_exactly1()")
        assert THE_MODULE.exactly1([False, False, True])
        assert not THE_MODULE.exactly1([False, True, True])
        assert not THE_MODULE.exactly1([False, False, False])
        assert not THE_MODULE.exactly1([])

    def test_string_diff(self):
        """Ensure string_diff works as expected"""
        debug.trace(4, "test_string_diff()")

        string_one = 'one\ntwo\nthree\nfour'
        string_two = 'one\ntoo\ntree\nfour'
        expected_diff = (
            '  one\n'
            '< two\n'
            '…  ^\n'
            '> too\n'
            '…  ^\n'
            '< three\n'
            '…  -\n'
            '> tree\n'
            '  four\n'
        )

        assert THE_MODULE.string_diff(string_one, string_two) == expected_diff

    def test_elide_string_values(self):
        """Ensure elide_string_values works as expected"""
        debug.trace(4, "test_elide_string_values()")
        hello = "hello"
        assert 'hell...' == THE_MODULE.elide_string_values(hello, max_len=4)

    def test_is_close(self):
        """ensure is_close works as expected"""
        debug.trace(4, "test_is_close()")
        assert     THE_MODULE.is_close(1.0 + 0.999 , 2.0, 0.001)
        assert not THE_MODULE.is_close(1.0 + 0.999 , 2.0, 0.0001)

    def test_get_date_ddmmmyy(self):
        """ensure get_date_ddmmmyy works as expected"""
        debug.trace(4, "test_get_date_ddmmmyy()")
        assert THE_MODULE.get_date_ddmmmyy(datetime.date(2004, 9, 16)) == '16sep04'

    def test_parse_timestamp(self):
        """ensure parse_timestamp works as expected"""
        debug.trace(4, "test_parse_timestamp()")
        ts = datetime.datetime(2004, 9, 16, 12, 30, 25, 123123)
        ts_iso = '2004-09-16T12:30:25.1231234Z'
        ts_iso_2 = '2004-09-16T12:30:25.123123Z'
        parsed_ts = THE_MODULE.parse_timestamp(ts_iso, truncate=True)
        parsed_ts_truncated = THE_MODULE.parse_timestamp(ts_iso_2, truncate=False)
        assert parsed_ts == ts
        assert parsed_ts_truncated == ts

    def test_add_timestamp_diff(self):
        """ensure add_timestamp_diff works as expected"""
        debug.trace(4, "test_add_timestamp_diff()")
        timestamp = "timestamp 2004-09-16T12:30:25.1231234Z"
        file_in = f"{self.temp_file}.in"
        file_out = f"{self.temp_file}.out"
        system.write_file(file_in, timestamp)
        THE_MODULE.add_timestamp_diff(file_in, file_out)
        contents = system.read_file(file_out)
        assert contents == f"{timestamp} [0]\n"

    def test_random_int(self):
        """ensure random_int works as expected"""
        debug.trace(4, "test_random_int()")
        assert 0 <= THE_MODULE.random_int(0,4) <= 4

    def test_random_float(self):
        """ensure random_float works as expected"""
        debug.trace(4, "test_random_float()")
        assert 0 <= THE_MODULE.random_float(0,4.3) < 4.3

    def test_time_function(self):
        """ensure time_function works as expected"""
        debug.trace(4, "test_time_function()")
        ms = THE_MODULE.time_function(time.sleep, 0.25)
        assert math.floor(ms) == 250

    def test_get_class_from_name(self):
        """ensure get_class_from_name works as expected"""
        debug.trace(4, "test_get_class_from_name()")
        result_class = THE_MODULE.get_class_from_name('date', 'datetime')
        assert result_class is datetime.date

    def check_apply_numeric_suffixes(self, text, expect, just_once=False):
        """Helper for test_apply_numeric_suffixes """
        debug.trace_expr(4, text, expect, prefix="in check_apply_numeric_suffixes: ")
        actual = THE_MODULE.apply_numeric_suffixes(text, just_once=just_once)
        assert actual.strip() == expect.strip()
    
    @pytest.mark.xfail                  # TODO: remove xfail
    @parametrize(
        "text, actual",
        ## TODO? ("text, actual")     # see https://github.com/adamchainz/unittest-parametrize
        [ (f"{ONE_MB - 1024 - 1} {ONE_MB} {ONE_MB + 1024}", "1022.999K 1M 1.001M"),
          ("0000", "0K"),                         # special cas
          ## TODO2: ("-00000000-", "-_00000000_?-"),
          ("-00000000-", "-0K-"),                 # esnure nuemric context
          (f"{int(1.5 * ONE_MB)}", "1.5M"),       # make sure not rounded
         ])
    def test_apply_numeric_suffixes(self, text, actual):
        """Check apply_numeric_suffixes"""
        debug.trace(5, f"TestIt.test_apply_numeric_suffixes(); self={self}")
        self.check_apply_numeric_suffixes(text, actual)

    def test_simple_apply_numeric_suffixes(self):
        """Check apply_numeric_suffixes"""
        debug.trace(5, f"TestIt.test_simple_apply_numeric_suffixes(); self={self}")
        self.check_apply_numeric_suffixes("2048 16384", "2K 16K")
        self.check_apply_numeric_suffixes("2048 16384", "2K 16384", just_once=True)

    @pytest.mark.xfail                  # TODO: remove xfail
    def test_stdin_apply_numeric_suffixes(self):
        """Check apply_numeric_suffixes_stdin"""
        debug.trace(5, f"TestIt.test_stdin_apply_numeric_suffixes(); self={self}")
        temp_file = self.create_temp_file("999 1024")
        self.monkeypatch.setattr("sys.stdin", system.open_file(temp_file))
        THE_MODULE.apply_numeric_suffixes_stdin()
        actual = self.get_stdout().strip()
        assert actual == "999 1K"

    @pytest.mark.xfail                  # TODO: remove xfail
    def test_GlobalSetter(self):
        """Ensure that GlobalSetter's changes are temporary"""
        self.patch_trace_level(3)
        unique_mod_3 = unique_mod_4 = []
        def get_unique_moduli(n, l):
            """Returns unique modulus results over N in [0, l-1]"""
            return system.unique_items(i % n for i in range(l))
        unique_mod_4 = get_unique_moduli(4, 13)
        with THE_MODULE.GlobalSetter(debug, 'trace_level', 8):
            unique_mod_3 = get_unique_moduli(3, 13)
        stderr = self.get_stderr()
        assert my_re.search("unique_items.*0, 1, 2", stderr)
        assert not my_re.search("unique_items.*0, 1, 2, 3", stderr)
        assert system.difference(unique_mod_4, unique_mod_3) == [3]

@pytest.mark.skipif(not mezcla_to_standard, reason="Unable to load mezcla_to_standard")
class TestFileToInstance(TestWrapper):
    """Class for testing convert_file_to_instances: external file loading to support mezcla_to_standard"""
    # note: script_module used in argument parsing sanity check (e.g., --help)
    ## TODO3: Add parameters to reduce redundancy in the various test_convert_*_to_instance methods,
    ## such as resource data file and conversion function.
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    expected_instances = [
        EqCall(gh.rename_file, dests=os.rename),
        EqCall(gh.dir_path, dests=os.path.dirname, eq_params={"filename": "p"}),
    ]

    @pytest.mark.xfail                  # TODO: remove xfail
    def check_instances(self, instances):
        """Check that INSTANCES match expected_instances"""
        assert self.expected_instances[0].targets[0].path == instances[0].targets[0].path
        assert self.expected_instances[0].dests[0].path == instances[0].dests[0].path

        assert self.expected_instances[1].targets[0].path == instances[1].targets[0].path
        assert self.expected_instances[1].dests[0].path == instances[1].dests[0].path
        
    
    @pytest.mark.xfail                  # TODO: remove xfail
    def test_convert_json_to_instance(self):
        """ensure convert_json_to_instance works as expected"""
        debug.trace(4, "test_convert_json_to_instance()")

        json_data = gh.form_path(gh.dirname(__file__), "resources", "instances.json")

        instances: list[EqCall] = THE_MODULE.convert_json_to_instance(
            json_data,
            "mezcla.mezcla_to_standard",
            "EqCall",
            mezcla_to_standard.EQCALL_FIELDS,
        )
        self.check_instances(instances)
        
    @pytest.mark.xfail                  # TODO: remove xfail
    def test_convert_yaml_to_instance(self):
        """ensure convert_yaml_to_instance works as expected"""
        debug.trace(4, "test_convert_yaml_to_instance()")

        yaml_data = gh.form_path(gh.dirname(__file__), "resources", "instances.yaml")

        instances: list[EqCall] = THE_MODULE.convert_yaml_to_instance(
            yaml_data,
            "mezcla.mezcla_to_standard",
            "EqCall",
            mezcla_to_standard.EQCALL_FIELDS,
        )
        self.check_instances(instances)

    @pytest.mark.skipif(SKIP_EXPECTED_ERRORS, reason=SKIP_EXPECTED_REASON)
    @pytest.mark.xfail                  # TODO: remove xfail
    def test_convert_csv_to_instance(self):
        """ensure convert_csv_to_instance works as expected"""
        debug.trace(4, "test_convert_csv_to_instance()")

        csv_data = gh.form_path(gh.dirname(__file__), "resources", "instances.csv")

        instances: list[EqCall] = THE_MODULE.convert_csv_to_instance(
            csv_data,
            "mezcla.mezcla_to_standard",
            "EqCall",
            mezcla_to_standard.EQCALL_FIELDS,
        )
        self.check_instances(instances)

    @pytest.mark.xfail                  # TODO: remove xfail
    def test_convert_py_data_to_instance(self):
        """verify convert_py_data_to_instance"""
        debug.trace(4, "test_convert_py_data_to_instance()")

        py_data = gh.form_path(gh.dirname(__file__), "resources", "instances.py-data")

        instances: list[EqCall] = THE_MODULE.convert_python_data_to_instance(
            py_data,
            "mezcla.mezcla_to_standard",
            "EqCall",
            mezcla_to_standard.EQCALL_FIELDS,
        )
        self.check_instances(instances)

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
