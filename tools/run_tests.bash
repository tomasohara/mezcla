#!/bin/bash
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
#
# Usage:
# $ ./tools/run_tests.bash
# $ ./tools/run_tests.bash --coverage
#

tools="$(dirname "$(realpath -s "$0")")"
base="$tools/.."
mezcla="$base/mezcla"
tests="$mezcla/tests"
example_tests="$mezcla/examples/tests"
TEST_REGEX="${TEST_REGEX:-"."}"
# Note: TEST_REGEX is for only running the specified tests, 
# and, FILTER_REGEX is for disabling particular tests.
# Both are meant as expedients, not long-term solutions.
## TEMP: DEFAULT_FILTER_REGEX="(test_audio|test_extract_document_text|test_format_profile|test_hugging_face_speechrec|test_hugging_face_translation|test_keras_param_search|test_kenlm_example|test_spell|test_text_processing)"
DEFAULT_FILTER_REGEX="(not-a-real-test.py)"
FILTER_REGEX="${FILTER_REGEX:-"$DEFAULT_FILTER_REGEX"}"
# shellcheck disable=SC2010
if [[ ("$TEST_REGEX" != ".") || ("$FILTER_REGEX" != "") ]]; then
    ## OLD:
    ## tests=$(ls "$tests"/*.py | grep --perl-regexp "$TEST_REGEX")
    ## example_tests=$(ls "$example_tests"/*.py | grep --perl-regexp "$TEST_REGEX")
    tests=$(ls "$tests"/*.py | grep --perl-regexp "$TEST_REGEX" | grep --invert-match --perl-regexp "$FILTER_REGEX")
    example_tests=$(ls "$example_tests"/*.py | grep --perl-regexp "$TEST_REGEX" | grep --invert-match --perl-regexp "$FILTER_REGEX")
fi

echo -e "Running tests on $tests; also running $example_tests\n"
echo -n "via "
python3 --version

# Remove mezcla package if running under Docker (or act)
# TODO2: check with Bruno whether still needed
if [ "$USER" == "docker" ]; then
    pip uninstall mezcla &> /dev/null  # Avoid conflicts with installed Mezcla
fi

export PYTHONPATH="$mezcla/:$PYTHONPATH"

# Run with coverage enabled
# shellcheck disable=SC2046,SC2086
if [ "$1" == "--coverage" ]; then
    export COVERAGE_RCFILE="$base/.coveragerc"
    export CHECK_COVERAGE='true'
    coverage erase
    coverage run -m pytest $tests $example_tests
    coverage combine
    coverage html
else
    pytest $tests $example_tests
fi
