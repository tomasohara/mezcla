#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Test(s) for ../unittest_wrapper.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_unittest_wrapper.py
#
# Warning:
# - It can be tricky to debug the do_assert and do_assert_equals tests.
# - Temporarily disabling the use of TL.DEFAULT below can help, so that the detailed
#   debugging traces are shown.
# - You might also need to temporarily enable the print-based tracing in resolve_assertion.
# - Don't use dangerous utilities like shutil.rmtree (or rm -r)!
#
# Tip:
# - Although the inference of TEMP_FILE from TEMP_BASE is blocked with PRESERVE_TEMP_FILE,
#   the implicit loading of modules via __init__.py can complicate matters. Enabling the
#   __file__ tracing and running as follows can help:
#      DEBUG_LEVEL=5 TEMP_BASE="/tmp/test-it/" test-python-script-method test_07 unittest_wrapper.py
#      egrep '__file__=|TEMP_FILE|init' $log | less -S
# - See https://github.com/tomasohara/shell-scripts for supporting aliases used above.
#

"""Tests for unittest_wrapper module"""

# Standard packages
# note: checks for temp-file settings made by unittest_wrapper
import os
PRESERVE_TEMP_FILE_LABEL = "PRESERVE_TEMP_FILE"
PRESERVE_TEMP_FILE_INIT = os.environ.get(PRESERVE_TEMP_FILE_LABEL)
TEMP_FILE_LABEL = "TEMP_FILE"
TEMP_FILE_INIT = os.environ.get(TEMP_FILE_LABEL)
## DEBUG: import sys; sys.stderr.write(f"{__file__=}\n")  # pylint: disable=multiple-statements

# Installed packages
## OLD: import atexit
## BAD: import shutil
import pytest

# Local packages
## TEST: os.environ["PRESERVE_TEMP_FILE"] = "1"
from mezcla.unittest_wrapper import TestWrapper, invoke_tests, trap_exception
from mezcla import debug
from mezcla.my_regex import my_re
from mezcla import system
from mezcla import glue_helpers as gh

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                  global module object
#    TestTemplate.script_module:  path to file
import mezcla.unittest_wrapper as THE_MODULE


## TODO (use TestWrapper directly):

