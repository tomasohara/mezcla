#! /usr/bin/env python
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
# TODO:
# - * Clarify TEMP_BASE vs. TEMP_FILE usage.
# - Clarify that this can co-exist with pytest-based tests (see tests/test_main.py).
# TODO2:
# - Clean up script_file usage (and unncessary settings in test scripts).
#
#-------------------------------------------------------------------------------
# Sample test (streamlined version of test_simple_main_example.py):
#
#   import unittest
#   from mezcla import system
#   from mezcla.unittest_wrapper import TestWrapper
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
#      unittest.main()
#-------------------------------------------------------------------------------
# TODO:
# - Add method to invoke unittest.main(), so clients don't need to import unittest.
# - Clarify how ALLOW_SUBCOMMAND_TRACING affects tests that invoke external scripts.
#

"""Unit test support class"""

# Standard packages
import inspect
import os
import tempfile
import unittest

# Installed packages
## TODO: import pytest

# Local packages
import mezcla
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla import system

# Constants (e.g., environment options)

TL = debug.TL
KEEP_TEMP = system.getenv_bool("KEEP_TEMP", debug.detailed_debugging(),
                               "keep temporary files")
TODO_FILE = "TODO FILE"
TODO_MODULE = "TODO MODULE"

# Note: the following is for transparent resolution of dotted module names
# for invocation of scripts via 'python -m package.module'. This is in support
# of transitioning from the old way of importing packages via 'import module'
# instead of 'import package.module'. (The former required that package be
# explicitly specified in the python path, such as via 'PYTHONPATH=package-dir:...'.)
THIS_PACKAGE = getattr(mezcla.debug, "__package__", None)
debug.assertion(THIS_PACKAGE == "mezcla")


def get_temp_dir(keep=None):
    """Get temporary directory, omitting later deletion if KEEP"""
    # NOTE: Unused function
    if keep is None:
        keep = KEEP_TEMP
    dir_path = tempfile.NamedTemporaryFile(delete=(not keep)).name
    gh.full_mkdir(dir_path)
    debug.trace(5, f"get_temp_dir() => {dir_path}")
    return dir_path


def trap_exception(function):
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
            system.print_exception_info(function)
            assert(False)
        return result
    #
    debug.trace(7, f"trap_exception() => {gh.elide(wrapper)}")
    return wrapper


def pytest_fixture_wrapper(function):
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


