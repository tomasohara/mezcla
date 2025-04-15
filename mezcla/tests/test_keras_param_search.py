#! /usr/bin/env python3
#
# Test(s) for ../keras_param_search.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_keras_param_search.py
#

"""Tests for keras_param_search module"""

# Standard packages
## TODO: import re

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla import system
from mezcla import text_utils
from mezcla.unittest_wrapper import TestWrapper, invoke_tests

# Load module conditionally because not part of default installation.
# Note: Two references are used for the module to be tested:
#    THE_MODULE:               module object (e.g., <module 'mezcla.main' ...>)
#    TestIt.script_module:     dotted module path (e.g., "mezcla.main")
try:
    import mezcla.keras_param_search as THE_MODULE
except:
    THE_MODULE = None
    debug.trace_exception(1, "keras_param_search import")

class TestKerasParamSearch(TestWrapper):
    """Class for testcase definition"""
    # note: script_module used in argument parsing sanity check (e.g., --help)
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.skipif(not THE_MODULE, reason="Unable to load module")
    def test_round3(self):
        """Ensure round3 works as expected"""
        debug.trace(4, f"test_round3(); self={self}")
        assert THE_MODULE.round3(1.0001) == 1.000
        assert THE_MODULE.round3(1.001) == 1.001

    @pytest.mark.skipif(not THE_MODULE, reason="Unable to load module")
    def test_non_negative(self):
        """Ensure non_negative works as expected"""
        debug.trace(4, f"test_non_negative(); self={self}")
        test_num = 32.86209423
        assert THE_MODULE.non_negative(test_num)

    @pytest.mark.skipif(not THE_MODULE, reason="Unable to load module")
    def test_round3_too(self):
        """Ensure test_round3 works as expected"""
        debug.trace(4, "test_non_negative()")
        test_num = 3.1415926543
        assert THE_MODULE.round3(test_num) == 3.142

    @pytest.mark.skipif(not THE_MODULE, reason="Unable to load module")
    def test_create_feature_mapping(self):
        """Ensure create_feature_mapping works as expected"""
        debug.trace(4, f"test_create_feature_mapping(); self={self}")
        assert THE_MODULE.create_feature_mapping(['c', 'b', 'b', 'a']) == {'c':0, 'b':1, 'a':2}

    @pytest.mark.skipif(not THE_MODULE, reason="Unable to load module")
    @pytest.mark.xfail
    def test_create_keras_model(self):
        """Ensure create_keras_model works as expected"""
        debug.trace(4, "test_create_keras_model()")
        model = THE_MODULE.create_keras_model(
            num_input_features = 100, 
            num_classes = 2,
            hidden_units = text_utils.getenv_ints("HIDDEN_UNITS", "20 30"))
        # Make sure model size makes sense
        # example: [100, 20, 20, 30, 30, 1] for following
        model_param_lens = [len(w) for w in model.get_weights()]
        debug.trace_expr(5, model_param_lens)
        assert system.intersection(model_param_lens, [100, 20, 30])

    @pytest.mark.xfail
    def test_MyKerasClassifier_check_params(self):
        """Ensure MyKerasClassifier.check_params works as expected"""
        debug.trace(4, "test_MyKerasClassifier_check_params()")
        ## TODO: test MyKerasClassifier class
        assert False, "TODO: code test"
        
    @pytest.mark.xfail
    def test_main(self):
        """Check main routine"""
        debug.trace(4, "test_main()")
        ## TODO: test main
        assert False, "TODO: code test"

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
