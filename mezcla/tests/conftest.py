#! /usr/bin/env python3
#
# This currently includes adhoc code for modifying how the tests are run.
# For example, there is an attempt at getting pytest not to swallow exceptions.
# In addition, there is code for refined results reporting with thresholding.
# Features are disabled by default so that pytest runs normally.
#

"""Adhoc configuration for pytest: disabled by default"""

# Standard packages
## OLD: import os

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla import system

# Environment options
ENABLE_PYTEST_RAISE = system.getenv_bool(
    "ENABLE_PYTEST_RAISE", False,
    desc="Raise exceptions in test code")
ENABLE_PYTEST_REPORTING = system.getenv_bool(
    "ENABLE_PYTEST_REPORTING", False,
    desc="Apply hooks for pytest threshold checks")

#--------------------------------------------------------------------------------

# Add optional hooks to disable exception swallowing
if ENABLE_PYTEST_RAISE:
    # Note:
    # - Better to Use @trap_exception: See unittest_wrapper.py
    #   and tests/template.py. In addition, using --capture=none can
    #   be helpful and likewise --runxfail for tests marked xfail.
    # - Based on https://stackoverflow.com/questions/62419998/how-can-i-get-pytest-to-not-catch-exceptions.
    # - Also see https://docs.pytest.org/en/7.1.x/reference/reference.html.

    def pytest_exception_interact(node, call, report):
        """Called when an exception was raised which can potentially be interactively handled"""
        debug.trace(5, f"pytest_exception_interact{((node, call, report))}")
        raise call.excinfo.value

    def pytest_internalerror(excrepr, excinfo):
        """Return True to suppress the fallback handling of printing an INTERNALERROR message directly to sys.stderr"""
        debug.trace(5, f"pytest_internalerror{(excrepr, excinfo)}")
        raise excinfo.value

#--------------------------------------------------------------------------------
# Note: this is experimental code that was pre-maturely commited

# Add optional hooks to allow for better test reporting along with thresholds.
if ENABLE_PYTEST_REPORTING:
    # TODO2:
    # - Document an overview of the processing (e.g., high-level intention)
    # - Explain how to invoke.
    # - Provide pointers to similar code.
    # - Don't commit such new code without warning!
    
    # Dictionary to store test results
    test_results = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'xfailed': 0,
        'xpassed': 0
    }

    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_setup(item):
        """Called before each test is run. Ensure total count is unique per test."""
        if item.nodeid not in test_results:
            test_results['total'] += 1
            test_results[item.nodeid] = True
    
    @pytest.hookimpl(tryfirst=True)
    def pytest_runtest_makereport(item, call):
        """Called to create a test report for each test phase."""
        report = pytest.TestReport.from_item_and_call(item, call)
    
        # Count passed, failed, and skipped tests
        if report.when == "call":
            if report.outcome == "passed":
                test_results['passed'] += 1
            elif report.outcome == "skipped":
                test_results['skipped'] += 1
            elif report.outcome == "failed":
                test_results['failed'] += 1
    
        if report.outcome == "skipped" and call.excinfo is None:
            test_results['skipped'] += 1
    
    def pytest_addoption(parser):
        """Add custom options to pytest command-line."""
        ## TODO4: Use getenv_float for default to simplify usgae
        parser.addoption(
            "--pass-threshold",
            action="store",
            default="80",
            help="Pass threshold percentage for tests",
        )
    
    def helper_calculate_pass_percentage():
        """Calculate the pass percentage for the test session."""
        actual_total = test_results['total'] - test_results['skipped']
        if actual_total == 0:
            return 0.0
        return (test_results['passed'] / actual_total) * 100
    
    @pytest.hookimpl(tryfirst=True)
    def pytest_sessionfinish(session):
        """Pytest hook: Called after the test session finishes."""
        pass_threshold = int(session.config.getoption("--pass-threshold"))
        pass_percentage = helper_calculate_pass_percentage()
    
        # Print test summary
        print("\n\nTest Summary\n" + "=" * 15)
        print(f"Total Tests: {test_results['total']}")
        print(f"Passed: {test_results['passed']}")
        print(f"Failed: {test_results['failed']}")
        print(f"Skipped: {test_results['skipped']}")
        print(f"Pass Percentage: {pass_percentage:.2f}% (Threshold: {pass_threshold}%)")
    
        # Set exit status based on pass percentage
        if pass_percentage < pass_threshold:
            print("[FAILED]")
            session.exitstatus = pytest.ExitCode.TESTS_FAILED
        else:
            session.exitstatus = pytest.ExitCode.OK
            print("[PASSED]")

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    system.print_stderr("Error: Not intended to be invoked directly")
