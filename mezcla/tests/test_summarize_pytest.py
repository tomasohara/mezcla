#! /usr/bin/env python3
#
# Test(s) for ../summarize_pytest.py
#
# Notes:
# - This can be run as follows (e.g., from root of repo):
#   $ pytest ./mezcla/examples/tests/test_summarize_pytest.py
#
#...............................................................................
# Sample tested input:
#
#   =================== 1 passed, 3 skipped, 3 xpassed in 1.23s ====================
#   ============================== 2 xpassed in 0.73s ==============================
#   ======================= 1 xfailed, 7 warnings in 36.99s ========================
#   ============================== 2 skipped in 0.24s ==============================
#   ======================== 1 xfailed, 1 xpassed in 1.64s =========================
#
# Alternative input:
#  tests/test_example.09jan25.12.out:================================= 22 failed, 44 passed, 4 skipped in 2.19s =================================
#  tests/test_another.09jan25.13.out:================================= 10 passed, 2 xfailed, 1 xpassed in 1.50s =================================
#  tests/test_third.09jan25.14.out:================================= 5 failed, 15 passed in 0.75s =================================
#

"""Tests for summarize_pytest module"""

# Standard modules
## TODO: from typing import Optional

# Installed modules
import pytest

# Local modules
from mezcla import debug
from mezcla.my_regex import my_re
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper, invoke_tests

# Note: Two references are used for the module to be tested:
#    THE_MODULE:               module object (e.g., <module 'mezcla.main' ...>)
#    TestIt.script_module:     dotted module path (e.g., "mezcla.main")
THE_MODULE = None
try:
    import mezcla.summarize_pytest as THE_MODULE
except:
    system.print_exception_info("summarize_pytest import") 

