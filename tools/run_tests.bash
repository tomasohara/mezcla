#!/bin/bash
#
# Run unitests and pytest files
# and generate coverage report
#

tools=$(dirname $(realpath -s $0))
mezcla=$tools/../mezcla
tests=$mezcla/tests

echo -e "Running tests on $tests\n"

pip uninstall mezcla &> /dev/null # Avoid conflicts with installed Mezcla

export PYTHONPATH="$mezcla/:$PYTHONPATH"

coverage run -m pytest $tests
coverage html
