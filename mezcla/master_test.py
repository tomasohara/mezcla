#!/usr/bin/env python3
#
# note: Tana's script for running Python tests as part of workflow
#


"""Master test script for shell-scripts repo"""

# Standard modules
import math
import subprocess
import os
from typing import Dict

# Installed modules
## OLD: import yaml

# Local modules
from mezcla import debug
from mezcla.file_utils import read_yaml
from mezcla import glue_helpers as gh
from mezcla.glue_helpers import default_subtrace_level, TEMP_BASE, TEMP_FILE, PRESERVE_TEMP_FILE
from mezcla.my_regex import my_re
from mezcla import xml_utils
from mezcla import tpo_common as tpo
## TODO3: from mezcla import misc_utils
from mezcla import system
from  mezcla.system import to_int

# Environment options
# Note: These are just intended for internal options, not for end users.
#
THRESHOLDS_FILE = system.getenv_text(
    "THRESHOLDS_FILE",
    "thresholds.yaml",
    description="thresholds file for master_test.py",
)
TEST_REGEX = system.getenv_value(
    "TEST_REGEX", None,
    description="Regex for tests to include; ex: '^test_c.*' for debugging")
MYPY_TEST_REGEX = system.getenv_value(
    "MYPY_TEST_REGEX",
    TEST_REGEX,
    description="Regex for source files for mypy checks",
)
PYTEST_TEST_REGEX = system.getenv_value(
    "PYTEST_TEST_REGEX",
    TEST_REGEX,
    description="Regex for pytest",
)
MYPY_CONFIG_FILE = system.getenv_text(
    "MYPY_CONFIG_FILE", "mypy.ini",
    description="config file for mypy ",
)
MYPY_TEST_PATH = system.getenv_text(
    "MYPY_TEST_PATH",
    gh.dirname(__file__),
    description="directory with source files for mypy test",
)
PYTEST_TEST_PATH = system.getenv_text(
    "PYTEST_TEST_PATH", gh.form_path(gh.dirname(__file__), "tests"),
    description="directory with pytest tests"
)
MYPY_OUTPUT_PATH = system.getenv_text(
    "MYPY_OUTPUT_PATH", gh.form_path("output-files", "mypy_reports"),
    description="directory to save mypy reports in"
)
MYPY_WEIGHT = system.getenv_float(
    "MYPY_WEIGHT", 0.0,
    description="final weight for mypy tests"
)
MYPY_COMBINED = system.getenv_bool(
    "MYPY_COMBINED", False,
    description="Run mypy over all files at same time")
PYTEST_WEIGHT = system.getenv_float(
    "PYTEST_WEIGHT", (1.0 - MYPY_WEIGHT),
    description="final weight for pytest tests"
)
PYTEST_OPTIONS = system.getenv_value(
    "PYTEST_OPTIONS", None,
    description="Options for pytest"
)

VERBOSE_OUTPUT = system.getenv_bool(
    "VERBOSE_OUTPUT", False,
    description="Verbose output mode")

# -------------------------------------------------------------------------------
# Utility functions


def load_thresholds(filename):
    """Load test failure thresholds from a YAML file."""
    result = read_yaml(filename)
    debug.trace(5, f"load_thresholds({filename}) => {result!r}")
    return result


def round_p2str(num):
    """Round NUM using precision of 2"""
    # EX: round_p2str(1.678) => "1.68"
    # EX: round_p2str(1.6) => "1.60"
    return system.round_as_str(num, 2)


