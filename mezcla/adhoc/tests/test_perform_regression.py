#! /usr/bin/env python3
#
# TODO: Test(s) for ../perform_regression.py
#
# Notes:
# - It would be a good idea to compare results versus commerial statistics
#   package (or at least Excel).
# - This can be run as follows (e.g., from root of repo):
#   $ pytest ./mezcla/adhoc/tests/test_perform_regression.py
#................................................................................
# Sample tested output (see input data below):
#
#   Call:
#   lm(formula = height ~ weight, data = data)
#   
#   Residuals:
#         Min        1Q    Median        3Q       Max 
#   -0.021355 -0.007024  0.002112  0.011106  0.014011 
#   
#   Coefficients:
#                Estimate Std. Error t value Pr(>|t|)    
#   (Intercept) 0.6484604  0.0292218   22.19 1.02e-11 ***
#   weight      0.0161443  0.0004679   34.50 3.60e-14 ***
#   ---
#   Signif. codes:  0 ‘***’ 0.001 ‘**’ 0.01 ‘*’ 0.05 ‘.’ 0.1 ‘ ’ 1
#   
#   Residual standard error: 0.01232 on 13 degrees of freedom
#   Multiple R-squared:  0.9892,	Adjusted R-squared:  0.9884 
#   F-statistic:  1190 on 1 and 13 DF,  p-value: 3.604e-14
#

"""Tests for perform_regression module"""

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
THE_MODULE = None
try:
    import mezcla.adhoc.perform_regression as THE_MODULE
except:
    system.print_exception_info("perform_regression import") 

## TODO:
## # Environment options
## # Note: These are just intended for internal options, not for end users.
## # It also allows for enabling options in one place.
## #
## FUBAR = system.getenv_bool(
##     "FUBAR", False,
##     description="Fouled Up Beyond All Recognition processing")

# Sample data
# Height in meters vs. weight in kilograms
# via https://en.wikipedia.org/wiki/Simple_linear_regression
HEIGHT = "height 1.47 1.50 1.52 1.55 1.57 1.60 1.63 1.65 1.68 1.70 1.73 1.75 1.78 1.80 1.83".split()
WEIGHT = "weight 52.21 53.12 54.48 55.84 57.20 58.57 59.93 61.29 63.11 64.47 66.28 68.10 69.92 72.19 74.46".split()
debug.assertion(len(HEIGHT) == len(WEIGHT))

#------------------------------------------------------------------------

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    #
    # TODO: use_temp_base_dir = True            # treat TEMP_BASE as directory
    # note: temp_file defined by parent (along with script_module, temp_base, and test_num)

    @pytest.mark.xfail                   # TODO: remove xfail
    ## DEBUG: @trap_exception            # TODO: remove when debugged
    def test_01_data_file(self):
        """Tests run_script w/ data file"""
        # Warning: see notes above about potential issues with run_script-based tests.
        debug.trace(4, f"TestIt.test_01_data_file(); self={self}")
        data = [f"{h},{WEIGHT[i]}" for i, h in enumerate(HEIGHT)]
        system.write_lines(self.temp_file, data)
        ## TODO: add use_stdin=True to following if no file argument
        output = self.run_script(options="", data_file=self.temp_file)
        self.do_assert(my_re.search(r"R-squared.*0.9", output.strip()))
        self.do_assert(my_re.search(r"Intercept.*\*\*\*", output.strip()))
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    ## DEBUG: @trap_exception            # TODO: remove when debugged
    def test_02_something_else(self):
        """Test for something_else: TODO..."""
        debug.trace(4, f"TestIt.test_02_something_else(); self={self}")
        self.do_assert(False, "TODO: implement")
        ## ex: self.do_assert(THE_MODULE.TODO_function() == TODO_value)
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    ## TODO2: here and elsewhere: invoke_tests(__file__)
    pytest.main([__file__])
