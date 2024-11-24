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

# Constants
MEZCLA_REGEX = "M[e]zcl[a]"

class TestMyRegex(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__)
    my_re = THE_MODULE.my_re            # TODO3: make global to cut down self usages

    ## OLD:
    ## @pytest.fixture(autouse=True)
    ## def capsys(self, capsys):
    ##     """Gets capsys"""
    ##     self.capsys = capsys

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_search(self):
        """Test search()"""
        debug.trace(4, f"test_search(); self={self}")
        self.do_assert(not self.my_re.search(MEZCLA_REGEX, "EZC"))
        debug.assertion("E" not in MEZCLA_REGEX)
        debug.assertion("e" in MEZCLA_REGEX)
        self.my_re.search(MEZCLA_REGEX, "EZC", flags=re.IGNORECASE)
        self.my_re.search(MEZCLA_REGEX, "ezc")
        self.do_assert(self.my_re.search_text == "ezc")

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_match(self):
        """Ensure match() works as expected"""
        debug.trace(4, f"test_match(); self={self}")
        debug.assertion("M" in MEZCLA_REGEX)
        debug.assertion("m" not in MEZCLA_REGEX)
        self.do_assert(not self.my_re.match(MEZCLA_REGEX, "MEZC"))
        self.my_re.match(MEZCLA_REGEX, "MEZC", flags=re.IGNORECASE)
        self.my_re.match(MEZCLA_REGEX, "Mezc")
        self.do_assert(self.my_re.search_text == "Mezc")

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_get_match(self):
        """Ensure get_match() works as expected"""
        debug.trace(4, f"test_get_match(); self={self}")
        self.do_assert(False, "TODO: implement")

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_group(self):
        """Ensure group() works as expected"""
        debug.trace(4, f"test_group(); self={self}")
        self.do_assert(False, "TODO: implement")

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_groups(self):
        """Ensure groups() works as expected"""
        debug.trace(4, f"test_groups(); self={self}")
        self.do_assert(False, "TODO: implement")

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_grouping(self):
        """Ensure grouping() works as expected"""
        debug.trace(4, f"test_grouping(); self={self}")
        self.do_assert(False, "TODO: implement")

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_start(self):
        """Ensure start() works as expected"""
        debug.trace(4, f"test_start(); self={self}")
        self.do_assert(False, "TODO: implement")

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_end(self):
        """Ensure end() works as expected"""
        debug.trace(4, f"test_end(); self={self}")
        self.do_assert(False, "TODO: implement")

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_sub(self):
        """Ensure sub() works as expected"""
        debug.trace(4, f"test_sub(); self={self}")
        self.do_assert(False, "TODO: implement")

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_span(self):
        """Ensure span() works as expected"""
        debug.trace(4, f"test_span(); self={self}")
        self.do_assert(False, "TODO: implement")

    @pytest.mark.xfail                   # TODO: remove xfail
    @trap_exception
    def test_f_string(self):
        """Ensure warning given about f-string like regex"""
        debug.trace(4, f"in test_f_string(); self={self}")
        self.my_re.search("{fubar}", "foobar")
        # TODO2: change usages elsewhere to make godawful pytest default more intuitive
        captured_stderr = self.get_stderr()
        debug.trace_expr(4, captured_stderr, max_len=4096)
        self.do_assert(self.my_re.search("Warning:.*f-string", captured_stderr))
        ## TEST: print(f"{self.my_re=}")
        debug.trace(5, "out test_f_string(); self={self}")

    def test_simple_regex(self):
        """"Test regex search with capturing"""
        debug.trace(4, f"test_simple_regex(); self={self}")
        self.do_assert(self.my_re.search(r"(\w+)\W+(\w+)", ">scrap ~!@\n#$ yard<",
                                         re.MULTILINE))
        self.do_assert(self.my_re.group(1) == "scrap")
        self.do_assert(self.my_re.group(2) == "yard")
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_pre_and_post_match(self):
        """Test pre/post_match() functions"""
        debug.trace(4, f"test_pre_and_post_match(); self={self}")
        self.my_re.search(r"[dD]ef", "abc_def_ghi")
        self.do_assert(self.my_re.pre_match() == "abc_")
        self.do_assert(self.my_re.post_match() == "_ghi")

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