def run(command, trace_level=4, subtrace_level=None, **namespace) -> str :
    """Wrapper around subprocess.run
    Invokes COMMAND via system shell, using TRACE_LEVEL for debugging output, returning result. The command can use format-style templates, resolved from caller's namespace. The optional SUBTRACE_LEVEL sets tracing for invoked commands (default is same as TRACE_LEVEL); this works around problem with stderr not being separated, which can be a problem when tracing unit tests.
    Notes:
    - The result includes stderr, so direct if not desired (see issue):
          run("ls /tmp/fubar 2> /dev/null")
    - This is only intended for running simple commands. It would be better to create a subprocess for any complex interactions.
    - This function doesn't work fully under Win32. Tabs are not preserved, so redirect stdout to a file if needed.
    - If TEMP_FILE or TEMP_BASE defined, these are modified to be unique to avoid conflicts across processeses.
    - If OUTPUT, the result will be printed.
    """
    ## NOTE: streamlined version of gh.run
    debug.assertion(isinstance(trace_level, int))
    debug.trace(6, f"run({command}, tl={trace_level}, sub_tr={subtrace_level}")
    # Keep track of current debug level setting
    debug_level_env = os.getenv("DEBUG_LEVEL")
    if subtrace_level is None:
        subtrace_level = default_subtrace_level
    if subtrace_level != trace_level:
        system.setenv("DEBUG_LEVEL", str(subtrace_level))
    save_temp_base = TEMP_BASE
    if TEMP_BASE:
        system.setenv("TEMP_BASE", TEMP_BASE + "_subprocess_")
    save_temp_file = TEMP_FILE
    if TEMP_FILE and (PRESERVE_TEMP_FILE is not True):
        system.setenv("TEMP_FILE", TEMP_FILE + "_subprocess_")
    # Expand the command template
    # TODO: make this optional
    command_line = command
    if my_re.search("{.*}", command):
        command_line = tpo.format(command_line, indirect_caller=True, ignore_exception=False, **namespace)
    debug.trace(6 , f"issuing: {command_line}")
    # Run the command
    result = str(subprocess.run(command_line, check=False, shell=True))
    # Restore debug level setting in environment
    system.setenv("DEBUG_LEVEL", debug_level_env or "")
    system.setenv("TEMP_BASE", save_temp_base or "")
    if save_temp_file and (PRESERVE_TEMP_FILE is not True):
        system.setenv("TEMP_FILE", save_temp_file or "")
    debug.trace_fmt(7, "run(_) => {{\n{r}\n}}", r=gh.indent_lines(result))
    return result


def resolve_tools_file(filename):
    """Resolve full path for FILENAME, defaulting to <repo>/tools dir if not found"""
    full_path = filename
    if not system.file_exists(full_path):
        tools_dir = gh.form_path(gh.dirname(__file__), "..", "tools")
        debug.assertion(system.file_exists(gh.form_path(tools_dir, "run_tests.bash")))
        full_path = gh.form_path(tools_dir, filename)
    if not system.file_exists(full_path):
        full_path = gh.resolve_path(filename, heuristic=True)
    debug.trace(5, f"resolve_tools_file({filename}) => {full_path!r}")
    return full_path

# -------------------------------------------------------------------------------
# Main code

def run_mypy(thresholds: Dict[str, float]) -> int:
    """Run mypy and return the number of failures"""
    ## TODO1: rework so that failure is based on errors, not imprecision
    mypy_config_file = resolve_tools_file(MYPY_CONFIG_FILE)
    debug.assertion(system.file_exists(mypy_config_file))
    xml_report = None
    config = (
        f" --config-file {mypy_config_file}" if system.file_exists(mypy_config_file) else ""
    )
    common_mypy_options = "--check-untyped-defs --install-types --non-interactive"
    gh.full_mkdir(MYPY_OUTPUT_PATH)
    if MYPY_COMBINED:
        cmd = f"python -m mypy {MYPY_TEST_PATH} {config} --xml-report {MYPY_OUTPUT_PATH} {common_mypy_options}"
        run(cmd, shell=True, check=False)
    failed = 0

    # Read and parse xml report file
    report_file = gh.form_path(MYPY_OUTPUT_PATH, "index.xml")
    if MYPY_COMBINED and not system.file_exists(report_file):
        debug.trace(4, f"{report_file} not found, skipping mypy checks")
    else:
        if MYPY_COMBINED:
            xml_report = xml_utils.parse_xml(system.read_file(report_file))

        num_processed = 0
        for filename, threshold in thresholds.items():
            debug.trace_expr(4, filename, threshold)
            file_path = gh.resolve_path(filename)
            filename_proper = gh.basename(filename)

            # Exclude certain test files (e.g., files outside of the mezcla module)
            include = True
            if my_re.search(rf"^mezcla{os.sep}(.*__.*).+\.py$", filename):
                debug.trace(4, f"mypy: skipping dunder module {filename!r}")
                include = False
            elif MYPY_TEST_REGEX and not my_re.search(rf"{MYPY_TEST_REGEX}", file_path):
                debug.trace(5, f"Filtering test {file_path} not matching MYPY_TEST_REGEX ({MYPY_TEST_REGEX})",)
                include = False
            elif not system.file_exists(file_path):
                debug.trace(4, f"Warning: skipping missing module {filename!r}")
                include = False
            if not include:
                continue

            if VERBOSE_OUTPUT:
                if num_processed:
                    print("-" * 132)
                print(f"Running mypy over {filename_proper}")

            num_processed += 1
            if not MYPY_COMBINED:
                basename = gh.basename(filename_proper, ".py")
                mypy_output_path = gh.form_path(MYPY_OUTPUT_PATH, basename)
                cmd = f"python -m mypy {filename} {config} --xml-report {mypy_output_path} {common_mypy_options}"
                run(cmd, shell=True, check=False)
                report_file = gh.form_path(mypy_output_path, "index.xml")
                xml_report = xml_utils.parse_xml(system.read_file(report_file))
            
            # find current module name in report
            results = xml_report.find(f"./file[@name='{filename_proper}']")

            # calculate imprecise percentage and compare to threshold
            any_hints = to_int(results.get("any"))
            imprecise_hints = to_int(results.get("imprecise"))
            total_hints = to_int(results.get("total"))
            impreciseness = 0.0
            if total_hints > 0:
                impreciseness = ((any_hints + imprecise_hints) / total_hints) * 100
            debug.assertion(impreciseness <= threshold)
            debug.trace(
                5, f"{filename}, threshold: {threshold}, impreciseness: {impreciseness}"
            )
            if impreciseness > threshold:
                failed += 1

    return failed


