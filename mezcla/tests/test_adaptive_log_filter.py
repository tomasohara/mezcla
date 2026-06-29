#! /usr/bin/env python3
# TODO: # -*- coding: utf-8 -*-
#
# Test(s) for ../adaptive_log_filter.py
#
# Notes:
# - This can be run as follows (e.g., from root of repo):
#   $ pytest mezcla/tests/test_adaptive_log_filter.py
# - Initial version produced with Gemini-3-Pro.
#

"""Tests for adaptive_log_filter module"""

# Standard modules
## TODO: from typing import Optional

# Installed modules
import pytest

# Local modules
from mezcla import debug
## TODO: from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla.tests.common_module import fix_indent

# Note: Two references are used for the module to be tested:
#    THE_MODULE:               module object (e.g., <module 'mezcla.main' ...>)
#    TestIt.script_module:     dotted module path (e.g., "mezcla.main")
THE_MODULE = None
try:
    import mezcla.adaptive_log_filter as THE_MODULE
    pass                                ## TODO: delete
except:
    system.print_exception_info("adaptive_log_filter import") 

# Note: sanity test for customization (TODO: remove if desired)
if not my_re.search(r"\btemplate.py$", __file__):
    debug.assertion("mezcla.*template" not in str(THE_MODULE))

## TODO:
## # Environment options
## # Note: These are just intended for internal options, not for end users.
## # It also allows for enabling options in one place.
## #
## FUBAR = system.getenv_bool(
##     "FUBAR", False,
##     description="Fouled Up Beyond All Recognition processing")

# Constants
# Note: modeled after pyside-tools/android_deploy.py buildozer log output
BUILDOZER_BASE = "/home/user/project/.buildozer/android/platform/build-arm64-v8a/build/other_builds/python3/"
DUMMY_UNFILTERED_CONTENTS = """
    \x1b[1m[INFO]\x1b[0m:    python3 has no prebuild_arm64_v8a, skipping
    \x1b[1m\x1b[90m[DEBUG]\x1b[39m\x1b[0m:   \tchecking for sys/time.h... yes
    \x1b[1m\x1b[90m[DEBUG]\x1b[39m\x1b[0m:   \tgcc -c -I{path}Include -o foo.o {path}foo.c
    \x1b[1m\x1b[90m[DEBUG]\x1b[39m\x1b[0m:   \tgcc -c -I{path}Include -o bar.o {path}bar.c
    \x1b[1m[INFO]\x1b[0m:    - copy ./PySide6/Qt/lib/libQt6Sql_arm64-v8a.so
    Compiling '{path}Lib/asyncio/log.py'...
    Progress 0.00%\rProgress 25.00%\rProgress 50.00%\rProgress 75.00%\rProgress 100.00%
    \x1b[1m[INFO]\x1b[0m:    - copy ./PySide6/Qt/translations/qt_zh_TW.qm
""".replace("{path}", BUILDOZER_BASE)
DUMMY_FILTERED_CONTENTS = """
    Substitution legend:
        {{path1}}: {path}
    [INFO]:    python3 has no prebuild_arm64_v8a, skipping
    [DEBUG]:   \tchecking for sys/time.h... yes
    [DEBUG]:   \tgcc -c -I{{path1}}Include -o foo.o {{path1}}foo.c
    [DEBUG]:   \tgcc -c -I{{path1}}Include -o bar.o {{path1}}bar.c
    [INFO]:    - copy ./PySide6/Qt/lib/libQt6Sql_arm64-v8a.so
    Compiling '{{path1}}Lib/asyncio/log.py'...
    Progress 0.00%
    Progress 25.00%
    Progress 50.00%
    Progress 75.00%
    Progress 100.00%
    [INFO]:    - copy ./PySide6/Qt/translations/qt_zh_TW.qm
""".replace("{path}", BUILDOZER_BASE).replace("{{path1}}", "{path1}")

