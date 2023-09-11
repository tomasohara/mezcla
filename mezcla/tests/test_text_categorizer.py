#! /usr/bin/env python
#
# Test(s) for ../text_categorizer.py
#
# Notes:
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_<module>.py
#

"""Tests for text_categorizer module"""

# Standard packages
## OLD: import random

# Installed packages
import pytest

# Local packages
from mezcla.unittest_wrapper import TestWrapper, trap_exception
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla import system
from mezcla import misc_utils

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
system.setenv("USE_XGB", "1")
import mezcla.text_categorizer as THE_MODULE

## TODO:
## # Environment options
## # Note: These are just intended for internal options, not for end users.
## # It also allows for enabling options in one place.
## #
## FUBAR = system.getenv_bool("FUBAR", False,
##                            description="Fouled Up Beyond All Recognition processing")


class TestTextCategorizerUtils(TestWrapper):
    """Class for utility test cases"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_sklearn_report(self):
        """Ensure sklearn_report works as expected"""
        debug.trace(4, "test_sklearn_report()")
        assert(False)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_create_tabular_file(self):
        """Ensure create_tabular_file works as expected"""
        debug.trace(4, "test_create_tabular_file()")
        assert(False)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_read_categorization_data(self):
        """Ensure read_categorization_data works as expected"""
        debug.trace(4, "test_read_categorization_data()")
        assert(False)

    def test_int_if_whole(self):
        """Ensure int_if_whole works as expected"""
        debug.trace(4, "test_int_if_whole()")
        assert THE_MODULE.int_if_whole(2.0) == 2
        assert THE_MODULE.int_if_whole(2.999) == 2.999

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_param_or_default(self):
        """Ensure param_or_default works as expected"""
        debug.trace(4, "test_param_or_default()")
        assert(False)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_data_file(self):
        """Makes sure TODO works as expected"""
        debug.trace(4, "TestTextCategorizer.test_data_file()")
        data = ["TODO1", "TODO2"]
        gh.write_lines(self.temp_file, data)
        output = self.run_script("", self.temp_file)
        assert my_re.search(r"TODO-pattern", output.strip())
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_format_index_html(self):
        """Ensure format_index_html works as expected"""
        debug.trace(4, "test_format_index_html()")
        assert(False)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_start_web_controller(self):
        """Ensure start_web_controller works as expected"""
        debug.trace(4, "test_start_web_controller()")
        assert(False)

class TestTextCategorizerScript(TestWrapper):
    """Class for main testcase definition"""
    script_file = TestWrapper.get_module_file_path(__file__)
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    resources = gh.resolve_path("resources")
    # TODO: use_temp_base_dir = True            # treat TEMP_BASE as directory
    # note: temp_file defined by parent (along with script_module, temp_base, and test_num)

    def test_usage(self):
        """Test usage statement"""
        # Current usage:
        #   Usage: ./text_categorizer.py model
        usage = self.run_script(options="--help")
        assert "model" in usage
    
    @trap_exception
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_test_untrained(self):
        """Make sure accuracy 0 if untrained (TODO: trap stderr)"""
        debug.trace(4, "test_test_untrained()")
        tc = THE_MODULE.TextCategorizer()
        accuracy = tc.test(__file__)
        assert(accuracy == 0)

    @trap_exception
    @pytest.mark.xfail
    def test_train(self):
        """Make sure training works"""
        debug.trace(4, "test_train()")
        data_file = gh.form_path(self.resources, "random-10pct-tweet-emotions.tsv")
        data = system.read_lines(data_file)
        tc = THE_MODULE.TextCategorizer(use_xgb=True)
        tc.train(data_file)
        num_ok = 0
        num_to_test = 10
        for _i in range(num_to_test):
            ## OLD: case = random.randint(1, len(data) - 1)
            case = misc_utils.random_int(1, len(data) - 1)
            expect_cat, expect_text = data[case].split("\t")
            actual_cat = tc.categorize(expect_text)
            debug.trace_expr(5, case, expect_cat, actual_cat)
            if (expect_cat == actual_cat):
                num_ok += 1
        debug.trace_expr(4, num_ok)
        assert(num_ok >= num_to_test // 2)
        

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
