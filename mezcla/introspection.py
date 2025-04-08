#!/usr/bin/env python
#
# Introspection support based on alexmojaki/executing package, such as used
# in icecream expression printer.
#
# Note:
# - To avoid circular dependencies this does not use debug.py.
# - Repos with source of code adapted here:
#   https://github.com/alexmojaki/executing
#   https://github.com/gruns/icecream
# - Other repos consulted:
#   https://github.com/samuelcolvin/python-devtools
#
# TODO:
# - Place within debug.py to allow for tracing and to avoid redundant functions.
#
#................................................................................
# MIT License
# 
# Portions Copyright (c) 2019 Alex Hall, (c) 2018 Ansgar Grunseid
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

"""
Module for introspection of arguments and source code
"""

# Standard packages
import ast
import sys
from datetime import datetime
import inspect
from os.path import basename, realpath
from types import FrameType

# Local packages

# Installed packages
# note: asttokens loaded dynamically when executed (so checked here for clients)
import asttokens                        # pylint: disable=unused-import
import pprint
from textwrap import dedent
import executing


# Globals
_absent = object()
## OLD (droppped for sake of mypy):
## intro = None


def stderr_print(*args):
    """
    prints args to sys.stderr
    """
    print(*args, file=sys.stderr)


def is_literal(s):
    """
    Returns whether argument is a literal or not
    """
    try:
        ast.literal_eval(s)
    except:
        return False
    return True


## OLD: DEFAULT_LINE_WRAP_WIDTH = 70  # Characters.
DEFAULT_LINE_WRAP_WIDTH = 256            # Characters.
DEFAULT_CONTEXT_DELIMITER = "; "
DEFAULT_ARG_TO_STRING_FUNCTION = pprint.pformat
DEFAULT_OUTPUT_FUNCTION = stderr_print


def call_or_value(obj):
    """
    Returns the value of calling obj if it's callable, else returns obj as is
    """
    return obj() if callable(obj) else obj


