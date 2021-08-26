#! /usr/bin/env python
#
# Test(s) for ../main.py
#
# Notes:
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python tests/test_main.py
# For pytest monkeypatch, see
#   https://stackoverflow.com/questions/38723140/i-want-to-use-stdin-in-a-pytest-test
#

"""Unit tests for main module"""

# Standard packages
from argparse import ArgumentParser
import io
import sys
## OLD: import unittest

# Installed packages
import pytest

# Local packages
import tomas_misc.tpo_common as tpo
from tomas_misc import debug
from tomas_misc.main import Main
from tomas_misc.unittest_wrapper import TestWrapper

class MyArgumentParser(ArgumentParser):
    """Version of ArgumentParser that doesn't exit upon failure"""

    def __init__(self, *args, **kwargs):
        """Constructor (relegating all to parent)"""
        ## OLD: super(MyArgumentParser, self).__init__(*args, **kwargs)
        super().__init__(*args, **kwargs)

    def exit(self, status=0, message=None):
        """Version of exit that doesn't really exit"""
        if message:
            self._print_message(message, sys.stderr)


class TestIt(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.derive_tested_module_name(__file__)
    ## HACK: globals for use in embedded classes
    input_processed = None
    main_step_invoked = None

    def test_script_options(self):
        """Makes sure script option specifications are parsed OK"""
        debug.trace(4, "test_script_options()")
        from tomas_misc.main import Main  # pylint: disable=import-outside-toplevel, redefined-outer-name, reimported
        class Test(Main):
            """"Dummy test class"""
            argument_parser = MyArgumentParser

        # note: format is ("option", "description", "default"), or just "option"
        app = Test(text_options=[("name", "Full name", "John Doe")],
                   boolean_options=["verbose"],
                   runtime_args=["--verbose"])
        #
        ## OLD
        ## self.assertEquals(app.parsed_args.get("name"), "John Doe")
        ## self.assertEquals(app.parsed_args.get("verbose"), True)
        self.assertEqual(app.parsed_args.get("name"), "John Doe")
        self.assertEqual(app.parsed_args.get("verbose"), True)

    def test_script_without_input(self):
        """Makes sure script class without input doesn't process input and that
        the main step gets invoked"""
        debug.trace(4, "test_script_without_input()")
        ## OLD: input_processed = None
        ## OLD: main_step_invoked = None

        # Create scriptlet checking for input and processing main step
        # TODO: rework with external script as argparse exits upon failure
        from tomas_misc.main import Main  # pylint: disable=import-outside-toplevel, redefined-outer-name, reimported
        class Test(Main):
            """"Dummy test class"""
            argument_parser = MyArgumentParser

            def setup(self):
                """Post-argument parsing processing: just displays context"""
                tpo.debug_format("setup(): self={s}", 5, s=self)
                tpo.trace_current_context(label="Test.setup", 
                                          level=tpo.QUITE_DETAILED)
                tpo.trace_object(self, tpo.QUITE_DETAILED, "Test instance")
            #
            def process_line(self, line):
                """Dummy input processing"""
                tpo.debug_format("Test.process_line({l}): self={s}", 5,
                                 l=line, s=self)
                ## OLDER: global input_processed
                ## OLD: input_processed = True
                TestIt.input_processed = True
                
            #
            def run_main_step(self):
                """Dummy main step"""
                tpo.debug_format("Test.run_main_step): self={s}", 5,
                                 s=self)
                ## OLDER: global main_step_invoked
                ## OLD: main_step_invoked = True
                TestIt.main_step_invoked = True

        # Test scriptlet with test script as input w/ and w/o input enabled
        TestIt.input_processed = None
        app1 = Test(skip_input=False, runtime_args=[__file__])
        try:
            app1.run()
        except:
            tpo.print_stderr("Exception during run method: {exc}",
                             exc=tpo.to_string(sys.exc_info()))
        ## OLD: self.assertTrue(input_processed)
        self.assertTrue(TestIt.input_processed)
        #
        TestIt.input_processed = None
        app2 = Test(skip_input=True, runtime_args=[__file__])
        try:
            app2.run()
        except:
            tpo.print_stderr("Exception during run method: {exc}",
                             exc=tpo.to_string(sys.exc_info()))
        ## OLD: self.assertFalse(input_processed)
        self.assertFalse(TestIt.input_processed)

        # Test scriptlet w/ input disabled and wihout arguments
        # note: auto_help disabled so that no arguments needed
        TestIt.main_step_invoked = None
        app3 = Test(skip_input=True, auto_help=False, runtime_args=[])
        try:
            app3.run()
        except:
            tpo.print_stderr("Exception during run method: {exc}",
                             exc=tpo.to_string(sys.exc_info()))
        ## OLD: self.assertTrue(main_step_invoked)
        self.assertTrue(TestIt.main_step_invoked)

class TestIt2:
    """Another class for testcase definition
    Note: Needed to avoid error with pytest due to inheritance with unittest.TestCase via TestWrapper"""

    def test_input_modes(self, capsys, monkeypatch):
        """Make sure input processed OK with respect to line/para/file mode"""
        debug.trace(4, f"test_input_modes({capsys}); self={self}")
        contents = "1\n\n2\n\n\n3\n\n\n\n4\n\n\n\n"
        num_lines = len(contents.split("\n"))
        _pre_captured = capsys.readouterr()
        # line input
        monkeypatch.setattr('sys.stdin', io.StringIO(contents))
        main = Main()
        main.run()
        captured = capsys.readouterr()
        assert(num_lines == len(captured.out.split("\n")))
        debug.trace_expr(5, main, num_lines)
        # paragraph input
        monkeypatch.setattr('sys.stdin', io.StringIO(contents))
        main = Main(paragraph_mode=True)
        main.run()
        captured = capsys.readouterr()
        assert(num_lines == len(captured.out.split("\n")))
        debug.trace_expr(5, main, num_lines)
        # file input
        monkeypatch.setattr('sys.stdin', io.StringIO(contents))
        main = Main(file_input_mode=True)
        main.run()
        captured = capsys.readouterr()
        assert(num_lines == len(captured.out.split("\n")))
        debug.trace_expr(5, main, num_lines)
        
    def test_missing_newline(self, capsys, monkeypatch):
        """Make sure file with missing newline at end processed OK"""
        debug.trace(4, f"test_missing_newline({capsys}); self={self}")
        contents = "1\n2\n3"
        num_lines = len(contents.split("\n"))
        _pre_captured = capsys.readouterr()
        monkeypatch.setattr('sys.stdin', io.StringIO(contents))
        main = Main()
        main.run()
        captured = capsys.readouterr()
        # note: 1 extra line ('') and 1 extra character (final newline)
        assert((1 + num_lines) == len(captured.out.split("\n")))
        assert((1 + len(contents)) == len(captured.out))
        debug.trace_expr(5, main, num_lines)
        
#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    ## OLD: unittest.main(file_input_mode=True)
    pytest.main([__file__])