class TestWrapper(unittest.TestCase):
    """Class for testcase definition
    Note:
    - script_module should be overriden to specify the module instance, such as via get_testing_module_name (see test/template.py)
    - set it to None to avoid command-line invocation checks
    """
    script_file = TODO_FILE             # path for invocation via 'python -m coverage run ...' (n.b., usually set via get_module_file_path)
    script_module = TODO_MODULE         # name for invocation via 'python -m' (n.b., usually set via derive_tested_module_name)
    temp_base = system.getenv_text("TEMP_BASE",
                                   tempfile.NamedTemporaryFile().name)
    check_coverage = system.getenv_bool("CHECK_COVERAGE", False,
                                        "Check coverage during unit testing")
    ## TODO: temp_file = None
    ## TEMP: initialize to unique value independent of temp_base
    temp_file = None
    use_temp_base_dir = system.is_directory(temp_base)
    test_num = 1
    
    ## TEST:
    ## NOTE: leads to pytest warning. See
    ##   https://stackoverflow.com/questions/62460557/cannot-collect-test-class-testmain-because-it-has-a-init-constructor-from
    ## def __init__(self, *args, **kwargs):
    ##     debug.trace_fmtd(5, "TestWrapper.__init__({a}): keywords={kw}; self={s}",
    ##                      a=",".join(args), kw=kwargs, s=self)
    ##     super().__init__(*args, **kwargs)
    ##    debug.trace_object(5, self, label="TestWrapper instance")
    ##
    ## __test__ = False                 # make sure not assumed test
        
    @classmethod
    def setUpClass(cls):
        """Per-class initialization: make sure script_module set properly"""
        debug.trace_fmtd(5, "TestWrapper.setupClass(): cls={c}", c=cls)
        super().setUpClass()
        debug.trace_object(5, cls, "TestWrapper class")
        debug.assertion(cls.script_module != TODO_MODULE)
        if (cls.script_module is not None):
            # Try to pull up usage via python -m mezcla.xyz --help
            help_usage = gh.run("python -m '{mod}' --help", mod=cls.script_module)
            debug.assertion("No module named" not in help_usage,
                            f"problem running via 'python -m {cls.script_module}'")
            # Warn about lack of usage statement unless "not intended for command-line" type warning issued
            # TODO: standardize the not-intended wording
            if (not ((my_re.search(r"warning:.*not intended", help_usage,
                                   flags=my_re.IGNORECASE))
                     or ("usage:" in help_usage.lower()))):
                system.print_stderr("Warning: script should implement --help")

        # Optionally, setup temp-base directory (normally just a file)
        if cls.use_temp_base_dir is None:
            cls.use_temp_base_dir = system.getenv_bool("USE_TEMP_BASE_DIR", False)
            # TODO: temp_base_dir = system.getenv_text("TEMP_BASE_DIR", " "); cls.use_temp_base_dir = bool(temp_base_dir.strip()); ...
        if cls.use_temp_base_dir:
            ## TODO: pure python
            ## TODO: gh.full_mkdir
            gh.run("mkdir -p {dir}", dir=cls.temp_base)

        return

    @staticmethod
    def derive_tested_module_name(test_filename):
        """Derive the name of the module being tested from TEST_FILENAME. Used as follows:
              script_module = TestWrapper.derive_tested_module_name(__file__)
        Note: *** Deprecated method *** (see get_testing_module_name)
        """
        debug.trace(3, "Warning: in deprecrated derive_tested_module_name")
        module = os.path.split(test_filename)[-1]
        module = my_re.sub(r".py[oc]?$", "", module)
        module = my_re.sub(r"^test_", "", module)
        debug.trace_fmtd(5, "derive_tested_module_name({f}) => {m}",
                         f=test_filename, m=module)
        return (module)

    @staticmethod
    def get_testing_module_name(test_filename, module_object=None):
        """Derive the name of the module being tested from TEST_FILENAME and MODULE_OBJECT
        Note: used as follows (see tests/template.py):
            script_module = TestWrapper.get_testing_module_name(__file__)
        """
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
    def get_module_file_path(test_filename):
        """Return absolute path of module being tested"""
        result = system.absolute_path(test_filename)
        result = my_re.sub(r'tests\/test_(.*\.py)', r'\1', result)
        debug.assertion(result.endswith(".py"))
        debug.trace(7, f'get_module_file_path({test_filename}) => {result}')
        return result

    def setUp(self):
        """Per-test initializations
        Notes:
        - Disables tracing scripts invoked via run() unless ALLOW_SUBCOMMAND_TRACING
        - Initializes temp file name (With override from environment)."""
        # Note: By default, each test gets its own temp file.
        debug.trace(4, "TestWrapper.setUp()")
        if not gh.ALLOW_SUBCOMMAND_TRACING:
            gh.disable_subcommand_tracing()
        # The temp file is an extension of temp-base file by default.
        # Optionally, if can be a file in temp-base subdrectory.
        if self.use_temp_base_dir:
            default_temp_file = gh.form_path(self.temp_base, "test-")
        else:
            default_temp_file = self.temp_base + "-test-"
        default_temp_file += str(TestWrapper.test_num)
        self.temp_file = system.getenv_text("TEMP_FILE", default_temp_file)
        gh.delete_existing_file(self.temp_file)
        TestWrapper.test_num += 1

        debug.trace_object(5, self, "TestWrapper instance")
        return

    def run_script(self, options=None, data_file=None, log_file=None, trace_level=4,
                   out_file=None, env_options=None, uses_stdin=None, post_options=None, background=None):
        """Runs the script over the DATA_FILE (optional), passing (positional)
        OPTIONS and optional setting ENV_OPTIONS. If OUT_FILE and LOG_FILE are
        not specified, they  are derived from self.temp_file. The optional POST_OPTIONS
        go after the data file.
        Notes:
        - issues warning if script invocation leads to error
        - if USES_STDIN, requires explicit empty string for DATA_FILE to avoid use of - (n.b., as a precaution against hangups)"""
        debug.trace_fmtd(trace_level + 1,
                         "TestWrapper.run_script(opts={opts}, data={df}, log={lf}, lvl={lvl}, out={of}, env={env}, stdin={stdin}, post={post}, back={back})",
                         opts=options, df=data_file, lf=log_file, lvl=trace_level, of=out_file,
                         env=env_options, stdin=uses_stdin, post=post_options, back=background)
        if options is None:
            options = ""
        if env_options is None:
            env_options = ""
        if post_options is None:
            post_options = ""

        # Derive the full paths for data file and log, and then invoke script.
        # TODO: derive from temp base and data file name?;
        # TODO1: derive default for uses_stdin based on use of filename argment (e.g., from usage)
        uses_stdin_false = ((uses_stdin is not None) and not bool(uses_stdin))
        data_path = ("" if uses_stdin_false else "-")
        if data_file is not None:
            data_path = (gh.resolve_path(data_file) if len(data_file) else data_file)
        if not log_file:
            log_file = self.temp_file + ".log"
        if not out_file:
            out_file = self.temp_file + ".out"
        # note: output is redirected to a file to preserve tabs

        # Set converage script path and command spec
        coverage_spec = ''
        script_module = self.script_module
        if self.check_coverage:
            debug.assertion(self.script_file)
            ## BAD: self.script_module = self.script_file
            script_module = self.script_file
            coverage_spec = 'coverage run'
        ## OLD:
        ## else:
        ##     debug.assertion(not self.script_module.endswith(".py"))
        debug.assertion(not script_module.endswith(".py"))
        amp_spec = "&" if background else ""

        # Run the command
        gh.issue("{env} python -m {cov_spec} {module}  {opts}  {path}  {post} 1> {out} 2> {log} {amp_spec}",
                 env=env_options, cov_spec=coverage_spec, module=script_module,
                 opts=options, path=data_path, out=out_file, log=log_file, post=post_options, amp_spec=amp_spec)
        output = system.read_file(out_file)
        # note; trailing newline removed as with shell output
        if output.endswith("\n"):
            output = output[:-1]
        debug.trace_fmtd(trace_level, "output: {{\n{out}\n}}",
                         out=gh.indent_lines(output), max_len=2048)

        # Make sure no python or bash errors. For example,
        #   "SyntaxError: invalid syntax" and "bash: python: command not found"
        log_contents = system.read_file(log_file)
        error_found = my_re.search(r"(\S+error:)|(no module)|(command not found)",
                                   log_contents.lower())
        debug.assertion(not error_found)
        debug.trace_expr(trace_level + 1, log_contents, max_len=2048)

        # Do sanity check for python exceptions
        traceback_found = my_re.search("Traceback.*most recent call", log_contents)
        debug.assertion(not traceback_found)

        return output

    def do_assert(self, condition, message=None):
        """Shows context for assertion failure with CONDITION and then issue assert
        If MESSAGE specified, included in assertion error
        Note:
        - Works around for maldito pytest, which makes it hard to do simple things like pinpointing errors.
        - Formatted similar to debug.assertion:
             Test assertion failed: <expr> (at <f><n>): <msg>
        """
        debug.trace(7, f"do_assert({condition}, msg={message})")
        if ((not condition) and debug.debugging(debug.TL.DEFAULT)):
            statement = filename = line_num = None
            try:
                # note: accounts for trap_exception and other decorators
                for caller in inspect.stack():
                    debug.trace_expr(8, caller)
                    (_frame, filename, line_num, _function, context, _index) = caller
                    statement = debug.read_line(filename, line_num).strip()
                    if "do_assert" in statement:
                        break
                debug.trace_expr(7, filename, line_num, context, prefix="do_assert: ")
            except:
                system.print_exception_info("do_assert")
            debug.assertion(statement)
            if statement:
                # TODO3: use abstract syntax tree (AST) based extraction
                # ex: self.do_assert(not my_re.search(r"cat|dog", description))  # no pets
                # Isolate condition
                cond = my_re.sub(r"^\s*\S+\.do_assert\((.*)\)", r"\1", statement)
                # Get expression proper, removing optional comments and semicolon 
                expr = my_re.sub(r";?\s*#.*$", "", cond)
                # Strip optional message
                qual = ""
                if message is not None:
                    expr = my_re.sub(r", *([\'\"]).*\1\s*$", "", expr)   # string arg
                    expr = my_re.sub(r", *[a-z0-9_]+$", "", expr,        # variable arg
                                     flags=my_re.IGNORECASE)
                    qual = f": {message}"
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
    
    def tearDown(self):
        """Per-test cleanup: deletes temp file unless detailed debugging"""
        debug.trace(4, "TestWrapper.tearDown()")
        if not KEEP_TEMP:
            gh.run("rm -vf {file}*", file=self.temp_file)
        return

    @classmethod
    def tearDownClass(cls):
        """Per-class cleanup: stub for tracing purposes"""
        debug.trace_fmtd(5, "TestWrapper.tearDownClass(); cls={c}", c=cls)
        if not KEEP_TEMP:
            ## TODO: use shutil
            if cls.use_temp_base_dir:
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
