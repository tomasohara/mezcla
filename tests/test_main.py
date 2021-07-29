#! /usr/bin/env python
#
# Test(s) for ../main.py
#
# Notes:
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python tests/test_main.py
#

"""Unit tests for main module"""

import sys
import unittest
from unittest_wrapper import TestWrapper
from argparse import ArgumentParser

import tomas_misc.tpo_common as tpo


class MyArgumentParser(ArgumentParser):
    """Version of ArgumentParser that doesn't exit upon failure"""

    def __init__(self, *args, **kwargs):
        """Constructor (relegating all to parent)"""
        super(MyArgumentParser, self).__init__(*args, **kwargs)

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
        # pylint: disable=import-outside-toplevel
        from tomas_misc.main import Main
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
        ## OLD: input_processed = None
        ## OLD: main_step_invoked = None

        # Create scriptlet checking for input and processing main step
        # TODO: rework with external script as argparse exits upon failure
        # pylint: disable=import-outside-toplevel
        from tomas_misc.main import Main
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

#------------------------------------------------------------------------

if __name__ == '__main__':
    tpo.trace_current_context()
    unittest.main()
