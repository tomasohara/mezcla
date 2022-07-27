#!/bin/bash
#
# Run unitests and pytest files
# and generate coverage report
#

tests=$(dirname $(realpath -s $0))

echo -e "Running tests on $tests\n"

pip uninstall mezcla &> /dev/null # Avoid conflicts with installed Mezcla
export PYTHONPATH="$tests/../:$PYTHONPATH"

for file in $(ls $tests/test_*.py)
do
    python $file
    coverage run -a $file
done

coverage html --directory $tests/htmlcov
