#! /usr/bin/env python
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
from mezcla.unittest_wrapper import TestWrapper
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
FIELDS_2_3_4_CSV = f'{RESOURCES}/cars-fields-2-3-4-csv.txt'
FIELDS_2_3_4_TSV = f'{RESOURCES}/cars-fields-2-3-4-tsv.txt'
CSV_SEMICOLON = f'{RESOURCES}/cars-csv-output-delim-semicolon.txt'

class TestCutUtils(TestWrapper):
    """Class for testcase definition of utility functions"""
    script_file = TestWrapper.get_module_file_path(__file__)
    script_module = TestWrapper.get_testing_module_name(__file__)

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
    script_module = TestWrapper.get_testing_module_name(__file__)

    def test_01_no_options_csv(self):
        """Test for file passed with no options"""
        script_output = self.run_script(options='', data_file=CSV_EXAMPLE)
        assert script_output
        assert script_output + '\n' == system.read_file(CSV_EXAMPLE)
    
    def test_02_no_options_tsv(self):
        """Test for file passed with no options"""
        script_output = self.run_script(options='', data_file=TSV_EXAMPLE)
        assert script_output
        assert script_output + '\n' == system.read_file(TSV_EXAMPLE)

    def test_03_csv_max_field_len(self):
        """Test for CSV file with max_field_len option"""
        script_output = self.run_script(options='--csv --max-field-len 3', data_file=CSV_EXAMPLE)
        assert script_output
        assert script_output + '\n' == system.read_file(CUTTED_CSV_LEN_3)

    def test_04_tsv_max_field_len(self):
        """Test for TSV file with max_field_len option"""
        script_output = self.run_script(options='--tsv --max-field-len 3', data_file=TSV_EXAMPLE)
        assert script_output
        assert script_output + '\n' == system.read_file(CUTTED_TSV_LEN_3)

    def test_05_fields(self):
        """Ensure fields parameter works as expected"""
        # Test for CSV files
        script_output = self.run_script(options='--csv --fields 2-4', data_file=CSV_EXAMPLE)
        assert script_output
        assert script_output + '\n' == system.read_file(FIELDS_2_3_4_CSV)
        script_output = self.run_script(options='--csv --fields 2,3,4', data_file=CSV_EXAMPLE)
        assert script_output
        assert script_output + '\n' == system.read_file(FIELDS_2_3_4_CSV)
        script_output = self.run_script(options='--csv --F2 --F3 --F4', data_file=CSV_EXAMPLE)
        assert script_output
        assert script_output + '\n' == system.read_file(FIELDS_2_3_4_CSV)
        
        # Test for TSV files
        script_output = self.run_script(options='--tsv --fields 2-4', data_file=TSV_EXAMPLE)
        assert script_output
        assert script_output + '\n' == system.read_file(FIELDS_2_3_4_TSV)
        script_output = self.run_script(options='--tsv --fields 2,3,4', data_file=TSV_EXAMPLE)
        assert script_output
        assert script_output + '\n' == system.read_file(FIELDS_2_3_4_TSV)
        script_output = self.run_script(options='--tsv --F2 --F3 --F4', data_file=TSV_EXAMPLE)
        assert script_output
        assert script_output + '\n' == system.read_file(FIELDS_2_3_4_TSV)

    def test_06_symbolic_fields(self):
        """Ensure symbolic field names resolved"""
        # Note: this involves the same test fields as test_fields
        script_output = self.run_script(options='--csv --fields symboling-fueltype', data_file=CSV_EXAMPLE)
        assert (script_output.strip() == system.read_file(FIELDS_2_3_4_CSV).strip())
        script_output = self.run_script(options='--csv --fields symboling,CarName,fueltype', data_file=CSV_EXAMPLE)
        assert (script_output.strip() == system.read_file(FIELDS_2_3_4_CSV).strip())

    def test_07_output_delimiter(self):
        """Test for output delimiter"""
        # Test for CSV files
        script_output = self.run_script(options='--csv  --output-delim=";"', data_file=CSV_EXAMPLE, env_options='DISABLE_QUOTING=1')
        assert script_output
        assert script_output + '\n' == system.read_file(CSV_SEMICOLON)
        # Test for TSV files
        script_output = self.run_script(options='--tsv  --output-delim=";"', data_file=TSV_EXAMPLE, env_options='DISABLE_QUOTING=1')
        assert script_output
        assert script_output + '\n' == system.read_file(CSV_SEMICOLON)

    def test_08_exclude_fields(self):
        """Text exclusion field option (numeric and symbolic)"""
        # Note: this involves the same test fields as test_fields
        script_output = self.run_script(options='--csv --exclude 1,5-26', data_file=CSV_EXAMPLE)
        assert (script_output.strip() == system.read_file(FIELDS_2_3_4_CSV).strip())
        script_output = self.run_script(options='--csv --x 1,5-26', data_file=CSV_EXAMPLE)
        assert (script_output.strip() == system.read_file(FIELDS_2_3_4_CSV).strip())
        script_output = self.run_script(options='--csv --exclude car_ID,aspiration-price', data_file=CSV_EXAMPLE)
        assert (script_output.strip() == system.read_file(FIELDS_2_3_4_CSV).strip())
        ## TODO2: check for invalid field spec (e.g., with car_ID renamed to car-ID)
        script_output = self.run_script(options='--csv --exclude 1-car-ID', data_file=CSV_EXAMPLE)
        self.assertEqual(script_output.strip(), "")

    def test_09_empty_row(self):
        """Text handling of empty rows"""
        csv_data = """
        "fubar?",
        "no",
        "",
        """
        temp_file = self.create_temp_file(csv_data.strip())
        script_output = self.run_script(options='--csv --exclude 1,5-26', data_file=temp_file)
        self.assertNotEqual(script_output.split(), "")
        self.assertEqual(len(script_output.split()), 3)
        for item in script_output.split():
            self.assertNotEqual(item, r"^[a-zA-Z0-9]+$")
            self.assertEqual(len(item), 2)

    def test_10_output_options(self):
        """Test for output options (--output-csv, --output-tsv)"""
        script_output = self.run_script(options='--csv --output-tsv', data_file=CSV_EXAMPLE, env_options='DISABLE_QUOTING=1')
        assert (script_output.strip() == system.read_file(TSV_EXAMPLE).strip())
        script_output = self.run_script(options='--tsv --output-csv', data_file=TSV_EXAMPLE, env_options='DISABLE_QUOTING=1')
        assert (script_output.strip() == system.read_file(CSV_EXAMPLE).strip())

    def test_11_convert_delim(self):
        """Test for convert delim option (--convert-delim)"""
        script_output = self.run_script(options='--csv --convert-delim', data_file=CSV_EXAMPLE, env_options='DISABLE_QUOTING=1')
        assert (script_output.strip() == system.read_file(TSV_EXAMPLE).strip())
        script_output = self.run_script(options='--tsv --convert-delim', data_file=TSV_EXAMPLE, env_options='DISABLE_QUOTING=1')
        assert (script_output.strip() == system.read_file(CSV_EXAMPLE).strip())

    def test_12_explicit_delim(self):
        """Test for explicit delim option (--delim)"""
        # In case of wrong delimiter used, the default output is provided even when output option is provided
        script_output = self.run_script(options='--delim=";" --output-tsv', data_file=CSV_EXAMPLE, env_options='DISABLE_QUOTING=1')
        self.assertNotEqual(script_output.strip(), system.read_file(TSV_EXAMPLE).strip())
        self.assertEqual(script_output.strip(), system.read_file(CSV_EXAMPLE).strip())
        # Conversion to CSV using right delimiter
        script_output = self.run_script(options='--delim="," --output-tsv', data_file=CSV_EXAMPLE, env_options='DISABLE_QUOTING=1')
        self.assertEqual(script_output.strip(), system.read_file(TSV_EXAMPLE).strip())


class TestCutLogic(TestWrapper):
    """Unit tests for CutLogic class in cut.py"""
    script_file = TestWrapper.get_module_file_path(__file__)
    script_module = TestWrapper.get_testing_module_name(__file__)


if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