class Source(executing.Source):
    """
    A class that extends the functionality of the `executing.Source` class to provide
    additional methods for handling and manipulating source code text with proper indentation.

    Methods
    -------
    get_text_with_indentation(node)
        Retrieves the text representation of the given AST node, preserving its indentation.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ## DEBUG: debug.trace_expr(TL.VERBOSE, self, args, kwargs, delim="\n\t", prefix="in {Source.__init__({a})")
        ## DEBUG: debug.trace_object(5, self, label="Source instance")

    def get_text_with_indentation(self, node):
        """
        Retrieves the text representation of the given AST node, preserving its indentation.
        """
        result = self.asttokens().get_text(node)
        ## DEBUG: sys.stderr.write(f"{node=} {result=}\n")
        if "\n" in result:
            result = " " * node.first_token.start[1] + result
            result = dedent(result)
        result = result.strip()
        return result

    @classmethod
    def for_frame(cls, frame, use_cache=True):
        return super(Source, cls).for_frame(frame, use_cache)


def prefix_lines(prefix: str, s: str, start_at_line=0) -> list[str]:
    """
    Separates every word in a string,
    adds a prefix and returns them as a list
    """
    lines = s.splitlines()

    for i in range(start_at_line, len(lines)):
        lines[i] = prefix + lines[i]

    return lines


def prefix_first_line_indent_remaining(prefix: str, s: str) -> list[str]:
    """
    Adds prefix to first line and indents the remaining,
    returns the lines as a list
    """
    indent = " " * len(prefix)
    lines = prefix_lines(indent, s, start_at_line=1)
    lines[0] = prefix + lines[0]
    return lines


def format_pair(prefix: str, arg, value):
    """
    Format the pair of argument and value and add prefix, return formatted string
    """
    if arg is _absent:
        arg_lines = []
        value_prefix = prefix
    else:
        arg_lines = prefix_first_line_indent_remaining(prefix, arg)
        value_prefix = arg_lines[-1] + "="

    looks_like_a_string = value[0] + value[-1] in ["''", '""']
    if looks_like_a_string:  # Align the start of multiline strings.
        value_lines = prefix_lines(" ", value, start_at_line=1)
        value = "\n".join(value_lines)

    value_lines = prefix_first_line_indent_remaining(value_prefix, value)
    lines = arg_lines[:-1] + value_lines
    return "\n".join(lines)


def argument_to_string(obj) -> str:
    """
    Converts argument to string using `DEFAULT_ARG_TO_STRING_FUNCTION` and preserves newlines
    """
    s = DEFAULT_ARG_TO_STRING_FUNCTION(obj)
    s = s.replace("\\n", "\n")  # Preserve string newlines in output.
    return s

def trace_frame(frame, label="frame"):
    """Trace info about FRAME to stderr"""
    ## DEBUG:
    sys.stderr.write(f"{label}: {frame.f_code.co_name} {inspect.getfile(frame)}:{frame.f_lineno}\n")

class MezclaDebugger:
    """
    A class used to provide debugging functionality with formatted output.

    Methods:
    -------
    format(self, *args, arg_offset=0)
        Formats the given arguments and returns the formatted string

    Note:
    - See debug.trace_expr for various kwargs supported:
      delim, no_eol, max_len, etc.
    """

    _pairSeparator = "; "
    _lineWrapWidth = DEFAULT_LINE_WRAP_WIDTH
    _contextDelimiter = DEFAULT_CONTEXT_DELIMITER

    def __init__(
        self,
        prefix="",
        output_function=DEFAULT_OUTPUT_FUNCTION,
        arg_to_string_function=argument_to_string,
        include_context=False,
        context_abs_path=False,
        icecream_like=None,
    ):
        self.enabled = True
        self.prefix = prefix
        self.include_context = include_context
        self.output_function = output_function
        self.arg_to_string_function = arg_to_string_function
        self.context_abs_path = context_abs_path
        self.icecream_like = icecream_like

    def __call__(self, *args, arg_offset=0, indirect=False, **kwargs):
        """
        Formats the given arguments and prints the formatted string
        
        :raises ValueError: If the call frame cannot be accessed
        """
        # NOTE: this is not separated into a function
        # as to not generate another call frame
        call_frame = inspect.currentframe() 
        ## DEBUG: trace_frame(call_frame, "call_frame0")
        if call_frame is not None:
            # note: only go back one frame from this function
            go_back = indirect or (call_frame.f_code.co_name != "__call__")
            call_frame = call_frame.f_back
            ## DEBUG: trace_frame(call_frame, "call_frame1")
            if go_back and call_frame is not None:
                call_frame = call_frame.f_back
                ## DEBUG: trace_frame(call_frame, "call_frame2")
        if call_frame is None:
            raise ValueError("Cannot access the call frame")
        self.output_function(self._format(call_frame, arg_offset, *args, **kwargs))
        
        if not args:
            passthrough = None
        elif len(args) == 1:
            passthrough = args[0]
        else:
            passthrough = args
        return passthrough

    def format(self, *args, arg_offset=0, indirect=False, **kwargs):
        """
        Formats the given arguments and returns the formatted string,
        ignoring the first `arg_offset` arguments
        
        :raises ValueError: If the call frame cannot be accessed
        """
        ## TODO2: add levels_back param (e.g., 2 for gh.assertion)
        # NOTE: this is not separated into a function
        # as to not generate another call frame
        call_frame = inspect.currentframe()
        ## DEBUG: trace_frame(call_frame, "call_frame0")
        if call_frame is not None:
            # note: only go back one frame from this function
            go_back = indirect or (call_frame.f_code.co_name != "format")
            call_frame = call_frame.f_back
            ## DEBUG: trace_frame(call_frame, "call_frame1")
            if go_back and call_frame is not None:
                call_frame = call_frame.f_back
                ## DEBUG: trace_frame(call_frame, "call_frame2")
        if call_frame is None:
            raise ValueError("Cannot access the call frame")
        out = self._format(call_frame, arg_offset, *args, **kwargs)
        return out
    
    def get_context(self, call_frame: FrameType):
        """
        Returns the context of the given call frame
        """
        return self._format_context(call_frame)

    def _format(self, call_frame: FrameType, arg_offset: int, *args, **kwargs):
        """
        Formats the given arguments and returns the formatted string
        """
        
        ## OLD: prefix = pref if (pref := kwargs.get('prefix')) is not None else call_or_value(self.prefix)
        pref = kwargs.get('prefix') or kwargs.get('_prefix')
        prefix = pref if pref is not None else call_or_value(self.prefix)
        ## HACK: uses _prefix kwarg to avoid conflict with positional arg
        kwargs["_prefix"] = prefix

        context = self._format_context(call_frame)
        if self.icecream_like and not args:
            time = self._format_time()
            out = prefix + context + time
        else:
            if not self.include_context:
                context = ""
            out = self._format_args(call_frame, arg_offset, prefix, context, args, **kwargs)

        return out

    def _format_args(self, call_frame, arg_offset, prefix, context, args, **kwargs):
        """
        formats the arguments in `call_frame` with `prefix`,
        ignoring the first `arg_offset` arguments,
        optionally by adding `context` to the output
        """
        ## DEBUG: sys.stderr.write(f"in _format_args: {call_frame=}, {arg_offset=}, {prefix=}, {context=}, {args=}, {kwargs=}\n")
        call_node = Source.executing(call_frame).node
        ## DEBUG: sys.stderr.write(f"call_node: {ast.dump(call_node)}\n")
        if call_node is not None:
            source = Source.for_frame(call_frame)
            # Note: disables mypy error: "EnhancedAST" has no attribute "args" [attr-defined]
            ## DEBUG: sys.stderr.write(f"{call_node=} {call_node.args=} {source=}\n")
            sanitized_arg_strs = [
                source.get_text_with_indentation(arg)
                for arg in call_node.args[arg_offset:]      # type: ignore [attr-defined]
            ]
            ## DEBUG: sys.stderr.write(f"{sanitized_arg_strs=}\n")
        else:
            sys.stderr.write(f"Warning: unable to resolve call node: {args=}\n")
            sanitized_arg_strs = [_absent] * len(args)

        pairs = list(zip(sanitized_arg_strs, args))
        ## OLD: no_eol = kwargs.get('eol', False)
        ## DEBUG: sys.stderr.write(f"{pairs=}\n")

        ## OLD: out = self._construct_argument_output(prefix, context, pairs, no_eol=no_eol, **kwargs)
        out = self._construct_argument_output(prefix, context, pairs, **kwargs)
        return out

    def _construct_argument_output(self, prefix, context, pairs, **kwargs):
        ## OLD: def _construct_argument_output(self, prefix, context, pairs, no_eol=False, **kwargs):
        """
        Constructs the output string from the given pairs of arguments and values,
        """
        def arg_prefix(arg, delim='=') -> str:
            """Return ARG concatenated with DELIM"""
            return f"{arg}{delim}"
        def format_value(val, max_len):
            """Return up to MAX_LEN of VAL text, adding ... if truncated"""
            result = val
            if isinstance(max_len, int) and len(val) > max_len:
                result = val[:max_len + 1] + "..."
            return result

        pairs = [(arg, self.arg_to_string_function(val)) for arg, val in pairs]
        if "max_len" in kwargs:
            pairs = [(arg, format_value(val, kwargs["max_len"]))
                     for (arg, val) in pairs]
        pair_strs = [
            val if (is_literal(arg) or arg is _absent) else (arg_prefix(arg) + val)
            for arg, val in pairs
        ]
        suffix = kwargs.get('suffix', '')
        ## OLD: separator = sep if (sep := kwargs.get('sep')) else self._pairSeparator
        separator = sep if (sep := kwargs.get('delim')) else self._pairSeparator
        all_args_on_one_line = separator.join(pair_strs)
        multiline_args = len(all_args_on_one_line.splitlines()) > 1

        # note: context stuff is relic of icecream
        context_delimiter = self._contextDelimiter if context else ""
        all_pairs = prefix + context + context_delimiter + all_args_on_one_line
        ## BAD: first_line_too_long = len(all_pairs.splitlines()[0]) > self._lineWrapWidth
        first_line_too_long = (len(all_pairs.splitlines()[0]) > self._lineWrapWidth if all_pairs else False)

        if self.icecream_like and (multiline_args or first_line_too_long):
            if context:
                lines = [prefix + context] + [
                    format_pair(len(prefix) * " ", arg, value) for arg, value in pairs
                ]
            else:
                arg_lines = [format_pair("", arg, value) for arg, value in pairs]
                lines = prefix_first_line_indent_remaining(prefix, "\n".join(arg_lines))
        else:
            ## OLD: lines = [prefix + context + context_delimiter + all_args_on_one_line + suffix]
            ## OLD2: lines = "".join((v if v else "") for v in
            ##                       [prefix, context, context_delimiter, all_args_on_one_line, suffix])
            lines = [(v if v else "") for v in
                     [prefix, context, context_delimiter, all_args_on_one_line, suffix]]
        ## DEBUG: sys.stderr.write(f"{prefix=}\n{context=}\n{context_delimiter=}\n{all_args_on_one_line=}\n{suffix=}\n")

        no_eol = kwargs.get('no_eol', False)
        end = "" if no_eol else "\n"
        ## OLD: return end.join(lines)
        return "".join(lines) + end

    def _format_context(self, call_frame: FrameType) -> str:
        """
        Formats the context of the given call frame
        """
        filename, line_number, parent_function = self._get_context(call_frame)

        if parent_function != "<module>":
            parent_function = f"{parent_function}()"

        context = f"{filename}:{line_number} in {parent_function}"
        return context

    def _format_time(self) -> str:
        """
        Formats the current time
        """
        now = datetime.now()
        formatted = now.strftime("%H:%M:%S.%f")[:-3]
        return f" at {formatted}"

    def _get_context(self, call_frame):
        """
        Returns the context of the given call frame
        """
        frame_info = inspect.getframeinfo(call_frame)
        line_number = frame_info.lineno
        parent_function = frame_info.function

        filepath = (realpath if self.context_abs_path else basename)(
            frame_info.filename
        )
        return filepath, line_number, parent_function

#...............................................................................

## OLD:
## # def init():

intro = MezclaDebugger()

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    stderr_print(f"Warning: {basename(__file__)} not intended for direct invocation!")