#------------------------------------------------------------------------

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    # note: script_module used in argument parsing sanity check (e.g., --help)
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    def setUp(self):
        """Per-test setup"""
        #
        debug.trace(6, f"TestIt.setUp(); self={self}")
        # note: must do parent processing first (e.g., for temp file support)
        super().setUp()
        
        # Create sample pytest output lines for testing
        self.sample_lines = [
            "tests/test_example.09jan25.12.out:================================= 22 failed, 44 passed, 4 skipped in 2.19s =================================",
            "tests/test_another.09jan25.13.out:================================= 10 passed, 2 xfailed, 1 xpassed in 1.50s =================================",
            "tests/test_third.09jan25.14.out:================================= 5 failed, 15 passed in 0.75s ================================="
        ]
        # TODO: debug.trace_current_context(level=debug.QUITE_DETAILED)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_01_data_file(self):
        """Tests run_script w/ data file"""
        # Warning: see notes above about potential issues with run_script-based tests.
        debug.trace(4, f"TestIt.test_01_data_file(); self={self}")
        system.write_lines(self.temp_file, self.sample_lines)
        output = self.run_script(options="", env_options="",
                                 data_file=self.temp_file)
        self.do_assert(my_re.search(r"Timestamp.*Pass.*Fail", output.strip()))
        self.do_assert("09jan25.12" in output)
        self.do_assert("44" in output)  # passed count
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_02_parse_single_line(self):
        """Test for parsing a single pytest output line"""
        debug.trace(4, f"TestIt.test_02_parse_single_line(); self={self}")
        summarizer = THE_MODULE.PytestSummarizer()
        result = summarizer.parse_pytest_line(self.sample_lines[0])
        
        self.do_assert(result is not None)
        self.do_assert(result.passed == 44)
        self.do_assert(result.failed == 22)
        self.do_assert(result.skipped == 4)
        self.do_assert(abs(result.duration - 2.19) < 0.01)
        self.do_assert(result.timestamp == '09jan25.12')
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_03_process_multiple_lines(self):
        """Test processing multiple pytest output lines"""
        debug.trace(4, f"TestIt.test_03_process_multiple_lines(); self={self}")
        summarizer = THE_MODULE.PytestSummarizer()
        results = summarizer.process(self.sample_lines)
        
        self.do_assert(len(results) == 3)
        self.do_assert(results[0].timestamp == '09jan25.12')
        self.do_assert(results[1].timestamp == '09jan25.13')
        self.do_assert(results[2].timestamp == '09jan25.14')
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_04_test_result_calculations(self):
        """Test TestResult calculations for total tests and OK rate"""
        debug.trace(4, f"TestIt.test_04_test_result_calculations(); self={self}")
        
        result = THE_MODULE.TestResult(
            passed=10, failed=5, xfailed=2, xpassed=1
        )
        
        # Test without treating xresults
        self.do_assert(result.total_tests(treat_xresults=False) == 15)  # 10 + 5
        self.do_assert(abs(result.ok_rate(treat_xresults=False) - 66.67) < 0.1)
        
        # Test with treating xresults
        self.do_assert(result.total_tests(treat_xresults=True) == 18)  # 10 + 5 + 2 + 1
        expected_ok = (10 + 1) * 100.0 / 18  # passed + xpassed
        self.do_assert(abs(result.ok_rate(treat_xresults=True) - expected_ok) < 0.1)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_05_ignore_timestamp(self):
        """Test ignoring timestamp requirement"""
        debug.trace(4, f"TestIt.test_05_ignore_timestamp(); self={self}")
        
        line_without_timestamp = "================================= 10 passed in 1.0s ================================="
        summarizer = THE_MODULE.PytestSummarizer(ignore_timestamp=True)
        result = summarizer.parse_pytest_line(line_without_timestamp)
        self.do_assert(result is not None)
        self.do_assert(result.timestamp == 'n/a')
        self.do_assert(result.passed == 10)
        self.do_assert(result.total_tests() == 10)
        self.do_assert(abs(result.duration - 1.0) < 0.01)

        line_without_timestamp = "=== 1 failed, 5 passed, 2 skipped, 17 xfailed, 39 xpassed, 13 warnings in 139.11s (0:02:19) ==="
        summarizer = THE_MODULE.PytestSummarizer(ignore_timestamp=True)
        result = summarizer.parse_pytest_line(line_without_timestamp)
        self.do_assert(result is not None)
        self.do_assert(result.timestamp == 'n/a')
        self.do_assert(result.failed == 1)
        self.do_assert(result.passed == 5)
        self.do_assert(result.skipped == 2)
        self.do_assert(result.xfailed == 17)
        self.do_assert(result.xpassed == 39)
        self.do_assert(result.total_tests(treat_xresults=False) == 6)
        self.do_assert(result.total_tests(treat_xresults=True) == 62)
        self.do_assert(abs(result.duration - 139) < 0.5)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_06_combine_results(self):
        """Test combining results with same timestamp"""
        debug.trace(4, f"TestIt.test_06_combine_results(); self={self}")
        
        lines_same_timestamp = [
            "test1.09jan25.out:================================= 10 passed in 1.0s =================================",
            "test2.09jan25.out:================================= 5 passed, 2 failed in 0.5s ================================="
        ]
        
        summarizer = THE_MODULE.PytestSummarizer(combine=True)
        results = summarizer.process(lines_same_timestamp)
        
        self.do_assert(len(results) == 1)
        self.do_assert(results[0].passed == 15)  # 10 + 5
        self.do_assert(results[0].failed == 2)
        self.do_assert(abs(results[0].duration - 1.5) < 0.01)  # 1.0 + 0.5
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_07_format_output(self):
        """Test formatting output as string table"""
        debug.trace(4, f"TestIt.test_07_format_output(); self={self}")
        
        summarizer = THE_MODULE.PytestSummarizer()
        results = summarizer.process(self.sample_lines[:1])
        output = summarizer.format_output(results)
        
        self.do_assert("Timestamp" in output)
        self.do_assert("Pass" in output)
        self.do_assert("OK-pct" in output)
        self.do_assert("09jan25.12" in output)
        self.do_assert("44" in output)  # passed count
        self.do_assert("22" in output)  # failed count
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_08_cli_header_only(self):
        """Test CLI with header-only option"""
        debug.trace(4, f"TestIt.test_08_cli_header_only(); self={self}")
        
        system.write_lines(self.temp_file, self.sample_lines)
        output = self.run_script(
            options=f"--{THE_MODULE.HEADER_ONLY_OPT}",
            data_file=self.temp_file
        )
        
        # Should have header but no data
        self.do_assert("Timestamp" in output)
        self.do_assert("09jan25" not in output)  # No data rows
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_09_cli_treat_xresults(self):
        """Test CLI with treat-xresults option"""
        debug.trace(4, f"TestIt.test_09_cli_treat_xresults(); self={self}")
        
        # Use line with xfailed and xpassed
        system.write_lines(self.temp_file, self.sample_lines)
        output = self.run_script(
            options=f"--{THE_MODULE.TREAT_XRESULTS_OPT}",
            data_file=self.temp_file
        )
        
        self.do_assert("09jan25.13" in output)
        # With treat_xresults, total should be 13 (10 + 2 + 1)
        self.do_assert(my_re.search(r"\s+13\s+", output))
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
