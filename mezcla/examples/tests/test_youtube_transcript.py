#! /usr/bin/env python
#
# TODO: Test(s) for ../<module>.py
#
# Notes:
# - Fill out TODO's below. Use numbered tests to order (e.g., test_1_usage).
# - * See test_python_ast.py for simple example of customization.
# - TODO: If any of the setup/cleanup methods defined, make sure to invoke base
#   (see examples below for setUp and tearDown).
# - For debugging the tested script, the ALLOW_SUBCOMMAND_TRACING environment
#   option shows tracing output normally suppressed by unittest_wrapper.py.
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_<module>.py
#
#................................................................................
# Sample test:
#
#   [via https://www.youtube.com/watch?v=E9yhGw66v2Q]
#   0:51        good morning mr. lover I thought I'd
#   0:57        find you out here how long have you been
#   1:04        painting Oh 60 years did you start
#   1:16        painting at Howard high school no I did
#   1:20        some painting I was just beginning to
#   ...
#   20:30       the neighborhood then they're gonna have
#   20:33       to struggle and work hard is that
#   20:35       Dickens to make sure they they win and
#   20:39       they can win all you gotta do is do it
#   22:25       you
#   
   
"""TODO: Tests for <module> module"""

# Standard modules
## TODO: from collections import defaultdict

# Installed modules
import pytest

# Local modules
from mezcla.unittest_wrapper import TestWrapper
from mezcla import debug
from mezcla.my_regex import my_re
from mezcla import system

# Conditional imports
youtube_transcript_api = None
try:
    import youtube_transcript_api
except:
    system.print_exception_info("youtube_transcript_api import")

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                        global module object
#    TestIt.script_module:              path to file
## TODO (vvv): insert new module name in commented out template teo lines below
import mezcla.examples.youtube_transcript as THE_MODULE
#
# Note: sanity test for customization (TODO: remove if desired)
if not my_re.search(__file__, r"\btemplate.py$"):
    debug.assertion("mezcla.template" not in str(THE_MODULE))

## TODO:
## # Environment options
## # Note: These are just intended for internal options, not for end users.
## # It also allows for enabling options in one place.
## #
## FUBAR = system.getenv_bool("FUBAR", False,
##                            description="Fouled Up Beyond All Recognition processing")

#------------------------------------------------------------------------

@pytest.mark.skipif(not youtube_transcript_api, reason="Unable to load youtube_transcript_api")
class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    #
    # TODO: use_temp_base_dir = True            # treat TEMP_BASE as directory
    # note: temp_file defined by parent (along with script_module, temp_base, and test_num)
    # TODO: use TestIt2 if capsys needed

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_run_script(self):
        """Tests run_script w/ data file"""
        debug.trace(4, f"TestIt.test_run_script(); self={self}")
        output = self.run_script(options="E9yhGw66v2Q", skip_stdin=True)
        self.do_assert(my_re.search(r"\d+:\d+.*Howard high school",
                                    output.strip(), flags=my_re.IGNORECASE))
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_YouTubeLikeFormatter(self):
        """Test YouTubeLikeFormatter class"""
        debug.trace(4, f"TestIt2.test_YouTubeLikeFormatter(); self={self}")
        # pylint: disable=protected-access
        formatter = THE_MODULE.YouTubeLikeFormatter()
        self.do_assert("7:37" == formatter._format_timestamp(0, 7, 37, 0))
        self.do_assert("1:07:37" == formatter._format_timestamp(1, 7, 37, 0))
        return

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])
