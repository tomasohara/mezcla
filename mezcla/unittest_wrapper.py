#! /usr/bin/env python3
#
# Wrapper class around unittest.TestCase
#
# Notes:
# - Based on template.py used in older test scripts
# - Creates per-test temp file, based on same class-wide temp-base file.
# - To treat temp-base as a subdirectory, set use_temp_base_dir to True in 
#   class member initialiation section.
# - Changes to temporary directory/file should be synchronized with ../main.py.
# - Overriding the temporary directory can be handy during debugging; however,
#   you might need to specify different ones if you invoke helper scripts. See
#   tests/test_extract_company_info.py for an example.
# - It can be confusing debugging tests that use run_script, because the trace level
#   is raised by default. To disable this, set the SUB_DEBUG_LEVEL as follows:
#      l=5; DEBUG_LEVEL=$l SUB_DEBUG_LEVEL=$l pytest -s tests/test_spell.py
#   See glue_helper.py for implementation along with related ALLOW_SUBCOMMAND_TRACING.
# TODO:
# - * Clarify TEMP_BASE vs. TEMP_FILE usage.
#   via glue_helpers.py: default base prefix vs fixed override
# - Add TEMP_DIR for more direct specification.
# - Clarify that this can co-exist with pytest-based tests (see tests/test_main.py).
# TODO2:
# - Clean up script_file usage (and unncessary settings in test scripts).
#
#-------------------------------------------------------------------------------
# Sample test (streamlined version of test_simple_main_example.py):
#
#   import unittest
#   from mezcla import system
#   from mezcla.unittest_wrapper import TestWrapper, invoke_tests
#
#   class TestIt(TestWrapper):
#       """Class for testcase definition"""
#       script_module = TestWrapper.derive_tested_module_name(__file__)
#  
#       def test_simple_data(self):
#           """Make sure simple data sample processed OK"""
#           system.write_file(self.temp_file, "really fubar")
#           output = self.run_script("--check-fubar", self.temp_file)
#           self.assertTrue("really" in output)
#
#   if __name__ == '__main__':
#      invoke_tests(__file__)
#-------------------------------------------------------------------------------
# TODO:
# - Add method to invoke unittest.main(), so clients don't need to import unittest.
#

"""Unit test support class"""

# Standard packages
import inspect
import os
import sys
import tempfile
import unittest
from typing import (
    Optional, Callable, Any, Tuple,
)
## DEBUG: sys.stderr.write(f"{__file__=}\n")

# Installed packages
import pytest

# Local packages
# note: Disables TEMP_FILE default used by glue_helpers.py.
PRESERVE_TEMP_FILE_LABEL = "PRESERVE_TEMP_FILE"
if PRESERVE_TEMP_FILE_LABEL not in os.environ:
    ## DEBUG: sys.stderr.write(f"Setting {PRESERVE_TEMP_FILE_LABEL}\n")
    os.environ[PRESERVE_TEMP_FILE_LABEL] = "1"
import mezcla
from mezcla import debug
from mezcla import glue_helpers as gh
## BAD: from mezcla.main import DISABLE_RECURSIVE_DELETE
DISABLE_RECURSIVE_DELETE = gh.DISABLE_RECURSIVE_DELETE
from mezcla.misc_utils import string_diff
from mezcla.my_regex import my_re
from mezcla import system
## DEBUG: debug.trace_expr(6, __file__)
from mezcla.debug import IntOrTraceLevel

# Constants (e.g., environment options)

TL = debug.TL
KEEP_TEMP = gh.KEEP_TEMP
PRUNE_TEMP = system.getenv_bool(
    "PRUNE_TEMP", False,
    desc="Delete temporary files ahead of time")
TODO_FILE = "TODO FILE"
TODO_MODULE = "TODO MODULE"
TEMP_BASE = gh.TEMP_BASE

# Note: the following is for transparent resolution of dotted module names
# for invocation of scripts via 'python -m package.module'. This is in support
# of transitioning from the old way of importing packages via 'import module'
# instead of 'import package.module'. (The former required that package be
# explicitly specified in the python path, such as via 'PYTHONPATH=package-dir:...'.)
THIS_PACKAGE = getattr(mezcla.debug, "__package__", None)
debug.assertion(THIS_PACKAGE == "mezcla")

