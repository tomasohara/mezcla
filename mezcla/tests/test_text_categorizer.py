#! /usr/bin/env python3
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
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla import system
from mezcla import misc_utils

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
## OLD: system.setenv("USE_XGB", "1")
THE_MODULE = None
try:
    ## TEMP: fails if xgboost not available (workaround for stupid docker issue)
    ## OLD:
    ## import xgboost
    ## debug.trace_expr(5, xgboost.XGBClassifier)
    import mezcla.text_categorizer as THE_MODULE
except:
    system.print_exception_info("text_categorizer import")

# Environment options
TEST_TBD = system.getenv_bool("TEST_TBD", False,
                              description="Test features to be designed: TBD")


class TestTextCategorizerUtils(TestWrapper):
    """Class for utility test cases"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_sklearn_report(self):
        """Ensure sklearn_report works as expected"""
        debug.trace(4, "test_sklearn_report()")
        self.do_assert(False, "TODO: implement")

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_create_tabular_file(self):
        """Ensure create_tabular_file works as expected"""
        debug.trace(4, "test_create_tabular_file()")
        self.do_assert(False, "TODO: implement")

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_read_categorization_data(self):
        """Ensure read_categorization_data works as expected"""
        debug.trace(4, "test_read_categorization_data()")
        # TODO: create resource file to test tab separated values
        self.do_assert(False, "TODO: implement")

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_int_if_whole(self):
        """Ensure int_if_whole works as expected"""
        debug.trace(4, "test_int_if_whole()")
        assert THE_MODULE.int_if_whole(2.0) == 2
        assert THE_MODULE.int_if_whole(2.999) == 2.999

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_param_or_default(self):
        """Ensure param_or_default works as expected"""
        debug.trace(4, "test_param_or_default()")
        default = THE_MODULE.param_or_default(None, "default")
        param = THE_MODULE.param_or_default("param", None)
        assert default == "default"
        assert param == "param"

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_data_file(self):
        """Makes sure TODO works as expected"""
        debug.trace(4, "TestTextCategorizer.test_data_file()")
        data = ["TODO1", "TODO2"]
        system.write_lines(self.temp_file, data)
        output = self.run_script("", self.temp_file)
        assert my_re.search(r"TODO-pattern", output.strip())
        return

    @pytest.mark.xfail  # TODO: remove xfail
    def test_format_index_html(self):
        """Ensure format_index_html works as expected"""
        debug.trace(4, "test_format_index_html()")
        
        # Example input data
        base_url = "http://127.0.0.1:8080"
        
        # Expected output
        expected_output = """
        <!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN">
        <html lang="en">
            <head>
                <meta content="text/html; charset=UTF-8" http-equiv="content-type">
                <title>Text categorizer</title>
            </head>
            <body>
                Try <a href="categorize">categorize</a> and <a href="class_probabilities">class_probabilities</a>.<br>
                note: You need to supply the <i><b>text</b></i> parameter.<br>
                <br>
                Examples:
                <ul>
                    <li>Category for <a href="categorize?text=Donald+Trump+was+President.">"Donald Trump was President."</a>:<br>
                        &nbsp;&nbsp;&nbsp;&nbsp;<code>http://127.0.0.1:8080/categorize?text=Donald+Trump+was+President.</code>
                    </li>
        
                    <li>Probability distribution for <a href="class_probabilities?text=My+dog+has+fleas.">"My dog has fleas."</a>:<br>
                        &nbsp;&nbsp;&nbsp;&nbsp;<code>http://127.0.0.1:8080/class_probabilities?text=My+dog+has+fleas.</code>
                    </li>
                </ul>
                
                <!-- Form for entering text for categorization -->
                <hr>
                <form action="http://127.0.0.1:8080/categorize" method="get">
                    <label for="textarea1">Categorize</label>
                    <br>
                    <textarea id="textarea1" rows="10" cols="100" name="text"></textarea>
                    <br>
                    <input type="submit">
                </form>
                <!-- Form for entering text for textcat probability distribution -->
                <hr>
                <form action="http://127.0.0.1:8080/probs" method="get">
                    <label for="textarea1">Probabilities</label>
                    <br>
                    <textarea id="textarea2" rows="10" cols="100" name="text"></textarea>
                    <br>
                    <input type="submit">
                </form>
            </body>
        </html>
        """
        
        # Call the function
        output = THE_MODULE.format_index_html(base_url)
        
        # Print the actual output for debugging
        print("Actual Output:\n", output)
        
        # Assert the output
        ## TODO3: check individually for specific segments
        assert output.strip() == expected_output.strip()

    @pytest.mark.skipif(not TEST_TBD, reason="Ignoring feature to be designed")
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_start_web_controller(self):
        """Ensure start_web_controller works as expected"""
        # Note: pytest has a quirk leading to a logging exception during cherrypy cleanup
        debug.trace(4, "test_start_web_controller()")
        TODO_MODEL = "todo.model"
        wc = THE_MODULE.start_web_controller(TODO_MODEL, nonblocking=True)
        html_listing = wc.index()
        assert("</html>" in html_listing)
        ## TODO2: wc.stop()
        debug.trace(4, "out test_start_web_controller")

class TestTextCategorizerScript(TestWrapper):
    """Class for main testcase definition"""
    script_file = TestWrapper.get_module_file_path(__file__)
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    resources = gh.resolve_path("resources")
    # TODO: use_temp_base_dir = True            # treat TEMP_BASE as directory
    # note: temp_file defined by parent (along with script_module, temp_base, and test_num)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_usage(self):
        """Test usage statement"""
        # Current usage:
        #   Usage: ./text_categorizer.py model
        usage = self.run_script(options="--help")
        assert "model" in usage
    
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_test_untrained(self):
        """Make sure accuracy 0 if untrained (TODO: trap stderr)"""
        debug.trace(4, "test_test_untrained()")
        tc = THE_MODULE.TextCategorizer()
        ## OLD: accuracy = tc.test(__file__)
        test_data = ["cat1\ta b c d e",
                     "cat2\tf g h i j"]
        system.write_lines(self.temp_file, test_data)
        accuracy = tc.test(self.temp_file)
        assert(accuracy == 0)

    @pytest.mark.xfail
    def test_train(self):
        """Make sure training works"""
        debug.trace(4, "test_train()")
        data_file = gh.form_path(self.resources, "random-10pct-tweet-emotions.tsv")
        data = system.read_lines(data_file)
        ## NOTE: Unfortunately xgboost takes too much disk space under Github actions
        ## OLD: tc = THE_MODULE.TextCategorizer(use_xgb=True)
        tc = THE_MODULE.TextCategorizer(use_xgb=False)
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
    invoke_tests(__file__)