def run_tests(thresholds: Dict[str, float]) -> int:
    """Run tests and compare the results with the allowed thresholds"""
    failed = 0
    for test_filename, threshold in thresholds.items():
        debug.trace_expr(4, test_filename, threshold)
        test_path = gh.resolve_path(test_filename)

        # Exclude certain test files (e.g., non-python test files listed in thresholds.yml)
        include = True
        if not my_re.search(r"^test_.*\.py$", gh.basename(test_filename)):
            debug.trace(5, f"Ignoring non-python test: {test_filename}")
            include = False
        elif PYTEST_TEST_REGEX and not my_re.search(rf"{PYTEST_TEST_REGEX}", test_filename):
            debug.trace(5, f"Filtering test {test_filename} not matching PYTEST_TEST_REGEX ({PYTEST_TEST_REGEX})",)
            include = False
        elif not system.file_exists(test_path):
            debug.trace(4, f"Warning: skipping missing test {test_path!r}")
            include = False
        if not include:
            continue

        # Collect test cases for the test
        ## BAD: cmd = f"pytest -k {test} --collect-only"
        cmd = f"pytest --collect-only {test_path}"
        collect_result = run(
            cmd, shell=True, text=True, capture_output=True, check=False
        )
        debug.trace_object(6, collect_result)
        total_tests = len(
            my_re.findall(
                r"<TestCaseFunction|<TestCaseClass|<Function|<Class",
                collect_result,
            )
        )
        # Compare against alternative way to detemine number of tests
        # ex: "=== 103 tests collected in 1.64s ==="
        if (total_tests == 0) or debug.debugging():
            summary_total_tests = 0
            if my_re.search(
                r"(\d+) tests collected", collect_result, flags=my_re.IGNORECASE
            ):
                summary_total_tests = system.to_int(my_re.group(1))
            debug.trace_expr(5, total_tests, summary_total_tests)
            debug.assertion(total_tests == summary_total_tests)
            total_tests = summary_total_tests if (total_tests == 0) else total_tests

        # Run tests for the test
        pytest_options = (PYTEST_OPTIONS or "")
        cmd = f"pytest {pytest_options} {test_path}"
        run_result = run(cmd)
        debug.trace_object(6, run_result)
        failed_tests = len(my_re.findall(r"FAILED", run_result))
        debug.assertion(failed_tests <= total_tests)
        # Compare against alternative way to detemine number of failures
        # ex: "=== 12 passed, 49 skipped, 13 xfailed, 29 xpassed in 4.76s ==="
        if debug.debugging():
            summary_failed_tests = 0
            if my_re.search(r"(\d+) failed", run_result, flags=my_re.IGNORECASE):
                summary_failed_tests = system.to_int(my_re.group(1))
            debug.trace_expr(5, failed_tests, summary_failed_tests)
            debug.assertion(failed_tests == summary_failed_tests)

        # Calculate the number of allowed failures
        # note: threshold is for success (e.g., 51 means 51% of tests passed)
        # TODO3: have sanity checks account for minor floatiing point differences
        required_successes = (
            math.ceil(total_tests * threshold / 100) if threshold else 0
        )
        debug.assertion(0 <= required_successes <= total_tests)
        allowed_failures = max(1 - required_successes, 0)

        # Check if the number of failed tests exceeds the allowed threshold
        if total_tests == 0:
            print(f"Warning: No tests were found for test {test_path}.")
            debug.trace_expr(5, collect_result, collect_result)
            continue
        module_failure = failed_tests and (failed_tests <= allowed_failures)
        failed_percent = round_p2str(failed_tests / total_tests * 100)
        success_percent = round_p2str(100.0 - (failed_tests / total_tests * 100))
        ## TODO3: debug.assertion(misc_utils.is_close(system.to_float(failed_percent) + system.to_float(success_percent), 100))
        debug.trace_expr(
            6,
            failed_tests,
            allowed_failures,
            total_tests,
            module_failure,
            required_successes,
        )

        # Format message to stdout: either error, warning or FYI on test summary.
        # note: format shows success rate to match batspp_report.py
        label = "Error" if module_failure else "Warning" if failed_tests else "FYI"
        ## OLD:
        ## print(f"{label}: {test_filename} {failed_tests} of {total_tests} tests failed ({failed_percent}%)",
        ##      end="")
        print(
            f"{label}: {test_filename} {failed_tests} of {total_tests} tests failed: {failed_percent}%; success ({success_percent}%); threshold={threshold}%",
            end="",
        )
        if module_failure:
            num_good = total_tests - failed_tests
            short = required_successes - num_good
            debug.assertion(0 <= required_successes <= total_tests)
            debug.assertion(0 <= short <= (total_tests - failed_tests) <= total_tests)
            print(
                (
                    f": {short} short of the {required_successes} required successes"
                    + f" (i.e., {round_p2str(threshold)}+%)"
                ),
                end="",
            )
            failed += 1
        print(".")
    return failed

    # Return amount of failed modules


