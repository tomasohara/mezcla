#! /usr/bin/env python
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
from mezcla.unittest_wrapper import TestWrapper
import mezcla.glue_helpers as gh

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                        global module object
#    TestIt.script_module:              path to file
import mezcla.debug as THE_MODULE # pylint: disable=reimported

# Environment options
# Note: These are just intended for internal options, not for end users.
# It also allows for enabling options in one place.
#
TEST_TBD = system.getenv_bool("TEST_TBD", False,
                              description="Test features to be designed: TBD")


class TestDebug(TestWrapper):
    """Class for test case definitions"""
    # Note: TestWrapper not used due to conflict with capsys
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
        THE_MODULE.set_level(5)
        assert THE_MODULE.trace_level == 5

    def test_get_level(self):
        """Ensure get_level works as expected"""
        debug.trace(4, f"test_get_level(): self={self}")
        THE_MODULE.trace_level = 5
        assert THE_MODULE.get_level() == 5

    def test_get_output_timestamps(self):
        """Ensure get_output_timestamps works as expected"""
        debug.trace(4, f"test_get_output_timestamps(): self={self}")
        THE_MODULE.output_timestamps = 'some-test-value'
        assert THE_MODULE.get_output_timestamps() == 'some-test-value'

    def test_set_output_timestamps(self):
        """Ensure set_output_timestamps works as expected"""
        debug.trace(4, f"test_set_output_timestamps(): self={self}")
        THE_MODULE.output_timestamps = False
        THE_MODULE.set_output_timestamps('some-test-value')
        assert THE_MODULE.output_timestamps == 'some-test-value'

    def test_trace(self):
        """Ensure trace works as expected"""
        debug.trace(4, f"test_trace(): self={self}")
        THE_MODULE.output_timestamps = True

        THE_MODULE.trace(-1, 'error foobar', indentation=' -> ')
        out,err  = self.get_stdout_stderr()
        assert " -> error foobar" in err
        assert not out

        # Test debug_file
        THE_MODULE.debug_file = sys.stdout
        THE_MODULE.trace(-1, 'some text to test debug file')
        out,err  = self.get_stdout_stderr()
        assert 'some text to test debug file' in out
        THE_MODULE.debug_file = None

        THE_MODULE.output_timestamps = False

    @pytest.mark.xfail
    def test_trace_fmtd(self):
        """Ensure trace_fmtd works as expected"""
        debug.trace(4, f"test_trace_fmtd(): self={self}")
        
        THE_MODULE.trace_fmtd(4, "trace_{fmtd}", **{"max_len": 5, "fmtd": "formatted"})
        stderr = self.get_stderr()
        assert "trace_forma..." in stderr
        
        self.clear_stderr()
        THE_MODULE.trace_fmtd(4, "trace_{fmtd}", **{"fmtd": "formatted"})
        stderr_2 = self.get_stderr()
        assert "trace_formatted" in stderr_2

    @pytest.mark.xfail
    def test_trace_object(self):
        """Ensure trace_object works as expected"""
        debug.trace(4, f"test_trace_object(): self={self}")
        class Test_class: 
            """Test class"""
            alive: bool = True
            age: int = 0
            __debt: int = 0
            
            def age_up(self) -> None:
                """Increase age"""
                self.age += 1
            
            def __has_debt(self) -> bool:
                return self.__debt > 0
                
        obj = Test_class()
        THE_MODULE.trace_object(level=1, obj=obj, show_all=True)
        err = self.get_stderr()
        assert "Test_class__debt: 0" in err
        assert "Test_class__has_debt:" in err
        assert "age_up:"
        assert "age: 0" in err
        assert "age_up: " in err
        
        self.clear_stdout_stderr()
        THE_MODULE.trace_object(level=1, obj=Test_class(), show_all=False, show_methods_etc=False, show_private=False)
        err_2 = self.get_stderr()
        assert "Test_class__has_debt:" not in err_2
        assert "Test_class__debt: 0" in err_2

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
        class Person:
            """Test class"""
            def __init__(self, name):
                self.name = name
            def __repr__(self):
                return f'Person("{self.name}")'
        THE_MODULE.trace_values(-1, [Person("Kiran")], use_repr=True)
        err = self.get_stderr()
        assert 'Person("Kiran")' in err

    def test_trace_expr(self):
        """Make sure trace_expr shows 'expr1=value1; expr2=value2'"""
        var1 = 3
        var2 = 6
        THE_MODULE.trace_expr(debug.get_level(), var1, var2)
        err = self.get_stderr()
        assert "var1=3;var2=6" in my_re.sub(r"\s+", "", err)

    @pytest.mark.xfail
    @pytest.mark.skipif(not TEST_TBD, reason="Ignoring feature to be designed")
    def test_trace_expr_expression(self):
        """Make sure trace_expr expression resolved when split across lines"""
        var1 = 3
        var2 = 6
        THE_MODULE.trace_expr(debug.get_level(),
                              var1,
                              var2)
        err = self.get_stderr()
        assert "var1=3.*var2=6" in my_re.sub(r"\s+", "", err)
        
    @pytest.mark.xfail
    def test_trace_current_context(self):
        """Ensure trace_current_context works as expected"""
        debug.trace(4, f"test_trace_current_context(): self={self}")
        number: int = 9
        THE_MODULE.trace_current_context(4)
        err = self.get_stderr()
        assert "test_debug.TestDebug testMethod=test_trace_current_context" in err  # name of current function
        assert "\'number\': 9" in err   # variable created in current function
        assert "\'__name__\': \'test_debug\'" in err    # name of file
        assert "\'__doc__\': \'Tests for debug module\'" in err # docstring of file
        assert __file__ in err  # path of file

    @pytest.mark.xfail
    def test_trace_exception(self):
        """Ensure trace_exception works as expected"""
        debug.trace(4, f"test_trace_exception(): self={self}")
        with pytest.raises(RuntimeError):
            raise RuntimeError("debug.trace failed")
        THE_MODULE.trace_exception(4, "debug.trace")
        err = self.get_stderr()
        assert "Exception during debug.trace" in err
        
    @pytest.mark.xfail
    def test_raise_exception(self):
        """Ensure raise_exception works as expected"""
        debug.trace(4, f"test_raise_exception(): self={self}")
        with pytest.raises(Exception):
            THE_MODULE.raise_exception()
        THE_MODULE.raise_exception(10)

    def test_assertion(self):
        """Ensure assertion works as expected"""
        debug.trace(4, f"test_assertion(): self={self}")
        # Not prints in stderr
        THE_MODULE.assertion((2 + 2 + 1) == 5)
        err = self.get_stderr()
        assert 'failed' not in err
        # Prints assertion failed in stderr
        THE_MODULE.assertion((2 + 2) == 5)
        err = self.get_stderr()
        assert "failed" in err
        assert "(2 + 2) == 5" in err

    @pytest.mark.xfail
    @pytest.mark.skipif(not TEST_TBD, reason="Ignoring feature to be designed")
    def test_assertion_expression(self):
        """Make sure assertion expression split across lines resolved"""
        debug.trace(4, f"test_assertion_expression(): self={self}")
        THE_MODULE.assertion(2 +
                             2 ==
                             5)
        err = self.get_stderr()
        assert "2+2==5" in my_re.sub(r"\s+", "", err)

    def test_val(self):
        """Ensure val works as expected"""
        debug.trace(4, f"test_val(): self={self}")
        save_trace_level = THE_MODULE.get_level()
        test_value = 22
        THE_MODULE.set_level(5)
        level5_value = THE_MODULE.val(5, test_value)
        THE_MODULE.set_level(0)
        level0_value = THE_MODULE.val(1, test_value)
        THE_MODULE.set_level(save_trace_level)
        assert level5_value == test_value
        assert level0_value is None

    def test_code(self):
        """Ensure code works as expected"""
        debug.trace(4, f"test_code(): self={self}")
        ## TODO: debug.assertion(debug_level, debug.code(debug_level, lambda: (8 / 0 != 0.0)))
        save_trace_level = THE_MODULE.get_level()
        count = 0
        def increment():
            """Increase counter"""
            nonlocal count
            count += 1
        THE_MODULE.set_level(4)
        THE_MODULE.code(4, lambda: increment)
        THE_MODULE.set_level(save_trace_level)
        assert(count == 0)

    @pytest.mark.xfail
    def test_debug_print(self):
        """Ensure debug_print works as expected"""
        debug.trace(4, f"test_debug_print(): self={self}")
        self.monkeypatch.setattr("mezcla.debug.output_timestamps", True)

        THE_MODULE.debug_print('error foobar', -1)
        out,err  = self.get_stdout_stderr()
        assert "error foobar" in err
        assert not out

        # Test debug_file
        self.monkeypatch.setattr("mezcla.debug.debug_file", sys.stdout)
        THE_MODULE.debug_print('some text to test debug file', -1)
        out,err  = self.get_stdout_stderr()
        assert 'some text to test debug file' in out

    @pytest.mark.xfail
    def test_timestamp(self):
        """Ensure timestamp works as expected"""
        debug.trace(4, f"test_timestamp(): self={self}")
        debug_timestamp = THE_MODULE.timestamp()
        new_timestamp = str(datetime.now())
        assert debug_timestamp == new_timestamp
        

    def test_debugging(self):
        """Ensure debugging works as expected"""
        debug.trace(4, f"test_debugging(): self={self}")
        THE_MODULE.set_level(4)
        assert THE_MODULE.debugging(2)
        assert THE_MODULE.debugging(4)
        assert not THE_MODULE.debugging(6)

    def test_detailed_debugging(self):
        """Ensure detailed_debugging works as expected"""
        debug.trace(4, f"test_detailed_debugging(): self={self}")
        THE_MODULE.set_level(2)
        assert not THE_MODULE.detailed_debugging()
        THE_MODULE.set_level(4)
        assert THE_MODULE.detailed_debugging()
        THE_MODULE.set_level(6)
        assert THE_MODULE.detailed_debugging()

    def test_verbose_debugging(self):
        """Ensure verbose_debugging works as expected"""
        debug.trace(4, f"test_verbose_debugging(): self={self}")
        THE_MODULE.set_level(2)
        assert not THE_MODULE.verbose_debugging()
        THE_MODULE.set_level(5)
        assert THE_MODULE.verbose_debugging()
        THE_MODULE.set_level(7)
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
        THE_MODULE.set_level(7)
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
        THE_MODULE.set_level(7)
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

    @pytest.mark.xfail                   # TODO: remove xfail
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

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_profile_function(self):
        """Ensure profile_function works as expected"""
        debug.trace(4, f"test_profile_function(): self={self}")
        frame = inspect.currentframe()
        
        # test function call
        THE_MODULE.profile_function(frame, 'test_profile_function call', 'something') 
        err = self.get_stderr()
        assert "test_profile_function call" in err
        assert "in: test_debug:test_profile_function(something)" in err
        
        # test function return
        self.clear_stderr()
        THE_MODULE.profile_function(frame, 'test_profile_function return', 'None') 
        err_2 = self.get_stderr()
        assert "out: test_debug:test_profile_function => None" in err_2
        
    @pytest.mark.xfail                   # TODO: remove xfail
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

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_read_line(self):
        """Ensure read_line works as expected"""
        debug.trace(4, f"test_read_line(): self={self}")
        content = """line1
        line2
        line3
"""
        
        temp_file = self.get_temp_file()
        system.write_file(temp_file, content)
        line_1 = THE_MODULE.read_line(temp_file, 1)
        line_2 = THE_MODULE.read_line(temp_file, 2)
        line_3 = THE_MODULE.read_line(temp_file, 3)
        assert (line_1 + line_2 + line_3) == content

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_debug_init(self):
        """Ensure debug_init works as expected"""
        debug.trace(4, f"test_debug_init(): self={self}")
        self.monkeypatch.setenv("DEBUG_FILE", "tmp_debug.txt")
        self.monkeypatch.setenv("ENABLE_LOGGING", "True")
        # NOTE: Setting MONITOR_FUNCTIONS to True breaks tests on windows
        today = str(datetime.now()).split(' ')[0]
        THE_MODULE.debug_init()
        err = self.get_stderr()
        err_file = system.form_path(gh.dirname(__file__), "err.txt")
        system.write_file(err_file, err)

        assert "debug_filename=tmp_debug.txt" in err
        assert "debug_file=<_io.TextIOWrapper name=\'tmp_debug.txt\'" in err
        assert f"[{THE_MODULE.__file__}] loaded at {today}" in err
        assert "Setting logger level to 10" in err
        assert "DEBUG_FILE: tmp_debug.txt" in err
        assert "ENABLE_LOGGING: True" in err

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_display_ending_time_etc(self):
        """Ensure display_ending_time_etc works as expected"""
        debug.trace(4, f"test_display_ending_time_etc(): self={self}")
        self.monkeypatch.setenv("SKIP_ATEXIT", "False")
        self.monkeypatch.delenv("DEBUG_FILE", raising=False)
        self.monkeypatch.setattr("mezcla.debug.debug_file", None)
        THE_MODULE.debug_init()
        err = self.get_stderr()
        err_file = system.form_path(gh.dirname(__file__), "err.txt")
        system.write_file(err_file, err)
        assert(False)

    def test_visible_simple_trace(self):
        """Make sure level-1 trace outputs to stderr"""
        debug.trace(4, f"test_visible_simple_trace()")
        self.setup_simple_trace()
        if not __debug__:
            self.expected_stderr_trace = ""
        pre_out, pre_err = self.get_stdout_stderr()
        save_trace_level = THE_MODULE.get_level()
        THE_MODULE.set_level(4)
        print(self.stdout_text)
        THE_MODULE.trace(3, self.stderr_text)
        THE_MODULE.set_level(save_trace_level)
        out, err = self.get_stdout_stderr()
        assert(self.expected_stdout_trace in out)
        assert(self.expected_stderr_trace in err)
        THE_MODULE.trace_expr(6, (pre_out, pre_err), (out,err))

    def test_hidden_simple_trace(self):
        """Make sure level-N+1 trace doesn't output to stderr"""
        debug.trace(4, f"test_hidden_simple_trace()")
        self.setup_simple_trace()
        ## TEST
        ## capsys.stop_capturing()
        ## capsys.start_capturing()
        pre_out, pre_err = self.get_stdout_stderr()
        self.expected_stderr_trace = ""
        save_trace_level = THE_MODULE.get_level()
        THE_MODULE.set_level(0)
        print(self.stdout_text)
        THE_MODULE.trace(1, self.stderr_text)
        out, err = self.get_stdout_stderr()
        THE_MODULE.set_level(save_trace_level)
        assert self.expected_stdout_trace in out
        assert self.expected_stderr_trace in err
        THE_MODULE.trace_expr(6, (pre_out, pre_err), (out,err))



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
        old_level = debug.get_level()
        new_level = old_level + 1
        debug.set_level(new_level)
        expected_level = (new_level if __debug__ else old_level)
        self.do_assert(debug.get_level() == expected_level)

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
