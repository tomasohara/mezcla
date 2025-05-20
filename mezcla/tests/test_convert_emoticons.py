#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Test(s) for ../convert_emoticons.py
#
# Sample input and output (n.b., U+1f638 is grinning-cat character):
#
# - input:
#
#   # Example Input:
#   Nothing to test 😸
#
# - output:
#
#   # Example output:
#   Nothing to test [grinning cat face with smiling eyes]
#

"""Tests for convert_emoticons module"""

# Standard packages
## TODO: from collections import defaultdict

# Installed packages
import pytest

# Local packages
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla.unittest_wrapper import trap_exception
from mezcla import debug
from mezcla.my_regex import my_re
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                  global module object
#    TestTemplate.script_module:  path to file
import mezcla.convert_emoticons as THE_MODULE

# Constants
D = system.path_separator()

class TestIt(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    script_file = TestWrapper.get_module_file_path(__file__)

    @pytest.mark.xfail                   # TODO: remove xfail
    ## TEST: @trap_exception
    def test_over_script(self):
        """Makes sure works as expected over script itself"""
        debug.trace(4, f"TestIt.test_over_script(); self={self}")
        output = self.run_script(options="", data_file=__file__)
        # the example usage should have input emoticon changed to match output
        # note: the example comments use ... for brevity and to simply regex matching
        test_script_contents = system.read_file(__file__)
        debug.trace_expr(6, test_script_contents, max_len=8192)
        char_desc = "grinning cat face with smiling eyes"
        # ex (see above): "# Input:\n#   Nothing to test 😸\n# Output:\n#   Nothing to test [Grinning Cat ...]"
        self.do_assert(not my_re.search(fr"(\[{char_desc}\]).*\1",
                                        test_script_contents, flags=my_re.DOTALL|my_re.IGNORECASE))
        # ex (see above): "# Input:\n#   Nothing to test [grinning...]\n#\n# Output:\n#   Nothing to test [Grinning...]"
        self.do_assert(my_re.search(fr"(\[{char_desc}\]).*\1", output,
                                    flags=my_re.DOTALL|my_re.IGNORECASE))

        # Make sure no emoticon byte sequences in UTF-8 sequences for output, although in script.
        # Note: Uses broader UTF8-based tests than Unicode character DB used in script.
        # Also, regex is done over byte sequences to account for misformed input.
        ## TODO3: use testing file for data not the tested script
        script_contents = system.read_file(self.script_file)
        loose_emoticon_regex = br"[\xE0-\xFF][\x80-\xFF]{1,3}"
        # ex: "# EX: convert_emoticons("天気") => "天気"   # Japanese for weather"
        self.do_assert(my_re.search(loose_emoticon_regex, script_contents.encode()))
        output_sans_cjk_examples = my_re.sub(r"^.*(Chinese|Japanese).*$", "", output,
                                             flags=my_re.MULTILINE)
        # ex: [same as above because CJK preserved]
        bad_match = my_re.search(loose_emoticon_regex, output_sans_cjk_examples.encode())
        debug.trace_expr(5, bad_match, output_sans_cjk_examples)
        self.do_assert(not bad_match)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_over_script_sans_comments(self):
        """Makes sure works as expected over script itself"""
        debug.trace(4, f"TestIt.test_over_script_sans_comments(); self={self}")

        # Strip comments from script and run conversion over it
        script_contents = system.read_file(__file__)
        script_contents_sans_comments = my_re.sub("#.*\n", "\n", script_contents)
        debug.trace_expr(6, script_contents_sans_comments)
        system.write_file(self.temp_file, script_contents_sans_comments)
        output = self.run_script(options="", data_file=self.temp_file)

        # There should be no extended ascii bytes
        self.do_assert(not my_re.search(b"[\x80-\xFF]", script_contents_sans_comments.encode()))
        self.do_assert(not my_re.search(b"[\x80-\xFF]", output.encode()))
        return

    @trap_exception
    def test_misc(self):
        """Test direct calls for conversion"""
        debug.trace(4, f"TestIt2.test_whatever(); self={self}")
        convert_emoticons = THE_MODULE.convert_emoticons
        cool_smile = "\U0001F60E"        # 😎
        self.do_assert(convert_emoticons(cool_smile) == "[smiling face with sunglasses]")
        self.do_assert(convert_emoticons(cool_smile, strip=True) == "")
        chinese_age = "\uF9A8"           # 令 ("age" in Chinese)
        self.do_assert(convert_emoticons(chinese_age) == chinese_age)
        return


#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
