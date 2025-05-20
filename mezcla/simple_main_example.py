#! /usr/bin/env python3
# 
# Sample script using Main class. By default, this outputs lines that contain
# "fubar". There is an option to check for lines matching a regular expression.
#

"""Simple illustration of Main class

Sample usage:
   echo $'foobar\\nfubar' | {script} --check-fubar -
"""

# Standard packages
## TODO: from collections import defaultdict

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main
from mezcla.my_regex import my_re

# Constants
TL = debug.TL
FUBAR_ARG = "check-fubar"
REGEX_ARG = "regex"
ENTIRE_ARG = "entire-file"
PARA_ARG = "para"

class SimpleFilter:
    """Regex filter for text"""

    def __init__(self, regex=None, flags=0):
        """Initialize class with PATTERN which can be a REGEX"""
        self.regex = regex
        self.flags = flags
        debug.trace_object(TL.DETAILED, self, label=f"{self.__class__.__name__} instance")

    def include(self, line):
        """Output line if filter met"""
        include = my_re.search(self.regex, line, flags=self.flags)
        debug.trace(TL.QUITE_VERBOSE, "SimpleFilter.include({line!r}) => {include}")
        return include

    
class Script(Main):
    """Input processing class"""
    filter_inst = None

    def setup(self):
        """Check results of command line processing"""
        debug.trace_fmtd(TL.DETAILED, "Script.setup(): self={s}", s=self)
        regex = self.get_parsed_option(REGEX_ARG, "")
        check_fubar = self.get_parsed_option(FUBAR_ARG, not regex)
        slurp_mode = self.get_parsed_option(ENTIRE_ARG)
        para_mode = self.get_parsed_option(PARA_ARG)
        debug.assertion(bool(regex) ^ bool(check_fubar))
        if check_fubar:
            regex = "fubar"
        if slurp_mode:
            self.file_input_mode = True
        if para_mode:
            self.paragraph_mode = True
        self.filter_inst = SimpleFilter(regex)
        debug.trace_object(TL.VERBOSE, self, label=f"{self.__class__.__name__} instance")

    def process_line(self, line):
        """Processes current LINE from input
        Note: can be a paragraph or an entire file (a la perl)"""
        debug.trace(TL.QUITE_DETAILED, f"Script.process_line({line!r})")
        if self.filter_inst.include(line):
            print(line)
        return

def main():
    """Entry point"""
    app = Script(
        description=__doc__.format(script=gh.basename(__file__)),
        boolean_options=[(FUBAR_ARG, "Check for 'fubar' in line"),
                         (PARA_ARG, "Process file in paragraphs (a la Perl)"),
                         (ENTIRE_ARG, "Apply filter to entire file (a la perl slurping")],
        text_options=[(REGEX_ARG, "Regular expression to check")])
    app.run()

#-------------------------------------------------------------------------------
    
if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    main()
