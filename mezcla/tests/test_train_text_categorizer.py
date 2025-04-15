#! /usr/bin/env python3
#
# Tests for train_text_categorizer module
#
# Notes:
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_train_text_categorizer.py
#

"""Tests for train_text_categorizer module"""

# Standard modules
## NOTE: this is empty for now

# Installed modules
import pytest

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper, invoke_tests

# Note: Rreference are used for the module to be tested:
#    THE_MODULE:	    global module object
system.setenv("USE_XGB", "1")
THE_MODULE = None
try:
    ## TEMP: fails if xgboost not available (workaround for stupid docker issue)
    import xgboost
    debug.trace_expr(5, xgboost.XGBClassifier)
    import mezcla.train_text_categorizer as THE_MODULE
except:
    system.print_exception_info("text_categorizer import")


@pytest.mark.skipif(not THE_MODULE, reason="Unable to load module")
class TestTrainTextCategorizer(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    resources = gh.resolve_path("resources")

    def test_usage(self):
        """Test usage statement"""
        # Current usage:
        #    Usage: ./train_text_categorizer.py training-file model-file [testing]
        #    ...
        #    - Currently, only tab-separated value (TSV) format is accepted:
        usage = self.run_script(options="--help")
        assert "model" in usage
        assert "TSV" in usage
    
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_data_file(self):
        """Makes sure TODO works as expected"""
        debug.trace(4, f"TestIt.test_data_file(); self={self}")
        data_file = gh.form_path(self.resources, "random-10pct-tweet-emotions.tsv")
        ## TODO: add use_stdin=True to following if no file argument
        output = self.run_script(options="", env_options="TEST_PERCENT=10 USE_XGB=1", data_file=data_file, post_options="-")
        assert my_re.search(r"Accuracy over.*: (\S+)", output.strip())
        accuracy = system.to_float(my_re.group(1))
        debug.trace_expr(5, accuracy)
        assert (accuracy > 0.20)
        return


if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
