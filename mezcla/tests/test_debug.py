#! /usr/bin/env python3
#
# Simple tests for debug.py, based on following:
#     https://stackoverflow.com/questions/16039463/how-to-access-the-py-test-capsys-from-inside-a-test
#
# Notes:
# - This can be run as follows:
#   $ SKIP_ATEXIT=1 PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_debug.py
# - For tests that capture standard error, see
#       https://docs.pytest.org/en/6.2.x/capture.html
# - This uses capsys fixture mentioned in above link.
# - Some tests take extra care to ensure that the output doesn't lead to false positives
#   by error-checking scripts like check_errors.py. For example, test_multiline_assertion
#   uses Spanish for error messages that would otherwise get flagged.
#................................................................................
# TODO:
# - make sure trace_fmt traps all exceptions
#   debug.trace_fmt(1, "fu={fu}", fuu=1)
#                           ^^    ^^^
#

"""Tests for debug module"""

# Standard packages
import sys
from datetime import datetime
import inspect

# Installed packages
import pytest

# Local packages
## TODO: make sure atexit support disabled unless explcitly requested
##   import os; os.environ["SKIP_ATEXIT"] = os.environ.get("SKIP_ATEXIT", "1")
from mezcla import debug
from mezcla.my_regex import my_re
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
import mezcla.glue_helpers as gh
import mezcla.tests.common_module as cm

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                        global module object
#    TestIt.script_module:              path to file
import mezcla.debug as THE_MODULE # pylint: disable=reimported

# Constants
ERROR_FUBAR = "falta fubar"            # spanish for error

#................................................................................
# Classes for testing

class Test_class: 
    """Test class for test_trace_object"""

    age: int = 25
    _debt: int = 5000
    __income: int = 75000
    
    def age_up(self) -> None:
        """Increase age"""
        self.age += 1
        
    def _has_debt(self) -> bool:          # pylint: disable=unused-private-member
        return self._debt > 0

    def __good_income(self) -> bool:      # pylint: disable=unused-private-member
        return self.__income > 50000

class Person:
    """Test class for test_trace_values"""
    
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return f'Person("{self.name}")'

#................................................................................

