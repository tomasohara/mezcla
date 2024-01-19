#! /usr/bin/env python
#
# Test(s) for ../my_regex.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_my_regex.py
#

"""Tests for my_regex module"""

# Standard packages
import re

# Installed packages
import pytest

# Local packages
from mezcla.unittest_wrapper import TestWrapper
from mezcla.unittest_wrapper import trap_exception
from mezcla import debug

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
import mezcla.my_regex as THE_MODULE

class TestMyRegex(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__)
    my_re = THE_MODULE.my_re

    ## OLD:
    ## @pytest.fixture(autouse=True)
    ## def capsys(self, capsys):
    ##     """Gets capsys"""
    ##     self.capsys = capsys

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_search(self):
        """Ensure search() works as expected"""
        debug.trace(4, "test_search()")
        assert(False)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_match(self):
        """Ensure match() works as expected"""
        debug.trace(4, "test_match()")
        assert(False)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_get_match(self):
        """Ensure get_match() works as expected"""
        debug.trace(4, "test_get_match()")
        assert(False)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_group(self):
        """Ensure group() works as expected"""
        debug.trace(4, "test_group()")
        assert(False)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_groups(self):
        """Ensure groups() works as expected"""
        debug.trace(4, "test_groups()")
        assert(False)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_grouping(self):
        """Ensure grouping() works as expected"""
        debug.trace(4, "test_grouping()")
        assert(False)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_start(self):
        """Ensure start() works as expected"""
        debug.trace(4, "test_start()")
        assert(False)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_end(self):
        """Ensure end() works as expected"""
        debug.trace(4, "test_end()")
        assert(False)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_sub(self):
        """Ensure sub() works as expected"""
        debug.trace(4, "test_sub()")
        assert(False)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_span(self):
        """Ensure span() works as expected"""
        debug.trace(4, "test_span()")
        assert(False)

    @pytest.mark.xfail                   # TODO: remove xfail
    @trap_exception
    def test_f_string(self):
        """Ensure warning given about f-string like regex"""
        debug.trace(4, "in test_f_string()")
        self.my_re.search("{fubar}", "foobar")
        # TODO2: change usages elsewhere to make godawful pytest default more intuitive
        captured_stderr = self.get_stderr()
        debug.trace_expr(4, captured_stderr, max_len=4096)
        self.do_assert(self.my_re.search("Warning:.*f-string", captured_stderr))
        ## TEST: print(f"{self.my_re=}")
        debug.trace(5, "out test_f_string()")

    def test_simple_regex(self):
        """"Test regex search with capturing"""
        debug.trace(4, "test_simple_regex()")
        if not self.my_re.search(r"(\w+)\W+(\w+)", ">scrap ~!@\n#$ yard<",
                                 re.MULTILINE):
            assert False, "simple regex search failed"
        assert self.my_re.group(1) == "scrap"
        assert self.my_re.group(2) == "yard"
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