# Environment options
VIA_UNITTEST = system.getenv_bool(
    "VIA_UNITTEST", False,
    description="Run tests via unittest instead of pytest")
PROFILE_CODE = system.getenv_boolean(
    "PROFILE_CODE", False,
    description="Profile each test invocation")
#
# For use in tests
RUN_SLOW_TESTS = system.getenv_bool(
    "RUN_SLOW_TESTS", False,
    description="Run tests that can a while to run")
debug.reference_var(RUN_SLOW_TESTS)

UNDER_COVERAGE = system.getenv_bool(
    "COVERAGE_RUN", False,
    description="whether or not tests are being run under coverage"
)


# Dynamic imports
if PROFILE_CODE:
    import cProfile
    import pstats

#-------------------------------------------------------------------------------

def get_temp_dir(keep: Optional[bool] = None, unique=None) -> str:
    """Get temporary directory, omitting later deletion if KEEP
    Note: Optionally returns UNIQUE dir
    """
    # TODO2: rework keep using atexit-style callback
    debug.assertion(not ((keep is False) and (unique is False)))
    if keep is None:
        keep = KEEP_TEMP
    dir_base = gh.get_temp_file()
    if unique:
        # Note: creates parent temp dir if temp file regular file
        if not system.is_directory(dir_base):
            dir_base += "_temp_dir_"
            gh.full_mkdir(dir_base)
        dir_path = tempfile.NamedTemporaryFile(
            delete=(not keep), dir=dir_base).name
    else:
        dir_path = dir_base
    if not system.is_directory(dir_path):
        gh.full_mkdir(dir_path, force=True)
    debug.trace(5, f"unittest_wrapper.get_temp_dir() => {dir_path}")
    return dir_path


def trap_exception(function: Callable) -> Any:
    """Decorator to trap exception during function execution
    Note:
    - Only intended for use in tests (e.g., fix for maldito pytest).
    - Issues assertion so that test fails.
    - Should be inside any pytest.mark.xfail decorators.
    """
    debug.trace(8, f"trap_exception({gh.elide(function)}")
    #
    def wrapper(*args):
        """Wrapper around variable arity function f"""   ## TODO: {function.__name__}
        debug.trace(7, f"in wrapper: args={args}")
        result = None
        try:
            result = function(*args)
        except AssertionError:
            raise
        except:
            system.print_exception_info(function.__name__)
            assert(False)
        return result
    #
    debug.trace(7, f"trap_exception() => {gh.elide(wrapper)}")
    return wrapper


def pytest_fixture_wrapper(function: Callable) -> Callable:
    """Decorator for use with pytest fixtures like capsys
    Usage:
        @pytest_fixture_wrapper
        @trap_exception
        def test_it(capsys):
            ...
    """
    # See https://stackoverflow.com/questions/19614658/how-do-i-make-pytest-fixtures-work-with-decorated-functions
    # Note: This is currently usused. It was previously used with trap_exception.
    debug.trace(8, f"pytest_fixture_wrapper({gh.elide(function)}")
    #
    def wrapper(x):
        """Wrapper around unary function f(x)"""   ## TODO: {function.__name__}
        debug.trace(7, f"in wrapper: x={x}")
        return function(x)
    #
    debug.trace(7, f"pytest_fixture_wrapper() => {gh.elide(wrapper)}")
    return wrapper


def invoke_tests(filename: str, via_unittest: bool = VIA_UNITTEST):
    """Invoke TESTS defined in FILENAME, optionally VIA_UNITTEST"""
    debug.trace(5, f"invoke_tests({filename}, [{via_unittest}])")
    try:
        if via_unittest:
            unittest.main(argv=sys.argv[:1])
        else:
            pytest.main([filename])
    except:
        debug.raise_exception(6)
        system.print_exception_info("invoke_tests")