class TestDebug(TestWrapper):
    """Class for test case definitions"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    stdout_text = None
    stderr_text = None
    expected_stdout_trace = None
    expected_stderr_trace = None

    def setup_simple_trace(self):
        """Common setup for simple tracing"""
        debug.trace(4, f"setup_common(): self={self}")
        self.stdout_text = "hello"
        self.stderr_text = "world"
        self.expected_stdout_trace = self.stdout_text + "\n"
        self.expected_stderr_trace = self.stderr_text + "\n"

    def test_set_level(self):
        """Ensure set_level works as expected"""
        debug.trace(4, f"test_set_level(): self={self}")
        self.patch_trace_level(5)
        assert (THE_MODULE.trace_level == 5) or (not __debug__)
        self.patch_trace_level(6)
        assert THE_MODULE.trace_level == 6 or (not __debug__)

    def test_get_level(self):
        """Ensure get_level works as expected"""
        debug.trace(4, f"test_get_level(): self={self}")
        self.patch_trace_level(5)
        assert THE_MODULE.get_level() == 5
        self.patch_trace_level(6)
        assert THE_MODULE.get_level() == 6

    def test_get_output_timestamps(self):
        """Ensure get_output_timestamps works as expected"""
        debug.trace(4, f"test_get_output_timestamps(): self={self}")
        ## BAD: THE_MODULE.output_timestamps = 'some-test-value'
        ## TODO1: Weed out other potential problems due to lack of mocking.
        self.monkeypatch.setattr(THE_MODULE, "output_timestamps", 'some-test-value')
        assert THE_MODULE.get_output_timestamps() == 'some-test-value'

    def test_set_output_timestamps(self):
        """Ensure set_output_timestamps works as expected"""
        debug.trace(4, f"test_set_output_timestamps(): self={self}")
        ## OLD: THE_MODULE.output_timestamps = False
        self.monkeypatch.setattr(THE_MODULE, "output_timestamps", False)
        THE_MODULE.set_output_timestamps('some-test-value')
        assert THE_MODULE.output_timestamps == 'some-test-value'

    def test_trace(self):
        """Ensure trace works as expected"""
        debug.trace(4, f"test_trace(): self={self}")
        THE_MODULE.output_timestamps = True

        THE_MODULE.trace(-1, ERROR_FUBAR, indentation=' -> ')
        out, err  = self.get_stdout_stderr()
        assert f" -> {ERROR_FUBAR}" in err
        assert not out

        # Test debug_file
        THE_MODULE.debug_file = sys.stdout
        THE_MODULE.trace(-1, 'some text to test debug file')
        out, err  = self.get_stdout_stderr()
        assert 'some text to test debug file' in out
        THE_MODULE.debug_file = None

        THE_MODULE.output_timestamps = False

    @pytest.mark.xfail
    def test_trace_fmtd(self):
        """Ensure trace_fmtd works as expected"""
        debug.trace(4, f"test_trace_fmtd(): self={self}")
        self.patch_trace_level(5)
        
        THE_MODULE.trace_fmtd(4, "trace_{fmtd}", **{"max_len": 8, "fmtd": "formatted"})
        stderr = self.get_stderr()
        assert "trace..." in stderr
        
        self.clear_stderr()
        THE_MODULE.trace_fmtd(4, "trace_{fmtd}", **{"fmtd": "formatted"})
        stderr_2 = self.get_stderr()
        assert "trace_formatted" in stderr_2

        ## TODO3 (re-instate after check reworked):
        ## self.clear_stderr()
        ## THE_MODULE.trace_fmtd(5, "x={x}", x=1, do_whatever=True)
        ## stderr_3 = self.get_stderr()
        ## assert my_re.search(r"Unexpected keyword.*['do_whatever']", stderr_3)

    @pytest.mark.xfail
    def test_trace_object(self):
        """Ensure trace_object works as expected"""
        debug.trace(4, f"test_trace_object(): self={self}")
        obj = Test_class()
        THE_MODULE.trace_object(level=1, obj=obj, show_all=True)
        stderr = self.get_stderr()
        # <class '__main__.Test_class'> 0x7e30e9e54f10: {
        # ... _Test_class__good_income: ('<bound method Test_class.__good_income ...)
        assert my_re.search(r"Test_class[^:]+_good_income:[^:]+bound method", stderr)
        # ... _Test_class__income: 75000
        assert my_re.search(r"Test_class[^:]+_income: 75000", stderr)
        # ... _debt: 5000
        assert my_re.search(r"_debt: 5000", stderr)
        # ... _has_debt: ('<bound method Test_class._has_debt ...)
        assert my_re.search(r"_has_debt:[^:]+bound method", stderr)
        # ... age: 0
        assert my_re.search(r"age: 25", stderr)
        # ... age_up: ('<bound method Test_class.age_up of
        assert my_re.search(r"age_up:[^:]+bound method", stderr)
        
    @pytest.mark.xfail
    def test_negative_trace_object(self):
        """Negative tests for trace_object"""
        debug.trace(4, f"test_negative_trace_object(): self={self}")
        obj = Test_class()
        THE_MODULE.trace_object(level=1, obj=obj,
                                show_all=False, show_methods_etc=False, show_private=False)
        stderr = self.get_stderr()
        assert "__has_debt:" not in stderr
        ## TODO: assert "__income" not in stderr

    def test_trace_values(self):
        """Ensure trace_values works as expected"""
        debug.trace(4, f"test_trace_values(): self={self}")
        # Level -1 is used to ensure that always will run

        collection_test = [
            'foobarerror',
            'some-error',
            'another error',
        ]

        # Test normal usage
        THE_MODULE.trace_values(-1, collection_test)
        err = self.get_stderr()
        for element in collection_test:
            assert f": {element}" in err

        # Test indentation
        THE_MODULE.trace_values(-1, collection_test, indentation=' -> ')
        err = self.get_stderr()
        for i, element in enumerate(collection_test):
            assert f" -> {i}: {element}" in err

        # Test non list collection (string)
        THE_MODULE.trace_values(-1, "somevalue")
        err = self.get_stderr()
        for char in "somevalue":
            assert f": {char}" in err

        # Test non list collection (tuple)
        THE_MODULE.trace_values(-1, 123)
        err = self.get_stderr()
        assert ": 123" in err

        # Test use_repr parameter
        THE_MODULE.trace_values(-1, [Person("Kiran")], use_repr=True)
        err = self.get_stderr()
        assert 'Person("Kiran")' in err

    @pytest.mark.xfail
    def test_simple_trace_expr(self):
        """Make sure trace_expr shows 'expr1=value1; expr2=value2'"""
        debug.trace(4, f"test_simple_trace_expr(): self={self}")
        var1 = 3
        var2 = 6
        THE_MODULE.trace_expr(debug.get_level(), var1, var2)
        err = self.get_stderr()
        assert(my_re.search(r"var1=3; var2=6;?", err))

    @pytest.mark.xfail
    def test_trace_expr_prefix(self):
        """Make sure trace_expr outputs prefix'"""
        debug.trace(4, f"test_trace_expr_prefix(): self={self}")
        var = 4
        THE_MODULE.trace_expr(debug.get_level(), var, prefix="here: ")
        err = self.get_stderr()
        assert(my_re.search(r"here: var=4;?", err))

    @pytest.mark.xfail
    def test_multiline_trace_expr(self):
        """Make sure trace_expr expression resolved when split across lines"""
        debug.trace(4, f"test_multiline_trace_expr(): self={self}")
        var1 = 3
        var2 = 6
        THE_MODULE.trace_expr(debug.get_level(),
                              var1,
                              var2)
        err = self.get_stderr()
        assert(my_re.search(r"var1=3; var2=6;?", err))
        
    @pytest.mark.xfail
    def test_newline_trace_expr(self):
        """Test trace_expr with newline delim"""
        debug.trace(4, f"test_newline_trace_expr(): self={self}")
        var1 = 3
        var2 = 6
        THE_MODULE.trace_expr(debug.get_level(), var1, var2, delim="\n")
        err = self.get_stderr()
        assert(my_re.search(r"var1=3\nvar2=6;?", err))

    def test_trace_expr_max_len(self):
        """Test trace_expr with max_len"""
        # See test_introspection.test_04_max_len for similar check.
        debug.trace(4, f"test_trace_expr_max_len(): self={self}")
        VAR_LEN = 32
        MAX_LEN = 16
        var = "-" * VAR_LEN
        self.patch_trace_level(1)
        THE_MODULE.trace_expr(1, var, max_len=MAX_LEN)
        err = self.get_stderr()
        # note: max_len now applies to value text only (as in test_introspection.test_04_max_len).
        # Previously, trace_expr was incorrectly applying additional clipping.
        assert my_re.search(rf"var='-{{{MAX_LEN}}}\.\.\.'", err)

    @pytest.mark.xfail
    def test_trace_expr_old_introspection(self):
        """Test trace_expr with max_len via old introspection"""
        debug.trace(4, f"test_trace_expr_old_introspection(): self={self}")
        # note: trace_expr had bug where OK up to hard-coded limit (e.g., 1024)
        MAX_LEN = 2048
        var = "-" * (2 * MAX_LEN)
        self.monkeypatch.setattr(THE_MODULE, "use_old_introspection", True)
        result = THE_MODULE.trace_expr(1, var, max_len=MAX_LEN)
        debug.trace(5, f"old: {len(result)=}")
        assert (len(result) > MAX_LEN)
        self.monkeypatch.setattr(THE_MODULE, "use_old_introspection", False)
        result = THE_MODULE.trace_expr(1, var, max_len=MAX_LEN)
        debug.trace(5, f"new: {len(result)=}")
        assert (len(result) > MAX_LEN)

    @pytest.mark.skipif(cm.SKIP_TBD_TESTS, reason=cm.SKIP_TBD_REASON)
    @pytest.mark.xfail
    def test_trace_expr_string(self):
        """Test trace_expr with string values (e.g., with and without max_len)"""
        # Note: this test was added to ensure that the introspection process produces similar
        # results regardless of whether max_len specified.
        debug.trace(4, f"test_trace_expr_string(): self={self}")
        var = "-" * 16
        assert(len(var) < THE_MODULE.max_trace_value_len)
        self.patch_trace_level(1)
        # Check for var='----------------' (n.b., a known failure)
        result = THE_MODULE.trace_expr(1, var)
        assert my_re.search(r"var='----------------'", result)
        result = THE_MODULE.trace_expr(1, var, max_len=256)
        assert my_re.search(r"var='----------------'", result)
        
    @pytest.mark.xfail
    def test_trace_current_context(self):
        """Ensure trace_current_context works as expected"""
        debug.trace(4, f"test_trace_current_context(): self={self}")
        number: int = 9                 # pylint: disable=unused-variable

        ## Note: patched trace level should be 1 higher than level used in call
        ## TODO3: straighten out trace level usage in trace_current_context
        base_trace_level = 4
        self.patch_trace_level(base_trace_level + 1)
        THE_MODULE.trace_current_context(base_trace_level, max_value_len=4096)
        err = self.get_stderr()
        script_filename = gh.basename(__file__)
        # globals: {\n  {value): {\n
        # ... '__name__': 'mezcla.tests.test_debug',
        assert my_re.search(r"__name__[^,]+test_debug", err)
        # ... '__doc__': 'Tests for debug module', 
        assert my_re.search(r"__doc__[^,]+Tests for debug", err)
        # ... '__file__': '/home/joe/Mezcla/mezcla/tests/test_debug.py',
        assert my_re.search(fr"__file__[^,]+{script_filename}", err)
        # locals: {\n  {value): {\n
        # ...  'self': <mezcla.tests.test_debug.TestDebug testMethod=test_trace_current_context>,
        assert my_re.search(r"self[^,]+testMethod=test_trace_current_context", err)
        # ... 'number': 9}
        assert my_re.search(r"number[^,]+ 9", err)

    @pytest.mark.xfail
    def test_trace_exception(self):
        """Ensure trace_exception works as expected"""
        # Note: This raised an exception and then verifies traced properly,
        # with "Exception during" reflecting custom error in trace_exception.
        debug.trace(4, f"test_trace_exception(): self={self}")
        self.patch_trace_level(4)
        with pytest.raises(RuntimeError):
            raise RuntimeError("debug.trace failed")
        THE_MODULE.trace_exception(4, "debug.trace")
        err = self.get_stderr()
        assert "Exception during debug.trace" in err
        
    @pytest.mark.xfail
    def test_raise_exception(self):
        """Check that raise_exception does so unless debug level too high"""
        debug.trace(4, f"test_raise_exception(): self={self}")
        self.patch_trace_level(3)
        with pytest.raises(Exception):
            THE_MODULE.raise_exception(3)
        THE_MODULE.raise_exception(4)

    @pytest.mark.xfail
    def test_assertion(self):
        """Ensure assertion works as expected"""
        debug.trace(4, f"test_assertion(): self={self}")

        # Set trace level to avoid details (e.g., false positive with check_errors.py)
        ## TODO3: add level to get_stderr, etc.
        self.patch_trace_level(3)
        
        # Doesn't print in stderr
        THE_MODULE.assertion((2 + 2 + 1) == 5)
        err = self.get_stderr()
        assert 'failed' not in err
        
        # Prints assertion failed in stderr
        THE_MODULE.assertion((2 + 2) == 5)
        err = self.get_stderr()
        assert "failed" in err
        assert "(2 + 2) == 5" in err

        # Just traces the variable expression as is
        gpu = None
        THE_MODULE.assertion(gpu)
        err = self.get_stderr()
        ## ex: Assertion failed: gpu=None\n (at <ipython-input-14-e3c30214f890>:1)
        assert("Assertion failed: gpu (at" in err)

        
    @pytest.mark.xfail
    def test_multiline_assertion(self):
        """Make sure assertion expression split across lines resolved"""
        # Note: issue uses the Spanish equivalent of "Assertion failed" in order to
        # avoid false positives with check_errors.py.
        debug.trace(4, f"test_multiline_assertion(): self={self}")
        THE_MODULE.assertion(2 +
                             2 ==
                             5, issue="Afirmación fallida")
        err = self.get_stderr()
        self.do_assert(my_re.search(r"2.*\+.*2.*==.*5", err,
                                    flags=my_re.DOTALL|my_re.MULTILINE))

    def test_val(self):
        """Ensure val works as expected"""
        debug.trace(4, f"test_val(): self={self}")
        test_value = 22
        self.patch_trace_level(5)
        level5_value = THE_MODULE.val(5, test_value)
        self.patch_trace_level(0)
        level0_value = THE_MODULE.val(1, test_value)
        assert level5_value == test_value
        assert level0_value is None

    def test_code(self):
        """Ensure code works as expected"""
        debug.trace(4, f"test_code(): self={self}")
        ## TODO: debug.assertion(debug_level, debug.code(debug_level, lambda: (8 / 0 != 0.0)))
        count = 0
        def increment():
            """Increase counter"""
            nonlocal count
            count += 1
        self.patch_trace_level(4)
        THE_MODULE.code(4, lambda: increment)
        assert(count == 0)

    @pytest.mark.xfail
    def test_debug_print(self):
        """Ensure debug_print works as expected"""
        debug.trace(4, f"test_debug_print(): self={self}")
        self.monkeypatch.setattr("mezcla.debug.output_timestamps", True)

        THE_MODULE.debug_print(ERROR_FUBAR, -1)
        out, err  = self.get_stdout_stderr()
        assert ERROR_FUBAR in err
        assert not out

        # Test debug_file
        self.monkeypatch.setattr("mezcla.debug.debug_file", sys.stdout)
        THE_MODULE.debug_print('some text to test debug file', -1)
        out, err  = self.get_stdout_stderr()
        assert 'some text to test debug file' in out

    @pytest.mark.xfail
    def test_timestamp(self):
        """Ensure timestamp works as expected"""
        debug.trace(4, f"test_timestamp(): self={self}")
        debug_timestamp = THE_MODULE.timestamp()
        # example: 2025-02-02 01:23:27.451258
        assert my_re.search(r"\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d", debug_timestamp)

    def test_debugging(self):
        """Ensure debugging works as expected"""
        debug.trace(4, f"test_debugging(): self={self}")
        self.patch_trace_level(4)
        assert THE_MODULE.debugging(2)
        assert THE_MODULE.debugging(4)
        assert not THE_MODULE.debugging(6)

    def test_detailed_debugging(self):
        """Ensure detailed_debugging works as expected"""
        debug.trace(4, f"test_detailed_debugging(): self={self}")
        self.patch_trace_level(2)
        assert not THE_MODULE.detailed_debugging()
        self.patch_trace_level(4)
        assert THE_MODULE.detailed_debugging()
        self.patch_trace_level(6)
        assert THE_MODULE.detailed_debugging()

    def test_verbose_debugging(self):
        """Ensure verbose_debugging works as expected"""
        debug.trace(4, f"test_verbose_debugging(): self={self}")
        self.patch_trace_level(2)
        assert not THE_MODULE.verbose_debugging()
        self.patch_trace_level(5)
        assert THE_MODULE.verbose_debugging()
        self.patch_trace_level(7)
        assert THE_MODULE.verbose_debugging()

    def test_format_value(self):
        """Ensure format_value works as expected"""
        debug.trace(4, f"test_format_value(): self={self}")
        assert(THE_MODULE.format_value("\n    ", max_len=5) == "\\n   ...")
        assert(THE_MODULE.format_value("123456", max_len=7) == "123456")
        assert(THE_MODULE.format_value("123456", max_len=6) == "123456")
        assert(THE_MODULE.format_value("123456", max_len=5) == "12345...")
        assert(THE_MODULE.format_value("123456", max_len=4) == "1234...")
        assert(THE_MODULE.format_value("123456", max_len=3) == "123...")
        assert(THE_MODULE.format_value("123456", max_len=2) == "12...")
        assert(THE_MODULE.format_value("123456", max_len=1) == "1...")
        assert(THE_MODULE.format_value("123456", max_len=0) == "...")

    def test_format_value_strict(self):
        """Ensure format_value w/ strict works as expected"""
        debug.trace(4, f"test_format_value(): self={self}")
        def format_value_strict(value, max_len):
            """Invokes debug.format_value with strict option"""
            return THE_MODULE.format_value(value, max_len=max_len,
                                    strict=True)
        assert(format_value_strict("\n    ", max_len=5) == "\\n...")
        assert(format_value_strict("123456", max_len=7) == "123456")
        assert(format_value_strict("123456", max_len=6) == "123456")
        assert(format_value_strict("123456", max_len=5) == "12...")
        assert(format_value_strict("123456", max_len=4) == "1...")
        assert(format_value_strict("123456", max_len=3) == "...")
        assert(format_value_strict("123456", max_len=2) == "..")
        assert(format_value_strict("123456", max_len=1) == ".")
        assert(format_value_strict("123456", max_len=0) == "")

    def test_xor(self):
        """Ensure xor works as expected"""
        debug.trace(4, f"test_xor(): self={self}")
        self.patch_trace_level(7)
        # Test the XOR table
        assert not THE_MODULE.xor(0, 0.0)
        assert THE_MODULE.xor(0, 1.0)
        assert THE_MODULE.xor(1, 0.0)
        assert not THE_MODULE.xor(1, 1.0)
        # Test stderr
        err = self.get_stderr()
        assert "xor" in err

    def test_xor3(self):
        """Ensure xor3 works as expected"""
        debug.trace(4, f"test_xor3(): self={self}")
        self.patch_trace_level(7)
        # Test the XOR table
        assert not THE_MODULE.xor3(0, 0, 0)
        assert THE_MODULE.xor3(0, 0, 1)
        assert THE_MODULE.xor3(0, 1, 0)
        assert not THE_MODULE.xor3(0, 1, 1)
        assert THE_MODULE.xor3(1, 0, 0)
        assert not THE_MODULE.xor3(1, 0, 1)
        assert not THE_MODULE.xor3(1, 1, 0)
        assert not THE_MODULE.xor3(1, 1, 1)
        # Test stderr
        err = self.get_stderr()
        assert "xor3" in err

    @pytest.mark.xfail
    def test_init_logging(self):
        """Ensure init_logging works as expected"""
        debug.trace(4, f"test_init_logging(): self={self}")
        
        # Test init_logging with env not GLOBAL_LOGGING
        self.monkeypatch.setenv("GLOBAL_LOGGING", 'False')
        THE_MODULE.init_logging()
        stderr_1 = self.get_stderr()
        assert "init_logging" in stderr_1
        assert "Setting root logger level " not in stderr_1
        
        # Test init_logging with env GLOBAL_LOGGING and detailed_debugging()
        self.clear_stdout_stderr()
        self.monkeypatch.setenv("GLOBAL_LOGGING", 'True')
        THE_MODULE.init_logging()
        new_level = THE_MODULE.logging.root.getEffectiveLevel()
        stderr_2 = self.get_stderr()
        assert "init_logging" in stderr_2
        assert "Setting root logger level " in stderr_2
        assert new_level == 10
        
        # Test init_logging with env GLOBAL_LOGGING and not detailed_debugging()
        self.clear_stdout_stderr()
        self.monkeypatch.setenv("GLOBAL_LOGGING", 'True')
        self.monkeypatch.setattr("mezcla.debug.trace_level", 3)
        THE_MODULE.init_logging()
        new_level = THE_MODULE.logging.root.getEffectiveLevel()
        assert new_level == 20

    @pytest.mark.xfail
    def test_profile_function(self):
        """Ensure profile_function works as expected"""
        debug.trace(4, f"test_profile_function(): self={self}")
        self.monkeypatch.setattr("mezcla.debug.trace_level", 6)
        frame = inspect.currentframe()
        
        # test function call
        THE_MODULE.profile_function(frame, 'call', 'arg') 
        stderr = self.get_stderr()
        assert "in: mezcla.tests.test_debug:test_profile_function(arg);" in stderr
        
        # test function return
        self.clear_stderr()
        THE_MODULE.profile_function(frame, 'return', 'result') 
        stderr = self.get_stderr()
        assert "out: mezcla.tests.test_debug:test_profile_function => result" in stderr
        
    @pytest.mark.xfail
    def test_reference_var(self):
        """Ensure reference_var works as expected"""
        debug.trace(4, f"test_reference_var(): self={self}")
        self.monkeypatch.setattr("mezcla.debug.trace_level", 10)
        THE_MODULE.reference_var("\'a\'")

        stderr = self.get_stderr()
        assert 'reference_var("\'a\'",)' in stderr

    def test_clip_value(self):
        """Ensure clip_value works as expected"""
        debug.trace(4, f"test_clip_value(): self={self}")
        assert THE_MODULE.clip_value('helloworld', 5) == 'hello...'
        assert THE_MODULE.clip_value('12345678910111213141516', 7) == '1234567...'

    @pytest.mark.xfail
    def test_read_line(self):
        """Ensure read_line works as expected"""
        debug.trace(4, f"test_read_line(): self={self}")
        content = cm.fix_indent(
            """
            line1
            line2
            line3
            """).lstrip("\n")
        
        temp_file = self.get_temp_file()
        system.write_file(temp_file, content)
        line_1 = THE_MODULE.read_line(temp_file, 1)
        line_2 = THE_MODULE.read_line(temp_file, 2)
        line_3 = THE_MODULE.read_line(temp_file, 3)
        assert my_re.search(fr"{line_1}.*{line_2}.*{line_3}", content)

    @pytest.mark.xfail
    def test_debug_init(self):
        """Ensure debug_init works as expected"""
        debug.trace(4, f"test_debug_init(): self={self}")
        self.patch_trace_level(6)
        temp_debug_filename = self.temp_file + ".debug.log"
        self.monkeypatch.setenv("DEBUG_FILE", temp_debug_filename)
        self.monkeypatch.setenv("ENABLE_LOGGING", "True")
        # NOTE: Setting MONITOR_FUNCTIONS to True breaks tests on windows
        today = str(datetime.now()).split(' ', maxsplit=1)[0]
        THE_MODULE.debug_init(force=True)
        # TODO3: why is _test*err.txt being output?
        err = self.get_stderr()
        err_file = system.form_path(gh.dirname(__file__),
                                    "_test_debug_init-err.txt")
        system.write_file(err_file, err)

        ## TODO2: use regex pattern matching to be less brittle
        assert f"debug_filename={temp_debug_filename}" in err
        assert f"debug_file=<_io.TextIOWrapper name=\'{temp_debug_filename}\'" in err
        assert f"[{THE_MODULE.__file__}] loaded at {today}" in err
        assert "Setting logger level to 10" in err
        assert f"DEBUG_FILE: {temp_debug_filename}" in err
        assert "ENABLE_LOGGING: True" in err

    @pytest.mark.xfail
    def test_display_ending_time_etc(self):
        """Ensure display_ending_time_etc works as expected"""
        debug.trace(4, f"test_display_ending_time_etc(): self={self}")
        self.monkeypatch.setenv("SKIP_ATEXIT", "False")
        self.monkeypatch.delenv("DEBUG_FILE", raising=False)
        temp_debug_file = system.open_file(self.temp_file + ".debug.log",
                                           mode="w")
        assert(not temp_debug_file.closed)
        self.monkeypatch.setattr("mezcla.debug.debug_file", temp_debug_file)
        # note: display_ending_time_etc needs to be extracted from debug_init
        THE_MODULE.display_ending_time_etc()
        # TODO3: why is _test*err.txt being output?
        err = self.get_stderr()
        err_file = system.form_path(gh.dirname(__file__),
                                    "_test_display_ending_time_etc-err.txt")
        system.write_file(err_file, err)
        assert(temp_debug_file.closed)

    def test_visible_simple_trace(self):
        """Make sure level-1 trace outputs to stderr"""
        debug.trace(4, f"test_visible_simple_trace(): self={self}")
        self.setup_simple_trace()
        if not __debug__:
            self.expected_stderr_trace = ""
        pre_out, pre_err = self.get_stdout_stderr()
        self.patch_trace_level(4)
        print(self.stdout_text)
        THE_MODULE.trace(3, self.stderr_text)
        out, err = self.get_stdout_stderr()
        assert(self.expected_stdout_trace in out)
        assert(self.expected_stderr_trace in err)
        THE_MODULE.trace_expr(6, (pre_out, pre_err), (out, err))

    def test_hidden_simple_trace(self):
        """Make sure level-N+1 trace doesn't output to stderr"""
        debug.trace(4, f"test_hidden_simple_trace(): self={self}")
        self.setup_simple_trace()
        ## TEST
        ## capsys.stop_capturing()
        ## capsys.start_capturing()
        pre_out, pre_err = self.get_stdout_stderr()
        self.expected_stderr_trace = ""
        self.patch_trace_level(0)
        print(self.stdout_text)
        THE_MODULE.trace(1, self.stderr_text)
        out, err = self.get_stdout_stderr()
        assert self.expected_stdout_trace in out
        assert self.expected_stderr_trace in err
        THE_MODULE.trace_expr(6, (pre_out, pre_err), (out, err))

    @pytest.mark.xfail
    def test_do_print(self):
        """Verifies do_print options"""
        out = THE_MODULE.do_print("1234567890", max_len=4, end=";")
        expected = "1...;"
        assert out == expected
        assert expected in self.get_stderr()


