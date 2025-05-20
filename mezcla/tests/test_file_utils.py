#! /usr/bin/env python3
#
# Test(s) for ../file_utils.py
#
# Notes:
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_file_utils.py
#

"""Tests for file_utils module"""

# Standard packages
import json
import re
import os
import datetime

# Installed packages
import pytest

# Local packages
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	                global module object
#    TestTemplate.script_module:        path to file
import mezcla.file_utils as THE_MODULE

class TestFileUtils(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.derive_tested_module_name(__file__)
    use_temp_base_dir = True

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_get_directory_listing(self):
        """
        Tests for get_directory_listing(path          = 'PATH',
                                        recursive     = False,
                                        long          = False,
                                        readable_size = False,
                                        return_string = True,
                                        make_unicode  = False)
        """

        # Setup files and folders
        folders     = [self.temp_base, gh.form_path(self.temp_base, 'other_folder')]
        filenames   = ['analize.py', 'debug.cpp', 'main.txt', 'misc_utils.perl']

        for foldername in folders:
            ## TODO3: use mezcla wrappers (e.g., gh.full_mkdir)
            system.create_directory(foldername)
            for filename in filenames:
                system.write_file(gh.form_path(foldername, filename), '')

        # Run Test
        list_result = THE_MODULE.get_directory_listing(f'{self.temp_base}', recursive=True, long=True, return_string=True)

        for line in list_result:
            assert bool(re.search(r"[drwx-]+\s+\d+\s+\w+\s+\w+\s+\d+\s+\w+\s+\d+\s+\d\d:\d\d\s+[\w/]+", line))

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_get_information(self):
        """Tests for def get_information(path,
                                         readable = False,
                                         return_string = False)
        """
        temp_file = self.get_temp_file()
        system.write_file(temp_file, '')

        if os.name == 'nt':
            ls_result = gh.run(f'dir {temp_file} /Q').split('\n')[5].strip()
            ls_result = re.sub(r'\s+', ' ', ls_result).split(' ')
            modif_time = ls_result[1]
            owner = ls_result[3].split('\\')[1]
            file_name = ls_result[-1]
            info = THE_MODULE.get_information(temp_file, return_string=False)
            
            assert modif_time in info[5]
            assert owner == info[2]
            assert file_name in info[-1]
            assert 'None' == info[3]
            assert os.stat(temp_file).st_size == int(info[4])
            # assert ls_result.lower() == info.lower()
        else:
            ls_result = gh.run(f'ls -l {temp_file}')
            ls_result = re.sub(r'\s+', ' ', ls_result)
            assert THE_MODULE.get_information(temp_file, return_string=True).lower() == ls_result.lower()

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_get_permissions(self):
        """Tests for get_permissions(path)"""

        # Setup
        test_file = gh.form_path(self.temp_base, 'some-file.cpp')
        system.write_file(test_file, '')

        # Run
        ## OLD:
        ## assert THE_MODULE.get_permissions(test_file) == '-rw-rw-rw-'
        ## assert THE_MODULE.get_permissions(self.temp_base) == 'drwxrwxrwx'
        assert my_re.search("-rw-r..r..", THE_MODULE.get_permissions(test_file))
        assert my_re.search("drwxr..r..", THE_MODULE.get_permissions(self.temp_base))

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_get_modification_date(self):
        """Tests for get_modification_date(path)"""
        system.write_file(self.temp_file, '')
        ls_date = os.stat(self.temp_file).st_mtime
        # Extract date
        char = '#' if os.name == 'nt' else '-'
        ls_date = datetime.datetime.fromtimestamp(ls_date).strftime(f'%b %{char}d %H:%M').lower()

        assert THE_MODULE.get_modification_date(self.temp_file).lower() == ls_date

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_json_to_jsonl(self):
        """Tests for json_to_jsonl"""
        in_file = gh.form_path(self.temp_base, "some-file.json")
        out_file = gh.form_path(self.temp_base, "some-file.jsonl")
        sample_array = [1, 2, 3]
        system.write_file(in_file, f"{sample_array}\n")
        THE_MODULE.json_to_jsonl(in_file, out_file)
        assert(system.read_lines(out_file) == list(map(str, sample_array)))

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_jsonl_to_json(self):
        """Tests for jsonl_to_json"""
        in_file = gh.form_path(self.temp_base, "another-file.jsonl")
        out_file = gh.form_path(self.temp_base, "another-file.json")
        sample_array = ["dog", "cat", {"fav": "???"}]
        system.write_lines(in_file, [json.dumps(item) for item in sample_array])
        THE_MODULE.jsonl_to_json(in_file, out_file)
        assert(json.loads(system.read_file(out_file)) == sample_array)


#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
