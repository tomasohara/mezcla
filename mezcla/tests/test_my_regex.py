#! /usr/bin/env python3
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
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla import debug

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
import mezcla.my_regex as THE_MODULE

# Constants
MEZCLA_REGEX = "M[e]zcl[a]"


class TestMyRegex(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    my_re = THE_MODULE.my_re            # TODO3: make global to cut down self usages

    def setUp(self):
        """Performs test setup with capsys disabled
           Note: This works around quirk with pytest stderr capturing"""
        try:
            with self.capsys.disabled():
                debug.trace(6, f"TestIt.setUp(); self={self}")
                super().setUp()
                debug.trace_current_context(level=debug.QUITE_DETAILED)
        except:
            # note: trace level high so as not to affect normal testing
            debug.trace_exception(7, "TestMyRegex.setUp")
            super().setUp()
   
    def helper_my_regex(self, regex, text, is_match=0):
        """Helper functions for my_regex"""
        ## TODO2: rename as get_regex_search_result
        if is_match:
            self.my_re.match(regex, text, 0)
        else:
            self.my_re.search(regex, text)
        output = self.my_re.get_match()
        return output
    
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_search(self):
        """Ensure search() works as expected"""
        debug.trace(4, f"test_search(); self={self}")
        text = "The quick brown fox jumps over the lazy dog."
        regex = r"\w{5}"
        output = self.helper_my_regex(regex, text)
        assert (output.group() == "quick" and output.span() == (4, 9))
    
    def test_search_alt(self):
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
        text = "1 kiss is all takes."
        regex = r"\d+"
        output = self.helper_my_regex(regex, text, is_match=1)
        assert(output.group() == "1" and output.span() == (0, 1))
        ## TODO: return the matched value (solved: use group() after my_re.get_match())
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
        # get_match() returns the last the result of match
        text = "333 little birds"
        regex = r"\d+"
        output = self.helper_my_regex(regex, text, is_match=1)
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

    def check_f_string(self, expected=True):
        """Check that f-string warning is ISSUED"""
        debug.trace(4, f"check_f_string({expected})")
        self.my_re.search("{fubar}", "foobar")
        captured_stderr = self.get_stderr()
        debug.trace_expr(4, captured_stderr, max_len=4096)
        has_warning = bool(self.my_re.search("Warning:.*f-string", captured_stderr))
        self.do_assert(has_warning == expected)
        
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_f_string_warning(self):
        """Ensure warning given about f-string like regex"""
        # Make sure shown by default
        debug.trace(4, f"in test_f_string(); self={self}")
        self.monkeypatch.setattr(THE_MODULE, 'REGEX_WARNINGS', True)
        self.check_f_string(expected=True)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_no_f_string_warning(self):
        """Make sure f-string warning can be disabled"""
        debug.trace(4, f"in test_no_f_string_warning(); self={self}")
        self.monkeypatch.setattr(THE_MODULE, 'REGEX_WARNINGS', False)
        self.check_f_string(expected=False)

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

    def check_pattern_helper(self, regex, expect_has_warning):
        """Make sure check_pattern warning for REGEX matches EXPECTED_HAS_WARNING"""
        # Note: Used in global test below, using separate tests due to capsys quirks.
        ## DEBUG: debug.trace(4, f"check_pattern_helper{(self, regex, expect_has_warning)}")
        ## TODO3: self.capsys.disabled() ...
        self.my_re.check_pattern(regex)
        captured_stderr = self.get_stderr()
        actual_has_warning = bool(self.my_re.search("Warning", captured_stderr))
        assert actual_has_warning == expect_has_warning


@pytest.mark.xfail                   # TODO: remove xfail
@pytest.mark.parametrize(
    ## TODO3: use unittest_parametrize (see test_mezcla_to_standard.py and https://pypi.org/project/unittest-parametrize)
    "regex, expect_warning",
    [
        ("{regex_var}", True),
        (b"{binary_regex_var}", True),
        ("regex_text", False),
        (b"binary_regex_text", False),
    ])
def test_check_pattern(regex, expect_warning, capsys):
    """Ensure check_pattern issues warning for REGEX if EXPECT_WARNING"""
    try:
        with capsys.disabled():
            debug.trace(4, f"test_check_pattern{(regex, expect_warning)}")
            debug.trace_expr(5, capsys)
            test_inst = TestMyRegex()
        test_inst.capsys = capsys
        test_inst.check_pattern_helper(regex, expect_warning)
    except AssertionError:
        debug.trace_exception(7, "test_check_pattern [assertion]")
        raise
    except:
        debug.trace_exception(5, "test_check_pattern [non-assertion]")

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