class TestDebug2(TestWrapper):
    """Another Class for test case definitions"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    
    def test_xor3_again(self):
        """Test xor3 again"""
        debug.trace(4, f"test_xor3_again(): self={self}")
        self.do_assert(debug.xor3(True, False, False))
        self.do_assert(not debug.xor3(True, True, True))
        self.do_assert(not debug.xor3(False, False, False))

    @pytest.mark.xfail
    def test_level(self):
        """"Make sure set_level honored (provided __debug__)"""
        debug.trace(4, f"test_level(): self={self}")
        old_level = debug.get_level()
        new_level = old_level + 1
        self.patch_trace_level(new_level)
        expected_level = (new_level if __debug__ else old_level)
        level_set_ok = (debug.get_level() == expected_level)
        self.do_assert(level_set_ok)

    @pytest.mark.xfail
    def test_trace_exceptions(self):
        """"Make sure debug.trace doesn't produce exceptions"""
        debug.trace(4, f"test_trace_exceptions(): self={self}")
        self.patch_trace_level(1)
        no_exception = True
        try:
            THE_MODULE.trace(1, 666)
        except:
            no_exception = False
            debug.trace_exception(5, "test_trace_exceptions")
        self.do_assert(no_exception)

    def test_debug_wrapper_class(self):
        """Verify DebugWrapper class exists and is the backing instance for module-level API"""
        debug.trace(4, f"test_debug_wrapper_class(): self={self}")
        self.do_assert(__debug__ == hasattr(THE_MODULE, 'DebugWrapper'))
        self.do_assert(__debug__ == hasattr(THE_MODULE, '_debug'))
        if __debug__:
            self.do_assert(isinstance(THE_MODULE._debug, THE_MODULE.DebugWrapper))

