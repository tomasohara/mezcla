#! /usr/bin/env python3
# 
# Evaluate '# EX:' tests placed in python source. This reformats EX comments
# into the doctest text format. For example,
#    # EX: system.is_number("3.14159") => False    # conventional PI
# gets converted as follows:
#    >>> system.is_number("3.14159")
#    False
#
# Note:
# - Post-expression comments are stripped if preceded by 2+ spaces (as above).
#

"""
Convert example comments in Python scource to doctest format and evaluate.

Sample usage:
   {script} text_utils.py
"""

# Standard modules
import sys
from types import ModuleType            # pylint: disable=unused-import
from typing import Optional

# Installed modules
## TODO2: import ast_tools

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main
from mezcla.my_regex import my_re
from mezcla import system

# Constants for switches, omitting leading dashes
OUTPUT_ARG = "just-output"

# Constants
TL = debug.TL

# Environment options
SKIP_BACKGROUND = system.getenv_bool(
    "SKIP_BACKGROUND", False,
    description="Skip example tests involving background jobs")
SKIP_NORMALIZE = system.getenv_bool(
    "SKIP_NORMALIZE", False,
    description="Skip normalization of outout for doctest")
NORMALIZE_RESULT = system.getenv_bool(
    "NORMALIZE_RESULT", not SKIP_NORMALIZE,
    description="Normalize result to acount for doctest quirks as with quotes")


class TestConverter:
    """Class to convert example EX-style comments into doctest text format"""

    def __init__(self):
        """Initializer"""
        debug.trace_fmtd(TL.VERBOSE, "Helper.__init__(): self={s}", s=self)
        self.test_text = ""
        debug.trace_object(5, self, label=f"{self.__class__.__name__} instance")

    def get_tests(self):
        """Returns set of tests as string"""
        result = self.test_text
        debug.trace(6, f"get_tests() => {result}")
        return result

    def add_module(self, module_spec, dir_path=None):
        """Add import-* spec from MODULE_SPEC"""
        ## TODO2: use sandbox namespace to avoid contaminating global one
        debug.trace(6, f"add_module({module_spec}, [{dir_path}])")
        # pylint: disable=eval-used,exec-used,
        if dir_path is not None:
            debug.trace(5, f"Appending {dir_path!r} to python path")
            sys.path.append(dir_path)
        exec(f"import {module_spec}")
        ## TEMP:
        exec(f"from {module_spec} import *")
        debug.assertion(eval(f"isinstance({module_spec}, ModuleType)"))
        self.test_text += f">>> from {module_spec} import *\n\n"

    def convert(self, line, line_num: Optional[int] = 0):
        """Convert example test in LINE at LINE_NUM"""
        debug.trace(7, f"convert({line}, [{line_num}])")
        expression = result = None
        OK = False
        in_line = line

        # Ignore comments (n.b., requires 2+ spaces before # and uses non-greedy search for expr)
        ## TODO2: make sure the comment start isn't part of the result (i.e., within quotes)
        line = line.strip()
        if my_re.search(r"^(.* EX: .*?)   *(#.*)$", line):
            line = my_re.group(1)
            comment = my_re.group(2)
            debug.trace(4, f"FYI: Ignoring comment at line {line_num}: {comment}")
        
        # Parse test expression
        if my_re.search(r"# +EX: (.*)\s*=>\s*(.*)", line):
            expression, result = my_re.groups()
            OK = True
        elif my_re.search(r"# +EX: (.*)", line):
            expression = my_re.group(1)
            result = "True"
            OK = True
        else:
            pass

        # Exclude certain commands
        if expression and SKIP_BACKGROUND and my_re.search(r"run|issue(.*&)", expression):
            debug.trace(4, f"FYI: Ignoring invocation of background job at {line_num}: {in_line}")
            OK = False

        # Normalize result (e.g., change double quote to single)
        ## OLD:
        ## ## TODO3: my_re.search(r'^".*[^"].*"$', result)
        ## if result and NORMALIZE_RESULT and my_re.search(r'^\s*(".*")\s*$', result):
        ##     ## OLD: result = f'{result[1:-1]}'
        ##     result_proper = my_re.sub(r"[^\\]'", "\\'", result[1:-1])
        ##     result = f"'{result_proper}'"
        if OK and result and NORMALIZE_RESULT:
            debug.trace_expr(5, expression, result)
            new_result = result
            try:
                ## TODO2: use sandbox namespace to avoid contaminating global one
                new_result = eval(f"""{result}""")    # pylint: disable=eval-used
            except:
                system.print_exception_info("normalization")
            if new_result != result:
                debug.trace(5, f"FYI: Normalized result to {new_result!r}")
                result = new_result

        # Add to tests
        if ((not OK) or ((expression is None) and (result is None))):
            debug.trace(6, f"Ignoring line {line_num}: {in_line}")
        else:
            if isinstance(result, str):
                result = repr(result)
            self.test_text += f">>> {expression.strip()}\n{result}\n\n"
        return OK


class Script(Main):
    """Input processing class"""
    output_arg = False
    exc = None
    num_tests = 0
    module = "???"

    def setup(self):
        """Check results of command line processing"""
        debug.trace_fmtd(TL.VERBOSE, "Script.setup(): self={s}", s=self)
        self.output_arg = self.get_parsed_option(OUTPUT_ARG, self.output_arg)
        self.exc = TestConverter()
        dir_path, module_file = system.split_path(self.filename)
        self.module = gh.basename(module_file, ".py")
        debug.assertion(my_re.search(r"^\w+$", self.module),
                        f"Module name {self.module!r} should be a valid python identifier")
        self.exc.add_module(self.module, dir_path=dir_path)
        debug.trace_object(5, self, label=f"{self.__class__.__name__} instance")

    def process_line(self, line):
        """Processes current line looking for EX comments and converting"""
        debug.trace_fmtd(TL.QUITE_DETAILED, "Script.process_line({l})", l=line)
        ok = self.exc.convert(line, self.line_num)
        if ok:
            self.num_tests += 1

    def wrap_up(self):
        """Output the final set of tests"""
        debug.trace_fmtd(TL.VERBOSE, "Script.wrap_up(): self={s}", s=self)
        test_spec = self.exc.get_tests()
        if self.output_arg:
            print(test_spec)
        elif self.num_tests:
            system.write_file(self.temp_file, test_spec)
            print(gh.run(f"python -m doctest -v {self.temp_file}"))
        else:
            debug.trace(4, "FYI: No tests extracted from module {self.module}")
        
def main():
    """Entry point"""
    app = Script(
        description=__doc__.format(script=gh.basename(__file__)),
        skip_input=False, manual_input=False,
        boolean_options=[(OUTPUT_ARG, "Output converted tests without running")])
    app.run()
    
#-------------------------------------------------------------------------------
    
if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    debug.trace(5, f"module __doc__: {__doc__}")
    main()
