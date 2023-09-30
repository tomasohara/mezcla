#! /usr/bin/env python
#
# Test(s) for ../bing_search.py
#
# Notes:
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by  unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_bing_search.py
#

"""Tests for bing_search module"""

# Standard packages
## NOTE: this is empty for now

# Installed packages
import pytest

# Local packages
from mezcla import debug

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
import mezcla.bing_search as THE_MODULE

class TestBingSearch:
    """Class for testcase definition"""

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_data_file(self):
        """Makes sure TODO works as expected"""
        debug.trace(4, f"TestIt.test_data_file(); self={self}")
        data = ["TODO1", "TODO2"]
        system.write_lines(self.temp_file, data)
        ## TODO: add use_stdin=True to following if no file argument
        output = self.run_script(options="", data_file=self.temp_file)
        assert my_re.search(r"TODO-pattern", output.strip())
        return


if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
