#! /usr/bin/env python
#
# Tests for format_profile module
#
# Notes:
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_train_language_model.py 

## TODO1: carefully review test/template.py
## TODO2: use a helper method to cut down on redundant tests; for example,
##    def check_format_profile_key(self, key):
##        ... run_script(env_options=f"PROFILE_KEY={key}", ...)
##    def test_formatprofile_PK_time(self): self.check_format_profile_key("time")
## NOTE:
## - Only need to test a few main keys in any depth, so generalize test_formatprofile_PK_calls
## so that it can handle alternative sort orders without substantial revision.
## - The minor keys can just check for "Ordered by" label differences.


"""Tests for format_profile module"""

# Standard packages
## OLD: import re

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper
from mezcla.unittest_wrapper import trap_exception

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                        global module object
#    TestIt.script_module:              path to file
import mezcla.format_profile as THE_MODULE

class TestFormatProfile(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    use_temp_base_dir = True    # treat TEMP_BASE as directory
    # For testing, let the dir be ./mezcla/mezcla/tests
    # TODO: Find a way to denote a random number in SAMPLE OUTPUT which may differ in each execution

    @pytest.mark.xfail                   # TODO: remove xfail
    @trap_exception                      # TODO: remove when debugged
    def test_formatprofile_PK_calls(self):
        "Ensures that test_formatprofile_PK_calls works as expected"
        ## TODO3: reword commment because test_formatprofile_PK_calls is not testing itself;
        ## Instead, use something like "ensure that PROFILE_KEY=calls works as expected".

        key_arg = "calls"
        ## OLD: testing_script = "test_glue_helpers.py"
        testing_script = gh.resolve_path("simple_main_example.py")
        ## OLD: SAMPLE_OUTPUT = ["1    0.001    0.000    0.000    0.000 cacheprovider.py:307(pytest_report_collectionfinish)", "{method 'popleft' of 'collections.deque' objects}"]

        # Sample output:
        #     Ordered by: call count
        # 
        #     ncalls  tottime  percall  cumtime  percall filename:lineno(function)
        #     3323    0.000    0.000    0.000    0.000 {built-in method builtins.isinstance}
        #     2670    0.000    0.000    0.000    0.000 {method 'rstrip' of 'str' objects}
        #     1825/1723    0.000    0.000    0.000    0.000 {built-in method builtins.len}
        #     1443    0.000    0.000    0.000    0.000 {method 'append' of 'list' objects}
        #
        
        debug.trace(4, f"test_formatprofile_PK_calls(); self={self}")
        ## OLD: empty_file1 = gh.get_temp_file()
        ## OLD: profile_log  = gh.get_temp_file()
        profile_data = self.temp_file + "-profile.data"
        ## OLD: test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        # note: runs simple_main_example.py over itself; for example,
        #   python -m cProfile -o /tmp/tmpp6zg9a5o/test-1-profile.data simple_main_example.py simple_main_example.py
        test_command_1 = f"python -m cProfile -o {profile_data} {testing_script} {testing_script}"
        ## BAD: test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"

        gh.run(test_command_1)
        ## BAD: gh.run(test_command_2)

        ## BAD: output = gh.read_file(empty_file1)
        output = self.run_script(env_options=f"PROFILE_KEY={key_arg}", data_file=profile_data)
        self.do_assert("Ordered by: call count" in output)
        my_re.search(r"^\s*(\S+)\s+.*method 'rstrip'", output, flags=my_re.MULTILINE)
        rstrip_count = system.to_float(my_re.group(1))
        my_re.search(r"^\s*(\S+)\s+.*method 'append'", output, flags=my_re.MULTILINE)
        join_count = system.to_float(my_re.group(1))
        self.do_assert(rstrip_count > join_count)

        return
    
    # Test Helper method
    @pytest.mark.skip
    def test_helper_formatprofile(
        self,
        key_arg,
        testing_script,
        ):
        """Helper function for format_profile tests"""
        debug.trace(4, f"test_helper_formatprofile(); self={self}")
        empty_file = gh.get_temp_file()
        profile_log = gh.get_temp_file()
        
        command1 = f"python3 -m cProfile -o {profile_log} {testing_script}"
        command2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file}"
        gh.run(command1)
        gh.run(command2)

        output = (gh.read_file(empty_file)).split("\n")
        output = [line.strip() for line in output]        
        return output

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_cumulative(self):
        "Ensures that test_formatprofile_PK_cumulative works as expected"

        key_arg = "cumulative"
        testing_script = "test_glue_helpers.py"
        # OLD: SAMPLE_OUTPUT = ["<frozen importlib._bootstrap>:211(_call_with_frames_removed)q", "2    0.000    0.000    0.000    0.000 logging.py:128(_get_auto_indent)"]
        SAMPLE_OUTPUT = [
            "1    0.000    0.000    0.000    0.000 <frozen importlib._bootstrap>:581(_module_repr_from_spec)", 
            "2    0.000    0.000    0.000    0.000 logging.py:128(_get_auto_indent)"
        ]

        debug.trace(4, f"test_formatprofile_PK_cumulative(); self={self}")
        # empty_file1 = gh.get_temp_file()
        # profile_log  = gh.get_temp_file()
        # test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        # test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"
        # gh.run(test_command_1)
        # gh.run(test_command_2)
        # output = gh.read_file(empty_file1)
        output = self.test_helper_formatprofile(key_arg, testing_script)
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
        return
    
    ## TODO: Find other input sample
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_cumtime(self):
        "Ensures that test_formatprofile_PK_cumtime works as expected"
        debug.trace(4, f"test_formatprofile_PK_cumtime(); self={self}")
        key_arg = "cumtime"
        testing_script = "test_glue_helpers.py"
        SAMPLE_OUTPUT = [
            "_hooks.py:244(__call__)qq", 
            "1    0.000    0.000    0.000    0.000 <attrs generated eq attr.validators._NumberValidator>:1(<module>)"
            ]
        ## OLD
        # empty_file1 = gh.get_temp_file()
        # profile_log  = gh.get_temp_file()
        # test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        # test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"

        # gh.run(test_command_1)
        # gh.run(test_command_2)

        # output = gh.read_file(empty_file1)
        output = self.test_helper_formatprofile(key_arg, testing_script)
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
        # return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_file(self):
        "Ensures that test_formatprofile_PK_file works as expected"

        key_arg = "file"
        testing_script = "test_glue_helpers.py"
        SAMPLE_OUTPUT = ["{built-in method __new__ of type object at 0x909780}", "{built-in method _ssl.txt2obj}"]
        
        debug.trace(4, f"test_formatprofile_PK_file(); self={self}")
        empty_file1 = gh.get_temp_file()
        profile_log  = gh.get_temp_file()
        test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"

        gh.run(test_command_1)
        gh.run(test_command_2)

        output = gh.read_file(empty_file1)
        assert (SAMPLE_OUTPUT[0] in output and SAMPLE_OUTPUT[1] in output)
        return
    
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_filename(self):
        "Ensures that test_formatprofile_PK_filename works as expected"

        key_arg = "filename"
        testing_script = "test_glue_helpers.py"
        SAMPLE_OUTPUT = ["1    0.000    0.000    0.000    0.000 :1(ReprEntryNativeAttributes)", "6768    0.000    0.000    0.000    0.000 :1(ReprEntryAttributes)"]


        ## OLD
        debug.trace(4, f"test_formatprofile_PK_filename(); self={self}")
        # empty_file1 = gh.get_temp_file()
        # profile_log  = gh.get_temp_file()
        # test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        # test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"

        # gh.run(test_command_1)
        # gh.run(test_command_2)

        # output = gh.read_file(empty_file1)

        output = self.test_helper_formatprofile(key_arg, testing_script)
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] not in output)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_module(self):
        "Ensures that test_formatprofile_PK_module works as expected"

        key_arg = "module"
        testing_script = "test_glue_helpers.py"
        SAMPLE_OUTPUT = ["1    0.000    0.000    0.000    0.000 :1(ExceptionChainReprAttributes)"]

        debug.trace(4, f"test_formatprofile_PK_module(); self={self}")
        empty_file1 = gh.get_temp_file()
        profile_log  = gh.get_temp_file()
        test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"

        gh.run(test_command_1)
        gh.run(test_command_2)

        output = gh.read_file(empty_file1)
        assert (SAMPLE_OUTPUT[0] in output)
        return

    ## TODO: Find other input sample
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_ncalls(self):
        "Ensures that test_formatprofile_PK_ncalls works as expected"

        key_arg = "ncalls"
        testing_script = "test_glue_helpers.py"
        SAMPLE_OUTPUT = ["{xxyyzzbuilt-in method builtins.len}", "ast.py:222(iter_child_nodes)"]

        debug.trace(4, f"test_formatprofile_PK_ncalls(); self={self}")

        ## OLD
        # empty_file1 = gh.get_temp_file()
        # profile_log  = gh.get_temp_file()
        # test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        # test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"
        # gh.run(test_command_1)
        # gh.run(test_command_2)
        # output = gh.read_file(empty_file1)
        output = self.test_helper_formatprofile(key_arg, testing_script)
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_pcalls(self):
        "Ensures that test_formatprofile_PK_pcalls works as expected"

        key_arg = "pcalls"
        testing_script = "test_glue_helpers.py"
        SAMPLE_OUTPUT = ["{method 'extend' of 'collections.deque' objects}", "typing.py:321(__hash__)"]

        debug.trace(4, f"test_formatprofile_PK_pcalls(); self={self}")
        empty_file1 = gh.get_temp_file()
        profile_log  = gh.get_temp_file()
        test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"

        gh.run(test_command_1)
        gh.run(test_command_2)

        output = gh.read_file(empty_file1)
        assert (SAMPLE_OUTPUT[0] in output and SAMPLE_OUTPUT[1] not in output)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_line(self):
        "Ensures that test_formatprofile_PK_line works as expected"

        key_arg = "line"
        testing_script = "test_glue_helpers.py"
        SAMPLE_OUTPUT = ["0.000    0.000    0.000    0.000 {method 'with_traceback' of 'BaseException' objects}", "0.000    0.000    0.000    0.000 {method 'replace' of 'kode' objects}"]

        debug.trace(4, f"test_formatprofile_PK_line(); self={self}")
        empty_file1 = gh.get_temp_file()
        profile_log  = gh.get_temp_file()
        test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"

        gh.run(test_command_1)
        gh.run(test_command_2)

        output = gh.read_file(empty_file1)
        assert (SAMPLE_OUTPUT[0] in output and SAMPLE_OUTPUT[1] not in output)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_name(self):
        "Ensures that test_formatprofile_PK_name works as expected"

        key_arg = "name"
        testing_script = "test_glue_helpers.py"
        SAMPLE_OUTPUT = ["{built-in method _csv.reader}", "{built-in method _sre.compiler}"]

        debug.trace(4, f"test_formatprofile_PK_name(); self={self}")
        empty_file1 = gh.get_temp_file()
        profile_log  = gh.get_temp_file()
        test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"

        gh.run(test_command_1)
        gh.run(test_command_2)

        output = gh.read_file(empty_file1)
        assert (SAMPLE_OUTPUT[0] in output and SAMPLE_OUTPUT[1] not in output)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_nfl(self):
        "Ensures that test_formatprofile_PK_nfl works as expected"

        key_arg = "nfl"
        testing_script = "test_glue_helpers.py"
        SAMPLE_OUTPUT = ["{built-in method _elementtree._set_factory}", "{built-in method _imp.is_frozen}"]

        debug.trace(4, f"test_formatprofile_PK_nfl(); self={self}")
        empty_file1 = gh.get_temp_file()
        profile_log  = gh.get_temp_file()
        test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"

        gh.run(test_command_1)
        gh.run(test_command_2)

        output = gh.read_file(empty_file1)
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
        return

    ## BAD
    ## @pytest.mark.xfail                   # TODO: remove xfail
    ## def test_formatprofile_PK_name(self):
    ##     "Ensures that test_formatprofile_PK_name works as expected"

    ##     key_arg = "name"
    ##     testing_script = "test_glue_helpers.py"
    ##     SAMPLE_OUTPUT = ["{built-in method _csv.reader}", "{built-in method _sre.compiler}"]

    ##     debug.trace(4, f"test_formatprofile_PK_name(); self={self}")
    ##     empty_file1 = gh.get_temp_file()
    ##     profile_log  = gh.get_temp_file()
    ##     test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
    ##     test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"

    ##     gh.run(test_command_1)
    ##     gh.run(test_command_2)

    ##     output = gh.read_file(empty_file1)
    ##     assert (SAMPLE_OUTPUT[0] in output and SAMPLE_OUTPUT[1] not in output)
    ##     return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_stdname(self):
        "Ensures that test_formatprofile_PK_stdname works as expected"

        key_arg = "stdname"
        testing_script = "test_glue_helpers.py"
        SAMPLE_OUTPUT = ["1(ExceptionChainReprAttributes)", "0.000    0.000    0.000    0.000 {method 'sub' of 're.Pattern' objects}"]

        debug.trace(4, f"test_formatprofile_PK_stdname(); self={self}")
        empty_file1 = gh.get_temp_file()
        profile_log  = gh.get_temp_file()
        test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"

        gh.run(test_command_1)
        gh.run(test_command_2)

        output = gh.read_file(empty_file1)
        assert (SAMPLE_OUTPUT[0] in output and SAMPLE_OUTPUT[1] in output)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_time(self):
        "Ensures that test_formatprofile_PK_time works as expected"

        key_arg = "time"
        testing_script = "test_glue_helpers.py"
        SAMPLE_OUTPUT = ["minidom.py:966(ProcessingInstruction)", "2    0.000    0.000    0.000    0.000 _synchronization.py:24(CapacityLimiterStatistics)"]

        debug.trace(4, f"test_formatprofile_PK_time(); self={self}")
        empty_file1 = gh.get_temp_file()
        profile_log  = gh.get_temp_file()
        test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"

        gh.run(test_command_1)
        gh.run(test_command_2)

        output = gh.read_file(empty_file1)
        assert (SAMPLE_OUTPUT[0] in output and SAMPLE_OUTPUT[1] not in output)
        return

    ## TODO: Find other input sample
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_tottime(self):
        "Ensures that test_formatprofile_PK_tottime works as expected"
        
        key_arg = "tottime"
        testing_script = "test_glue_helpers.py"
        SAMPLE_OUTPUT = ["<attrs generated init attr.validators._IsCallableValidator>:1(__init__)q", "1    0.000    0.000    0.000    0.000 unix_events.py:1252(ThreadedChildWatcher)"]

        debug.trace(4, f"test_formatprofile_PK_tottime(); self={self}")
        
        ## OLD
        # empty_file1 = gh.get_temp_file()
        # profile_log  = gh.get_temp_file()
        # test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        # test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"
        # gh.run(test_command_1)
        # gh.run(test_command_2)
        # output = gh.read_file(empty_file1)
        output = self.test_helper_formatprofile(key_arg, testing_script)
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
        return

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
