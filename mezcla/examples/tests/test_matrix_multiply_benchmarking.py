#! /usr/bin/env python3
#
# Test(s) for ../test_matrix_multiply_benchmarking.py
#
# Notes:
# - Sample output tested
#   $ SKIP_CUDA=1 ../matrix_multiply_benchmarking.py --numba --numpy
#   numpy	0.304ms
#   numba	11817.419ms
# - This can be run as follows (e.g., from root of repo):
#   $ pytest ./mezcla/examples/tests/test_test_matrix_multiply_benchmarking.py
#

## TODO1: [Warning] Make sure this template adhered to as much as possible. For,
## example, only delete todo comments not regular code, unless suggested in tip).
## In particular, it is critical that script_module gets initialized properly.

"""TODO: Tests for test_matrix_multiply_benchmarking module"""

# Standard modules
## TODO: from collections import defaultdict

# Installed modules
import pytest

# Local modules
from mezcla.unittest_wrapper import TestWrapper
## TODO: from mezcla.unittest_wrapper import trap_exception
from mezcla import debug
## TODO: from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                        global module object
#    TestIt.script_module:              path to file
try:
    import mezcla.examples.matrix_multiply_benchmarking as THE_MODULE
except:
    THE_MODULE = None
    system.print_exception_info("matrix_multiply_benchmarking import")
#
# Note: sanity test for customization (TODO: remove if desired)
if not my_re.search(__file__, r"\btemplate.py$"):
    debug.assertion("mezcla.template" not in str(THE_MODULE))

## TODO:
## # Environment options
## # Note: These are just intended for internal options, not for end users.
## # It also allows for enabling options in one place.
## #
## FUBAR = system.getenv_bool(
##     "FUBAR", False,
##     description="Fouled Up Beyond All Recognition processing")

#------------------------------------------------------------------------

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.xfail                   # TODO: remove xfail
    ## DEBUG: @trap_exception            # TODO: remove when debugged
    def test_01_data_file(self):
        """Tests run_script w/ data file"""
        debug.trace(4, f"TestIt.test_01_data_file(); self={self}")
        output = self.run_script(options="", env_options="", skip_stdin=True)
        # note: make sure some time mentioned for numpy
        # ex: numpy	0.304ms
        self.do_assert(my_re.search(r"numpy.*\d+.\d+\s*ms", output.strip()))
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    ## DEBUG: @trap_exception            # TODO: remove when debugged
    def test_02_something_else(self):
        """Test for something_else: TODO..."""
        debug.trace(4, f"TestIt.test_02_something_else(); self={self}")
        self.do_assert(False)
        ## ex: self.do_assert(THE_MODULE.TODO_function() == TODO_value)
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    ## TODO2: here and elsewhere: invoke_tests(__file__)
    pytest.main([__file__])
