#! /usr/bin/env python
# 
# Sample script using Main class.
#

"""Simple illustration of Main class"""

import re
from tomas_misc import debug
from tomas_misc.main import Main

class Script(Main):
    """Input processing class"""
    regex = None
    check_fubar = None

    def setup(self):
        """Check results of command line processing"""
        self.regex = self.parsed_args['regex']
        self.check_fubar = self.get_parsed_option('check-fubar', not self.regex)
        debug.assertion(bool(self.regex) ^ self.check_fubar)
        debug.trace_object(5, self, label="Script instance")

    def process_line(self, line):
        """Processes current line from input"""
        if self.check_fubar and "fubar" in line:
            debug.trace(4, f"Fubar line {self.line_num}: {line}")
            print(line)
        elif self.regex and re.search(self.regex, line):
            debug.trace(4, f"Regex line {self.line_num}: {line}")
            print(line)
        return

if __name__ == '__main__':
    app = Script(description=__doc__,
                 boolean_options=["check-fubar"],
                 text_options=[("regex", "Regular expression")])
    app.run()
