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
        debug.trace(4, f"test_search(); self={self}")
        text = "The quick brown fox jumps over the lazy dog."
        regex = r"\w{5}"
        self.my_re.search(regex, text)
        output = self.my_re.get_match()
        assert (output.group() == "quick" and output.span() == (4, 9))
    
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_match(self):
        """Ensure match() works as expected"""
        debug.trace(4, f"test_match(); self={self}")
        text = "1 kiss is all takes."
        regex = r"\d+"
        self.my_re.match(regex, text, 0)
        output = self.my_re.get_match()
        assert(output.group() == "1" and output.span() == (0, 1))
        ## TODO: return the matched value (solved: use group() after my_re.get_match())

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_get_match(self):
        """Ensure get_match() works as expected"""
        debug.trace(4, f"test_get_match(); self={self}")
        # get_match() returns the last the result of match
        text = "333 little birds"
        regex = r"\d+"
        self.my_re.match(regex, text, 0)
        output = self.my_re.get_match()
        assert isinstance(output, re.Match)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_group(self):
        """Ensure group() works as expected"""
        debug.trace(4, f"test_group(); self={self}")
        text = "three, 7, eight"
        regex = r"\w{5},"
        self.my_re.search(regex, text, 0)
        output = self.my_re.group(0)
        assert (output == 'three,')

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_groups(self):
        """Ensure groups() works as expected"""
        debug.trace(4, f"test_groups(); self={self}")
        text = "John Doe: 30 years old, Jane Smith: 25 years old"
        regex = r"(\w+\s\w+): (\d+) years"
        self.my_re.search(regex, text)
        output = self.my_re.groups()
        assert(output == ('John Doe', '30'))

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_grouping(self):
        """Ensure grouping() works as expected"""
        debug.trace(4, f"test_grouping(); self={self}")
        text = "John Doe: 30 years old, Jane Smith: 25 years old"
        regex = r"(\w+\s\w+): (\d+) years"
        self.my_re.search(regex, text)
        output = self.my_re.grouping()
        assert(output == ('John Doe', '30'))

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_start(self):
        """Ensure start() works as expected"""
        debug.trace(4, f"test_start(); self={self}")
        text = "three little birds"
        regex = r"\w{5}"
        self.my_re.search(regex, text)
        output = self.my_re.start()
        # start() returns starting index
        assert(output == 0)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_end(self):
        """Ensure end() works as expected"""
        debug.trace(4, f"test_end(); self={self}")
        text = "three big birds"
        regex = r"\w{5}"
        self.my_re.search(regex, text)
        output = self.my_re.end()
        # start() returns ending index
        assert(output == 5)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_sub(self):
        """Ensure sub() works as expected"""
        debug.trace(4, f"test_sub(); self={self}")
        text = "The quick brown fox jumps over the lazy dog."
        regex = r"\w{4}"
        replacement = "****"
        output_sample = "The ****k ****n fox ****s **** the **** dog."
        output = self.my_re.sub(pattern=regex, string=text, replacement=replacement)
        assert(output == output_sample)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_span(self):
        """Ensure span() works as expected"""
        debug.trace(4, f"test_span(); self={self}")
        text = "The quick brown fox jumps over the lazy dog."
        regex = r"\w{4}"
        self.my_re.search(regex, text)
        output = self.my_re.span()
        assert(output == (4, 8))
    
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_split(self):
        """Ensure split() works as expected"""
        debug.trace(4, f"test_split(); self={self}")
        text = "three,little,birds"
        regex = r","
        output = self.my_re.split(pattern=regex, string=text)
        assert(output == text.split(","))

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_findall(self):
        """Ensure findall() works as expected"""
        debug.trace(4, f"test_findall(); self={self}")
        text = "There are 32768 possible combinations, with 256 other combinations and 0 impossible combinations."
        regex = r"\d+"
        output = self.my_re.findall(pattern=regex, string=text)
        assert(output == ['32768', '256', '0'])

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_escape(self):
        """Ensure escape() works as expected"""
        debug.trace(4, f"test_escape(); self={self}")
        text = "foo*bar"
        output = self.my_re.escape(text)
        assert(r"\*" in output)

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
