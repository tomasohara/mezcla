#! /usr/bin/env python3
#
# Test(s) for ../merge_notes.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_merge_notes.py
#

"""Tests for merge_notes module"""

# Standard packages
## NOTE: this is empty for now

# Installed packages
import pytest
import datetime

# Local packages
from mezcla import debug
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:               module object (e.g., <module 'mezcla.main' ...>)
#    TestIt.script_module:     dotted module path (e.g., "mezcla.main")
import mezcla.merge_notes as THE_MODULE

class TestMergeNotes(TestWrapper):
    """Class for testcase definition"""
    # note: script_module used in argument parsing sanity check (e.g., --help)
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    def test_resolve_date(self):
        """Ensure resolve_date works as expected"""
        debug.trace(4, "test_resolve_date()")
        assert THE_MODULE.resolve_date("1 Jan 00") == datetime.datetime(2000, 1, 1, 0, 0)
        assert THE_MODULE.resolve_date("0 Jan 00", datetime.datetime(2000, 1, 1, 0, 0)) == datetime.datetime(2000, 1, 1, 0, 0)
        assert THE_MODULE.resolve_date("Sun 18 Jul 2021") == datetime.datetime(2021, 7, 18, 0, 0)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_01_data_file(self):
        """Tests run_script w/ data file"""
        ## TODO: test main script invocation
        # Warning: see notes above about potential issues with run_script-based tests.
        debug.trace(4, f"TestIt.test_01_data_file(); self={self}")
        data = ["TODO1", "TODO2"]
        system.write_lines(self.temp_file, data)
        ## TODO: add use_stdin=True to following if no file argument
        output = self.run_script(options="", data_file=self.temp_file)
        self.do_assert(my_re.search(r"TODO-pattern", output.strip()))
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
