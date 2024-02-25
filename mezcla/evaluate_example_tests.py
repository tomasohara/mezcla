#! /usr/bin/env python
# 
# Evaluate '#: EX' tests placed in python source. This reformats EX comments
# into the doctest text format. For example,
#    # EX: is_symbolic("3.14159") => False
# gets converted as follows:
#    >>> is_symbolic("3.14159")
#    False
#

"""
Convert example comments in Python scource to doctest format and evaluate.

Sample usage:
   {script} text_utils.py
"""

# Standard modules
from types import ModuleType

# Installed modules
## TODO2: import ast_tools

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main
from mezcla.my_regex import my_re
from mezcla import system

# Constants for switches omitting leading dashes
OUTPUT_ARG = "output"

# Constants
TL = debug.TL

# Environment options
# Note: These are just intended for internal options, not for end users.
# It also allows for enabling options in one place rather than four
# (e.g., [Main member] initialization, run-time value, and argument spec., along
# with string constant definition).
# WARNING: To minimize environment comflicts with other programs make the names
# longer such as two or more tokens (e.g., "FUBAR" => "FUBAR_LEVEL").
#
TODO_FUBAR = system.getenv_bool("TODO_FUBAR", False,
                                description="TODO:Fouled Up Beyond All Recognition processing")

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

    def add_module(self, module_spec):
        """Add import-* spec from MODULE_SPEC"""
        # pylint: disable=eval-used,exec-used
        ## TODO2: debug.assertion(eval("isintance(eval({module_spec!r}, module)"))
        exec(f"import {module_spec}")
        debug.assertion(eval(f"isinstance({module_spec}, ModuleType)"))
        self.test_text += f">>> from {module_spec} import *\n\n"
    
    def convert(self, line, line_num):
        """Convert example test in LINE at LINE_NUM"""
        expression = result = None
        OK = False
        if my_re.search(r"EX: (.*) => (.*)", line):
            expression, result = my_re.groups()
            OK = True
        elif my_re.search(r"EX: (.*)", line):
            expression = my_re.group(1)
            result = "True"
            OK = True
        else:
            pass
        if ((expression is None) and (result is None)):
            debug.trace(6, f"Ignoring line {line_num}: {line}")
        else:
            self.test_text += f">>> {expression.strip()}\n{result.strip()}\n\n"
        return OK


class Script(Main):
    """Input processing class"""
    output_arg = False
    exc = None

    def setup(self):
        """Check results of command line processing"""
        debug.trace_fmtd(TL.VERBOSE, "Script.setup(): self={s}", s=self)
        ## TODO: extract argument values
        self.output_arg = self.get_parsed_option(OUTPUT_ARG, self.output_arg)
        ## TODO:
        ## self.text_arg = self.get_parsed_option(TEXT_ARG, self.text_arg)
        ## self.alt_filename = self.get_parsed_argument(ALT_FILENAME)
        self.exc = TestConverter()
        module = gh.basename(self.filename, ".py")
        self.exc.add_module(module)
        debug.trace_object(5, self, label=f"{self.__class__.__name__} instance")

    def process_line(self, line):
        """Processes current line looking for EX comments and converting"""
        debug.trace_fmtd(TL.QUITE_DETAILED, "Script.process_line({l})", l=line)
        self.exc.convert(line, self.line_num)

    def wrap_up(self):
        """Output the final set of tests"""
        debug.trace_fmtd(TL.VERBOSE, "Script.wrap_up(): self={s}", s=self)
        test_spec = self.exc.get_tests()
        if self.output_arg:
            print(test_spec)
        else:
            system.write_file(self.temp_file, test_spec)
            print(gh.run("python -m doctest -v {self.temp_file}"))
        
def main():
    """Entry point"""
    app = Script(
        description=__doc__.format(script=gh.basename(__file__)),
        skip_input=False,
        manual_input=False,
        boolean_options=[(OUTPUT_ARG, "Output converted tests without running")],
        float_options=None)
    app.run()
    
#-------------------------------------------------------------------------------
    
if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    debug.trace(5, f"module __doc__: {__doc__}")
    debug.assertion("TODO:" not in __doc__)
    main()
