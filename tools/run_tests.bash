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
if [ "$TEST_REGEX" != "" ]; then
    # shellcheck disable=SC2010
    tests=$(ls "$tests"/*.py | grep --perl-regexp "$TEST_REGEX")
fi

echo -e "Running tests on $tests\n"

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
    coverage run -m pytest $tests
    coverage combine
    coverage html
else
    pytest $tests
fi
