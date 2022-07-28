#!/bin/bash
#
# Run unitests and pytest files
# and generate coverage report
#

tests=$(dirname $(realpath -s $0))

echo -e "Running tests on $tests\n"

pip uninstall mezcla &> /dev/null # Avoid conflicts with installed Mezcla

export PYTHONPATH="$tests/../:$PYTHONPATH"

coverage run -m pytest $tests
coverage html --directory $tests/htmlcov
