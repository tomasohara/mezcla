#! /usr/bin/env python3
#
# Test(s) for ../data_utils.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_data_utils.py
#

"""Tests for data_utils module"""

# Standard packages
## TODO: from typing import Optional

# Installed packages
import pandas as pd
import pytest

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper, invoke_tests

# Note: Two references are used for the module to be tested:
#    THE_MODULE:            global module object
import mezcla.data_utils as THE_MODULE

class TestDataUtils(TestWrapper):
    """Class for testcase definition"""
    # note: script_module used in argument parsing sanity check (e.g., --help)
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    ## OLD: path = os.path.dirname(os.path.realpath(__file__))
    iris_csv_path = gh.resolve_path("iris.csv", base_dir=".", heuristic=True)

    def test_read_csv(self):
        """Ensure read_csv works as expected over actual CSV files"""
        debug.trace(4, "test_read_csv()")
        df = THE_MODULE.read_csv(self.iris_csv_path)
        assert df.shape == (150, 5)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_simple_read_csv(self):
        """Verify read_csv over simple CSV files"""
        debug.trace(4, "test_simple_read_csv()")
        temp_csv = self.temp_file + ".csv"
        system.write_lines(temp_csv, [
            "query,style",
            '"modern art","Dan Rothko"'])
        df = THE_MODULE.read_csv(temp_csv)
        assert df.shape == (1, 2)
        #
        temp_tsv = self.temp_file + ".tsv"
        system.write_lines(temp_tsv, [
            "query\tstyle",
            "modern art\tDan Rothko"])
        df = THE_MODULE.read_csv(temp_tsv)
        assert df.shape == (1, 2)

    def test_to_csv(self):
        """Ensure to_csv works as expected"""
        debug.trace(4, "test_to_csv()")
        ## OLD: system.setenv("DELIM", ",")
        self.monkeypatch.setattr(THE_MODULE, "DELIM", ",")
        # Setup
        temp_file = self.get_temp_file()
        df = pd.DataFrame()
        df['sepal_length'] = [5.1, 4.9, 4.7, 4.6, 5.0]
        df['sepal_width'] = [3.5, 3.0, 3.2, 3.1, 3.6]
        df['petal_length'] = [1.4, 1.4, 1.3, 1.5, 1.4]
        df['petal_width'] = [0.2, 0.2, 0.2, 0.2, 0.2]
        df['class'] = ['Iris-setosa', 'Iris-virginica', 'Iris-versicolor', 'Iris-setosa', 'Iris-setosa']
        THE_MODULE.to_csv(temp_file, df)
        df.to_csv(temp_file, index=False)
        # Test
        expected = (
            'sepal_length,sepal_width,petal_length,petal_width,class\n' +
            '5.1,3.5,1.4,0.2,Iris-setosa'
        )
        assert expected in system.read_file(temp_file)

    def test_lookup_df_value(self):
        """Ensure lookup_df_value works as expected"""
        debug.trace(4, "test_lookup_df_value()")
        df = THE_MODULE.read_csv(self.iris_csv_path)
        assert THE_MODULE.lookup_df_value(df, "sepal_length", "petal_length", "3.8") == "5.5" 

    def test_main(self):
        """Ensure main works as expected"""
        debug.trace(4, "main()")
        THE_MODULE.main()
        captured = self.get_stderr()
        assert "Error" in captured

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
