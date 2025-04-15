#! /usr/bin/env python3
#
# Test(s) for ../bing_search.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_bing_search.py
#

"""Tests for bing_search module"""

# Standard packages
## NOTE: this is empty for now

# Installed packages
import pytest

# Local packages
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla import debug
from mezcla.my_regex import my_re

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
import mezcla.bing_search as THE_MODULE

MISSING_API_KEY = (not THE_MODULE.BING_KEY.strip())
MISSING_REASON = "BING_KEY not defined"

class TestBingSearch(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.skipif(MISSING_API_KEY, reason=MISSING_REASON)
    def test_simple_query(self):
        """Makes sure simple query works as expected"""
        debug.trace(4, f"TestIt.test_simple_query(); self={self}")
        output = self.run_script(options="my dawg and his fleas")
        for keyword in ["webSearchUrl", "snippet"]:
            self.do_assert(my_re.search(fr"\b{keyword}\b", output.strip()), f"Expected keyword {keyword}")
        return

    @pytest.mark.skipif(MISSING_API_KEY, reason=MISSING_REASON)
    def test_direct_query(self):
        """Makes sure query API works as expected"""
        debug.trace(4, f"TestIt.test_direct_query(); self={self}")
        result = THE_MODULE.bing_search("my dawg and his fleas",
                                        non_phrasal=True)
        num_expected_results = 10
        minimum_result_len = (num_expected_results // 2)
        self.do_assert(isinstance(result, dict))
        self.do_assert(len(result) >= minimum_result_len)
        good_count = 0
        for hit in result["webPages"]["value"]:
            self.do_assert(isinstance(hit, dict))
            if (("url" in hit) and ("snippet" in hit)):
                good_count += 1
        self.do_assert(good_count >= minimum_result_len)
        return

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
