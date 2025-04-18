#! /usr/bin/env bash
#
# Run unit tests and pytest files
# and generate coverage report
#
# Note:
# - The status of the last command determines whether the dockerfile run fails.
# - This is normally pytest which returns success (0) if no tests fail,
#   excluding tests marked with xfail.
# - Disables nitpicking shellcheck:
#   SC2010: Don't use ls | grep
#   SC2046: Quote this to prevent word splitting.
#   SC2086: Double quote to prevent globbing and word splitting.
# - Environment options:
#   TEST_REGEX: tests to include
#   FILTER_REGEX: tests to exclude
#   DRY_RUN:-just show commands to be run
#   INVOKE_PYTEST_DIRECTLY: uses pytest instead of master_test.py wrapper
#   PYTEST_OPTIONS: options for pytest
#   RUN_PYTHON_TESTS: (deprecated) invoke master_test.py
#
# TODO2:
# - Document environment variables (e.g. overrides in _temp_test_settings.bash):
#   DEBUG_LEVEL, TRACE, VERBOSE, TEST_REGEX, FILTER_REGEX
#
# Usage:
# $ ./tools/run_tests.bash
# $ ./tools/run_tests.bash --coverage
#

# Set bash regular and/or verbose tracing
DEBUG_LEVEL=${DEBUG_LEVEL:-0}
if [ "$DEBUG_LEVEL" -ge 3 ]; then
    echo "in $0 $* [$(date)]"
fi
if [ "${TRACE:-0}" = "1" ]; then
    set -o xtrace
fi
if [ "${VERBOSE:-0}" = "1" ]; then
    set -o verbose
fi

# Get directory locations
dir=$(dirname "${BASH_SOURCE[0]}")
base="$dir/.."
mezcla="$base/mezcla"
tests="$mezcla/tests"
example_tests="$mezcla/examples/tests"

# Optionally source temporary settings script
temp_script="$dir/_temp_test_settings.bash"
if [ -e "$temp_script" ]; then
    env_before=$(printenv)
    source "$temp_script"
    env_after=$(printenv)
    if [ "$env_before" != "$env_after" ]; then
        echo "FYI: environment changes made via $temp_script"
    fi
fi
##
## TEMP:
echo "DEBUG_LEVEL=$DEBUG_LEVEL"

# Get tests to run
DEFAULT_TEST_REGEX="."
TEST_REGEX="${TEST_REGEX:-$DEFAULT_TEST_REGEX}"
# Note: TEST_REGEX is for only running the specified tests, 
# and, FILTER_REGEX is for disabling particular tests.
# Both are meant as expedients, not long-term solutions.
## TEMP: DEFAULT_FILTER_REGEX="(test_audio|test_extract_document_text|test_format_profile|test_hugging_face_speechrec|test_hugging_face_translation|test_keras_param_search|test_kenlm_example|test_spell|test_text_processing)"
DEFAULT_FILTER_REGEX="(not-a-real-test.py)"
FILTER_REGEX="${FILTER_REGEX:-"$DEFAULT_FILTER_REGEX"}"
# shellcheck disable=SC2010
if [[ ("$TEST_REGEX" != "$DEFAULT_TEST_REGEX") || ("$FILTER_REGEX" != "$DEFAULT_FILTER_REGEX") ]]; then
    tests=$(ls "$tests"/*.py | grep --perl-regexp "$TEST_REGEX" | grep --invert-match --perl-regexp "$FILTER_REGEX")
    example_tests=$(ls "$example_tests"/*.py | grep --perl-regexp "$TEST_REGEX" | grep --invert-match --perl-regexp "$FILTER_REGEX")
fi
#
echo -n "Running tests on $tests"
if [ "$example_tests" == "" ]; then
    echo "; running no example tests"
else
    echo "; also running $example_tests"
fi
echo ""
echo -n "via "
python3 --version

# Just echo command if dry run
pre_cmd=""
if [ "${DRY_RUN:-0}" == 1 ]; then
   pre_cmd="echo"
fi

# Remove mezcla package if running under Docker (or act)
# TODO2: check with Bruno whether still needed
if [ "$USER" == "docker" ]; then
    pip uninstall mezcla &> /dev/null  # Avoid conflicts with installed Mezcla
fi

# Make sure mezcla in python path, along with main tests directory.
# Note: Latter required for test_mezcla_to_standard.py
export PYTHONPATH="$mezcla/:$mezcla/tests:$PYTHONPATH"

# Get environment overrides
# TODO2: cleanup stuff inherited from shell-script repo
# shellcheck disable=SC2046,SC2086
# TODO3: Get optional environment settings from _test-config.bash
## DEBUG: export DEBUG_LEVEL=6
## TEST: export TEST_REGEX="calc-entropy-tests"
# Show environment if detailed debugging
## OLD: DEBUG_LEVEL=${DEBUG_LEVEL:-0}
if [ "$DEBUG_LEVEL" -ge 5 ]; then
    ## OLD: echo "in $0 $*"
    echo "Environment: {"
    printenv | sort | perl -pe "s/^/    /;"
    echo "   }"
fi

# Run the python tests 
# note: the python stdout and stderr streams are unbuffered so interleaved
## OLD: dir=$(dirname "${BASH_SOURCE[0]}")
test_result=0
if [ "$1" == "--coverage" ]; then
    $pre_cmd export COVERAGE_RCFILE="$base/.coveragerc"
    $pre_cmd export CHECK_COVERAGE='true'
    $pre_cmd coverage erase
    $pre_cmd coverage run -m pytest $tests $example_tests
    $pre_cmd coverage combine
    $pre_cmd coverage html
    test_result="$?"
elif [ "${INVOKE_PYTEST_DIRECTLY:-0}" == "1" ]; then
    # note: Runs pytest directly, which is useful for pin-pointing errors
    # in GitHub actions web interface.
    pytest_options="${PYTEST_OPTIONS:-}"
    $pre_cmd pytest $pytest_options $tests $example_tests
    test_result="$?"    
elif [ "${RUN_PYTHON_TESTS:-1}" == "1" ]; then
    # note: use master test script allowing for thresholds and mypy usage
    export PYTHONUNBUFFERED=1
    echo -n "Running tests under "
    python3 --version
    python3 "$mezcla"/master_test.py
    test_result="$?"
else
    echo "Warning: not running tests"
fi

# End of processing
if [ "$DEBUG_LEVEL" -ge 3 ]; then
    echo "out $0 [$(date)]"
fi

# Return status code used by Github actions
## TODO3: integrate support for Jupyter notebooks tests and use combined result;
## see run_tests.bash in shell-scripts repo.
exit "$test_result"