#------------------------------------------------------------------------

class TestDebugWrapper(TestWrapper):                # pylint: disable=protected-access
    """Tests for DebugWrapper class methods accessed via THE_MODULE._debug.
    Verifies that the OO API works correctly and shares state with the
    module-level functional API."""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    def test_dw_instance(self):
        """DebugWrapper class and _debug global instance exist with correct type"""
        debug.trace(4, f"test_dw_instance(): self={self}")
        self.do_assert(__debug__ == hasattr(THE_MODULE, 'DebugWrapper'))
        self.do_assert(__debug__ == hasattr(THE_MODULE, '_debug'))
        if __debug__:
            self.do_assert(isinstance(THE_MODULE._debug, THE_MODULE.DebugWrapper))
            self.do_assert(inspect.isclass(THE_MODULE.DebugWrapper))

    def test_dw_new_instance(self):
        """Ensure a separate DebugWrapper instance can be created independently"""
        debug.trace(4, f"test_dw_new_instance(): self={self}")
        if not __debug__:
            return
        new_debug = THE_MODULE.DebugWrapper()
        assert hasattr(new_debug, 'trace')
        assert hasattr(new_debug, 'assertion')
        assert hasattr(new_debug, 'trace_expr')
        assert callable(new_debug.trace)

    def test_dw_module_funcs_delegate(self):
        """Ensure module-level functions delegate to _debug instance methods"""
        debug.trace(4, f"test_dw_module_funcs_delegate(): self={self}")
        if not __debug__:
            return
        # Module-level wrappers should produce identical results to _debug methods
        self.patch_trace_level(5)
        assert THE_MODULE.get_level() == THE_MODULE._debug.get_level()
        assert THE_MODULE.val(5, 42) == THE_MODULE._debug.val(5, 42)
        assert THE_MODULE.val(6, 42) == THE_MODULE._debug.val(6, 42)

    def test_dw_set_get_level(self):
        """_debug.set_level/_debug.get_level share state with module-level wrappers"""
        debug.trace(4, f"test_dw_set_get_level(): self={self}")
        if not __debug__:
            return
        old_level = THE_MODULE._debug.get_level()
        # OO setter reflected by module-level getter
        THE_MODULE._debug.set_level(old_level + 1)
        self.do_assert(THE_MODULE.get_level() == old_level + 1)
        # Module-level setter reflected by OO getter
        THE_MODULE.set_level(old_level + 2)
        self.do_assert(THE_MODULE._debug.get_level() == old_level + 2)
        THE_MODULE._debug.set_level(old_level)

    def test_dw_output_timestamps(self):
        """_debug get/set_output_timestamps share state with module global"""
        debug.trace(4, f"test_dw_output_timestamps(): self={self}")
        if not __debug__:
            return
        orig = THE_MODULE.output_timestamps
        THE_MODULE._debug.set_output_timestamps(True)
        self.do_assert(THE_MODULE.output_timestamps is True)
        self.do_assert(THE_MODULE._debug.get_output_timestamps() is True)
        THE_MODULE._debug.set_output_timestamps(orig)

    def test_dw_do_print(self):
        """_debug.do_print outputs to stderr and respects max_len"""
        debug.trace(4, f"test_dw_do_print(): self={self}")
        if not __debug__:
            return
        THE_MODULE._debug.do_print("oo-hello")
        err = self.get_stderr()
        self.do_assert("oo-hello" in err)
        # max_len truncation: "1234567890" with max_len=4 => "1..."
        out = THE_MODULE._debug.do_print("1234567890", max_len=4)
        self.do_assert("1..." in out)

    def test_dw_trace(self):
        """_debug.trace outputs at the right level and is silent below it"""
        debug.trace(4, f"test_dw_trace(): self={self}")
        if not __debug__:
            return
        self.patch_trace_level(3)
        THE_MODULE._debug.trace(3, "oo-visible-trace")
        err = self.get_stderr()
        self.do_assert("oo-visible-trace" in err)
        self.clear_stderr()
        THE_MODULE._debug.trace(4, "oo-hidden-trace")
        err = self.get_stderr()
        self.do_assert("oo-hidden-trace" not in err)

    @pytest.mark.xfail
    def test_dw_trace_fmtd(self):
        """_debug.trace_fmtd formats text with kwargs and respects max_len"""
        debug.trace(4, f"test_dw_trace_fmtd(): self={self}")
        if not __debug__:
            return
        self.patch_trace_level(5)
        THE_MODULE._debug.trace_fmtd(4, "oo-val={v}", v="fmtd-test")
        err = self.get_stderr()
        self.do_assert("oo-val=fmtd-test" in err)
        self.clear_stderr()
        THE_MODULE._debug.trace_fmtd(4, "oo-{txt}", txt="formatted", max_len=8)
        err = self.get_stderr()
        self.do_assert("oo-..." in err)

    @pytest.mark.xfail
    def test_dw_trace_expr(self):
        """_debug.trace_expr resolves expression names via introspection"""
        debug.trace(4, f"test_dw_trace_expr(): self={self}")
        if not __debug__:
            return
        self.patch_trace_level(3)
        oo_var = 77
        THE_MODULE._debug.trace_expr(3, oo_var)
        err = self.get_stderr()
        self.do_assert(my_re.search(r"oo_var=77;?", err))

    def test_dw_trace_values(self):
        """_debug.trace_values outputs each element of a collection"""
        debug.trace(4, f"test_dw_trace_values(): self={self}")
        if not __debug__:
            return
        THE_MODULE._debug.trace_values(-1, ["oo-alpha", "oo-beta"])
        err = self.get_stderr()
        self.do_assert(": oo-alpha" in err)
        self.do_assert(": oo-beta" in err)

    def test_dw_trace_frame(self):
        """_debug.trace_frame outputs function name and file for a given frame"""
        debug.trace(4, f"test_dw_trace_frame(): self={self}")
        if not __debug__:
            return
        frame = inspect.currentframe()
        self.patch_trace_level(5)
        THE_MODULE._debug.trace_frame(4, frame, label="oo-frame")
        err = self.get_stderr()
        self.do_assert("oo-frame" in err)
        self.do_assert("test_dw_trace_frame" in err)

    def test_dw_trace_stack(self):
        """_debug.trace_stack outputs a stack trace including the caller"""
        debug.trace(4, f"test_dw_trace_stack(): self={self}")
        if not __debug__:
            return
        self.patch_trace_level(5)
        THE_MODULE._debug.trace_stack(5)
        err = self.get_stderr()
        self.do_assert("test_dw_trace_stack" in err)

    def test_dw_trace_exception(self):
        """_debug.trace_exception outputs exception info"""
        debug.trace(4, f"test_dw_trace_exception(): self={self}")
        if not __debug__:
            return
        self.patch_trace_level(5)
        try:
            raise ValueError("oo-exc-test")
        except:                             # pylint: disable=bare-except
            THE_MODULE._debug.trace_exception(4, "oo-task")
        err = self.get_stderr()
        self.do_assert("Exception during oo-task" in err)

    @pytest.mark.xfail
    def test_dw_raise_exception(self):
        """_debug.raise_exception re-raises at level; no-op when level not met"""
        debug.trace(4, f"test_dw_raise_exception(): self={self}")
        if not __debug__:
            return
        self.patch_trace_level(1)
        with pytest.raises(Exception):
            THE_MODULE._debug.raise_exception(1)
        # level above trace_level: should be a no-op
        THE_MODULE._debug.raise_exception(10)

    @pytest.mark.xfail
    def test_dw_assertion(self):
        """_debug.assertion warns on failure but not on success"""
        debug.trace(4, f"test_dw_assertion(): self={self}")
        if not __debug__:
            return
        THE_MODULE._debug.assertion(1 == 1)
        err = self.get_stderr()
        self.do_assert("failed" not in err)
        THE_MODULE._debug.assertion(1 == 2)
        err = self.get_stderr()
        self.do_assert("Assertion failed" in err)

    def test_dw_val(self):
        """_debug.val returns value at level, None when level not met"""
        debug.trace(4, f"test_dw_val(): self={self}")
        if not __debug__:
            return
        self.patch_trace_level(5)
        self.do_assert(THE_MODULE._debug.val(5, 55) == 55)
        self.patch_trace_level(0)
        self.do_assert(THE_MODULE._debug.val(1, 55) is None)

    def test_dw_code(self):
        """_debug.code executes function at level, skips it below level"""
        debug.trace(4, f"test_dw_code(): self={self}")
        if not __debug__:
            return
        count = [0]
        def increment():
            """Increment counter"""
            count[0] += 1
        self.patch_trace_level(4)
        THE_MODULE._debug.code(4, increment)
        self.do_assert(count[0] == 1)
        THE_MODULE._debug.code(5, increment)   # level 5 > trace_level 4: skipped
        self.do_assert(count[0] == 1)

    def test_dw_call(self):
        """_debug.call invokes function with args at level, returns None otherwise"""
        debug.trace(4, f"test_dw_call(): self={self}")
        if not __debug__:
            return
        self.patch_trace_level(4)
        result = THE_MODULE._debug.call(4, lambda x: x * 3, 7)
        self.do_assert(result == 21)
        self.patch_trace_level(0)
        result = THE_MODULE._debug.call(1, lambda x: x * 3, 7)
        self.do_assert(result is None)

    def test_dw_get_elapsed_time(self):
        """_debug.get_elapsed_time returns a non-negative float"""
        debug.trace(4, f"test_dw_get_elapsed_time(): self={self}")
        if not __debug__:
            return
        elapsed = THE_MODULE._debug.get_elapsed_time()
        self.do_assert(isinstance(elapsed, float))
        self.do_assert(elapsed >= 0)

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
