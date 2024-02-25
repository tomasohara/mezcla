#! /usr/bin/env bash
#
# Bash file for making temporary settings for the tests. This is intended
# for adhoc debugging and avoids having to specify settings seperately
# for Docker images vs. Github VM runners. This get sourced via run_tests.bash.
#
# Warning:
# - *** It is ok to check-in change in temporary changes for testing Github
#   actions on your branch. However, make sure no temporary changes are pushed
#   to main (e.g., SCP_OUTPUT=1 or any use of TEST_REGEX).
#
# Example settings:
#    export DEBUG_LEVEL=5               # run with verbose tracing
#
#    export TEST_REGEX="tips|README"    # run tests with tips or README in file
#
## export DEBUG_LEVEL=4               # use verbose tracing

# Override settings if under testing VM
# Note: 1. Most settings off so user can override when running locally,
# but, it is awkward to do so for docker or Github runner jobs.
# 2. For other Github Actions env. vars, see https://www.theserverside.com/blog/Coffee-Talk-Java-News-Stories-and-Opinions/environment-variables-full-list-github-actions
MIN_DEBUG_LEVEL=2
if [ "$DEPLOYMENT_BASEPATH" == "/opt/runner" ]; then
    MIN_DEBUG_LEVEL=4
fi
DEBUG_LEVEL="${DEBUG_LEVEL:-0}"
if [ "$DEBUG_LEVEL" -lt "$MIN_DEBUG_LEVEL" ]; then
    export DEBUG_LEVEL=MIN_DEBUG_LEVEL
fi
if [ "$DEBUG_LEVEL" -ge 4 ]; then
    export PYTEST_OPTIONS="-v -s"
fi
export TEST_REGEX=unittest_wrapper
