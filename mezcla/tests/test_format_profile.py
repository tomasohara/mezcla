#! /usr/bin/env python3
#
# Tests for format_profile module
#
# Notes:
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_train_language_model.py
#
#-------------------------------------------------------------------------------
# Tested script usage:
#
#   $ format_profile.py 
#   
#   Usage: /home/tomohara/Mezcla/mezcla/format_profile.py profile-log
#   
#   Notes:
#   - Use FULL_PATH to include directoy for filename
#     (e.g., helps to resolve all those __init__.py entries).
#   - Use PROFILE_KEY to over default sorting (cumulative).
#   - Main keys: 
#          cumtime, filename, ncalls, tottime
#   - Other keys: 
#          module, pcalls, line, name, nfl, stdname
#   - Alternative keys:
#          calls, cumulative, file, time
#   - Unfortunately, memory profiling is not supported.
#   - For more details, check following:
#       http://docs.python.org/3/library/profile.html
#   
#   Example (assumes bash):
#       $ python -m cProfile -o /tmp/profile.data simple_main_example.py
#       $ PROFILE_KEY=calls /home/tomohara/Mezcla/mezcla/format_profile.py /tmp/profile.data | head
#
#-------------------------------------------------------------------------------
# Sample tested output:
#
#   Fri Oct  3 21:58:02 2025    /tmp/test_format_profile/test-1-0
#   
#            48514 function calls (47753 primitive calls) in 0.029 seconds
#   
#      Ordered by: call count
#   
#      ncalls  tottime  percall  cumtime  percall filename:lineno(function)
#        4212    0.000    0.000    0.000    0.000 {built-in method builtins.isinstance}
#        3887    0.000    0.000    0.000    0.000 {method 'rstrip' of 'str' objects}
#   2057/1982    0.000    0.000    0.000    0.000 {built-in method builtins.len}
#        2013    0.000    0.000    0.000    0.000 {method 'join' of 'str' objects}
#        1957    0.000    0.000    0.000    0.000 <frozen importlib._bootstrap>:244(_verbose_message)
#        1897    0.001    0.000    0.002    0.000 <frozen importlib._bootstrap_external>:126(_path_join)
#        1897    0.001    0.000    0.001    0.000 <frozen importlib._bootstrap_external>:128(<listcomp>)
#        1011    0.000    0.000    0.000    0.000 {method 'append' of 'list' objects}
#         792    0.000    0.000    0.000    0.000 {built-in method builtins.hasattr}
#         790    0.000    0.000    0.000    0.000 {built-in method builtins.getattr}
#
#-------------------------------------------------------------------------------
## TODO0: convert test_formatprofile_PK_cumtime through test_formatprofile_PK_tottime using
##    an AI assistant such as Clause Opus 4.1! Follow Tom's tips on getting tests to be more mezcla
##    like.
## TODO1: Very carefully review test/template.py,
## TODO2: Follow the mezcla conventions! For example, do not comment out code without
##        indicating why! See previous todo.
##
## TIP:
## - Only need to test a few main keys in any depth, so generalize test_formatprofile_PK_calls
##   so that it can handle alternative sort orders without substantial revision.
## - The minor keys can just check for "Ordered by" label differences.
##

"""Tests for format_profile module"""

# Standard packages
from typing import Optional

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper, invoke_tests

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                        global module object
#    TestIt.script_module:              path to file
import mezcla.format_profile as THE_MODULE

