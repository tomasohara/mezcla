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
    
    # Track which tests we've seen to avoid double-counting
    seen_tests = set()

    # OLD: Used pytest_runtest_setup to count tests, but this doesn't properly
    # handle test collection and was checking nodeids against the wrong dictionary.
    # Also used pytest_runtest_makereport which only handled basic outcomes and
    # never incremented xfailed or xpassed counters despite having them defined.
    # The old approach had broken logic and double-counting issues for skipped tests.
    #
    # NEW: Use pytest_runtest_logreport which is called after each test phase
    # and provides proper access to test outcomes including xfail/xpass.
    # Process both 'setup' and 'call' phases because skipped tests are marked
    # during setup phase and never reach the call phase.
    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_logreport(report):
        """Called after each test phase (setup/call/teardown) to log the report."""
        outcome = yield
        
        test_id = report.nodeid
        
        # Process each test only once by checking which phase has the outcome
        if test_id not in seen_tests:
            # OLD: Didn't properly distinguish between xfailed (expected fail that failed)
            # and regular skipped tests because both appear as "skipped" in setup phase
            # NEW: Check the outcome attribute which differentiates xfailed from skipped
            
            # Handle skipped tests during 'setup' phase
            if report.when == 'setup' and report.skipped:
                seen_tests.add(test_id)
                test_results['total'] += 1
                
                # Check outcome to distinguish xfailed from regular skipped
                if hasattr(report, 'wasxfail') or (hasattr(report, 'outcome') and report.outcome == 'skipped' and 'xfail' in str(report.longrepr).lower()):
                    test_results['xfailed'] += 1
                else:
                    test_results['skipped'] += 1
            
            # Handle passed/failed tests during 'call' phase
            elif report.when == 'call':
                seen_tests.add(test_id)
                test_results['total'] += 1
                
                if report.skipped:
                    # Some xfails are marked during call phase
                    if hasattr(report, 'wasxfail'):
                        test_results['xfailed'] += 1
                    else:
                        test_results['skipped'] += 1
                        
                elif report.passed:
                    # Check if it's an unexpected pass (xpass)
                    if hasattr(report, 'wasxfail'):
                        test_results['xpassed'] += 1
                    else:
                        test_results['passed'] += 1
                        
                elif report.failed:
                    # Check if it's an expected failure (xfail)
                    if hasattr(report, 'wasxfail'):
                        test_results['xfailed'] += 1
                    else:
                        test_results['failed'] += 1

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
        # OLD: Used (total - skipped) as denominator
        # NEW: Also exclude xfailed tests since they're expected failures
        # and shouldn't count against pass percentage
        actual_total = test_results['total'] - test_results['skipped'] - test_results['xfailed']
        if actual_total == 0:
            return 0.0
        # Only count actual passes, not xpasses (those are surprises, not reliable passes)
        return (test_results['passed'] / actual_total) * 100
    
    @pytest.hookimpl(tryfirst=True)
    def pytest_sessionfinish(session):
        """Pytest hook: Called after the test session finishes."""
        pass_threshold = int(session.config.getoption("--pass-threshold"))
        pass_percentage = helper_calculate_pass_percentage()
        
        # Calculate numerator and denominator for [X/Y] display
        numerator = test_results['passed']
        denominator = test_results['total'] - test_results['skipped'] - test_results['xfailed']
    
        # Print test summary
        print("\n\nTest Summary\n" + "=" * 15)
        print(f"Total Tests: {test_results['total']}")
        print(f"Passed: {test_results['passed']}")
        print(f"Failed: {test_results['failed']}")
        print(f"Skipped: {test_results['skipped']}")
        # NEW: Actually display xfailed and xpassed counts now that they work
        print(f"Xfailed: {test_results['xfailed']}")
        print(f"Xpassed: {test_results['xpassed']}")
        print(f"Pass Percentage: {pass_percentage:.2f}% (Threshold: {pass_threshold}%) [{numerator}/{denominator}]")
        # NEW: Show denominator calculation breakdown
        print(f"Denominator: TOTAL({test_results['total']}) - SKIPPED({test_results['skipped']}) - XFAILED({test_results['xfailed']}) = {denominator}")

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