# -------------------------------------------------------------------------------


def main():
    """Main function"""

    # Load the thresholds from the YAML file, falling back to defaults for all test files
    # in the tests directory (TODO: merge the two sources with file trumping default).
    # note: uses default of 25% succeses allowed just for sake of getting tests operational
    # under Github actions (TODO: lower to 50%).
    thresholds_path = resolve_tools_file(THRESHOLDS_FILE)
    mypy_thresholds = {
        module: 40.0 for module in gh.get_matching_files(f"{MYPY_TEST_PATH}/*.py")
    }
    test_thresholds = {
        test_file: 25.0 for test_file in gh.get_matching_files(f"{PYTEST_TEST_PATH}/*.py")
    }
    # note: thresholds = mypy_thresholds | test_thresholds for python 3.9+
    default_thresholds = {**mypy_thresholds, **test_thresholds}
    debug.trace_expr(5, default_thresholds, prefix="default thresholds: ")
    if system.file_exists(thresholds_path):
        new_thresholds: Dict[str, float] = load_thresholds(thresholds_path)
        for filename, threshold in new_thresholds.items():
            if my_re.search(r"^.*(tests{os.sep}).*", filename):
                test_thresholds[filename] = threshold
            elif my_re.search(r"^.*\.py$", filename):
                mypy_thresholds[filename] = threshold
            else:
                debug.trace(4, f"Warning: ignoring threshold for file {filename!r}")
    else:
        debug.trace(2, f"Warning: unable to find {thresholds_path}")
    debug.trace_expr(
        5, {**mypy_thresholds, **test_thresholds}, prefix="final thresholds"
    )

    # Run tests and compare the results with the allowed thresholds
    test_failures = 0
    mypy_failures = 0    
    if PYTEST_WEIGHT > 0:
        test_failures = run_tests(test_thresholds)
    if MYPY_WEIGHT > 0:
        mypy_failures = run_mypy(mypy_thresholds)
    failed = (mypy_failures * MYPY_WEIGHT) + (test_failures * PYTEST_WEIGHT)

    message = "All OK"
    code = 0
    if failed > 0:
        code = failed
        message = f"Error: {test_failures} module failed, and {mypy_failures} mypy problems: combined score {failed:.2f}"
    system.exit(message, status_code=code)


if __name__ == "__main__":
    main()