#------------------------------------------------------------------------

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    # note: script_module used in argument parsing sanity check (e.g., --help)
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    #
    # TODO: use_temp_base_dir = True    # treat TEMP_BASE as dir (e.g., for simpler organization with many tests)
    # note: temp_file defined by parent (along with script_module, temp_base, and test_num)

    def test_01_data_file(self):
        """Tests run_script w/ data file"""
        debug.trace(4, f"TestIt.test_01_data_file(); self={self}")
        contents = fix_indent(DUMMY_UNFILTERED_CONTENTS)
        # Note: DUMMY_FILTERED_CONTENTS in the script expected the multi-line progress, 
        # but our refiner now collapses it to a single line.
        expected = fix_indent(DUMMY_FILTERED_CONTENTS)
        temp_file = self.create_temp_file(contents)
        # Warning: see notes above about potential issues with run_script-based tests.
        ## TODO: add uses_stdin=True to following if no file argument
        actual = self.run_script(options="--collapse --adaptive",
                                 data_file=temp_file)
        # Using pytest style assertions
        assert(expected.strip() == actual.strip())
        return

    def test_02_collapse_logic(self):
        """Verify that tqdm-style \\r lines are collapsed and ANSI codes stripped."""
        refiner = THE_MODULE.LogRefiner(collapse=True)
        input_data = [
            "Step 1: [==  ]\rStep 1: [====]\rStep 1: Done",
            "\x1b[1m\x1b[90m[DEBUG]\x1b[39m\x1b[0m:   \tCompiling...",
            "Download: 50%\rDownload: 100%"
        ]
        result = refiner.process(input_data)
        
        assert len(result) == 3
        assert result[0] == "Step 1: Done"
        assert result[1] == "[DEBUG]:   \tCompiling..."
        assert result[2] == "Download: 100%"

    def test_03_adaptive_paths(self):
        """Verify long nested buildozer paths are tokenized."""
        # Note: Path must be > 40 chars and have > 4 levels to match current regex
        # Note: regex finds all sub-paths; sorted longest first for substitution
        p4a_base = "/home/user/project/.buildozer/android/platform/build-arm64-v8a/build/other_builds/python3/"
        refiner = THE_MODULE.LogRefiner(adaptive=True)
        
        input_data = [
            f"[DEBUG]:   \tgcc -I{p4a_base}Include -o foo.o {p4a_base}foo.c",
            f"[DEBUG]:   \tgcc -I{p4a_base}Include -o bar.o {p4a_base}bar.c",
            "[INFO]:    - copy ./PySide6/Qt/lib/libQt6Sql.so"
        ]
        
        result = refiner.process(input_data)
        
        # Verify the adaptive identification worked
        assert p4a_base in refiner.path_map
        token = refiner.path_map[p4a_base]
        assert token in result[0]
        # Verify short relative path was NOT tokenized
        assert "./PySide6/Qt/lib/libQt6Sql.so" in result[2]

    def test_04_sampling_fidelity(self):
        """Verify head/tail sampling preserves error messages but not [DEBUG] lines."""
        refiner = THE_MODULE.LogRefiner(sample=True)
        
        # Create 5000 lines of [DEBUG] output (like real buildozer log), place error in middle
        input_data = [f"[DEBUG]:   \tLine {i}" for i in range(5000)]
        critical_error = "SyntaxError: unknown encoding: uft-8"
        input_data[2500] = critical_error
        
        result = refiner.process(input_data)
        
        # Assertions
        assert len(result) < 5000
        assert any(critical_error in line for line in result)
        assert any("SNIP" in line for line in result)
        assert result[0] == "[DEBUG]:   \tLine 0"
        assert result[-1] == "[DEBUG]:   \tLine 4999"

    def test_05_substr_detection(self):
        """Verify that frequent substrings are detected and substituted."""
        refiner = THE_MODULE.LogRefiner(substr=True)

        # Simulate compiler flags with long repeated substrings
        flag_prefix = "-I/home/user/project/build/arm64-v8a"
        input_data = [
            f"gcc -c {flag_prefix}/include1 -o foo.o {flag_prefix}/src1/foo.c",
            f"gcc -c {flag_prefix}/include2 -o bar.o {flag_prefix}/src2/bar.c",
            f"gcc -c {flag_prefix}/include3 -o baz.o {flag_prefix}/src3/baz.c",
            f"gcc -c {flag_prefix}/include1 -o qux.o {flag_prefix}/src1/qux.c",
            f"gcc -c {flag_prefix}/include2 -o abc.o {flag_prefix}/src2/abc.c",
            "[INFO]:    - copy ./PySide6/Qt/lib/libQt6Sql.so"
        ]

        result = refiner.process(input_data)

        # Verify a substitution was made for the common prefix
        assert len(refiner.substr_map) > 0
        tokens = list(refiner.substr_map.values())
        # At least one token should appear in the output
        assert any(tok in line for line in result for tok in tokens)
        # Short unrelated line should NOT be affected
        assert "./PySide6/Qt/lib/libQt6Sql.so" in result[-1]

    def test_10_devious_ansi_and_control_chars(self):
        """Devious cases for ANSI escapes and control characters."""
        refiner = THE_MODULE.LogRefiner(collapse=True)
        
        input_data = [
            # 1. Backspacing typed characters in shell
            # \x08 is the Backspace character; 'stat' followed by 3 backspaces and 'tatus' should become 'status'.
            "git stat\x08\x08\x08tatus",
            # 2. Backspacing through ANSI codes (should preserve text correctly)
            # Verifies that backspacing correctly handles characters even when ANSI color codes (\x1b[31m) are present.
            "Color\x1b[31mRed\x1b[0m\x08\x08\x08Blue",
            # 3. OSC (Operating System Command) Window Title with BEL (\x07) terminator
            "\x1b]2;User@Host: /path\x07Visible text",
            # 4. OSC Window Title with String Terminator (ST) sequence (\x1b\\)
            "\x1b]2;Title\x1b\\More visible text",
            # 5. Complex CSI (Control Sequence Introducer) sequences (Cursor Movement, Clear Screen)
            # \x1b[H moves cursor to home, \x1b[2J clears the screen.
            "\x1b[H\x1b[2JTop of screen text",
            # 6. Bracketed paste and other modes (CSI sequences ending in 'h' or 'l')
            "\x1b[?2004h$ ls\x1b[?2004l",
            # 7. Multiple backspaces at start of line (should not crash)
            "\x08\x08\x08Leading",
            # 8. Script-style trailing \r (should be stripped)
            "Trailing CR\r",
            # 9. Combinations: ANSI + \r + Backspace
            # Tests multiple control characters in one line to ensure they are processed correctly in sequence.
            "Original\r\x1b[1mReplaced\x1b[0m with typo\x08\x08\x08\x08fixed"
        ]
        
        result = refiner.process(input_data)
        
        assert result[0] == "git status"
        assert result[1] == "ColorBlue"
        assert result[2] == "Visible text"
        assert result[3] == "More visible text"
        assert result[4] == "Top of screen text"
        assert result[5] == "$ ls"
        assert result[6] == "Leading"
        assert result[7] == "Trailing CR"
        assert result[8] == "Replaced with fixed"
    