def init_temp_settings():
    """Initialize settings related to temp-file names"""
    ok = True
    # Re-initalize glue helper temp file settings
    ## TODO?: system.setenv("PRESERVE_TEMP_FILE", "1")
    debug.trace_expr(4, os.environ.get(PRESERVE_TEMP_FILE_LABEL))
    ## TEST: os.environ["PRESERVE_TEMP_FILE"] = "1"
    if not system.getenv(PRESERVE_TEMP_FILE_LABEL):
        system.setenv(PRESERVE_TEMP_FILE_LABEL, "1")
    gh.init()
    debug.trace_expr(4, os.environ.get(PRESERVE_TEMP_FILE_LABEL))
    return ok
        
#-------------------------------------------------------------------------------

class TestWrapper(unittest.TestCase):
    """Class for testcase definition
    Note:
    - script_module should be overriden to specify the module instance, such as via get_testing_module_name (see test/template.py)
    - set it to None to avoid command-line invocation checks
    """
    init_ok = init_temp_settings()

    script_file = TODO_FILE             # path for invocation via 'python -m coverage run ...' (n.b., usually set via get_module_file_path)
    script_module = TODO_MODULE         # name for invocation via 'python -m' (n.b., usually set via derive_tested_module_name)
    temp_base = TEMP_BASE
    check_coverage = system.getenv_bool(
        "CHECK_COVERAGE", False,
        desc="Check coverage during unit testing")
    ## TODO: temp_file = None
    ## TEMP: initialize to unique value independent of temp_base
    temp_file = None
    use_temp_base_dir = (system.is_directory(temp_base) if temp_base else False)
    ## OLD: test_num = 1
    test_num = 0
    temp_file_count = 0
    class_setup = False
    profiler = None
    monkeypatch = None
    capsys = None

    ## TEST:
    ## NOTE: leads to pytest warning. See
    ##   https://stackoverflow.com/questions/62460557/cannot-collect-test-class-testmain-because-it-has-a-init-constructor-from
    ## def __init__(self, *args, **kwargs):
    ##     debug.trace_fmtd(6, "TestWrapper.__init__({a}): keywords={kw}; self={s}",
    ##                      a=",".join(args), kw=kwargs, s=self)
    ##     super().__init__(*args, **kwargs)
    ##     debug.trace_object(7, self, label="TestWrapper instance")
    ##
    ## __test__ = False                 # make sure not assumed test
        
    @classmethod
    def setUpClass(cls, filename=None, module=None):
        """Per-class initialization: make sure script_module set properly
        Note: Optional FILENAME is path for testing script and MODULE the imported object for tested script
        """
        debug.trace(5, f"TestWrapper.setUpClass({cls}, fn={filename}, mod={module})")
        super().setUpClass()
        cls.class_setup = True
        debug.trace_object(7, cls, "init TestWrapper class")
        debug.assertion(cls.script_module != TODO_MODULE)
        if (cls.script_module is not None):
            # Try to pull up usage via python -m mezcla.xyz --help
            help_usage = gh.run("python -m '{mod}' --help", mod=cls.script_module)
            debug.assertion("No module named" not in help_usage,
                            f"problem running via 'python -m {cls.script_module}'")
            # Warn about lack of usage statement unless "not intended for command-line" type warning issued
            # TODO: standardize the not-intended wording
            if (not ((my_re.search(r"(warning|FYI):.*not intended", help_usage,
                                   flags=my_re.IGNORECASE))
                     or ("usage:" in help_usage.lower()))):
                system.print_stderr("Warning: script should implement --help")

        # Optionally, setup temp-base directory (normally just a file)
        debug.assertion(cls.init_ok)
        if cls.use_temp_base_dir is None:
            cls.use_temp_base_dir = gh.USE_TEMP_BASE_DIR
        if not cls.temp_base:
            cls.temp_base = cls.temp_file
        if not cls.temp_base:
            cls.temp_base = gh.get_temp_file()
        if cls.use_temp_base_dir:
            gh.full_mkdir(cls.temp_base, force=True)

        # Warn that coverage support is limited
        if cls.check_coverage:
            # note: For proper invocation info, see https://coverage.readthedocs.io/en/latest
            test_module = "pytest ..." if not VIA_UNITTEST else "unittest discover"
            debug.trace(4, "FYI: coverage check only covers run_script usages; "
                        "invoke externally for more general support:\n"
                        f"    python -m coverage run -m {test_module}")

        # Enable code profiling if desired
        if PROFILE_CODE:
            cls.profiler = cProfile.Profile()
            
        # Optionally, setup up script_file and script_module
        if filename:
            cls.set_module_info(filename, module_object=module)
        debug.trace_object(6, cls, "finalized TestWrapper class")

        return

    @staticmethod
    def derive_tested_module_name(test_filename: str) -> str:
        """Derive the name of the module being tested from TEST_FILENAME. Used as follows:
              script_module = TestWrapper.derive_tested_module_name(__file__)
        Note: *** Deprecated method *** (see get_testing_module_name)
        """
        debug.trace(3, "Warning: in deprecrated derive_tested_module_name")
        debug.trace(5, f"TestWrapper.derive_tested_module_name({test_filename})")
        module = os.path.split(test_filename)[-1]
        module = my_re.sub(r".py[oc]?$", "", module)
        module = my_re.sub(r"^test_", "", module)
        debug.trace_fmtd(5, "derive_tested_module_name({f}) => {m}",
                         f=test_filename, m=module)
        return (module)

    @staticmethod
    def get_testing_module_name(test_filename: str, module_object: Optional[object] = None) -> str:
        """Derive the name of the module being tested from TEST_FILENAME and MODULE_OBJECT
        Note: used as follows (see tests/template.py):
            script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
        """
        debug.trace(6, f"TestWrapper.get_testing_module_name({test_filename}, {module_object})")
        # Note: Used to resolve module name given THE_MODULE (see template).
        module_name = os.path.split(test_filename)[-1]
        module_name = my_re.sub(r".py[oc]?$", "", module_name)
        module_name = my_re.sub(r"^test_", "", module_name)
        package_name = THIS_PACKAGE
        if module_object is not None:
           package_name = getattr(module_object, "__package__", "")
           debug.trace_expr(4, package_name)
        if package_name:
            full_module_name = package_name + "." + module_name
        else:
            full_module_name = module_name
        debug.trace_fmtd(4, "get_testing_module_name({f}, [{mo}]) => {m}",
                         f=test_filename, m=full_module_name, mo=module_object)
        return (full_module_name)

    @staticmethod
    def get_module_file_path(test_filename: str) -> str:
        """Return absolute path of module being tested"""
        result = system.absolute_path(test_filename)
        ## TODO3: use os.path.delim instead of /
        result = my_re.sub(r'tests\/test_(.*\.py)', r'\1', result)
        debug.assertion(result.endswith(".py"))
        debug.trace(6, f'get_module_file_path({test_filename}) => {result}')
        return result

    @classmethod
    def set_module_info(cls, test_filename: str, module_object: Optional[object] = None) -> None:
        """Sets both script_module and script_path
        Note: normally invoked in setUpClass method
        Usage: cls.set_module_info(__file__, THE_MODULE)
        """
        debug.trace(7, f'set_module_info({test_filename}, {module_object})')
        cls.script_module = cls.get_testing_module_name(test_filename, module_object)
        cls.script_file = cls.get_module_file_path(test_filename)
        return 
    
    def ensure_file_dir_exists(self, filename):
        """Make sure that directory for FILENAME exists"""
        debug.trace(5, f"TestWrapper.ensure_file_dir_exists({filename})")
        dir_path = gh.dirname(filename)
        if not system.is_directory(dir_path):
            debug.trace(4, f"FYI: Creating output directory {dir_path!r}\n\t{self.temp_file=}")
            gh.full_mkdir(dir_path)

    def setUp(self) -> None:
        """Per-test initializations
        Notes:
        - Disables tracing scripts invoked via run() unless ALLOW_SUBCOMMAND_TRACING
        - Initializes temp file name (With override from environment)."""
        # Note: By default, each test gets its own temp file.
        debug.trace(5, "TestWrapper.setUp()")
        if not self.class_setup:
            debug.trace(3, "Warning: invoking setUpClass in setUp; make sure seUpClass calls parent")
            TestWrapper.setUpClass(self.__class__)
        if not gh.ALLOW_SUBCOMMAND_TRACING:
            gh.disable_subcommand_tracing()
        # The temp file is an extension of temp-base file by default.
        # Optionally, if can be a file in temp-base subdrectory.
        if self.use_temp_base_dir:
            default_temp_file = gh.form_path(self.temp_base, "test-")
        else:
            default_temp_file = self.temp_base + "-test-"
        temp_file_basename = default_temp_file
        TestWrapper.test_num += 1
        default_temp_file += str(TestWrapper.test_num)
        debug.trace_expr(5, default_temp_file)

        # Get new temp file and delete existing file and variants based on temp_file_count,
        # such as /tmp/test-2, /tmp/test-2-1, and /tmp/test-2-2 (but not /tmp/test-[13]*).
        # Warning: using TEMP_FILE is not recommended due to clobbering by different tests
        self.temp_file = (gh.TEMP_FILE or default_temp_file)
        if PRUNE_TEMP:
            gh.delete_existing_file(f"{self.temp_file}")
            for f in gh.get_matching_files(f"{temp_file_basename}-[0-9]*"):
                gh.delete_existing_file(f)

        # Start the profiler
        if PROFILE_CODE:
            assert self.profiler is not None
            self.profiler.enable()
        
        debug.trace_object(6, self, "TestWrapper instance")
        return

    def run_script(
            self,
            options: Optional[str] = None,
            data_file: Optional[str] = None,
            log_file: Optional[str] = None,
            trace_level: IntOrTraceLevel = 4,
            out_file: Optional[str] = None,
            env_options: Optional[str] = None,
            uses_stdin: Optional[bool] = None,
            post_options: Optional[str] = None,
            background: Optional[str] = None,
            skip_stdin: Optional[bool] = None
        ) -> str:
        """Runs the script over the DATA_FILE (optional), passing (positional)
        OPTIONS and optional setting ENV_OPTIONS. If OUT_FILE and LOG_FILE are
        not specified, they  are derived from self.temp_file. The optional POST_OPTIONS
        go after the data file.
        Notes:
        - OPTIONS uses quotes around shell special characters used (e.g., '<', '>', '|')
        - issues warning if script invocation leads to error
        - if USES_STDIN, requires explicit empty string for DATA_FILE to avoid use of - (n.b., as a precaution against hangups)
        - if SKIP_STDIN, then - omitted from command line
        - By default, stderr is not included in the output
        """
        debug.trace_fmtd(trace_level + 1,
                         "TestWrapper.run_script(opts={opts!r}, data={df}, log={lf}, lvl={lvl}, out={of}, env={env}, stdin={stdin}, post={post}, back={back})",
                         opts=options, df=data_file, lf=log_file, lvl=trace_level, of=out_file,
                         env=env_options, stdin=uses_stdin, post=post_options, back=background)
        if options is None:
            options = ""
        if env_options is not None:
            suffix = ' '
            preffix = ' '
            if os.name == 'nt':
                suffix = '&& '
                preffix = 'SET '
            list_options = [ f"{preffix}{option}{suffix}" for option in env_options.split(' ')]
            env_options = " ".join(list_options)
        else:
            env_options = ""
        if post_options is None:
            post_options = ""
        if skip_stdin is None:
            skip_stdin = False

        # Derive the full paths for data file and log, and then invoke script.
        # TODO: derive from temp base and data file name?;
        # TODO1: derive default for uses_stdin based on use of filename argment (e.g., from usage)
        uses_stdin_false = ((uses_stdin is not None) and not bool(uses_stdin))
        data_path = ("" if (skip_stdin or uses_stdin_false) else "-")
        if data_file is not None:
            data_path = (gh.resolve_path(data_file) if len(data_file) else data_file)
        assert isinstance(self.temp_file, str)
        if not log_file:
            log_file = self.temp_file + ".log"
        if not out_file:
            out_file = self.temp_file + ".out"
        # note: output is redirected to a file to preserve tabs

        # Make sure output and log files are in valid dirs
        self.ensure_file_dir_exists(out_file)
        self.ensure_file_dir_exists(log_file)

        # Set converage script path and command spec
        coverage_spec = ''
        script_module = self.script_module
        if self.check_coverage:
            debug.assertion(self.script_file)
            script_module = self.script_file
            coverage_spec = 'coverage run'
        debug.assertion(not script_module.endswith(".py"))
        amp_spec = "&" if background else ""

        # Run the command
        ## TODO3: allow for stdin_command (e.g., "echo hey" | ...)
        ## TODO2: add sanity check for special shell characters
        ##   shell_tokens = ['<', '>', '|']
        ##   debug.assertion(not system.intersection(options.split(), shell_tokens))
        gh.issue("{env} python -m {cov_spec} {module}  {opts}  {path}  {post} 1> {out} 2> {log} {amp_spec}",
                 env=env_options, cov_spec=coverage_spec, module=script_module,
                 opts=options, path=data_path, out=out_file, log=log_file, post=post_options, amp_spec=amp_spec)
        output = system.read_file(out_file)
        # note: trailing newline removed as with shell output
        if output.endswith("\n"):
            output = output[:-1]
        debug.trace_fmtd(trace_level, "output: {{\n{out}\n}}",
                         out=gh.indent_lines(output), max_len=4096)

        # Make sure no python or bash errors. For example,
        #   "SyntaxError: invalid syntax" and "bash: python: command not found"
        log_contents = system.read_file(log_file)
        error_found = my_re.search(r"(\S+error:)|(no module)|(command not found)",
                                   log_contents.lower())
        debug.assertion(not error_found)
        debug.trace_expr(trace_level + 1, log_contents, max_len=4096)

        # Do sanity check for python exceptions
        traceback_found = my_re.search("Traceback.*most recent call", log_contents)
        debug.assertion(not traceback_found)

        return output

    def resolve_assertion(
            self,
            function_label: str,
            message: Optional[str]
        ) -> Tuple[
            Optional[str],
            Optional[str],
            Optional[int],
            Optional[str],
            Optional[str]
        ]:
        """Returns statement text, filename, line number, and qualifier for FUNCTION_LABEL assertion failure"""
        ## TODO2: use new introspection module
        statement = filename = line_num = expr = qual = None
        try:
            # note: accounts for trap_exception and other decorators
            for caller in inspect.stack():
                debug.trace_expr(8, caller)
                ## DEBUG: print(f"{caller=}")
                (_frame, filename, line_num, _function, context, _index) = caller
                statement = debug.read_line(filename, line_num).strip()
                ## DEBUG: print(f"{statement=}")
                if f".{function_label}(" in statement:
                    break
            # TODO3: use abstract syntax tree (AST) based extraction
            # ex: self.do_assert(not my_re.search(r"cat|dog", description))  # no pets
            # Isolate condition
            cond = my_re.sub(fr"^\s*\S+\.{function_label}\((.*)\)", r"\1", statement)
            # Get expression proper, removing optional comments and semicolon 
            expr = my_re.sub(r";?\s*#.*$", "", cond)
            # Strip optional message
            qual = ""
            if message is not None:
                expr = my_re.sub(r", *([\'\"]).*\1\s*$", "", expr)   # string arg
                expr = my_re.sub(r", *[a-z0-9_]+$", "", expr,        # variable arg
                                 flags=my_re.IGNORECASE)
                qual = f": {message}"
            debug.trace_expr(7, filename, line_num, context, prefix="resolve_assertion: ")
        except:
            system.print_exception_info("resolve_assertion")
        debug.assertion(statement)
        result = (statement, filename, line_num, expr, qual)
        debug.trace(7, f"resolve_assertion({function_label}) => {result}")
        return result
    
    def do_assert(
            self,
            condition: bool,
            message: Optional[str] = None
        ) -> None:
        """Shows context for assertion failure with CONDITION and then issue assert
        If MESSAGE specified, included in assertion error
        Note:
        - Works around for maldito pytest, which makes it hard to do simple things like pinpointing errors.
        - Formatted similar to debug.assertion:
             Test assertion failed: <expr> (at <f><n>): <msg>
        """
        debug.trace(7, f"do_assert({condition}, msg={message})")
        if ((not condition) and debug.debugging(debug.TL.DEFAULT)):
            (statement, filename, line_num, expr, qual) = self.resolve_assertion("do_assert", message)
            if statement:
                # Format assertion error with optional qualification (i.e., user message)
                debug.trace(1, f"Test assertion failed: {expr} (at {filename}:{line_num}){qual}")
                debug.trace(5, f"\t{statement}")
            else:
                system.print_error("Warning: unexpected condition in do_assert")
        assert condition, message
    #
    ## TODO:
    ## assert = do_assert
    ##
    ## TEST:
    ## def assert(self, *args, **kwargs):
    ##     """Wrapper around do_assert (q.v.)"""
    ##     self.do_assert(*args, **kwargs)

    def do_assert_equals(
            self,
            value1: Any,
            value2: Any,
            message: Optional[str] = None
        ) -> None:
        """Make sure VALUE1 equals VALUE2, using optional MESSAGE"""
        equals = value1 == value2
        if ((not equals) and debug.debugging(debug.TL.DEFAULT)):
            (statement, filename, line_num, expr, qual) = self.resolve_assertion("do_assert_equals", message)
            if statement:
                # Format assertion error with optional qualification (i.e., user message)
                debug.trace(1, f"Test equality assertion failed: {expr} (at {filename}:{line_num}){qual}")
                debug.trace(5, f"\t{statement}")
                debug.trace(2, "diff:\n" + string_diff(value1, value2))
            else:
                system.print_error("Warning: unexpected condition in do_assert_equals")
        assert equals, message
    
    @pytest.fixture(autouse=True, name='monkeypatch')
    def monkeypatch_fixture(self, monkeypatch) -> None:
        """Support for using pytest monkeypatch to modify objects (e.g., dictionaries or environment variables)"""
        # See https://docs.pytest.org/en/latest/how-to/monkeypatch.html
        self.monkeypatch = monkeypatch

    @pytest.fixture(autouse=True, name='capsys')
    def capsys_fixture(self, capsys) -> None:
        """Support for capturing stdout and stderr"""
        # See https://docs.pytest.org/en/latest/how-to/capture-stdout-stderr.html
        self.capsys = capsys

    def get_stdout_stderr(self) -> Tuple[str, str]:
        """Get currently captured standard output and error
        Note: Clears both stdout and stderr captured afterwards. This might
        be needed beforehand to clear capsys buffer.

        Warning: The capsys clearing workaround is not foolproof, so you
        might need to disable capsys beforehand (e.g., in setUp): see
        tests/template.py. Alternatively, use multiple test functions:
            https://stackoverflow.com/questions/56187165/how-to-clear-captured-stdout-stderr-in-between-of-multiple-assert-statements
        """
        stdout, stderr = ("", "")
        try:
            with self.capsys.disabled():
                stdout, stderr = self.capsys.readouterr()
                ## TODO4: resolve issue with resolve_assertion call-stack tracing being clippped
                debug.trace_expr(5, stdout, stderr, prefix="get_stdout_stderr:\n", delim="\n", max_len=16384)
        except:
            # note: trace level high so as not to affect normal testing
            debug.trace_exception(7, "get_stdout_stderr")
        return stdout, stderr
        
    def get_stdout(self) -> str:
        """Get currently captured standard output (see get_stdout_stderr)
        Warning: You might need to invoke beforehand to clear buffer.
        """
        stdout, _stderr = self.get_stdout_stderr()
        return stdout
        
    def get_stderr(self) -> str:
        """Get currently captured standard error (see get_stdout_stderr)
        Warning: You might need to invoke beforehand to clear buffer.
        """
        _stdout, stderr = self.get_stdout_stderr()
        return stderr

    def clear_stdout_stderr(self) -> None:
        """Clears stdout and stderr by issuing dummy call.
        Warning: See disclaimer under get_stdout_stderr.
        """
        _result = self.get_stdout_stderr()
        return
    #
    clear_stdout = clear_stdout_stderr
    clear_stderr = clear_stdout_stderr
    
    def get_temp_file(self, delete: Optional[bool] = None, static: Optional[bool] = None) -> str:
        """Return name of temporary file based on self.temp_file, optionally with DELETE.
        Normally, the file is based on the test base, current test number and usage count
        (e.g., /tmp/_temp-fi7huvmb_-test-1-3 for third temp file used in first test).
        Note:
        - This returns a new file each time called unless STATIC specified.
        - The delete option is not yet functional.
        """
        # Note: delete defaults to False if detailed debugging
        # TODO: allow for overriding other options to NamedTemporaryFile
        if delete is None and debug.detailed_debugging():
            delete = False
        temp_file_name = self.temp_file
        if not static:
            temp_file_name += f"-{self.temp_file_count}"
        self.temp_file_count += 1
        debug.assertion(not delete, "Support for delete not implemented")
        debug.trace(5, f"TestWrapper.get_temp_file() => {temp_file_name!r}")
        return temp_file_name

    def get_temp_dir(self, delete: Optional[bool] = None,
                     skip_create: Optional[bool] = None,
                     static: Optional[bool] = None) -> str:
        """Return name of temporary dir based on self.temp_file, optionally with DELETE.
        Also, the directory will be created unless SKIP_CREATE;
        this possibly overwrites existing file with same name.
        In addition, the directory will be unique unless STATIC specified.
        Note: delete option not yet functional
        """
        temp_dir = self.get_temp_file(delete=delete, static=static)
        if not skip_create:
            gh.full_mkdir(temp_dir, force=True)
        debug.trace(5, f"get_temp_dir() => {temp_dir!r}")
        return temp_dir
    
    def create_temp_file(self, contents: Any,  binary: bool = False) -> str:
        """Create temporary file with CONTENTS and return full path"""
        temp_filename = self.get_temp_file()
        system.write_file(temp_filename, contents, binary=binary)
        debug.trace(6, f"create_temp_file({contents!r}) => {temp_filename}")
        return temp_filename

    def patch_trace_level(self, level):
        """Monkey patch the trace LEVEL (e.g., DEBUG_LEVEL)"""
        self.monkeypatch.setattr("mezcla.debug.trace_level", level)

    def tearDown(self) -> None:
        """Per-test cleanup: deletes temp file unless detailed debugging"""
        debug.trace(6, "TestWrapper.tearDown()")
        if not KEEP_TEMP:
            gh.run("rm -vf {file}*", file=self.temp_file)
            for i in range(self.temp_file_count):
                gh.run(f"rm -vf {self.temp_file}-{i}")
        self.temp_file_count = 0

        # Show results of code profiling if enabled
        if PROFILE_CODE:
            assert self.profiler is not None
            self.profiler.disable()
            ## TODO: debug.trace(1, f"Test {self.test_num} code profiling results")
            print(f"Test {self.test_num} code profiling results")
            ## OLD: self.profiler.print_stats(sort='cumulative')
            ## NOTE: Based on cProfile's print_stats (in order to use stderr)
            stats = pstats.Stats(self.profiler, stream=sys.stderr)
            stats.strip_dirs().sort_stats('cumulative').print_stats()
        return

    @classmethod
    def tearDownClass(cls) -> None:
        """Per-class cleanup: stub for tracing purposes"""
        debug.trace_fmtd(5, "TestWrapper.tearDownClass(); cls={c}", c=cls)
        if not KEEP_TEMP:
            ## TODO: use shutil
            if cls.use_temp_base_dir:
                if DISABLE_RECURSIVE_DELETE:
                    debug.trace(4, f"FYI: Only deleting top-level files in {cls.temp_base} to avoid potentially dangerous rm -r")
                    gh.run("rm -f {dir}/* {dir}/.*", dir=cls.temp_base)
                    gh.run("rm -f {dir}", dir=cls.temp_base)
                else:
                    debug.trace(4, f"FYI: Using potentially dangerous rm -r over {cls.temp_base}")
                    gh.run("rm -rvf {dir}", dir=cls.temp_base)
            else:
                gh.run("rm -vf {base}*", base=cls.temp_base)
        super().tearDownClass()
        return

## TODO: TestWrapper.assert = TestWrapper.do_assert

#-------------------------------------------------------------------------------
    
if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_DETAILED)
    debug.trace(TL.USUAL, "Warning: not intended for command-line use\n")
