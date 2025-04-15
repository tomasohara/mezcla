#! /usr/bin/env python3
#
# Test(s) for ../cut.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_cut.py
#

"""Tests for cut module"""

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla import glue_helpers as gh
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
import mezcla.cut as THE_MODULE

# Constants
RESOURCES = f'{gh.dir_path(__file__)}/resources'
CSV_EXAMPLE = f'{RESOURCES}/cars.csv'
TSV_EXAMPLE = f'{RESOURCES}/cars.tsv'
CUTTED_TSV_LEN_3 = f'{RESOURCES}/cars-tsv-len-3.txt'
CUTTED_CSV_LEN_3 = f'{RESOURCES}/cars-csv-len-3.txt'
FIELDS_2_3_4 = f'{RESOURCES}/cars-fields-2-3-4.txt'

class TestCutUtils(TestWrapper):
    """Class for testcase definition of utility functions"""
    script_file = TestWrapper.get_module_file_path(__file__)
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    def test_elide_values(self):
        """Ensure elide_values works as expected"""
        debug.trace(4, "elide_values()")
        assert THE_MODULE.elide_values(["1234567890", 1234567890, True, False], max_len=4) == ["1234...", "1234...", "True", "Fals..."]

    def test_flatten_list_of_strings(self):
        """Ensure flatten_list_of_strings works as expected"""
        debug.trace(4, "test_flatten_list_of_strings()")
        assert THE_MODULE.flatten_list_of_strings([["l1i1", "l1i2"], ["l2i1"]]) == ["l1i1", "l1i2", "l2i1"]

class TestCutScript(TestWrapper):
    """Class for testcase definition of main class"""
    script_file = TestWrapper.get_module_file_path(__file__)
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    def test_cut_csv(self):
        """Ensure csv files are cutted as expected"""
        script_output = self.run_script(options='--csv --max-field-len 3', data_file=CSV_EXAMPLE)
        assert script_output
        assert script_output + '\n' == system.read_file(CUTTED_CSV_LEN_3)

    def test_cut_tsv(self):
        """Ensure tsv files are cutted as expected"""
        script_output = self.run_script(options='--tsv --max-field-len 3', data_file=TSV_EXAMPLE)
        assert script_output
        assert script_output + '\n' == system.read_file(CUTTED_TSV_LEN_3)

    def test_fields(self):
        """Ensure fields parameter works as expected"""
        script_output = self.run_script(options='--csv --fields 2-4', data_file=CSV_EXAMPLE)
        assert script_output
        assert script_output + '\n' == system.read_file(FIELDS_2_3_4)
        script_output = self.run_script(options='--csv --fields 2,3,4', data_file=CSV_EXAMPLE)
        assert script_output
        assert script_output + '\n' == system.read_file(FIELDS_2_3_4)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_symbolic_fields(self):
        """Ensure symbolic field names resolved"""
        # Note: this involves the same test fields as test_fields
        script_output = self.run_script(options='--csv --fields symboling-fueltype', data_file=CSV_EXAMPLE)
        assert (script_output.strip() == system.read_file(FIELDS_2_3_4).strip())
        script_output = self.run_script(options='--csv --fields symboling,CarName,fueltype', data_file=CSV_EXAMPLE)
        assert (script_output.strip() == system.read_file(FIELDS_2_3_4).strip())

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_exclude_fields(self):
        """Text exclusion field option (numeric and symbolic)"""
        # Note: this involves the same test fields as test_fields
        script_output = self.run_script(options='--csv --exclude 1,5-26', data_file=CSV_EXAMPLE)
        assert (script_output.strip() == system.read_file(FIELDS_2_3_4).strip())
        script_output = self.run_script(options='--csv --exclude car_ID,aspiration-price', data_file=CSV_EXAMPLE)
        assert (script_output.strip() == system.read_file(FIELDS_2_3_4).strip())
        ## TODO2: check for invalid field spec (e.g., with car_ID renamed to car-ID)
        ## script_output = self.run_script(options='--csv --exclude 1-car-ID', data_file=CSV_EXAMPLE)
        ## (script_output.strip() != "")

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_empty_row(self):
        """Text handling of empty rows"""
        csv_data = """
        "fubar?",
        "no",
        "",
        """
        temp_file = self.create_temp_file(csv_data)
        script_output = self.run_script(options='--csv --exclude 1,5-26', data_file=temp_file)
        assert (script_output.strip() != "")
        

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
