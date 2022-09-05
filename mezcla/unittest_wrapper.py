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

import os
import re
import tempfile
import unittest

import mezcla
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import system
from mezcla import tpo_common as tpo

TODO_MODULE = "TODO MODULE"

# Note: the following is for transparent resolution of dotted module names
# for invocation of scripts via 'python -m package.module'. This is in support
# of transitioning from the old way of importing packages via 'import module'
# instead of 'import package.module'. (The former required that package be
# explicitly specified in the python path, such as via 'PYTHONPATH=package-dir:...'.)
THIS_PACKAGE = getattr(mezcla.debug, "__package__", None)
debug.assertion(THIS_PACKAGE == "mezcla")


class TestWrapper(unittest.TestCase):
    """Class for testcase definition"""
    script_module = TODO_MODULE         # name for invocation via 'python -m' (n.b., usuually set via derive_tested_module_name)
    temp_base = system.getenv_text("TEMP_BASE",
                                   tempfile.NamedTemporaryFile().name)
    ## TODO: temp_file = None
    ## TEMP: initialize to unique value independent of temp_base
    temp_file = tempfile.NamedTemporaryFile().name
    use_temp_base_dir = None
    test_num = 1

    @classmethod
    def setUpClass(cls):
        """Per-class initialization: make sure script_module set properly"""
        tpo.debug_format("TestWrapper.setupClass(): cls={c}", 5, c=cls)
        super(TestWrapper, cls).setUpClass()
        debug.trace_object(5, cls, "TestWrapper class")
        debug.assertion(cls.script_module != TODO_MODULE)
        if cls.script_module:
            # Try to pull up usage via python -m mezcla.xyz --help
            help_usage = gh.run("python -m '{mod}' --help", mod=cls.script_module)
            debug.assertion("No module named" not in help_usage,
                            f"problem running via 'python -m {cls.script_module}'")
            # Warn about lack of usage statement unless "not intended for command-line" type warning issued
            # OLD: (re.search(r"not intended.*(command|standalone)", help_usage))
            # TODO: standardize the not-intended wording
            if (not ((re.search(r"warning:.*not intended", help_usage,
                                re.IGNORECASE))
                     or ("usage:" in help_usage.lower()))):
                system.print_stderr("Warning: mezcla scripts should implement --help")

        # Optionally, setup temp-base directory (normally just a file)
        if cls.use_temp_base_dir is None:
            cls.use_temp_base_dir = system.getenv_bool("USE_TEMP_BASE_DIR", False)
            # TODO: temp_base_dir = system.getenv_text("TEMP_BASE_DIR", " "); cls.use_temp_base_dir = bool(temp_base_dir.strip()); ...
        if cls.use_temp_base_dir:
            ## TODO: pure python
            gh.run("mkdir -p {dir}", dir=cls.temp_base)

        return

    @staticmethod
    def derive_tested_module_name(test_filename):
        """Derive the name of the module being tested from TEST_FILENAME. Used as follows:
              script_module = TestWrapper.derive_tested_module_name(__file__)
        Note: Deprecated method (see get_testing_module_name)
        """
        tpo.debug_format("Warning: in deprecrated derive_tested_module_name", 5)
        module = os.path.split(test_filename)[-1]
        module = re.sub(r".py[oc]?$", "", module)
        module = re.sub(r"^test_", "", module)
        tpo.debug_format("derive_tested_module_name({f}) => {m}", 5,
                         f=test_filename, m=module)
        return (module)

    @staticmethod
    def get_testing_module_name(test_filename, module_object=None):
        """Derive the name of the module being tested from TEST_FILENAME and MODULE_OBJECT"""
        # TODO: used as follows (see tests/test_template.py):
        #    script_module = TestWrapper.get_testing_module_name(__file__)
        module_name = os.path.split(test_filename)[-1]
        module_name = re.sub(r".py[oc]?$", "", module_name)
        module_name = re.sub(r"^test_", "", module_name)
        package_name = THIS_PACKAGE
        if module_object is not None:
           package_name = getattr(module_object, "__package__", "")
           debug.trace_expr(4, package_name)
        if package_name:
            full_module_name = package_name + "." + module_name
        else:
            full_module_name = module_name
        tpo.debug_format("get_testing_module_name({f}) => {m}", 4,
                         f=test_filename, m=full_module_name)
        return (full_module_name)

    def setUp(self):
        """Per-test initializations
        Notes:
        - Disables tracing scripts invoked via run() unless ALLOW_SUBCOMMAND_TRACING
        - Initializes temp file name (With override from environment)."""
        # Note: By default, each test gets its own temp file.
        tpo.debug_print("TestWrapper.setUp()", 4)
        if not gh.ALLOW_SUBCOMMAND_TRACING:
            gh.disable_subcommand_tracing()
        # The temp file is an extension of temp-base file by default.
        # Opitonally, if can be a file in temp-base subdrectory.
        if self.use_temp_base_dir:
            default_temp_file = gh.form_path(self.temp_base, "test-")
        else:
            default_temp_file = self.temp_base + "-test-"
        default_temp_file += str(TestWrapper.test_num)
        self.temp_file = system.getenv_text("TEMP_FILE", default_temp_file)
        gh.delete_existing_file(self.temp_file)
        TestWrapper.test_num += 1

        ## OLD: tpo.trace_object(self, 5, "TestWrapper instance")
        debug.trace_object(5, self, "TestWrapper instance")
        return

    def run_script(self, options=None, data_file=None, log_file=None, trace_level=4,
                   out_file=None, env_options=None, uses_stdin=False):
        """Runs the script over the DATA_FILE (optional), passing (positional)
        OPTIONS and optional setting ENV_OPTIONS. If OUT_FILE and LOG_FILE are
        not specifed, they  are derived from self.temp_file.
        Notes:
        - issues warning if script invocation leads to error
        - if USES_STDIN, requires explicit empty string for DATA_FILE to avoid use of - (n.b., as a precaution against hangups)"""
        tpo.debug_format("TestWrapper.run_script({opts}, {df}, {lf}, {of}, {env})", trace_level + 1,
                         opts=options, df=data_file, lf=log_file, 
                         of=out_file, env=env_options)
        if options is None:
            options = ""
        if env_options is None:
            env_options = ""

        # Derive the full paths for data file and log, and then invoke script.
        # TODO: derive from temp base and data file name?;
        data_path = ("" if uses_stdin else "-")
        if data_file is not None:
            data_path = (gh.resolve_path(data_file) if len(data_file) else data_file)
        if not log_file:
            log_file = self.temp_file + ".log"
        if not out_file:
            out_file = self.temp_file + ".out"
        # note: output is redirected to a file to preserve tabs
        debug.assertion(not self.script_module.endswith(".py"))
        gh.issue("{env} python  -m {module}  {opts}  {path} 1> {out} 2> {log}",
                 env=env_options, module=self.script_module, 
                 opts=options, path=data_path, out=out_file, log=log_file)
        output = gh.read_file(out_file)
        # note; trailing newline removed as with shell output
        if output.endswith("\n"):
            output = output[:-1]
        tpo.debug_format("output: {{\n{out}\n}}", trace_level,
                         out=gh.indent_lines(output))

        # Make sure no python or bash errors. For example,
        #   "SyntaxError: invalid syntax" and "bash: python: command not found"
        log_contents = gh.read_file(log_file)
        error_found = re.search(r"(\S+error:)|(no module)|(command not found)",
                                log_contents.lower())
        gh.assertion(not error_found)
        tpo.debug_format("log contents: {{\n{log}\n}}", trace_level + 1,
                         log=gh.indent_lines(log_contents))

        # Do sanity check for python exceptions
        traceback_found = re.search("Traceback.*most recent call", log_contents)
        gh.assertion(not traceback_found)

        return output

    def tearDown(self):
        """Per-test cleanup: deletes temp file unless detailed debugging"""
        tpo.debug_print("TestWrapper.tearDown()", 4)
        if not tpo.detailed_debugging():
            gh.run("rm -vf {file}*", file=self.temp_file)
        return

    @classmethod
    def tearDownClass(cls):
        """Per-class cleanup: stub for tracing purposes"""
        tpo.debug_format("TestWrapper.tearDownClass(); cls={c}", 5, c=cls)
        if not tpo.detailed_debugging():
            if cls.use_temp_base_dir:
                gh.run("rm -rvf {dir}", dir=cls.temp_base)
            else:
                gh.run("rm -vf {base}*", base=cls.temp_base)
        super(TestWrapper, cls).tearDownClass()
        return
