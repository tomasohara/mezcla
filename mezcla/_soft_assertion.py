#! /usr/bin/env python
#

"""Simple assertion that doesn't abort upon failure"""

import inspect
from mezcla import debug
from mezcla import system

if __debug__:

    def soft_assertion(expression):
        """Issue warning if EXPRESSION is not True"""
        debug.trace_expr(5, expression)
        if not expression:
            debug.trace(4, "expression failed")
            caller = inspect.stack()[1]
            (_frame, filename, line_number, _function, _context, _index) = caller
            system.print_error(f"Warning: assertion failed at {filename}:{line_number}\n")

else:

    def soft_assertion(_expression):
        """no-op for assertion check"""
        pass                             # pylint: disable=unnecessary-pass


def main():
    """Entry point for script"""
    system.print_error("Warning: not intended for command line usage.")
    debug.trace(1, "Examples follow.")
    soft_assertion(0 <= debug.get_level() <= 10)
    soft_assertion((2 + 2) == 5)

if __name__ == '__main__':
    main()
