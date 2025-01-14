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

test_results = {
    'total': 0,
    'passed': 0,
    'failed': 0,
    'skipped': 0,
    'xfailed': 0,
    'xpassed': 0
}

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
        """Handles exceptions interactively during test runs."""
        debug.trace(5, f"pytest_exception_interact: {node}, {call}, {report}")
        raise call.excinfo.value

    def pytest_internalerror(excrepr, excinfo):
        """Handles internal pytest errors."""
        debug.trace(5, f"pytest_internalerror: {excrepr}, {excinfo}")
        raise excinfo.value


def pytest_addoption(parser):
    """Adds the --pass-threshold option to pytest."""
    parser.addoption(
        "--pass-threshold",
        action="store",
        default=None,
        help="Pass threshold percentage for tests"
    )
    print("Pass-threshold option added to parser")


def is_threshold_tracking_enabled(config):
    """Checks if threshold tracking is enabled."""
    return config.getoption("--pass-threshold") is not None


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """Hook to execute before each test is run."""
    test_results['total'] += 1
    print(f"Test setup: {item.name}. Total tests so far: {test_results['total']}")


@pytest.hookimpl(tryfirst=True)
def pytest_runtest_makereport(item, call):
    """Hook to process test results after each test run."""
    if call.when == "call":
        if call.excinfo is None:
            if hasattr(item, "wasxfail"):
                test_results['xpassed'] += 1
                # print(f"Test unexpectedly passed (xpassed): {item.name}")
            else:
                test_results['passed'] += 1
                # print(f"Test passed: {item.name}")
        else:  # Test failed (AssertionError or other)
            if hasattr(item, "wasxfail"):
                test_results['xfailed'] += 1
                # print(f"Test failed as expected (xfailed): {item.name}")
            else:
                test_results['failed'] += 1
                # print(f"Test failed: {item.name}")
    elif call.when == "setup" and call.excinfo:
        test_results['skipped'] += 1
        # print(f"Test skipped during setup: {item.name}")


def calculate_pass_percentage():
    """Calculates the percentage of tests that passed."""
    actual_total = test_results['total'] - test_results['skipped'] - test_results['xfailed']
    if actual_total <= 0:
        return 0.0
    pass_percentage = (test_results['passed'] / actual_total) * 100
    print(f"Pass percentage calculated: {pass_percentage:.2f}%")
    return pass_percentage


def pytest_sessionfinish(session):
    """Hook to execute at the end of the pytest session."""
    pass_threshold = session.config.getoption("--pass-threshold")
    if pass_threshold is None:
        # print("No pass threshold specified; skipping pass/fail evaluation.")
        return

    pass_threshold = int(pass_threshold)
    pass_percentage = calculate_pass_percentage()

    print("\n\nTest Summary\n" + "=" * 15)
    for key, value in test_results.items():
        print(f"{key.capitalize()}: {value}")
    print(f"Pass Percentage: {pass_percentage:.2f}% (Threshold: {pass_threshold}%)")

    if pass_percentage < pass_threshold:
        print("[FAILED]")
        session.exitstatus = pytest.ExitCode.TESTS_FAILED
    else:
        print("[PASSED]")
        session.exitstatus = pytest.ExitCode.OK

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    system.print_stderr("Error: Not intended to be invoked directly")
    