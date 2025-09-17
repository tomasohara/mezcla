#! /usr/bin/env python3
#
# Test(s) for ../<module>.py
#
# Notes:
# - This can be run as follows (e.g., from root of repo):
#   $ pytest ./mezcla/tests/test_<module>.py
#

"""Tests for introspection module"""

# Installed modules
import pytest

# Local modules
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla import debug
from mezcla.my_regex import my_re
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                        global module object
#    TestIt.script_module:              path to file
THE_MODULE = None
try:
    import mezcla.introspection as THE_MODULE
except:
    system.print_exception_info("introspection import") 

#------------------------------------------------------------------------

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    # note: script_module used in argument parsing sanity check (e.g., --help)
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_01_simple_introspection(self):
        """Test for simple introspection"""
        debug.trace(4, f"TestIt.test_01_simple_introspection(); self={self}")
        fubar = 123.321
        fubar_expr = THE_MODULE.intro.format(fubar)
        self.do_assert(my_re.search("fubar.*123.321", fubar_expr))
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_02_multiline_introspection(self):
        """Test for multi-line introspection"""
        debug.trace(4, f"TestIt.test_02_multiline_introspection(); self={self}")
        multiline_value_expr = THE_MODULE.intro.format(
            2
            +
            2
            ==
            5)
        debug.trace_expr(5, multiline_value_expr)
        self.do_assert(my_re.search(r"2.*\+.*2.*==.*5", multiline_value_expr,
                                    flags=my_re.DOTALL|my_re.MULTILINE))
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_03_prefix(self):
        """Test for prefix added to introspection result"""
        debug.trace(4, f"TestIt.test_03_prefix(); self={self}")
        var = 456
        var_expr = THE_MODULE.intro.format(var, _prefix="here: ")
        assert my_re.search("here: var.*456", var_expr)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_04_max_len(self):
        """Test for introspection truncation"""
        debug.trace(4, f"TestIt.test_04_max_len(); self={self}")
        var = "-" * 123
        var_expr = THE_MODULE.intro.format(var, max_len=4)
        ## TODO2: assert my_re.search("var='----\.\.\.'", var_expr)
        ##                                            ^ (i.e., make sure quote closed)
        assert my_re.search(r"var='----\.\.\.", var_expr)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_05_quirks(self):
        """Test for known introspection quirks"""
        debug.trace(4, f"TestIt.test_05_quirks(); self={self}")
        # pylint: disable=unnecessary-lambda-assignment
        indirect_introspection = lambda x: THE_MODULE.intro.format(x, indirect=True)

        # Quirk 1: Unable to resolve variable defined on same line as call
        #
        ## NOTE: attempts to reproduce following:
        ##   In [150]: fu=123; MezclaDebugger().format(fu)
        ##   Warning: unable to resolve call node: args=(123,)
        ##   Out[150]: '123\n'
        ## versus:
        ##   In [151]: MezclaDebugger().format(fu)
        ##   Out[151]: 'fu=123\n'
        #
        ## TODO:
        ## pylint: disable=multiple-statements
        ## same_line_var = 123; expr = indirect_introspection(same_line_var)
        ## assert my_re.search(rf"^{same_line_var}", expr)
        #
        other_line_var = 321
        expr = indirect_introspection(other_line_var)
        assert my_re.search(rf"^other_line_var={other_line_var}", expr)

        # Quirk 2: Unable to resolve expressions embedded in function calls
        num = 7
        add1 = lambda num: 1 + num      
        assert not my_re.search(r"^add.*add.*num.*=", indirect_introspection(add1(add1(num))))
        #
        add1_add1_num = add1(add1(num))
        expr = indirect_introspection(add1_add1_num)
        assert my_re.search(rf"^add1_add1_num={add1_add1_num}", expr)
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