#------------------------------------------------------------------------

def test_06_env_options_are_ints_not_bools():
    """Verify environment tuning constants are numeric, not boolean flags."""
    assert type(THE_MODULE.MIN_PATH_LEN) is int
    assert type(THE_MODULE.MAX_PATHS) is int
    assert type(THE_MODULE.SAMPLE_HEAD_SIZE) is int
    assert type(THE_MODULE.SAMPLE_TAIL_SIZE) is int
    assert type(THE_MODULE.SAMPLE_MAX_INTEREST) is int
    assert THE_MODULE.MIN_PATH_LEN > 0
    assert THE_MODULE.MAX_PATHS > 0
    assert THE_MODULE.SAMPLE_HEAD_SIZE > 0
    assert THE_MODULE.SAMPLE_TAIL_SIZE > 0
    assert THE_MODULE.SAMPLE_MAX_INTEREST > 0


def test_07_adaptive_prefix_aggregation_for_unique_paths():
    """Verify adaptive mode can generalize across unique deep paths."""
    base = "/home/user/project/.buildozer/android/platform/build-arm64-v8a/build/other_builds/python3/"
    input_data = [
        f"Compiling '{base}one/src/file1.c'",
        f"Compiling '{base}two/src/file2.c'",
        f"Compiling '{base}three/src/file3.c'",
    ]
    refiner = THE_MODULE.LogRefiner(adaptive=True)
    result = refiner.process(input_data)

    assert base in refiner.path_map
    shared_token = refiner.path_map[base]
    assert all(shared_token in line for line in result)


def test_08_final_substitution_uses_longest_match_first():
    """Verify overlapping substitutions prefer longer text before shorter text."""
    refiner = THE_MODULE.LogRefiner(adaptive=True, substr=True)
    refiner._get_common_paths = (
        lambda _lines, min_len=THE_MODULE.MIN_PATH_LEN, limit=THE_MODULE.MAX_PATHS: ["/alpha/"])
    refiner._get_common_substrings = (
        lambda _lines,
        min_len=THE_MODULE.MIN_SUBSTR_LEN,
        min_freq=THE_MODULE.MIN_SUBSTR_FREQ,
        limit=THE_MODULE.MAX_SUBSTRS: ["/alpha/beta/"])

    result = refiner.process(["run /alpha/beta/file.c"])
    assert result[0] == "run {sub1}file.c"
    assert "{path1}beta/" not in result[0]


def test_09_sampling_limits_interest_lines(monkeypatch):
    """Verify sampling caps middle interest lines via SAMPLE_MAX_INTEREST."""
    monkeypatch.setattr(THE_MODULE, "SAMPLE_HEAD_SIZE", 2)
    monkeypatch.setattr(THE_MODULE, "SAMPLE_TAIL_SIZE", 2)
    monkeypatch.setattr(THE_MODULE, "SAMPLE_MAX_INTEREST", 1)
    refiner = THE_MODULE.LogRefiner(sample=True)
    input_data = [
        "head-1", "head-2",
        "warning: one",
        "error: two",
        "mid-plain",
        "tail-1", "tail-2"
    ]

    result = refiner.process(input_data)
    interest = [line for line in result if my_re.search(r'warning|error', line, my_re.I)]
    assert len(interest) == 1
    assert "warning: one" in interest[0]

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
