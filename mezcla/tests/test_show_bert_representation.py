#! /usr/bin/env python3
#
# Test(s) for ../show_bert_representation.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_show_bert_representation.py
#
# IMPORTANT:
# - this is more like a bureaucratic test file, this module has priority NONE to be tested (for now)

"""Tests for show_bert_representation module"""

# Standard packages
## NOTE: this is empty for now

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:               module object (e.g., <module 'mezcla.main' ...>)
#    TestIt.script_module:     dotted module path (e.g., "mezcla.main")
try:
    import mezcla.show_bert_representation as THE_MODULE
except:
    THE_MODULE = None
    system.print_exception_info("THE_MODULE import")

class TestShowBertRepresentation(TestWrapper):
    """Class for testcase definition"""
    # note: script_module used in argument parsing sanity check (e.g., --help)
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    def test_cosine_distance(self):
        """Ensure cosine_distance works as expected"""
        debug.trace(4, "test_cosine_distance()")
        assert THE_MODULE.cosine_distance([1, 0, 0], [0, 0, 1]) == 1.0 
        assert THE_MODULE.cosine_distance([1, 0, 0], [2, 0, 0]) == 0.0 
        assert THE_MODULE.cosine_distance([1, 0, 0, 0], [1, 1, 1, 1]) == 0.5 

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_show_cosine_distances(self):
        """Ensure show_cosine_distances works as expected"""
        debug.trace(4, "test_show_cosine_distances()")
        self.do_assert(False, "TODO: implement")

    ## TODO: test ExtractFeatures class
    ## TODO: test Script class

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
