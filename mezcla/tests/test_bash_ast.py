#! /usr/bin/env python3
#
# Test(s) for ../bash_ast.py
#
# TODO:
# - Test for features in https://github.com/tomasohara/bashlex fork,
#   which attempts to make bashlex more usable in the wild.
#
#--------------------------------------------------------------------------------
# Sample output tested:
#
# $ bash_ast.py - <<<'let sum=2 + 2; if [ $sum -eq 5 ]; then echo "WTH?"; fi'
# ListNode(pos=(0, 54), parts=[
#   CommandNode(pos=(0, 13), parts=[
#     WordNode(pos=(0, 3), word='let'),
#     WordNode(pos=(4, 9), word='sum=2'),
#     WordNode(pos=(10, 11), word='+'),
#     WordNode(pos=(12, 13), word='2'),
#   ]),
#   OperatorNode(op=';', pos=(13, 14)),
#   CompoundNode(list=[
#     IfNode(pos=(15, 54), parts=[
# ...
#       ReservedwordNode(pos=(34, 38), word='then'),
#       ListNode(pos=(39, 51), parts=[
#           CommandNode(pos=(39, 50), parts=[
#             WordNode(pos=(39, 43), word='echo'),
#             WordNode(pos=(44, 50), word='WTH?'),
#           ]),
# ...
#   ], pos=(15, 54)),
# ])
#

# $ bash_ast.py - <<<'touch /tmp-$$/fubar; echo $?'
# ListNode(pos=(0, 28), parts=[
#   CommandNode(pos=(0, 19), parts=[
#     WordNode(pos=(0, 5), word='touch'),
#     WordNode(pos=(6, 19), word='/tmp-$$/fubar', parts=[
# ...
#   CommandNode(pos=(21, 28), parts=[
#     WordNode(pos=(21, 25), word='echo'),
#     WordNode(pos=(26, 28), word='$?', parts=[
# ...
# ])


"""Tests for bash_ast module"""

# Standard modules
## TODO: from collections import defaultdict

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
try:
    ## TEST: raise RuntimeError
    import mezcla.bash_ast as THE_MODULE
except:
    THE_MODULE = None
    debug.trace_exception(4, "bash_ast import")

#------------------------------------------------------------------------

@pytest.mark.skipif(not THE_MODULE, reason="Unable to load module")
class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_01_data_file(self):
        """Tests run_script w/ data file"""
        debug.trace(4, f"TestIt.test_01_data_file(); self={self}")
        data = ["let sum=2 + 2;",
                "if [ $sum -eq 5 ]; then echo 'WTH?'; fi"]
        system.write_lines(self.temp_file, data)
        output = self.run_script(options="", data_file=self.temp_file)
        self.do_assert(my_re.search(
            r"ListNode.*WordNode.*let.*ReservedwordNode.*if.*ReservedwordNode.*then",
            output, flags=my_re.DOTALL|my_re.MULTILINE))
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_02_something_else(self):
        """Test for something_else: TODO..."""
        debug.trace(4, f"TestIt.test_02_something_else(); self={self}")
        ast = THE_MODULE.BashAST("touch /tmp-$$/fubar; echo $?")
        output = ast.dump()
        self.do_assert(my_re.search(
            r"ListNode.*CommandNode.*touch.*CommandNode.*WordNode.*echo",
            output, flags=my_re.DOTALL|my_re.MULTILINE))
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
