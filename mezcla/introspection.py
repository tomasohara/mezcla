#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
module for introspection of arguments and source code
"""

# Standard packages
import sys
from datetime import datetime
import inspect
import ast
from os.path import basename, realpath
from types import FrameType


# Local packages

# Installed packages
import pprint
from textwrap import dedent
import executing


_absent = object()


def stderr_print(*args):
    """
    prints args to sys.stderr
    """
    print(*args, file=sys.stderr)


def is_literal(s):
    """
    Returns wether argument is a literal or not
    """
    try:
        ast.literal_eval(s)
    except Exception:
        return False
    return True


DEFAULT_LINE_WRAP_WIDTH = 70  # Characters.
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

    def get_text_with_indentation(self, node):
        """
        Retrieves the text representation of the given AST node, preserving its indentation.
        """
        result = self.asttokens().get_text(node)
        if "\n" in result:
            result = " " * node.first_token.start[1] + result
            result = dedent(result)
        result = result.strip()
        return result


def prefix_lines(prefix: str, s: str, start_at_line=0):
    """
    Separates every word in a string,
    adds a prefix and returns them as a list
    """
    lines = s.splitlines()

    for i in range(start_at_line, len(lines)):
        lines[i] = prefix + lines[i]

    return lines


def prefix_first_line_indent_remaining(prefix: str, s):
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


class MezclaDebugger:
    """
    A class used to provide debugging functionality with formatted output.

    Methods:
    -------
    format(self, *args, arg_offset=0)
        Formats the given arguments and returns the formatted string
    """

    _pairSeparator = ";"
    _lineWrapWidth = DEFAULT_LINE_WRAP_WIDTH
    _contextDelimiter = DEFAULT_CONTEXT_DELIMITER

    def __init__(
        self,
        prefix="",
        output_function=DEFAULT_OUTPUT_FUNCTION,
        arg_to_string_function=argument_to_string,
        include_context=False,
        context_abs_path=False
    ):
        self.enabled = True
        self.prefix = prefix
        self.include_context = include_context
        self.output_function = output_function
        self.arg_to_string_function = arg_to_string_function
        self.context_abs_path = context_abs_path

    def __call__(self, *args, arg_offset=0):
        """
        Formats the given arguments and prints the formatted string
        
        :raises ValueError: If the call frame cannot be accessed
        """
        # NOTE: this is not separated into a function
        # as to not generate another call frame
        call_frame = inspect.currentframe() 
        if call_frame is not None:
            call_frame = call_frame.f_back
            if call_frame is not None:
                call_frame = call_frame.f_back
        if call_frame is None:
            raise ValueError("Cannot access the call frame")
        self.output_function(self._format(call_frame, arg_offset, *args))
        
        if not args:
            passthrough = None
        elif len(args) == 1:
            passthrough = args[0]
        else:
            passthrough = args
        return passthrough

    def format(self, *args, arg_offset=0, **kwargs):
        """
        Formats the given arguments and returns the formatted string,
        ignoring the first `arg_offset` arguments
        
        :raises ValueError: If the call frame cannot be accessed
        """
        # NOTE: this is not separated into a function
        # as to not generate another call frame
        call_frame = inspect.currentframe()
        if call_frame is not None:
            call_frame = call_frame.f_back
            if call_frame is not None:
                call_frame = call_frame.f_back
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
        
        prefix = pref if (pref := kwargs.get('prefix')) is not None else call_or_value(self.prefix)

        context = self._format_context(call_frame)
        if not args:
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
        call_node = Source.executing(call_frame).node
        if call_node is not None:
            source = Source.for_frame(call_frame)
            sanitized_arg_strs = [
                source.get_text_with_indentation(arg)
                for arg in call_node.args[arg_offset:]
            ]
        else:
            sanitized_arg_strs = [_absent] * len(args)

        pairs = list(zip(sanitized_arg_strs, args))
        no_eol = kwargs.get('eol', False)

        out = self._construct_argument_output(prefix, context, pairs, no_eol=no_eol, **kwargs)
        return out

    def _construct_argument_output(self, prefix, context, pairs, no_eol=False, **kwargs):
        """
        Constructs the output string from the given pairs of arguments and values,
        """
        def arg_prefix(arg, delim='=') -> str:
            return f"{arg}{delim}"

        pairs = [(arg, self.arg_to_string_function(val)) for arg, val in pairs]
        pair_strs = [
            val if (is_literal(arg) or arg is _absent) else (arg_prefix(arg) + val)
            for arg, val in pairs
        ]
        suffix = kwargs.get('suffix', '')
        separator = sep if (sep := kwargs.get('sep')) else self._pairSeparator
        all_args_on_one_line = separator.join(pair_strs)
        multiline_args = len(all_args_on_one_line.splitlines()) > 1

        context_delimiter = self._contextDelimiter if context else ""
        all_pairs = prefix + context + context_delimiter + all_args_on_one_line
        first_line_too_long = len(all_pairs.splitlines()[0]) > self._lineWrapWidth

        if multiline_args or first_line_too_long:
            if context:
                lines = [prefix + context] + [
                    format_pair(len(prefix) * " ", arg, value) for arg, value in pairs
                ]
            else:
                arg_lines = [format_pair("", arg, value) for arg, value in pairs]
                lines = prefix_first_line_indent_remaining(prefix, "\n".join(arg_lines))
        else:
            lines = [prefix + context + context_delimiter + all_args_on_one_line + suffix]

        end = "" if no_eol else "\n"
        return end.join(lines)

    def _format_context(self, call_frame:FrameType) -> str:
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

# def init():
    

intro = MezclaDebugger()
