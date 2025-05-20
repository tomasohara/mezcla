#! /usr/bin/env python3
#
# Test(s) for glue_helpers.py
#
# Notes:
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_glue_helpers.py
#
# TODO:
# - Add support for write_lines & read_lines.
# - Add support for other commonly used functions.
# TODO2:
# - Use gh.form_path instead of hard-coding path delimiters.
# TODO3
# - Flag tests that assume Unix (posix).
#

"""Tests for glue_helpers module"""

# Standard packages
import os
## OLD: from os import path
from io import StringIO
import sys
## OLD: import atexit
## OLD: import tempfile

# Installed packages
import pytest

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla import tpo_common as tpo    # Deprecated, only used for mock
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla import system
from mezcla.tests.common_module import mezcla_root_dir

# Note: Two references are used for the module to be tested:
#    THE_MODULE:	    global module object
import mezcla.glue_helpers as THE_MODULE # pylint: disable=reimported

class TestGlueHelpers(TestWrapper):      ## TODO: (TestWrapper)
    """Class for testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    ## OLD: temp_file = self.get_temp_file()

    @pytest.mark.xfail                   # TODO: remove xfail
    ## DEBUG: @trap_exception            # TODO: remove when debugged
    def test_01_data_file(self):
        """Tests run_script w/ data file"""
        # Warning: see notes above about potential issues with run_script-based tests.
        debug.trace(4, f"TestIt.test_01_data_file(); self={self}")
        data = ["item1", "item2"]
        system.write_lines(self.temp_file, data)
        output = self.run_script(options="--help", data_file=self.temp_file)
        self.do_assert(my_re.search(r"gluing.*scripts", output))
        captured = self.get_stderr()
        self.do_assert(my_re.search(r"not.*intended", captured))
        return

    def test_get_temp_file(self):
        """Ensure get_temp_file works as expected"""
        debug.trace(4, "test_get_temp_file()")
        assert isinstance(THE_MODULE.get_temp_file(), str)

    def test_remove_extension(self):
        """Ensure remove_extension works as expected"""
        debug.trace(4, "test_remove_extension()")
        ## TODO2: remove path or use form_path
        assert THE_MODULE.remove_extension("/tmp/solr-4888.log", ".log") == "/tmp/solr-4888"
        assert THE_MODULE.remove_extension("/tmp/fubar.py", ".py") == "/tmp/fubar"
        assert THE_MODULE.remove_extension("/tmp/fubar.py", "py") == "/tmp/fubar."

    def test_dir_path(self):
        """Ensure dir_path works as expected"""
        debug.trace(4, "test_dir_path()")
        debug.assertion(os.name == "posix")
        assert THE_MODULE.dir_path("/tmp/solr-4888.log") == "/tmp"

    def test_file_exists(self):
        """Ensure file_exists works as expected"""
        debug.trace(4, "test_file_exists()")
        # Existent file
        test_filename = self.get_temp_file()
        system.write_file(test_filename, 'some content')
        assert THE_MODULE.file_exists(test_filename)
        # Not existent file
        assert not THE_MODULE.file_exists('bad_filename')

    def test_non_empty_file(self):
        """Ensure non_empty_file works as expected"""
        debug.trace(4, "test_non_empty_file()")

        # Test valid file
        file_with_content = self.get_temp_file()
        system.write_file(file_with_content, 'content')
        assert THE_MODULE.non_empty_file(file_with_content)

        # Test non existent file
        assert not THE_MODULE.non_empty_file('bad_file_name')

        # Test empty file
        empty_file = self.get_temp_file()
        with open(empty_file, 'wb') as _:
            pass # system.write_file cant be used because appends a newline
        assert not THE_MODULE.non_empty_file(empty_file)

    @pytest.mark.xfail
    def test_form_path(self):
        """Ensure form_path works as expected"""
        debug.trace(4, "test_form_path()")
        debug.assertion(os.name == "posix")
        assert(THE_MODULE.form_path("/", "home", "User", "Desktop", "file.txt")
               == "/home/User/Desktop/file.txt")
        ## TEMP:
        self.temp_file += "-test_form_path"
        # Make sure can create directory
        test_temp_dir = THE_MODULE.form_path(self.temp_file, "test_dir")
        test_temp_file = THE_MODULE.form_path(test_temp_dir, "test_file",
                                              create=True)
        assert(system.file_exists(test_temp_dir))
        assert(not system.file_exists(test_temp_file))

    @pytest.mark.xfail
    def test_create_directory(self):
        """Ensure create_directory works as expected"""
        debug.trace(4, "test_create_directory()")
        ## OLD: test_dir = THE_MODULE.dir_path(__file__)
        # Note: Use of temp files in repo tree should be avoided.
        ## BAD: res_2_dir = THE_MODULE.form_path(test_dir, "resources_2")
        res_2_dir = gh.form_path(gh.get_temp_dir(), "resources_2")
        ## OLD: _ = THE_MODULE.form_path(test_dir, "resources")
        THE_MODULE.create_directory(res_2_dir)
        ## OLD:
        ## # cleanup created directory
        ## atexit.register(THE_MODULE.delete_directory, res_2_dir)
        assert THE_MODULE.is_directory(res_2_dir)

    @pytest.mark.xfail
    def test_full_mkdir(self):
        """Ensure full_mkdir works as expected"""
        debug.trace(4, "test_full_mkdir()")
        temp_dir_abc = gh.form_path(gh.TMP, "a", "b", "c", str(system.get_process_id()))
        debug.assertion(not system.is_directory(temp_dir_abc))
        THE_MODULE.full_mkdir(temp_dir_abc)
        assert  system.is_directory(temp_dir_abc)

    @pytest.mark.xfail
    def test_get_temp_dir(self):
        """Tests get_temp_dir"""
        debug.trace(4, "test_get_temp_dir()")
        static_temp_dir = gh.form_path(self.get_temp_dir(), "test_get_temp_dir")

        # Make sure new temp dirs used each time unless pre-specified
        self.monkeypatch.setattr(gh, "TEMP_FILE", None)
        temp_dir1 = THE_MODULE.get_temp_dir()
        temp_dir2 = THE_MODULE.get_temp_dir()
        assert temp_dir1 != temp_dir2
        assert system.is_directory(temp_dir1)
        assert system.is_directory(temp_dir2)

        # note: not deleted for debugging purposes
        ## OLD: static_temp_dir = tempfile.NamedTemporaryFile(delete=False).name
        self.monkeypatch.setattr(gh, "TEMP_FILE", static_temp_dir)
        temp_dir3 = THE_MODULE.get_temp_dir()
        temp_dir4 = THE_MODULE.get_temp_dir()
        assert temp_dir3 == temp_dir4 == static_temp_dir
        assert system.is_directory(temp_dir3)

    @pytest.mark.xfail
    def test_real_path(self):
        """Ensure real_path works as expected"""
        ## TODO3: skip if not posix
        debug.trace(4, "test_real_path()")
        debug.assertion(my_re.search("ubuntu", gh.run("uname -a"),
                                     flags=my_re.IGNORECASE))
        assert THE_MODULE.real_path("/etc/mtab").startswith("/proc")

    def test_indent(self):
        """Ensure indent works as expected"""
        debug.trace(4, "test_indent()")
        test_text = 'this is an example text to be indented'
        tab_indented_text = '\tthis is an example text to be indented'
        assert THE_MODULE.indent(test_text, '\t') == tab_indented_text

    def test_indent_lines(self):
        """Ensure indent_lines works as expected"""
        debug.trace(4, "test_indent_lines()")
        test_text = (
            'this is\n'
            'an example text\n'
            'to be indented\n'
        )
        tab_indented_text = (
            '\tthis is\n'
            '\tan example text\n'
            '\tto be indented\n'
        )
        assert THE_MODULE.indent_lines(test_text, '\t') == tab_indented_text

    def test_elide(self):
        """Ensure elide works as expected"""
        debug.trace(4, "test_elide()")
        assert THE_MODULE.elide("=" * 80, max_len=8) == "========..."
        assert THE_MODULE.elide(None, 10) == ""

    def test_elide_values(self):
        """Ensure elide_values works as expected"""
        debug.trace(4, "test_elide_values()")
        assert THE_MODULE.elide_values(["1", "22", "333"], max_len=2) == ["1", "22", "33..."]

    @pytest.mark.xfail
    def test_disable_subcommand_tracing(self):
        """Ensure disable_subcommand_tracing works as expected
        Warning: This test relies upon various assumptions about the tracing
        level. The overall level is set to 7, so that the run invocation is shown;
        and the issue command trace level is set to 5 for the get/setenv tracing.
        """
        debug.trace(4, "test_disable_subcommand_tracing()")
        test_dir = THE_MODULE.dirname(__file__)
        ## TODO4: rework to use html input file (e.g., for posthoc conversion validation)
        resource_file = THE_MODULE.form_path(test_dir, "resources", "example_text.txt")
        self.patch_trace_level(7)

        # Test with sub-tracing
        ## NOTE: capsys doesn't work across processes, hence sub-stderr based on log
        ## TODO3: look into capfd
        out_file1 = self.temp_file + ".out1"
        log_file1 = self.temp_file + ".log1"
        command = f"STDOUT=1 python -m mezcla.extract_document_text {resource_file} > {out_file1} 2> {log_file1}"
        THE_MODULE.issue(command, trace_level=5, subtrace_level=5)
        assert "Combined Work" in system.read_file(out_file1)
        stderr_1 = self.get_stderr()
        assert my_re.search(r"run.*extract_document_text", stderr_1)
        sub_stderr_1 = system.read_file(log_file1)
        assert my_re.search(r"getenv_int\(SUB_DEBUG_LEVEL, \d+\) => 5", sub_stderr_1)

        # Test without sub-tracing
        out_file2 = self.temp_file + ".out2"
        log_file2 = self.temp_file + ".log2"
        command = f"STDOUT=1 python -m mezcla.extract_document_text {resource_file} > {out_file2} 2> {log_file2}"
        THE_MODULE.disable_subcommand_tracing()
        THE_MODULE.issue(command, trace_level=5)
        assert "Combined Work" in system.read_file(out_file2)
        stderr_2 = self.get_stderr()
        sub_stderr_2 = system.read_file(log_file2)
        assert my_re.search(r"setenv\(DEBUG_LEVEL, 0\)", stderr_2)
        assert not sub_stderr_2.strip()

    @pytest.mark.xfail
    def test_run(self):
        """Ensure run works as expected"""
        debug.trace(4, "test_run()")
        assert "root" in THE_MODULE.run("ls /")

    def test_issue(self):
        """Ensure issue works as expected"""
        debug.trace(4, "test_issue()")

        # Simple command test
        temp_file = self.get_temp_file()
        THE_MODULE.issue(f'echo "this is a simple test" > {temp_file}')
        assert 'this is a simple test' in gh.read_file(temp_file)

        # Setup log file
        log_file = self.get_temp_file()
        system.write_file(log_file, 'random content')
        def debugging_mock():
            return True
        self.monkeypatch.setattr(tpo, 'debugging', debugging_mock)
        self.monkeypatch.setenv('TEMP_LOG_FILE', log_file, prepend=False)

        # Run test with log file
        THE_MODULE.issue('bash bad_filename.bash')

        # Check result of test with log file
        if debug.debugging():
            captured = self.get_stderr()
            assert 'stderr' in captured
            assert 'bad_filename.bash' in captured
        ## TODO: for some reason the log_file is not being overriden
        ## assert 'random content' not in gh.read_file(log_file)
        ## assert 'bad_filename.bash' in gh.read_file(log_file)

    def test_get_hex_dump(self):
        """Ensure get_hex_dump works as expected"""
        debug.trace(4, "test_get_hex_dump()")
        ## TODO: mock hexview.perl output
        ## assert THE_MODULE.get_hex_dump("Tomás") == "00000000  54 6F 6D C3 A1 73       -                          Tom..s"

    def test_extract_matches(self):
        """Tests for extract_matches(pattern, lines)"""
        assert THE_MODULE.extract_matches(r"Mr. (\S+)", ["Mr. Smith", "Mr. Jones", "Mr.X"]) == ["Smith", "Jones"]
        assert THE_MODULE.extract_matches(r"\t\S+", ["abc\tdef", "123\t456"]) != ["def", "456"]

    def test_extract_match(self):
        """Ensure extract_match works as expected"""
        debug.trace(4, "test_extract_match()")
        assert THE_MODULE.extract_match(r"Mr. (\S+)", ["Mr. Smith", "Mr. Jones", "Mr.X"]) == "Smith"

    def test_basename(self):
        """Tests for basename(path, extension)"""
        assert THE_MODULE.basename("fubar.py", ".py") == "fubar"
        assert not THE_MODULE.basename("fubar.py", "") == "fubar"
        assert THE_MODULE.basename("/tmp/solr-4888.log", ".log") == "solr-4888"

    @pytest.mark.xfail
    def test_resolve_path(self):
        """Tests for resolve_path(filename)"""
        script = "glue_helpers.py"
        test_script = "test_glue_helpers.py"
        test_dir = gh.dir_path(__file__)
        debug.assertion(test_script in __file__)
        # The main script should resolve to parent directory but this one to test dir
        assert not (gh.real_path(THE_MODULE.resolve_path(script))
                    == gh.form_path(test_dir, test_script))
        assert (gh.real_path(THE_MODULE.resolve_path(test_script))
                == gh.form_path(test_dir, test_script))

    @pytest.mark.xfail
    def test_heuristic_resolve_path(self):
        """Tests for heuristic version of resolve_path(filename)"""
        requirements_filename = "requirements.txt"
        module_dir = gh.form_path(gh.dir_path(__file__), "..")
        # note: the requirements normally isn't resolved
        assert(THE_MODULE.resolve_path(requirements_filename,
                                       base_dir=module_dir, heuristic=False)
               == requirements_filename)
        assert(gh.real_path(THE_MODULE.resolve_path(requirements_filename,
                                                    base_dir=module_dir, heuristic=True))
               == gh.real_path(gh.form_path(mezcla_root_dir, requirements_filename)))

    def test_extract_match_from_text(self):
        """Ensure extract_match_from_text works as expected"""
        debug.trace(4, "test_extract_match_from_text()")
        assert THE_MODULE.extract_match_from_text(r"Mr. (\S+)", "Mr. Smith\nMr. Jones\nMr.X") == "Smith"

    def test_extract_matches_from_text(self):
        """Ensure extract_matches_from_text works as expected"""
        debug.trace(4, "test_extract_matches_from_text()")
        assert THE_MODULE.extract_matches_from_text(".", "abc") == ["a", "b", "c"]
        assert THE_MODULE.extract_matches_from_text(".", "abc", multiple=False) == ["a"]

    def test_count_it(self):
        """Ensure count_it works as expected"""
        debug.trace(4, "test_count_it()")
        assert dict(THE_MODULE.count_it("[a-z]", "Panama")) == {"a": 3, "n": 1, "m": 1}
        assert THE_MODULE.count_it(r"\w+", "My d@wg's fleas have fleas")["fleas"] == 2

    def test_read_lines(self):
        """Ensure read_lines works as expected"""
        debug.trace(4, "test_read_lines()")

        # Test valid file
        temp_file = self.get_temp_file()
        system.write_file(temp_file, 'file\nwith\nmultiple\nlines\n')
        assert THE_MODULE.read_lines(temp_file) == ['file', 'with', 'multiple', 'lines']

        # Test no filename (read from stdin)
        self.monkeypatch.setattr('sys.stdin', StringIO('my input\nsome line'))
        assert THE_MODULE.read_lines() == ['my input', 'some line']
        ##
        ## TODO: solve "ValueError: I/O operation on closed file."
        ##   THE_MODULE.read_lines()
        ##   captured = capsys.readouterr()
        ##   assert 'stdin' in captured.err

        # Test invalid filename
        assert(not THE_MODULE.read_lines(filename='bad_filename.txt'))
        if debug.debugging():
            captured = self.get_stderr()
            assert 'Warning:' in captured

    def test_write_lines(self):
        """Ensure write_lines works as expected"""
        debug.trace(4, "test_write_lines()")

        content = (
            'this is\n'
            'a multiline\n'
            'text used\n'
        )
        content_in_lines = [
            'this is',
            'a multiline',
            'text used',
        ]

        # Test normal usage
        filename = self.get_temp_file()
        THE_MODULE.write_lines(filename, content_in_lines)
        assert THE_MODULE.read_file(filename) == content

        # Test append
        THE_MODULE.write_lines(filename, ['for testing'], append=True)
        assert THE_MODULE.read_file(filename) == content + 'for testing\n'

    def test_read_file(self):
        """Ensure read_file works as expected"""
        debug.trace(4, "test_read_file()")
        temp_file = self.get_temp_file()
        system.write_file(temp_file, 'file\nwith\nmultiple\nlines\n')
        assert THE_MODULE.read_file(temp_file) == 'file\nwith\nmultiple\nlines\n'

    def test_write_file(self):
        """Ensure write_file works as expected"""
        debug.trace(4, "test_write_file()")

        # Test normal usage
        filename = self.get_temp_file()
        THE_MODULE.write_file(filename, "some test")
        assert THE_MODULE.read_file(filename) == "some test\n"

        # Test append argument
        THE_MODULE.write_file(filename, "with appended text", append=True)
        assert THE_MODULE.read_file(filename) == "some test\nwith appended text\n"

    def test_copy_file(self):
        """Ensure copy_file works as expected"""
        debug.trace(4, "test_copy_file()")
        first_temp_file = self.get_temp_file()
        second_temp_file = f"{first_temp_file}_target_copy"
        system.write_file(first_temp_file, 'some random content')
        THE_MODULE.copy_file(first_temp_file, second_temp_file)
        assert gh.read_file(second_temp_file) == 'some random content\n'

    def test_rename_file(self):
        """Ensure rename_file works as expected"""
        debug.trace(4, "test_rename_file()")
        test_filename = self.get_temp_file()
        new_test_filename = self.get_temp_file() + '_this_append_avoids_bad_file_exists'
        system.write_file(test_filename, 'some content')

        # Check existense of files before rename
        assert gh.file_exists(test_filename)
        assert not gh.file_exists(new_test_filename)

        THE_MODULE.rename_file(test_filename, new_test_filename)

        # Check integrity of renamed file
        assert gh.file_exists(new_test_filename)
        assert not gh.file_exists(test_filename)
        assert gh.read_file(new_test_filename) == 'some content\n'

    def test_delete_file(self):
        """Ensure delete_file works as expected"""
        debug.trace(4, "test_delete_file()")

        # Test valid file to delete
        test_filename = self.get_temp_file()
        system.write_file(test_filename, 'some content')
        assert gh.file_exists(test_filename)
        THE_MODULE.delete_file(test_filename)
        assert not gh.file_exists(test_filename)

        # Test invalid file
        THE_MODULE.delete_file('bad_filename.txt')
        if debug.debugging():
            captured = self.get_stderr()
            assert 'assertion failed' in captured.lower()

    def test_file_size(self):
        """Ensure file_size works as expected"""
        debug.trace(4, "test_file_size()")
        temp_file = self.get_temp_file()
        system.write_file(temp_file, 'content')
        if os.name == 'nt':
            # CRLF line-end occupies 1 byte more than LF
            assert THE_MODULE.file_size(temp_file) == 9
        elif os.name == 'posix':
            assert THE_MODULE.file_size(temp_file) == 8
        else:
            assert False, "unsupported OS"
        assert THE_MODULE.file_size('non-existent-file.txt') == -1

    @pytest.mark.xfail
    def test_get_matching_files(self):
        """Ensure get_matching_files works as expected"""
        debug.trace(4, "test_get_matching_files()")
        test_dir = THE_MODULE.dirname(__file__)
        system.set_current_directory(test_dir)
        assert THE_MODULE.basename(__file__) in THE_MODULE.get_matching_files("test_*.py")

        _ = THE_MODULE.get_matching_files(pattern="non-existent-file", warn=True)
        stderr = self.get_stderr()
        assert "Warning: no matching files for non-existent-file" in stderr

    @pytest.mark.xfail
    def test_get_files_matching_specs(self):
        """Ensure get_files_matching_specs works as expected"""
        debug.trace(4, "test_get_files_matching_specs()")
        test_dir = THE_MODULE.dirname(__file__)
        system.set_current_directory(test_dir)
        matches = THE_MODULE.get_files_matching_specs(
            [f"{test_dir}/test_*.py", "resources", "*.batspp"])
        assert THE_MODULE.basename(__file__)
        assert "regression.batspp" in matches
        assert "resources" in matches


    @pytest.mark.xfail
    def test_get_directory_listing(self):
        """Ensure get_directory_listing works as expected"""
        debug.trace(4, "test_get_directory_listing()")
        test_temp_dir = self.get_temp_dir(static=True)
        full_filenames = []
        for i in range(5):
            full_filenames.append(gh.form_path(test_temp_dir, f"f{i}.list"))
            system.write_file(full_filenames[-1], f"content for temp. file {i}")
        filenames = [f.replace(f"{test_temp_dir}{os.sep}", "") for f in full_filenames]
        assert set(filenames).issubset(THE_MODULE.get_directory_listing(test_temp_dir))

    def test_getenv_filename(self):
        """Ensure getenv_filename works as expected"""
        debug.trace(4, "test_getenv_filename()")

        # Test valid filename with valid content
        test_filename = self.get_temp_file()
        system.write_file(test_filename, 'random content')
        self.monkeypatch.setenv('TEST_ENV_FILENAME', test_filename, prepend=False)
        assert THE_MODULE.getenv_filename('TEST_ENV_FILENAME') == test_filename

        # Test valid filename with empty content
        test_filename = self.get_temp_file()
        with open(test_filename, 'wb') as _:
            pass # system.write_file cant be used because appends a newline
        debug.set_level(7)
        self.monkeypatch.setenv('TEST_ENV_FILENAME', test_filename, prepend=False)
        # This avoids flaky tpo.stderr due to other tests
        ## TODO: fix tpo.restore_stderr() to work with pytest
        tpo.stderr = sys.stderr
        THE_MODULE.getenv_filename('TEST_ENV_FILENAME')
        captured = self.get_stderr() # Note: capfd must be used instead of capsys to capture stderr
        assert 'Error' in captured
        assert test_filename in captured

        # Test non enviroment var
        assert THE_MODULE.getenv_filename('BAD_ENV_FILE_VAR', default='missing-file') == 'missing-file'

    @pytest.mark.xfail
    def test_non_empty_directory(self):
        """Make sure non_empty_directory works for empty and non-empty dir"""
        ## TODO3: use monkeypatvh to ensure TEMP_FILE not set
        debug.assertion(not THE_MODULE.TEMP_FILE)
        temp_dir = self.get_temp_dir()
        assert not THE_MODULE.non_empty_directory(temp_dir)
        system.write_file(gh.form_path(temp_dir, "temp_file.list"), "dummy text")
        assert THE_MODULE.non_empty_directory(temp_dir)

    @pytest.mark.xfail
    def test_copy_directory(self):
        """Ensure copy_directory works as expected"""
        debug.trace(4, "test_copy_directory()")
        ## OLD:
        ## temp_dir = '/tmp/test_copy_dir_'
        ## system.create_directory(f'{temp_dir}1')
        temp_dir_1 = self.get_temp_dir()
        temp_dir_2 = self.get_temp_dir(skip_create=True)
        assert temp_dir_1 != temp_dir_2
        ## BAD: system.write_file(f'{temp_dir}1/test_file', "copy")
        copy_file_name = "copy_file.list"
        copy_contents = "copy contents"
        system.write_file(gh.form_path(temp_dir_1, copy_file_name),
                          copy_contents)
        assert copy_file_name in system.read_directory(temp_dir_1)
        THE_MODULE.copy_directory(temp_dir_1, temp_dir_2)
        assert copy_file_name in system.read_directory(temp_dir_2)
        ## BAD: assert 'copy' in system.read_file(f'{temp_dir}2/test_file')
        assert copy_contents in system.read_file(
            gh.form_path(temp_dir_2, copy_file_name))

    @pytest.mark.xfail
    def test_delete_directory(self):
        """Ensure delete_directory works as expected"""
        debug.trace(4, "test_delete_directory()")
        ## TODO3: use monkeypatch
        old = THE_MODULE.DISABLE_RECURSIVE_DELETE
        test_temp_dir = self.get_temp_dir(static=True)

        # test an empty directory gets deleted
        ## OLD: empty_dir = '/tmp/test_delete_directory-1/'
        empty_dir = gh.form_path(test_temp_dir, "test_delete_directory-1")
        system.create_directory(empty_dir)
        assert THE_MODULE.is_directory(empty_dir)
        assert THE_MODULE.delete_directory(empty_dir) is None

        # test a directory with files gets deleted
        ## OLD: non_empty_dir = '/tmp/test_delete_directory-2'
        non_empty_dir = gh.form_path(test_temp_dir, "test_delete_directory-2")
        system.create_directory(non_empty_dir)
        system.write_file(gh.form_path(non_empty_dir, "test_delete_directory.list"), '2')
        assert THE_MODULE.is_directory(non_empty_dir)
        assert THE_MODULE.delete_directory(non_empty_dir) is None

        # test a directory with subdirs doesnt get deleted if DISABLE_RECURSIVE_DELETE
        THE_MODULE.DISABLE_RECURSIVE_DELETE = True
        ## OLD: dir_with_subdirs = '/tmp/test_delete_directory-3'
        dir_with_subdirs = gh.form_path(test_temp_dir, "test_delete_directory-3")
        subdir = gh.form_path(dir_with_subdirs, "subdir")
        system.create_directory(dir_with_subdirs)
        system.create_directory(subdir)
        system.write_file(gh.form_path(subdir, "subdir_file.list"), '3')
        assert THE_MODULE.is_directory(subdir)
        assert not THE_MODULE.delete_directory(dir_with_subdirs)

        # test a directory with subdirs gets deleted if not DISABLE_RECURSIVE_DELETE
        assert THE_MODULE.is_directory(subdir)
        system.write_file(gh.form_path(subdir, "subdir_file.list"), '4')
        THE_MODULE.DISABLE_RECURSIVE_DELETE = False
        assert THE_MODULE.delete_directory(dir_with_subdirs) is None

        THE_MODULE.DISABLE_RECURSIVE_DELETE = old

    @pytest.mark.xfail
    def test_get_temp_file_deletion(self):
        """Make sure temp file returned properly when TEMP_FILE not set
        Note: accounts for odd NamedTemporaryFile behavior with delete
        """
        self.monkeypatch.setattr(gh, 'TEMP_FILE', None)
        #
        self.monkeypatch.setattr(gh, 'KEEP_TEMP', True)
        temp_file_without_delete = THE_MODULE.get_temp_file(delete=False)
        assert system.file_exists(temp_file_without_delete)
        #
        self.monkeypatch.setattr(gh, 'KEEP_TEMP', False)
        temp_file_with_delete = THE_MODULE.get_temp_file(delete=True)
        assert system.file_exists(temp_file_with_delete)
 
    @pytest.mark.xfail
    def test_zend_initialization(self):
        """Make sure module initialized OK
        Warning: This test involves subtle maniulation of the temp file environment
        settings and related globals. It can be tedious to debug, in which case
        it can help to run with a high tracing level (e.g., 6); check the log for 
        changes to TEMP_FILE-related settings.
        """
        # note: "zend" used so test runs last (in case module state messed up)
        # TODO1: add checks for TEMP_BASE and TEMP_FILE, along with PRESERVE_TEMP_FILE
        # TODO3: add checks for TEMP_LOG_FILE and TEMP_SCRIPT_FILE
        test_temp_dir = self.get_temp_dir(static=True)

        # attrs that won't be changed
        PID = 1
        self.monkeypatch.setattr('mezcla.glue_helpers.PID', PID)
        PID_basename = f"temp-{PID}"
        self.monkeypatch.setattr('mezcla.glue_helpers.PID_BASENAME', PID_basename)

        # Case of USE_TEMP_BASE_DIR False but TEMP_BASE
        self.monkeypatch.setattr('mezcla.glue_helpers.USE_TEMP_BASE_DIR', False)
        self.monkeypatch.setenv("PRESERVE_TEMP_FILE", "0")
        ## OLD: self.monkeypatch.setattr('mezcla.glue_helpers.PRESERVE_TEMP_FILE', False)
        # delete TEMP_FILE to check use of temp_file_default
        self.monkeypatch.delenv('TEMP_FILE', raising=False)
        self.monkeypatch.setattr(
            'mezcla.glue_helpers.TEMP_BASE', gh.form_path(test_temp_dir, "temp_file"))
        THE_MODULE.init()
        assert not system.is_directory(THE_MODULE.TEMP_BASE)
        assert THE_MODULE.TEMP_FILE == f"{THE_MODULE.TEMP_BASE}-{PID_basename}"

        # Case of USE_TEMP_BASE_DIR True
        self.monkeypatch.setattr('mezcla.glue_helpers.USE_TEMP_BASE_DIR', True)
        self.monkeypatch.setenv("PRESERVE_TEMP_FILE", "0")
        self.monkeypatch.delenv("TEMP_FILE", raising=False)
        # note: subdirectory created to ensure proper interpretation
        temp_base = gh.form_path(test_temp_dir, "temp_dir")
        gh.full_mkdir(temp_base)
        self.monkeypatch.setattr(
            'mezcla.glue_helpers.TEMP_BASE', temp_base)
        ## OLD: self.monkeypatch.setattr('mezcla.glue_helpers.USE_TEMP_BASE_DIR', True)
        ## OLD: self.monkeypatch.setattr('mezcla.glue_helpers.TEMP_FILE', None)
        self.monkeypatch.delenv('TEMP_LOG_FILE', raising=False)
        self.monkeypatch.delenv('TEMP_SCRIPT_FILE', raising=False)
        THE_MODULE.init()
        ## OLD: atexit.register(THE_MODULE.delete_directory, THE_MODULE.TEMP_BASE) # cleanup
        assert system.is_directory(THE_MODULE.TEMP_BASE)
        ## OLD: assert THE_MODULE.TEMP_FILE == system.form_path(THE_MODULE.TEMP_BASE, f"{PID_basename}.list")
        assert THE_MODULE.TEMP_FILE == gh.form_path(THE_MODULE.TEMP_BASE, PID_basename)
        assert THE_MODULE.TEMP_LOG_FILE.split('-')[0] == THE_MODULE.TEMP_SCRIPT_FILE.split('-')[0]


if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
