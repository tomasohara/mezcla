#! /usr/bin/env python3
#
# Test(s) for ../check_time_tracking.py
#
# Notes:
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_check_time_tracking.py
#

"""Tests for check_time_tracking module"""

# Standard modules
## TODO: from collections import defaultdict

# Installed modules
import pytest

# Local modules
from mezcla.unittest_wrapper import TestWrapper
## TODO: from mezcla.unittest_wrapper import trap_exception
from mezcla import debug
## TODO: from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                        global module object
#    TestIt.script_module:              path to file
try:
    import mezcla.adhoc.check_time_tracking as THE_MODULE
except:
    debug.assertion(False, "TODO1: FIXME")
    THE_MODULE = None
debug.trace_expr(5, THE_MODULE)
#
# Note: sanity test for customization (TODO: remove if desired)
if not my_re.search(__file__, r"\btemplate.py$"):
    debug.assertion("mezcla.template" not in str(THE_MODULE))

TEMPLATE = """
    # Time tracking for work Jan 2222
    # John J. Doe
    #
    # legend:
    # XYZ: XYZ, Inc.
    # JJD: personal stuff
    #
    
    --------------------------------------------------------------------------------
    
    Week of Sunday DD MMM YYYY
    
    Sun:            # dd mmm
    Hours:
    
    Mon:
    # <here>
    Hours:
    
    Tues:
    Hours:
    
    Wed:
    12-1: [JJD] break
    Hours:
    
    Thurs:
    Hours:
    
    Fri:
    Hours:
    
    Sat:
    Hours:
    
    # TODO
    # Misc: task1, task2, ..., task3
    # Hours:
    
    Weekly hours:
    
    --------------------------------------------------------------------------------
    
    Total hours:
"""

#------------------------------------------------------------------------

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    #
    # TODO: use_temp_base_dir = True            # treat TEMP_BASE as directory
    # note: temp_file defined by parent (along with script_module, temp_base, and test_num)

    @pytest.mark.xfail                   # TODO: remove xfail
    ## DEBUG: @trap_exception            # TODO: remove when debugged
    def test_01_data_file(self):
        """Tests run_script w/ data file"""
        debug.trace(4, f"TestIt.test_01_data_file(); self={self}")
        system.write_file(self.temp_file, TEMPLATE)
        output = self.run_script(options="", data_file=self.temp_file)
        self.do_assert(my_re.search(r"Total hours: 0", output.strip()))
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    ## DEBUG: @trap_exception            # TODO: remove when debugged
    def test_02_something_else(self):
        """Test for something_else: TODO..."""
        debug.trace(4, f"TestIt.test_02_something_else(); self={self}")
        self.do_assert(False)
        ## ex: self.do_assert(THE_MODULE.TODO_function() == TODO_value)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_03_tagged_hours(self):
        """Test printed report for tags (capsys-like)"""
        debug.trace(4, f"TestIt2.test_03_tagged_hours(); self={self}")
        tag_hash = {"JJD": 1.0}
        THE_MODULE.show_tagged_hours(tag_hash)
        captured = self.get_stdout()
        self.do_assert("Hours by tag.*JJD" in captured)
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    ## TODO2: here and elsewhere: invoke_tests(__file__)
    pytest.main([__file__])
