#! /usr/bin/env python
#
# Test(s) for glue_helpers.py. This can be run as follows:
# $ PYTHONPATH="." tests/test_glue_helpers.py
#
# TODO:
# - Add support for write_lines & read_lines.
# - Add support for other commonly used functions.
#

"""Tests for glue_helpers module"""

# Standard packages
import os
import re

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla.unittest_wrapper import TestWrapper

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
#    TestIt.script_module   string name
import mezcla.glue_helpers as THE_MODULE

class TestIt(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.derive_tested_module_name(__file__)

    def test_get_temp_file(self):
        """Ensure get_temp_file works as expected"""
        debug.trace(4, "test_get_temp_file()")
        ## TODO: WORK-IN=PROGRESS

    def test_remove_extension(self):
        """Ensure remove_extension works as expected"""
        debug.trace(4, "test_remove_extension()")
        assert THE_MODULE.remove_extension("/tmp/solr-4888.log", ".log") == "/tmp/solr-4888"
        assert THE_MODULE.remove_extension("/tmp/fubar.py", ".py") == "/tmp/fubar"
        assert THE_MODULE.remove_extension("/tmp/fubar.py", "py") == "/tmp/fubar."

    def test_dir_path(self):
        """Ensure dir_path works as expected"""
        debug.trace(4, "test_dir_path()")
        assert THE_MODULE.dir_path("/tmp/solr-4888.log") == "/tmp" 

    def test_file_exists(self):
        """Ensure file_exists works as expected"""
        debug.trace(4, "test_file_exists()")
        ## TODO: WORK-IN=PROGRESS

    def test_form_path(self):
        """Ensure form_path works as expected"""
        debug.trace(4, "test_form_path()")
        ## TODO: WORK-IN=PROGRESS

    def test_create_directory(self):
        """Ensure create_directory works as expected"""
        debug.trace(4, "test_create_directory()")
        ## TODO: WORK-IN=PROGRESS

    def test_full_mkdir(self):
        """Ensure full_mkdir works as expected"""
        debug.trace(4, "test_full_mkdir()")
        ## TODO: WORK-IN=PROGRESS

    def test_real_path(self):
        """Ensure real_path works as expected"""
        debug.trace(4, "test_real_path()")
        assert re.search("vmlinuz.*\d.\d", THE_MODULE.real_path("/vmlinuz"))

    def test_indent(self):
        """Ensure indent works as expected"""
        debug.trace(4, "test_indent()")
        ## TODO: WORK-IN=PROGRESS

    def test_indent_lines(self):
        """Ensure indent_lines works as expected"""
        debug.trace(4, "test_indent_lines()")
        ## TODO: WORK-IN=PROGRESS

    def test_elide(self):
        """Ensure elide works as expected"""
        debug.trace(4, "test_elide()")
        assert THE_MODULE.elide("=" * 80, max_len=8) == "========..."
        assert THE_MODULE.elide(None, 10) == None

    def test_elide_values(self):
        """Ensure elide_values works as expected"""
        debug.trace(4, "test_elide_values()")
        assert THE_MODULE.elide_values(["1", "22", "333"], max_len=2) == ["1", "22", "33..."]

    def test_disable_subcommand_tracing(self):
        """Ensure disable_subcommand_tracing works as expected"""
        debug.trace(4, "test_disable_subcommand_tracing()")
        ## TODO: WORK-IN=PROGRESS

    def test_run(self):
        """Ensure run works as expected"""
        debug.trace(4, "test_run()")
        assert "root" in THE_MODULE.run("ls /")

    def test_issue(self):
        """Ensure issue works as expected"""
        debug.trace(4, "test_issue()")
        assert THE_MODULE.issue("ls /") == None
        assert THE_MODULE.issue("xeyes &")

    def test_get_hex_dump(self):
        """Ensure get_hex_dump works as expected"""
        debug.trace(4, "test_get_hex_dump()")
        ## TODO: mock hexview.perl output
        ## assert THE_MODULE.get_hex_dump("Tomás") == "00000000  54 6F 6D C3 A1 73       -                          Tom..s" 

    def test_extract_matches(self):
        """Tests for extract_matches(pattern, lines)"""
        ## OLD
        ## assert gh.extract_matches("Mr. (\S+)", ["Mr. Smith", "Mr. Jones", "Mr.X"]) == ["Smith", "Jones"]
        ## assert not gh.extract_matches("\t\S+", ["abc\tdef", "123\t456"]) == ["def", "456"]
        assert THE_MODULE.extract_matches(r"Mr. (\S+)", ["Mr. Smith", "Mr. Jones", "Mr.X"]) == ["Smith", "Jones"]
        assert not THE_MODULE.extract_matches(r"\t\S+", ["abc\tdef", "123\t456"]) == ["def", "456"]
        return

    def test_extract_match(self):
        """Ensure extract_match works as expected"""
        debug.trace(4, "test_extract_match()")
        ## TODO: WORK-IN=PROGRESS

    def test_basename(self):
        """Tests for basename(path, extension)"""
        assert THE_MODULE.basename("fubar.py", ".py") == "fubar"
        assert not THE_MODULE.basename("fubar.py", "") == "fubar"
        assert THE_MODULE.basename("/tmp/solr-4888.log", ".log") == "solr-4888"
        return

    def test_resolve_path(self):
        """Tests for resolve_path(filename)"""
        script = "glue_helpers.py"
        test_script = "test_glue_helpers.py"
        # The main script should resolve to parent directory but this one to test dir
        assert not THE_MODULE.resolve_path(script) == os.path.join(os.path.dirname(__file__), test_script)
        assert THE_MODULE.resolve_path(test_script) == os.path.join(os.path.dirname(__file__), test_script)
        return

    def test_extract_match_from_text(self):
        """Ensure extract_match_from_text works as expected"""
        debug.trace(4, "test_extract_match_from_text()")
        ## TODO: WORK-IN=PROGRESS

    def test_extract_matches_from_text(self):
        """Ensure extract_matches_from_text works as expected"""
        debug.trace(4, "test_extract_matches_from_text()")
        assert THE_MODULE.extract_matches_from_text(".", "abc") == ["a", "b", "c"]
        assert THE_MODULE.extract_matches_from_text(".", "abc", multiple=False) == ["a"]

    def test_count_it(self):
        """Ensure count_it works as expected"""
        debug.trace(4, "test_count_it()")
        assert dict(THE_MODULE.count_it("[a-z]", "Panama")) == {"a": 3, "n": 1, "m": 1}
        assert THE_MODULE.count_it("\w+", "My d@wg's fleas have fleas")["fleas"] == 2

    def test_read_lines(self):
        """Ensure read_lines works as expected"""
        debug.trace(4, "test_read_lines()")
        ## TODO: WORK-IN=PROGRESS

    def test_write_lines(self):
        """Ensure write_lines works as expected"""
        debug.trace(4, "test_write_lines()")
        ## TODO: WORK-IN=PROGRESS

    def test_read_file(self):
        """Ensure read_file works as expected"""
        debug.trace(4, "test_read_file()")
        ## TODO: WORK-IN=PROGRESS

    def test_write_file(self):
        """Ensure write_file works as expected"""
        debug.trace(4, "test_write_file()")
        ## TODO: WORK-IN=PROGRESS

    def test_copy_file(self):
        """Ensure copy_file works as expected"""
        debug.trace(4, "test_copy_file()")
        ## TODO: WORK-IN=PROGRESS

    def test_rename_file(self):
        """Ensure rename_file works as expected"""
        debug.trace(4, "test_rename_file()")
        ## TODO: WORK-IN=PROGRESS

    def test_delete_file(self):
        """Ensure delete_file works as expected"""
        debug.trace(4, "test_delete_file()")
        ## TODO: WORK-IN=PROGRESS

    def test_file_size(self):
        """Ensure file_size works as expected"""
        debug.trace(4, "test_file_size()")
        ## TODO: WORK-IN=PROGRESS

    def test_get_matching_files(self):
        """Ensure get_matching_files works as expected"""
        debug.trace(4, "test_get_matching_files()")
        ## TODO: WORK-IN=PROGRESS

    def test_get_files_matching_specs(self):
        """Ensure get_files_matching_specs works as expected"""
        debug.trace(4, "test_get_files_matching_specs()")
        ## TODO: WORK-IN=PROGRESS

    def test_get_directory_listing(self):
        """Ensure get_directory_listing works as expected"""
        debug.trace(4, "test_get_directory_listing()")
        ## TODO: WORK-IN=PROGRESS

    def test_getenv_filename(self):
        """Ensure getenv_filename works as expected"""
        debug.trace(4, "test_getenv_filename()")
        ## TODO: WORK-IN=PROGRESS


if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