class TestFormatProfile(TestWrapper):
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    use_temp_base_dir = True    # treat TEMP_BASE as directory
    # note: The run involves a usage statement from an archived script to minimize maintenance.
    # Aside: This also makes the test much quicker than the previous version using test_glue_helpers.
    testing_env = "USE_LUCENE=0"
    testing_script = gh.resolve_path(gh.form_path("archive", "search_table_file_index.py"),
                                     heuristic=True)
    testing_options = ""
    old_testing_script = gh.resolve_path(gh.form_path("test_glue_helpers.py"), heuristic=True)

    @staticmethod
    def encode(output, regex=False):
        r"""Convert OUTPUT to encoded representation (e.g., N for each digit).
        Optionally, encodes as REGEX and replaces "..." with ".*".
        For example: 
        >>> TestFormatProfile.encode('0.077 debug.py\n...0.052 system.py', regex=True)
        'N\.NNN debug\.py.*N\.NNN system\.py'
        """
        # EX: TestFormatProfile.encode("7    0.000    0.000    0.540    0.077 debug.py:608(trace_expr)") => "N N.NNN N.NNN N.NNN N.NNN debug.py:NNN(trace_expr)
        in_output = output.strip()
        output = my_re.sub(r"[ \t]+", " ", output)
        output = my_re.sub(r"^ *", "", output, flags=my_re.MULTILINE)
        output = my_re.sub(r" \n", " ", output, flags=my_re.MULTILINE)
        output = my_re.sub(r"[0-9]", "N", output)
        if regex:
            output = my_re.escape(output)
            output = output.replace(r"\.\.\.", ".*")
        debug.trace(7, f"encode({in_output!r}) => {output!r}")
        return output
    
    def helper_format_profile(
            self, key_arg, order_indicator: Optional[str] = None,
            good_sample_output: Optional[str] = None, bad_sample_output: Optional[str] = None,
            testing_script: Optional[str] = None, testing_env: Optional[str] = None, testing_options: Optional[str] = None):
        """Helper function for format_profile tests, using KEY_ARG to order and verifying via ORDER_INDICATOR.
        The optional arguments give GOOD_SAMPLE_OUTPUT and BAD_SAMPLE_OUTPUT. Each should be a multiline string
        in order to test for proper ordering of entries. 
        Note: Digits will be encoded by N to make the tests more robust. In addition, whitespace will be collapsed.
        Other optional arguments give the TESTING_SCRIPT, TESTING_ENV, and TESTING_OPTIONS.

        Sample invocation: 
            GOOD_SAMPLE_OUTPUT = "    11    0.000    0.000    0.625    0.057 __init__.py:1(<module>)\n    147/1    0.001    0.000    0.583    0.583 {built-in method builtins.exec}"
            BAD_SAMPLE_OUTPUT = "        2    0.000    0.000    0.254    0.127 asttokens.py:132(mark_tokens)\n        1    0.000    0.000    0.340    0.340 debug.py:1366(debug_init)"
            output = self.helper_format_profile("cumtime", "cumulative time", GOOD_SAMPLE_OUTPUT, BAD_SAMPLE_OUTPUT)
        """

        # Get options
        if testing_script is None:
            testing_script = self.testing_script
        if testing_env is None:
            testing_env = (self.testing_env if (testing_script == self.testing_script) else "")
        if testing_options is None:
            testing_options = self.testing_options
        debug.assertion(system.file_exists(testing_script))

        # Run script to produce profile and then run profile formatter
        # note: It runs under the default debugging level to avoid extraenous profiling entries.
        profile_log = self.get_temp_file()
        command_cprofile = f"python3 -m cProfile -o {profile_log} {testing_script}"
        _cprofile_output = gh.run(f"{testing_env} {command_cprofile} {testing_options}")
        output = self.run_script(
            env_options=f"DEBUG_LEVEL=2 PROFILE_KEY={key_arg}",
            data_file=profile_log,
        )

        # Make sure ordered by desired metric
        assert("Ordered by:" in output)
        if order_indicator:
            assert(my_re.search(fr"Ordered by: *{order_indicator}", output))
        encoded_output = self.encode(output)
        debug.assertion("N.NNN" in encoded_output)
        if good_sample_output:
            assert(my_re.search(self.encode(good_sample_output, regex=True), encoded_output,
                                flags=my_re.DOTALL|my_re.MULTILINE))
        if bad_sample_output:
            assert(not my_re.search(self.encode(bad_sample_output, regex=True), encoded_output,
                                    flags=my_re.DOTALL|my_re.MULTILINE))

        return output

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_calls(self):
        """Ensures that PROFILE_KEY=calls works as expected"""
        debug.trace(4, f"test_formatprofile_PK_calls(); self={self}")

        # Specify good and bad output:
        # ncalls tottime  percall  cumtime  percall filename:lineno(function)
        GOOD_SAMPLE_OUTPUT = (
            "1    0.000    0.000    0.000    0.000 search_table_file_index.py:545(main)\n" +
            "..." + 
            "1    0.000    0.000    0.573    0.573 search_table_file_index.py:1(<module>)\n")
        BAD_SAMPLE_OUTPUT = (
            "14986    0.021    0.000    0.041    0.000 tokenize.py:433(_tokenize)\n" +
            "..." +            
            "15087    0.002    0.000    0.003    0.000 inspect.py:283(ismodule)\n")
        debug.trace(4, f"helper_format_profile(); self={self}")
        _output = self.helper_format_profile("calls", "call count", GOOD_SAMPLE_OUTPUT, BAD_SAMPLE_OUTPUT)
        return
        
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_cumulative(self):
        """Ensures that PROFILE_KEY=cumulative works as expected"""

        GOOD_SAMPLE_OUTPUT = "<frozen importlib._bootstrap_externals>:877(exec_module)"
        BAD_SAMPLE_OUTPUT = "1    0.000    0.000    0.000    0.000 {built-in method posix.readlink}"

        debug.trace(4, f"test_formatprofile_PK_cumulative(); self={self}")
        _output = self.helper_format_profile("cumulative", "cumulative time", GOOD_SAMPLE_OUTPUT, BAD_SAMPLE_OUTPUT)
        return
    
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_cumtime(self):
        """Ensures that PROFILE_KEY=cumtime works as expected"""
        ## TODO: Find other input sample
        debug.trace(4, f"test_formatprofile_PK_cumtime(); self={self}")
        key_arg = "cumtime"
        SAMPLE_OUTPUT = [
            "test_glue_helper.py:1(<module>)", # Incorrect Line 
            "1    0.000    0.000    0.000    0.000 {method 'fileno' of '_io.BufferedWriter' objects}"
            ]

        # output = gh.read_file(empty_file1)
        output = self.helper_format_profile(key_arg, testing_script=self.old_testing_script)
        # print(output)
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
        # return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_file(self):
        """Ensures that PROFILE_KEY=file works as expected"""

        key_arg = "file"
        SAMPLE_OUTPUT = [
            "<frozen importlib._bootstraps>:391(cached)", 
            "1    0.000    0.000    0.000    0.000 {method 'union' of 'frozenset' objects}"
            ]
        
        debug.trace(4, f"test_formatprofile_PK_file(); self={self}")
        output = self.helper_format_profile(key_arg, testing_script=self.old_testing_script)

        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
    
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_filename(self):
        """Ensures that PROFILE_KEY=filename works as expected"""

        key_arg = "filename"
        SAMPLE_OUTPUT = [
            "1    0.000    0.000    0.000    0.000 :1(ReprEntryNativeAttributes)", 
            "6768    0.000    0.000    0.000    0.000 :1(ReprEntryAttributes)"
        ]


        debug.trace(4, f"test_formatprofile_PK_filename(); self={self}")
        output = self.helper_format_profile(key_arg, testing_script=self.old_testing_script)
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] not in output)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_module(self):
        """Ensures that PROFILE_KEY=module works as expected"""

        key_arg = "module"
        SAMPLE_OUTPUT = [
            "ElementTree.pytest:1771(C14NWriterTarget)",
            "1    0.000    0.000    0.000    0.000 terminal.py:1306(_build_normal_summary_stats_line)"
        ]

        debug.trace(4, f"test_formatprofile_PK_module(); self={self}")
        output = self.helper_format_profile(key_arg, testing_script=self.old_testing_script)
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_ncalls(self):
        """Ensures that PROFILE_KEY=ncalls works as expected"""
        ## TODO: Find other input sample

        key_arg = "ncalls"
        ## OLD: testing_script = old_testing_script
        SAMPLE_OUTPUT = [
            "{method 'extend' of 'collections.deque' objections}", 
            "1    0.000    0.000    0.000    0.000 test_glue_helpers.py:385(test_get_files_matching_specs)"
            ]

        debug.trace(4, f"test_formatprofile_PK_ncalls(); self={self}")

        output = self.helper_format_profile(key_arg, testing_script=self.old_testing_script)
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_pcalls(self):
        """Ensures that PROFILE_KEY=pcalls works as expected"""

        key_arg = "pcalls"
        SAMPLE_OUTPUT = [
            "unix_events.py:1022(SafestChildWatcher)",
            "1    0.000    0.000    0.000    0.000 <frozen importlib._bootstrap>:294(_module_repr)"
        ]

        debug.trace(4, f"test_formatprofile_PK_pcalls(); self={self}")
        output = self.helper_format_profile(key_arg, testing_script=self.old_testing_script)
        
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
        # return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_line(self):
        """Ensures that PROFILE_KEY=line works as expected"""

        key_arg = "line"
        SAMPLE_OUTPUT = [
            "{method 'with_traceback' of 'BaseExceptions' objects}", 
            "1    0.000    0.000    0.000    0.000 {method 'rjust' of 'str' objects}"
        ]
        debug.trace(4, f"test_formatprofile_PK_line(); self={self}")

        output = self.helper_format_profile(key_arg, testing_script=self.old_testing_script)

        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_name(self):
        """Ensures that PROFILE_KEY=name works as expected"""

        key_arg = "name"
        SAMPLE_OUTPUT = [
            "{method 'fileno' of '_io.BufferedReaders' objects}", 
            "6    0.000    0.000    0.000    0.000 {method 'pop' of 'collections.deque' objects}"
        ]

        debug.trace(4, f"test_formatprofile_PK_name(); self={self}")
        output = self.helper_format_profile(key_arg, testing_script=self.old_testing_script)
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_nfl(self):
        """Ensures that PROFILE_KEY=nfl works as expected"""

        key_arg = "nfl"
        
        SAMPLE_OUTPUT = [
            "{built-in methods _imp.is_frozen}",
            "1    0.000    0.000    0.000    0.000 {built-in method _stat.S_IMODE}", 
        ]

        debug.trace(4, f"test_formatprofile_PK_nfl(); self={self}")
        
        output = self.helper_format_profile(key_arg, testing_script=self.old_testing_script)
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_stdname(self):
        """Ensures that PROFILE_KEY=stdname works as expected"""

        key_arg = "stdname"

        SAMPLE_OUTPUT = [
            "zipperfile.py:1(<module>)", 
            "1    0.000    0.000    0.000    0.000 _synchronization.py:70(SemaphoreStatistics)"
        ]

        debug.trace(4, f"test_formatprofile_PK_stdname(); self={self}")

        output = self.helper_format_profile(key_arg, self.testing_script)
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_time(self):
        """Ensures that PROFILE_KEY=time works as expected"""

        key_arg = "time"

        SAMPLE_OUTPUT = [
            "<frozen importlibrary._bootstrap_external>:380(cache_from_source)", 
            "1    0.000    0.000    0.000    0.000 glue_helpers.py:731(delete_existing_file)"
        ]

        debug.trace(4, f"test_formatprofile_PK_time(); self={self}")
        output = self.helper_format_profile(key_arg, testing_script=self.old_testing_script)
        
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_formatprofile_PK_tottime(self):
        """Ensures that PROFILE_KEY=tottime works as expected"""
        ## TODO: Find other input sample
        
        key_arg = "tottime"
        SAMPLE_OUTPUT = [
            "{method 'split' of 're.Pattern' objections}", 
            "1    0.000    0.000    0.000    0.000 cacheprovider.py:390(pytest_sessionfinish)"
        ]

        debug.trace(4, f"test_formatprofile_PK_tottime(); self={self}")
        
        output = self.helper_format_profile(key_arg, testing_script=self.old_testing_script)
        assert (SAMPLE_OUTPUT[0] not in output and SAMPLE_OUTPUT[1] in output)
        return

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
