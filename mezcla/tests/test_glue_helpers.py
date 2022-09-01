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

# Installed packages
import os
import pytest

# Local packages
from mezcla import debug
from mezcla.unittest_wrapper import TestWrapper
import mezcla.glue_helpers as gh


class TestIt(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.derive_tested_module_name(__file__)

    def test_extract_matches(self):
        """Tests for extract_matches(pattern, lines)"""
        ## OLD
        ## assert gh.extract_matches("Mr. (\S+)", ["Mr. Smith", "Mr. Jones", "Mr.X"]) == ["Smith", "Jones"]
        ## assert not gh.extract_matches("\t\S+", ["abc\tdef", "123\t456"]) == ["def", "456"]
        assert gh.extract_matches(r"Mr. (\S+)", ["Mr. Smith", "Mr. Jones", "Mr.X"]) == ["Smith", "Jones"]
        assert not gh.extract_matches(r"\t\S+", ["abc\tdef", "123\t456"]) == ["def", "456"]
        return

    def test_basename(self):
        """Tests for basename(path, extension)"""
        assert gh.basename("fubar.py", ".py") == "fubar"
        assert not gh.basename("fubar.py", "") == "fubar"
        return

    def test_resolve_path(self):
        """Tests for resolve_path(filename)"""
        script = "glue_helpers.py"
        test_script = "test_glue_helpers.py"
        # The main script should resolve to parent directory but this one to test dir
        assert not gh.resolve_path(script) == os.path.join(os.path.dirname(__file__), test_script)
        assert gh.resolve_path(test_script) == os.path.join(os.path.dirname(__file__), test_script)
        return


if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
