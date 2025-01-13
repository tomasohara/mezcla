#! /usr/bin/env python
#
# TLDR: Attempt at getting maldito pytest not to swallow exceptions.
#
# Note:
# - *** This doesn't work: instead use trap_exception decorator in unittest_wrapper.py.
# - Based on https://stackoverflow.com/questions/62419998/how-can-i-get-pytest-to-not-catch-exceptions.
# - See https://docs.pytest.org/en/7.1.x/reference/reference.html.
#

"""Configuration so that pytest doesn't swallow exceptions"""

# Standard packages
## OLD: import os

# Installed packages
## TODO: import pytest
import pytest

# Local packages
from mezcla import debug
from mezcla import system

# Have pytest enable exceptions
ENABLE_PYTEST_RAISE = system.getenv_bool('_PYTEST_RAISE', False,
                                         desc="Raise exceptions in test code")

# Dictionary to store test results
test_results = {'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0}

if ENABLE_PYTEST_RAISE:
    ## OLD
    ## @pytest.hookimpl(tryfirst=True)
    ## def pytest_exception_interact(call):
    ##     debug.trace(5, "pytest_exception_interact({call})")
    ##     raise call.excinfo.value
    ##
    ## @pytest.hookimpl(tryfirst=True)
    ## def pytest_internalerror(excinfo):
    ##     debug.trace(5, "pytest_internalerror({excinfo})")
    ##     raise excinfo.value
    
    def pytest_exception_interact(node, call, report):
        """Called when an exception was raised which can potentially be interactively handled"""
        debug.trace(5, f"pytest_exception_interact{((node, call, report))}")
        raise call.excinfo.value

    def pytest_internalerror(excrepr, excinfo):
        """Return True to suppress the fallback handling of printing an INTERNALERROR message directly to sys.stderr"""
        debug.trace(5, f"pytest_internalerror{(excrepr, excinfo)}")
        raise excinfo.value

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
