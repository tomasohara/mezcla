#!/bin/bash
#
# Run unitests and pytest files
# and generate coverage report
#

tools=$(dirname $(realpath -s $0))
base=$tools/..
mezcla=$base/mezcla
tests=$mezcla/tests

echo -e "Running tests on $tests\n"

pip uninstall mezcla &> /dev/null # Avoid conflicts with installed Mezcla

export PYTHONPATH="$mezcla/:$PYTHONPATH"
export COVERAGE_RCFILE="$base/.coveragerc"
export CHECK_COVERAGE='true'

coverage run -m pytest $tests
coverage combine
coverage html
