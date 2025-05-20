#! /usr/bin/env python3
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
## OLD: from mezcla.my_regex import my_re
## OLD: from mezcla import system
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
## OLD: from mezcla.unittest_wrapper import trap_exception

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                        global module object
#    TestIt.script_module:              path to file
import mezcla.format_profile as THE_MODULE

class TestFormatProfile(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    use_temp_base_dir = True    # treat TEMP_BASE as directory
    testing_script = gh.resolve_path("test_glue_helpers.py", heuristic=True)
    
    # For testing, let the dir be ./mezcla/mezcla/tests
    # TODO: Find a way to denote a random number in SAMPLE OUTPUT which may differ in each execution

    # ## OLD: Doesn't use helper function
    # @pytest.mark.xfail                   # TODO: remove xfail
    # @trap_exception                      # TODO: remove when debugged
    # def test_formatprofile_PK_calls(self):
    #     "Ensures that test_formatprofile_PK_calls works as expected"
    #     ## TODO3: reword commment because test_formatprofile_PK_calls is not testing itself;
    #     ## Instead, use something like "ensure that PROFILE_KEY=calls works as expected".

    #     key_arg = "calls"
    #     ## OLD: testing_script = "test_glue_helpers.py"
    #     testing_script = gh.resolve_path("simple_main_example.py")
    #     ## OLD: SAMPLE_OUTPUT = ["1    0.001    0.000    0.000    0.000 cacheprovider.py:307(pytest_report_collectionfinish)", "{method 'popleft' of 'collections.deque' objects}"]

    #     # Sample output:
    #     #     Ordered by: call count
    #     # 
    #     #     ncalls  tottime  percall  cumtime  percall filename:lineno(function)
    #     #     3323    0.000    0.000    0.000    0.000 {built-in method builtins.isinstance}
    #     #     2670    0.000    0.000    0.000    0.000 {method 'rstrip' of 'str' objects}
    #     #     1825/1723    0.000    0.000    0.000    0.000 {built-in method builtins.len}
    #     #     1443    0.000    0.000    0.000    0.000 {method 'append' of 'list' objects}
    #     #
        
    #     debug.trace(4, f"test_formatprofile_PK_calls(); self={self}")
    #     ## OLD: empty_file1 = self.get_temp_file()
    #     ## OLD: profile_log  = self.get_temp_file()
    #     profile_data = self.temp_file + "-profile.data"
    #     ## OLD: test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
    #     # note: runs simple_main_example.py over itself; for example,
    #     #   python -m cProfile -o /tmp/tmpp6zg9a5o/test-1-profile.data simple_main_example.py simple_main_example.py
    #     test_command_1 = f"python -m cProfile -o {profile_data} {testing_script} {testing_script}"
    #     ## BAD: test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"

    #     gh.run(test_command_1)
    #     ## BAD: gh.run(test_command_2)

    #     ## BAD: output = gh.read_file(empty_file1)
    #     output = self.run_script(env_options=f"PROFILE_KEY={key_arg}", data_file=profile_data)
    #     self.do_assert("Ordered by: call count" in output)
    #     my_re.search(r"^\s*(\S+)\s+.*method 'rstrip'", output, flags=my_re.MULTILINE)
    #     rstrip_count = system.to_float(my_re.group(1))
    #     my_re.search(r"^\s*(\S+)\s+.*method 'append'", output, flags=my_re.MULTILINE)
    #     join_count = system.to_float(my_re.group(1))
    #     self.do_assert(rstrip_count > join_count)

    #     return
    
    def helper_format_profile(
        self,
        key_arg,
        testing_script,
        ):
        """Helper function for format_profile tests"""
        debug.trace(4, f"helper_format_profile(); self={self}")
        
        # # OLD: Uses gh.run() approach
        # empty_file = self.get_temp_file()
        # profile_log = self.get_temp_file()
        # command1 = f"python3 -m cProfile -o {profile_log} {testing_script}"
        # command2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file}"
        # gh.run(command1)
        # gh.run(command2)
        # output = gh.read_file(empty_file)
        # return output

        ## OLD: profile_log = self.get_temp_file()
        profile_log = self.get_temp_file()
        command_cprofile = f"python3 -m cProfile -o {profile_log} {testing_script}"
        _cprofile_output = gh.run(command_cprofile)
        output = self.run_script(
            env_options=f"PROFILE_KEYS={key_arg}",
            data_file=profile_log,
        )
        assert("Ordered by:" in output)
        return output

    @pytest.mark.xfail                   # TODO: remove xfail
    # @trap_exception                      # TODO: remove when debugged
    def test_formatprofile_PK_calls(self):
        """Ensures that PROFILE_KEY=calls works as expected"""

        key_arg = "calls"
        ## OLD: testing_script = "test_glue_helpers.py"
        ## OLD: SAMPLE_OUTPUT = ["1    0.001    0.000    0.000    0.000 cacheprovider.py:307(pytest_report_collectionfinish)", "{method 'popleft' of 'collections.deque' objects}"]
        SAMPLE_OUTPUT = [
            "test_glue_helpers.py:232(test_heuristic_resolve_paths)",
            "1    0.000    0.000    0.000    0.000 tempfile.py:800(SpooledTemporaryFile)", 
        ]
        debug.trace(4, f"test_formatprofile_PK_calls(); self={self}")
        output = self.helper_format_profile(key_arg, self.testing_script)
        # print(output)
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
        return
        
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_cumulative(self):
        """Ensures that PROFILE_KEY=cumulative works as expected"""

        key_arg = "cumulative"
        ## OLD: testing_script = "test_glue_helpers.py"
        # OLD: SAMPLE_OUTPUT = ["<frozen importlib._bootstrap>:211(_call_with_frames_removed)q", "2    0.000    0.000    0.000    0.000 logging.py:128(_get_auto_indent)"]
        SAMPLE_OUTPUT = [
            "<frozen importlib._bootstrap_externals>:877(exec_module)", 
            "1    0.000    0.000    0.000    0.000 {built-in method posix.readlink}"
        ]

        debug.trace(4, f"test_formatprofile_PK_cumulative(); self={self}")
        # empty_file1 = self.get_temp_file()
        # profile_log  = self.get_temp_file()
        # test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        # test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"
        # gh.run(test_command_1)
        # gh.run(test_command_2)
        # output = gh.read_file(empty_file1)
        output = self.helper_format_profile(key_arg, self.testing_script)
        # print(output)
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
        return
    
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_cumtime(self):
        """Ensures that PROFILE_KEY=cumtime works as expected"""
        ## TODO: Find other input sample
        debug.trace(4, f"test_formatprofile_PK_cumtime(); self={self}")
        key_arg = "cumtime"
        ## OLD: testing_script = "test_glue_helpers.py"
        SAMPLE_OUTPUT = [
            "test_glue_helper.py:1(<module>)", # Incorrect Line 
            "1    0.000    0.000    0.000    0.000 {method 'fileno' of '_io.BufferedWriter' objects}"
            ]
        ## OLD
        # SAMPLE_OUTPUT = [
        #     "_hooks.py:244(__call__)qq", 
        #     "1    0.000    0.000    0.000    0.000 <attrs generated eq attr.validators._NumberValidator>:1(<module>)"
        #     ]
        # empty_file1 = self.get_temp_file()
        # profile_log  = self.get_temp_file()
        # test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        # test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"

        # gh.run(test_command_1)
        # gh.run(test_command_2)

        # output = gh.read_file(empty_file1)
        output = self.helper_format_profile(key_arg, self.testing_script)
        # print(output)
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
        # return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_file(self):
        """Ensures that PROFILE_KEY=file works as expected"""

        key_arg = "file"
        ## OLD: testing_script = "test_glue_helpers.py"
        SAMPLE_OUTPUT = [
            "<frozen importlib._bootstraps>:391(cached)", 
            "1    0.000    0.000    0.000    0.000 {method 'union' of 'frozenset' objects}"
            ]
        
        debug.trace(4, f"test_formatprofile_PK_file(); self={self}")
        # empty_file1 = self.get_temp_file()
        # profile_log  = self.get_temp_file()
        # test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        # test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"

        # gh.run(test_command_1)
        # gh.run(test_command_2)
        output = self.helper_format_profile(key_arg, self.testing_script)

        # output = gh.read_file(empty_file1)
        # print(output)
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
        # return
    
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_filename(self):
        """Ensures that PROFILE_KEY=filename works as expected"""

        key_arg = "filename"
        ## OLD: testing_script = "test_glue_helpers.py"
        SAMPLE_OUTPUT = [
            "1    0.000    0.000    0.000    0.000 :1(ReprEntryNativeAttributes)", 
            "6768    0.000    0.000    0.000    0.000 :1(ReprEntryAttributes)"
        ]


        ## OLD
        debug.trace(4, f"test_formatprofile_PK_filename(); self={self}")
        # empty_file1 = self.get_temp_file()
        # profile_log  = self.get_temp_file()
        # test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        # test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"

        # gh.run(test_command_1)
        # gh.run(test_command_2)

        # output = gh.read_file(empty_file1)

        output = self.helper_format_profile(key_arg, self.testing_script)
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] not in output)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_module(self):
        """Ensures that PROFILE_KEY=module works as expected"""

        key_arg = "module"
        ## OLD: testing_script = "test_glue_helpers.py"
        # OLD: SAMPLE_OUTPUT = ["1    0.000    0.000    0.000    0.000 :1(ExceptionChainReprAttributes)"]
        SAMPLE_OUTPUT = [
            "ElementTree.pytest:1771(C14NWriterTarget)",
            "1    0.000    0.000    0.000    0.000 terminal.py:1306(_build_normal_summary_stats_line)"
        ]

        debug.trace(4, f"test_formatprofile_PK_module(); self={self}")
        output = self.helper_format_profile(key_arg, self.testing_script)
        # empty_file1 = self.get_temp_file()
        # profile_log  = self.get_temp_file()
        # test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        # test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"
        # gh.run(test_command_1)
        # gh.run(test_command_2)
        # output = gh.read_file(empty_file1)
        # print(output)
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
        # return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_ncalls(self):
        """Ensures that PROFILE_KEY=ncalls works as expected"""
        ## TODO: Find other input sample

        key_arg = "ncalls"
        ## OLD: testing_script = "test_glue_helpers.py"
        SAMPLE_OUTPUT = [
            "{method 'extend' of 'collections.deque' objections}", 
            "1    0.000    0.000    0.000    0.000 test_glue_helpers.py:385(test_get_files_matching_specs)"
            ]

        debug.trace(4, f"test_formatprofile_PK_ncalls(); self={self}")

        ## OLD
        # empty_file1 = self.get_temp_file()
        # profile_log  = self.get_temp_file()
        # test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        # test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"
        # gh.run(test_command_1)
        # gh.run(test_command_2)
        # output = gh.read_file(empty_file1)
        output = self.helper_format_profile(key_arg, self.testing_script)
        # print (output)
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_pcalls(self):
        """Ensures that PROFILE_KEY=pcalls works as expected"""

        key_arg = "pcalls"
        ## OLD: testing_script = "test_glue_helpers.py"
        SAMPLE_OUTPUT = [
            "unix_events.py:1022(SafestChildWatcher)",
            "1    0.000    0.000    0.000    0.000 <frozen importlib._bootstrap>:294(_module_repr)"
        ]

        debug.trace(4, f"test_formatprofile_PK_pcalls(); self={self}")
        output = self.helper_format_profile(key_arg, self.testing_script)
        # SAMPLE_OUTPUT = ["{method 'extend' of 'collections.deque' objects}", "typing.py:321(__hash__)"]
        # empty_file1 = self.get_temp_file()
        # profile_log  = self.get_temp_file()
        # test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        # test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"
        # gh.run(test_command_1)
        # gh.run(test_command_2)
        # output = gh.read_file(empty_file1)
        # print(output)
        
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
        # return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_line(self):
        """Ensures that PROFILE_KEY=line works as expected"""

        key_arg = "line"
        ## OLD: testing_script = "test_glue_helpers.py"
        SAMPLE_OUTPUT = [
            "{method 'with_traceback' of 'BaseExceptions' objects}", 
            "1    0.000    0.000    0.000    0.000 {method 'rjust' of 'str' objects}"
        ]
        debug.trace(4, f"test_formatprofile_PK_line(); self={self}")

        output = self.helper_format_profile(key_arg, self.testing_script)

        ## OLD
        # SAMPLE_OUTPUT = ["0.000    0.000    0.000    0.000 {method 'with_traceback' of 'BaseException' objects}", "0.000    0.000    0.000    0.000 {method 'replace' of 'kode' objects}"]
        # empty_file1 = self.get_temp_file()
        # profile_log  = self.get_temp_file()
        # test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        # test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"
        # gh.run(test_command_1)
        # gh.run(test_command_2)
        # output = gh.read_file(empty_file1)
        # print(output)
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_name(self):
        """Ensures that PROFILE_KEY=name works as expected"""

        key_arg = "name"
        ## OLD: testing_script = "test_glue_helpers.py"
        SAMPLE_OUTPUT = [
            "{method 'fileno' of '_io.BufferedReaders' objects}", 
            "6    0.000    0.000    0.000    0.000 {method 'pop' of 'collections.deque' objects}"
        ]

        debug.trace(4, f"test_formatprofile_PK_name(); self={self}")
        output = self.helper_format_profile(key_arg, self.testing_script)
        # SAMPLE_OUTPUT = ["{built-in method _csv.reader}", "{built-in method _sre.compiler}"]
        # empty_file1 = self.get_temp_file()
        # profile_log  = self.get_temp_file()
        # test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        # test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"
        # gh.run(test_command_1)
        # gh.run(test_command_2)
        # output = gh.read_file(empty_file1)
        # print(output)
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_nfl(self):
        """Ensures that PROFILE_KEY=nfl works as expected"""

        key_arg = "nfl"
        ## OLD: testing_script = "test_glue_helpers.py"
        
        SAMPLE_OUTPUT = [
            "{built-in methods _imp.is_frozen}",
            "1    0.000    0.000    0.000    0.000 {built-in method _stat.S_IMODE}", 
        ]

        debug.trace(4, f"test_formatprofile_PK_nfl(); self={self}")
        
        # SAMPLE_OUTPUT = ["{built-in method _elementtree._set_factory}", "{built-in method _imp.is_frozen}"]
        # empty_file1 = self.get_temp_file()
        # profile_log  = self.get_temp_file()
        # test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        # test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"
        # gh.run(test_command_1)
        # gh.run(test_command_2)
        # output = gh.read_file(empty_file1)
        output = self.helper_format_profile(key_arg, self.testing_script)
        # print(output)
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
        # return

    ## BAD
    ## @pytest.mark.xfail                   # TODO: remove xfail
    ## def test_formatprofile_PK_name(self):
    ##     "Ensures that test_formatprofile_PK_name works as expected"

    ##     key_arg = "name"
    ##     testing_script = "test_glue_helpers.py"
    ##     SAMPLE_OUTPUT = ["{built-in method _csv.reader}", "{built-in method _sre.compiler}"]

    ##     debug.trace(4, f"test_formatprofile_PK_name(); self={self}")
    ##     empty_file1 = self.get_temp_file()
    ##     profile_log  = self.get_temp_file()
    ##     test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
    ##     test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"

    ##     gh.run(test_command_1)
    ##     gh.run(test_command_2)

    ##     output = gh.read_file(empty_file1)
    ##     assert (SAMPLE_OUTPUT[0] in output and SAMPLE_OUTPUT[1] not in output)
    ##     return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_stdname(self):
        """Ensures that PROFILE_KEY=stdname works as expected"""

        key_arg = "stdname"
        ## OLD: testing_script = "test_glue_helpers.py"

        SAMPLE_OUTPUT = [
            "zipperfile.py:1(<module>)", 
            "1    0.000    0.000    0.000    0.000 _synchronization.py:70(SemaphoreStatistics)"
        ]

        debug.trace(4, f"test_formatprofile_PK_stdname(); self={self}")

        ## OLD
        # SAMPLE_OUTPUT = [
        #     "1(ExceptionChainReprAttributes)", 
        #     "0.000    0.000    0.000    0.000 {method 'sub' of 're.Pattern' objects}"
        # ]
        # empty_file1 = self.get_temp_file()
        # profile_log  = self.get_temp_file()
        # test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        # test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"
        # gh.run(test_command_1)
        # gh.run(test_command_2)
        # output = gh.read_file(empty_file1)

        output = self.helper_format_profile(key_arg, self.testing_script)
        # print(output)
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_time(self):
        """Ensures that PROFILE_KEY=time works as expected"""

        key_arg = "time"
        ## OLD: testing_script = "test_glue_helpers.py"

        SAMPLE_OUTPUT = [
            "<frozen importlibrary._bootstrap_external>:380(cache_from_source)", 
            "1    0.000    0.000    0.000    0.000 glue_helpers.py:731(delete_existing_file)"
        ]

        debug.trace(4, f"test_formatprofile_PK_time(); self={self}")
        output = self.helper_format_profile(key_arg, self.testing_script)
        
        ## OLD
        # SAMPLE_OUTPUT = [
        #     "minidom.py:966(ProcessingInstruction)", 
        #     "2    0.000    0.000    0.000    0.000 _synchronization.py:24(CapacityLimiterStatistics)"
        # ]
        # empty_file1 = self.get_temp_file()
        # profile_log  = self.get_temp_file()
        # test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        # test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"
        # gh.run(test_command_1)
        # gh.run(test_command_2)
        # output = gh.read_file(empty_file1)
        # print(output)
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_tottime(self):
        """Ensures that PROFILE_KEY=tottime works as expected"""
        ## TODO: Find other input sample
        
        key_arg = "tottime"
        ## OLD: testing_script = "test_glue_helpers.py"
        SAMPLE_OUTPUT = [
            "{method 'split' of 're.Pattern' objections}", 
            "1    0.000    0.000    0.000    0.000 cacheprovider.py:390(pytest_sessionfinish)"
        ]

        debug.trace(4, f"test_formatprofile_PK_tottime(); self={self}")
        
        ## OLD
        # empty_file1 = self.get_temp_file()
        # profile_log  = self.get_temp_file()
        # test_command_1 = f"python -m cProfile -o {profile_log} {testing_script}"
        # test_command_2 = f"PROFILE_KEY={key_arg} ../format_profile.py {profile_log} > {empty_file1}"
        # gh.run(test_command_1)
        # gh.run(test_command_2)
        # output = gh.read_file(empty_file1)
        output = self.helper_format_profile(key_arg, self.testing_script)
        # print(output)
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
        return

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