# Globals
last_self = None                        # Reserved for test_05_check_temp_part1/2

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    last_temp_file = None               # Reserved for test_05_check_temp_part1/2
    use_temp_base_dir = True            # treat TEMP_BASE as directory

    @pytest.mark.xfail
    def test_01_usage(self):
        """Make sure usage warns that not intended for command line and that no stdout"""
        debug.trace(4, f"TestIt.test_01_usage(); self={self}")
        log_file = self.temp_file + ".log"
        ## BAD: output = self.run_script(log_file=log_file)
        output = self.run_script(env_options="DEBUG_LEVEL=4", log_file=log_file)
        self.do_assert(not output.strip())
        log_contents = system.read_file(log_file)
        debug.trace_expr(5, log_contents)
        self.do_assert(my_re.search(r"Warning: not intended.*command-line", log_contents))
        return

    @pytest.mark.skipif(not __debug__, reason="Must be under __debug__")
    @trap_exception
    def test_02_do_assert(self):
        """Ensure do_assert identifies failing line"""
        debug.trace(4, f"TestIt.test_02_do_assert(); self={self}")

        # Get instance for test class
        # TODO3: use TestWrapper() instead of SubTestIt()
        class SubTestIt(TestWrapper):
            """Embedded test suite"""
            pass
        #
        sti = SubTestIt()

        # Make assertion, ensuring debugging level set at minimum required (2)
        captured_trace = ""
        message = "Good math"
        # TODO3: use pytest patch support (monkey?)
        old_debug_level = debug.get_level()
        _old_captured_trace = self.get_stderr()   # resets capsys capture
        try:
            # Note: see warning with tips on debugging in header comments
            debug.set_level(debug.TL.DEFAULT)
            sti.do_assert(2 + 2 == 5, message)    # Orwell's condition
        except AssertionError:
            pass
        finally:
            debug.set_level(old_debug_level)
        captured_trace = self.get_stderr()
        debug.trace_expr(4, captured_trace, max_len=2048)
        
        #  The condition and message should be displayed
        # example: Test assertion failed: 2 + 2 == 5 (at .../mezcla/tests/test_unittest_wrapper.py:77): Good math
        assert("2 + 2 == 5" in captured_trace)
        assert(message in captured_trace)
        
        # Make sure stuff properly stripped (i.e., message arg and comment)
        assert("message" not in captured_trace)
        assert("Orwell" not in captured_trace)
        assert("sti.do_assert" not in captured_trace)
        return

    @pytest.mark.skipif(not __debug__, reason="Must be under __debug__")
    @trap_exception
    def test_03_do_assert_equals(self):
        """Ensure do_assert_equals shows diff"""
        debug.trace(4, f"TestIt.test_03_do_assert_equals(); self={self}")

        # Get instance for test class
        # TODO3: use TestWrapper() instead of SubTestIt()
        class SubTestIt(TestWrapper):
            """Embedded test suite"""
            pass
        #
        sti = SubTestIt()

        # Make assertion, ensuring debugging level set at minimum required (2)
        captured_trace = ""
        message = "dawg diff"
        # TODO3: use pytest patch support (monkey?)
        old_debug_level = debug.get_level()
        _old_captured_trace = self.get_stderr()   # resets capsys capture
        try:
            # Note: see warning with tips on debugging in header comments
            debug.set_level(debug.TL.DEFAULT)
            sti.do_assert_equals("dog's bark", "dawg's bark", message)
        except AssertionError:
            pass
        finally:
            debug.set_level(old_debug_level)
        captured_trace = self.get_stderr()
        debug.trace_expr(4, captured_trace, max_len=2048)
        
        # The condition and message should be displayed
        # example: Test equality assertion failed: "dog\'s bark", "dawg\'s bark" (at .../mezcla/tests/test_unittest_wrapper.py:118): dawg diff
        assert(my_re.search(r"dog.*dawg", captured_trace))
        assert(message in captured_trace)

        # The value diff should also be displayed
        # example: "diff:\n< dog\'s bark\n…  ^\n> dawg\'s bark\n…  ^^\n\n"
        assert(my_re.search(r" \^\n.* \^\^\n", captured_trace, flags=my_re.DOTALL))
        
        # Make sure stuff properly stripped (i.e., message arg and comment)
        assert("sti.do_assert_equals" not in captured_trace)
        return

    @pytest.mark.xfail
    def test_04_get_temp_dir(self):
        """Tests get_temp_dir"""
        ## TODO3: Cleanup this test: rework to work around disabled rmtree and atexit calls
        ## NOTE: By default temp files placed under /tmp, which system will delete if needed.
        ## TODO3: skip if not posix
        ##
        debug.trace(4, f"TestIt.test_04_get_temp_dir(); self={self}")
        ## BAD: tmp_dir = system.form_path(system.getenv_text("TMP"), 'test_get_temp_dir')
        tmp_dir = gh.form_path(gh.get_temp_dir(), 'test_get_temp_dir')
        self.monkeypatch.setattr("mezcla.glue_helpers.TEMP_FILE", tmp_dir)
        #
        if system.is_directory(tmp_dir):
            # Note: Should only occurs when TEMP_FILE or TEMP_BASE overriden (for debugging).
            debug.trace(4, "Warning: Temporary directory unexpectedly exists: {tmp_dir!r}")
            ## BAD: shutil.rmtree(tmp_dir, ignore_errors=True)
        assert not system.is_directory(tmp_dir)
        unittest_temp_dir = THE_MODULE.get_temp_dir(keep=False)
        ## OLD: atexit.register(gh.delete_directory, unittest_temp_dir)
        #
        assert tmp_dir == unittest_temp_dir
        assert system.is_directory(tmp_dir)
        ## BAD: shutil.rmtree(tmp_dir, ignore_errors=True)
        
        # Test argument unique=True
        ## BAD: tmp_dir_2 = system.form_path(system.getenv_text("TMP"), 'test_get_temp_dir_2')
        tmp_dir_2 = gh.form_path(gh.get_temp_dir(), 'test_get_temp_dir_2')
        self.monkeypatch.setattr("mezcla.glue_helpers.TEMP_FILE", tmp_dir_2)
        if system.is_directory(tmp_dir_2):
            ## Note: Should only occurs when TEMP_FILE or TEMP_BASE overriden (for debugging).
            debug.trace(4, "Warning: Temporary directory unexpectedly exists: {tmp_dir!r}")
            ## BAD: shutil.rmtree(tmp_dir_2, ignore_errors=True)
        assert not system.is_directory(tmp_dir_2)
        #
        unittest_temp_dir_2 = THE_MODULE.get_temp_dir(keep=False, unique=True)
        ## OLD: atexit.register(gh.delete_directory, unittest_temp_dir_2)
        #
        assert (tmp_dir_2 + '_temp_dir_') in unittest_temp_dir_2
        assert system.is_directory(unittest_temp_dir_2)

    @pytest.mark.xfail
    def test_05_check_temp_part1(self):
        """Make sure self.temp setup OK"""
        debug.trace(4, f"TestIt.test_05_check_temp_part1(); self={self!r}; id={id(self)}")
        debug.trace_expr(5, self.last_temp_file, self.temp_file)
        assert(self.last_temp_file is None)
        self.last_temp_file = self.temp_file
        global last_self                # TODO4 (use class member)
        debug.assertion(last_self is None)
        last_self = self

    @pytest.mark.xfail
    def test_06_check_temp_part2(self):
        """Make sure self.temp unique"""
        debug.trace(4, f"TestIt.test_06_check_temp_part2(); self={self!r}; id={id(self)}")
        debug.trace_expr(5, self.last_temp_file, self.temp_file)
        assert self.last_temp_file != self.temp_file
        ## TODO2: assert(self.last_temp_file is not None)
        debug.assertion(self.last_temp_file is not None)
        global last_self                # TODO4 (use class member)
        # NOTE: The following will fail: apparently each test is run using
        # a separate class instance.
        debug.assertion(last_self == self)

    @pytest.mark.xfail
    def test_07_preserve_temp_file(self):
        """Make sure PRESERVE_TEMP_FILE set appropriately"""
        debug.trace(4, f"TestIt.test_07_preserve_temp_file(); self={self!r}")
        # Get setting related to temp-file name inference
        PRESERVE_TEMP_FILE_VALUE = os.environ.get(PRESERVE_TEMP_FILE_LABEL)
        TEMP_FILE_VALUE = os.environ.get(TEMP_FILE_LABEL)
        ## TODO: debug.trace(5, f"env. {PRESERVE_TEMP_FILE_LABEL}={PRESERVE_TEMP_FILE_VALUE!r} {TEMP_FILE_LABEL}={TEMP_FILE_VALUE!r}")
        debug.trace_expr(5, PRESERVE_TEMP_FILE_INIT, PRESERVE_TEMP_FILE_VALUE)
        debug.trace_expr(5, TEMP_FILE_INIT, TEMP_FILE_VALUE)

        # Check tests unless settings might cause conflict
        fyi_warning = "FYI: test_07_preserve_temp_file not applicable"
        if PRESERVE_TEMP_FILE_INIT is not None:
            debug.trace(4, f"{fyi_warning}: {PRESERVE_TEMP_FILE_INIT=}")
        elif TEMP_FILE_INIT:
            debug.trace(4, f"{fyi_warning}: {TEMP_FILE_INIT=}")
        else:
            assert PRESERVE_TEMP_FILE_LABEL == THE_MODULE.PRESERVE_TEMP_FILE_LABEL
            assert PRESERVE_TEMP_FILE_VALUE == "1"
            # note: should be test-7 (or test-1 if run in isolation)
            assert my_re.search(r"test-[1-7]", self.temp_file)
            

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
