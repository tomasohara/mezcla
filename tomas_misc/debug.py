#! /usr/bin/env python
#
# Functions for debugging, such as console tracing. This is for intended
# for verbose tracing not suitable for the logging facility.
#
# Notes:
# - These are no-op's unless __debug__ is True.
# - Running python with the -O (optimized) option ensures that __debug__ is False.
# - So that other local packages can use tracing freely, this only
#   imports standard packages. In particular, system.py is not imported,
#   so functionality must be reproduced here (e.g., _to_utf8).
# - Gotta hate Pythonista's who prevailed in Python3 breaking lots of Python2
#   code just for the sake of simplicity, a la manera moronista (i.e., only one moronic way to do things)!
# - A few functions from system are re-implemented here without tracing to
#   avoid circular dependencies (e.g., _to_utf8).
#
# TODO:
# - * Add sanity checks for unused environment variables specified on command line (e.g., FUBAR=1 python script.py ...)!
# - Rename as debug_utils so clear that non-standard package.
# - Add exception handling throughout (e.g., more in trace_object).
#
#

"""Debugging functions (e.g., tracing)"""

## OLD: if sys.version_info.major == 2:
## OLD:    from __future__ import print_function
from __future__ import print_function

# Standard packages
import atexit
from datetime import datetime
import inspect
from itertools import zip_longest
import logging
import os
from pprint import pprint
import re
import six
import sys
import time

# Local packages
# note: The following redefines sys.version_info to be python3 compatible;
# this is used in _to_utf8, which should be reworked via six-based wrappers.
import tomas_misc.sys_version_info_hack      # pylint: disable=unused-import


# Constants for pre-defined tracing levels
ALWAYS = 0
ERROR = 1
WARNING = 2
USUAL = 3
DETAILED = 4
VERBOSE = 5
QUITE_DETAILED = 6
QUITE_VERBOSE = 7
MOST_DETAILED = 8
MOST_VERBOSE = 9

# Other constants
UTF8 = "UTF-8"
STRING_TYPES = six.string_types

if __debug__:    

    # Initialize debug tracing level
    DEBUG_LEVEL_LABEL = "DEBUG_LEVEL"
    trace_level = 1
    output_timestamps = False           # prefix output with timestamp
    use_logging = False                 # traces via logging (and stderr)
    debug_file = None                   # file for log output
    #
    try:
        trace_level = int(os.environ.get(DEBUG_LEVEL_LABEL, trace_level))
    except:
        sys.stderr.write("Warning: Unable to set tracing level from {v}: {exc}\n".
                         format(v=DEBUG_LEVEL_LABEL, exc=sys.exc_info()))


    def set_level(level):
        """Set new trace level"""
        global trace_level
        trace_level = level
        return


    def get_level():
        """Get current tracing level"""
        ## global trace_level
        return trace_level


    def get_output_timestamps():
        """Return whether outputting timestamps"""
        return output_timestamps


    def set_output_timestamps(do_output_timestamps):
        """Enable for disable the outputting of timestamps"""
        global output_timestamps
        output_timestamps = do_output_timestamps


    def _to_utf8(text):
        """Convert TEXT to UTF-8 (e.g., for I/O)"""
        # Note: version like one from system.py to avoid circular dependency
        result = text
        if ((sys.version_info.major < 3) and (isinstance(text, unicode))):  # pylint: disable=undefined-variable
            result = result.encode("UTF-8", 'ignore')
        return result


    def _to_unicode(text, encoding=None):
        """Ensure TEXT in ENCODING is Unicode, such as from the default UTF8"""
        # TODO: rework from_utf8 in terms of this
        if not encoding:
            encoding = UTF8
        result = text
        if ((sys.version_info.major < 3) and (not isinstance(result, unicode))): # pylint: disable=undefined-variable
            result = result.decode(encoding, 'ignore')
        return result


    def _to_string(text):
        """Ensure TEXT is a string type"""
        result = text
        if (not isinstance(result, STRING_TYPES)):
            # Values are coerced using % operator for proper Unicode handling,
            # except for tuples which are converted recursively. This avoids a
            # type error due to arguments not being converted (e.g., second 
            # tuple constituent, etc.), as in ("%s" % (9, 1)).
            if isinstance(result, tuple):
                result = "(" + ", ".join([_to_string(v) for v in result]) + ")"
            else:
                result = "%s" % result
        return result

    
    def trace(level, text):
        """Print TEXT if at trace LEVEL or higher, including newline"""
        # Note: trace should not be used with text that gets formatted to avoid
        # subtle errors
        ## DEBUG: sys.stderr.write("trace({l}, {t})\n".format(l=level, t=text))
        if (trace_level >= level):
            # Prefix trace with timestamp w/o date
            if output_timestamps:
                # Get time-proper from timestamp (TODO: find standard way to do this)
                timestamp_time = re.sub(r"^\d+-\d+-\d+\s*", "", timestamp())

                print("[" + timestamp_time + "]", end=": ", file=sys.stderr)
                if debug_file:
                    print("[" + timestamp_time + "]", end=": ", file=debug_file)
            # Print trace, converted to UTF8 if necessary (Python2 only)
            # TODO: add version of assertion that doesn't use trace or trace_fmtd
            ## TODO: assertion(not(re.search(r"{\S*}", text)))
            print(_to_utf8(text), file=sys.stderr)
            if use_logging:
                logging.debug(_to_utf8(text))
            if debug_file:
                print(_to_utf8(text), file=debug_file)
        return


    def trace_fmtd(level, text, **kwargs):
        """Print TEXT with formatting using optional format KWARGS if at trace LEVEL or higher, including newline"""
        # Note: To avoid interpolated text as being interpreted as variable
        # references, this function does the formatting.
        # TODO: weed out calls that use (level, text.format(...)) rather than (level, text, ...)
        if (trace_level >= level):
            try:
                try:
                    # TODO: add version of assertion that doesn't use trace or trace_fmtd
                    ## TODO: assertion(re.search(r"{\S*}", text))
                    ## OLD: assertion("{" in text)
                    ## OLD: trace(level, text.format(**kwargs))
                    kwargs_unicode = {k: _to_unicode(_to_string(v)) for (k, v) in list(kwargs.items())}
                    trace(level, _to_unicode(text).format(**kwargs_unicode))
                except(KeyError, ValueError, UnicodeEncodeError):
                    raise_exception(max(VERBOSE, level + 1))
                    sys.stderr.write("Warning: Problem in trace_fmtd: {exc}\n".
                                     format(exc=sys.exc_info()))
                    # Show arguments so trace contents recoverable
                    sys.stderr.write("   text=%r\n" % _to_utf8(clip_value(text)))
                    ## OLD: kwargs_spec = ", ".join(("%s:%r" % (k, clip_value(v))) for (k, v) in kwargs.iteritems())
                    kwargs_spec = ", ".join(("%s:%r" % (k, clip_value(v))) for (k, v) in list(kwargs.items()))
                    sys.stderr.write("   kwargs=%s\n" % _to_utf8(kwargs_spec))
            except(AttributeError):
                # Note: This can occur when profile_function set
                raise_exception(max(VERBOSE, level + 1))
                sys.stderr.write("Error: Unexpected problem in trace_fmtd: {exc}\n".
                                 format(exc=sys.exc_info()))
        return


    STANDARD_TYPES = (int, float, dict, list)
    #
    MAX_OBJECT_VALUE_LEN = 128
    #
    def trace_object(level, obj, label=None, show_all=False, indentation=None, pretty_print=None):
        """Trace out OBJ's members to stderr if at trace LEVEL or higher"""
        # HACK: Members for STANDARD_TYPES omitted unless show_all.
        # Note: This is intended for arbitrary objects, use trace_values for objects known to be lists or hashes.
        # See https://stackoverflow.com/questions/383944/what-is-a-python-equivalent-of-phps-var-dump.
        # TODO: support recursive trace; specialize show_all into show_private and show_methods
        ## OLD: print("{stmt} < {current}: {r}".format(stmt=level, current=trace_level,
        ##                                       r=(trace_level < level)))
        trace_fmt(10, "trace_object({dl}, {obj}, label={lbl}, show_all={sa}, indent={ind}, pretty={pp})",
                  dl=level, obj=object, lbl=label, sa=show_all, ind=indentation, pp=pretty_print)
        if (pretty_print is None):
            pretty_print = (trace_level >= 6)
        if (trace_level < level):
            return
        type_id_label = str(type(obj)) + " " + hex(id(obj))
        if label is None:
            ## BAD: label = str(type(obj)) + " " + hex(hash(obj))
            ## OLD: label = str(type(obj)) + " " + hex(id(obj))
            label = type_id_label
        elif verbose_debugging():
            label += " [" + type_id_label + "]"
        else:
            pass
        if indentation is None:
            indentation = "   "
        trace(0, label + ": {")
        ## OLD: for (member, value) in inspect.getmembers(obj):
        member_info = []
        try:
            member_info = inspect.getmembers(obj)
        except:
            trace_fmtd(7, "Warning: Problem getting member list in trace_object: {exc}",
                       exc=sys.exc_info())
        ## HACK: show standard type value as special member
        if isinstance(obj, STANDARD_TYPES):
            member_info = [("(value)", obj)] + [(("__(" + m + ")__"), v) for (m, v) in member_info]
            trace_fmtd(7, "{ind}Special casing standard type as member {m}",
                       ind=indentation, m=member_info[0][0])
        for (member, value) in member_info:
            # TODO: value = clip_text(value)
            trace_fmtd(8, "{i}{m}={v}; type={t}", i=indentation, m=member, v=value, t=type(value))
            if (trace_level >= 9):
                ## print(indentation + member + ":", value, file=sys.stderr)
                sys.stderr.write(indentation + member + ":")
                if pretty_print:
                    pprint(value, stream=sys.stderr)
                else:
                    sys.stderr.write(value, file=sys.stderr)
                sys.stderr.write("\n")
                if use_logging:
                    logging.debug(_to_utf8((indentation + member + ":" + str(value))))
                continue
            ## TODO: pprint.pprint(member, stream=sys.stderr, indent=4, width=512)
            try:
                try:
                    value_spec = "%s" % ((value),)
                    if (len(value_spec) > MAX_OBJECT_VALUE_LEN):
                        value_spec = value_spec[:MAX_OBJECT_VALUE_LEN] + "..."
                except(TypeError, ValueError):
                    trace_fmtd(7, "Warning: Problem in tracing member {m}: {exc}",
                               m=member, exc=sys.exc_info())
                    value_spec = "__n/a__"
            except(AttributeError):
                # Note: This can occur when profile_function set
                trace_fmtd(7, "Error: unexpected problem in trace_object: {exc}",
                           exc=sys.exc_info())
                value_spec = "__n/a__"
            if (show_all or (not (member.startswith("__") or 
                                  re.search(r"^<.*(method|module|function).*>$", value_spec)))):
                ## trace(0, indentation + member + ": " + value_spec)
                sys.stderr.write(indentation + member + ": ")
                if pretty_print:
                    # TODO: remove quotes from numbers and booleans
                    pprint(value_spec, stream=sys.stderr, indent=len(indentation))
                else:
                    ## sys.stderr.write(value_spec)
                    sys.stderr.write(_to_utf8(value_spec))
                    sys.stderr.write("\n")
                if use_logging:
                    logging.debug(_to_utf8((indentation + member + ":" + value_spec)))
        trace(0, indentation + "}")
        return


    def trace_values(level, collection, label=None, indentation=None):
        """Trace out elements of array or hash COLLECTION if at trace LEVEL or higher"""
        trace_fmt(10, "trace_values(dl, {coll}, label={lbl}, indent={ind})",
                  dl=level, lbl=label, coll=collection, ind=indentation)
        ## OLD: assert(isinstance(collection, (list, dict)))
        if (trace_level < level):
            return
        ## TODO: assertion(isinstance(collection, (list, dict), "Should be a list or dict", skip_trace=True)
        if (not isinstance(collection, (list, dict))):
            trace(level, "Warning: [trace_values] coercing collection into a list")
            collection = list(collection)
        if indentation is None:
            indentation = "   "
        if label is None:
            ## BAD: label = str(type(collection)) + " " + hex(hash(collection))
            label = str(type(collection)) + " " + hex(id(collection))
            indentation = "   "
        trace(0, label + ": {")
        ## OLD: keys_iter = collection.iterkeys() if isinstance(collection, dict) else xrange(len(collection))
        ## OLD2: keys_iter = collection.iterkeys() if isinstance(collection, dict) else range(len(collection))
        keys_iter = list(collection.keys()) if isinstance(collection, dict) else range(len(collection))
        ## NOTE: Gotta hate python3 for dropping xrange [la manera moronista!]
        for k in keys_iter:
            try:
                trace_fmtd(0, "{ind}{k}: {v}", ind=indentation, k=k,
                           v=_to_utf8(collection[k]))
            except:
                trace_fmtd(7, "Warning: Problem tracing item {k}",
                           k=_to_utf8(k), exc=sys.exc_info())
        trace(0, indentation + "}")
        return


    def trace_expr(level, *values, sep=None):
        """Trace each of the arguments, using introspection to derive label for expression;
        Notes:
        - For simplicity, the values are separated by ', ' (or SEP).
        - See misc_utils.trace_named_objects for similar function taking string input, which is more general but harder to use and maintain"""
        trace_fmt(10, "trace_expr({l}, args={args}, sep={s})",
                  l=level, args=values, s=sep)
        # Get symbolic expressions for the values
        # TODO: handle cases split across lines
        if sep is None:
            sep = ", "
        try:
            # TODO: rework introspection following icecream (e.g., using abstract syntax tree)
            caller = inspect.stack()[1]
            (_frame, filename, line_number, _function, _context, _index) = caller
            statement = read_line(filename, line_number).strip()
            # Extract list of argument expressions
            statement = re.sub(r"#.*$", "", statement)
            statement = re.sub(r"^\s*\S*trace_expr\s*\(", "", statement)
            ## OLD: statement = re.sub(r"^\s*\d+,\s*", "", statement)
            statement = re.sub(r"\);?\s*$", "", statement)
            # Skip first argument (level)
            expressions = statement.split(sep)[1:]
        except:
            trace_fmtd(0, "Exception isolating expression in trace_vals: {exc}",
                       exc=sys.exc_info())
            expressions = []
        for expression, value in zip_longest(expressions, values):
            assertion(not (value and expression is None), "Warning: Likely problem resolving expression text (try reworking trace_expr call)")
            trace_fmt(level, "{expr}={val}", expr=expression, val=value)
        return

    
    def trace_current_context(level=QUITE_DETAILED, label=None, 
                              show_methods_etc=False):
        """Traces out current context (local and global variables), with output
        prefixed by "LABEL context" (e.g., "current context: {\nglobals: ...}").
        Notes: By default the debugging level must be quite-detailed (6).
        If the debugging level is higher, the entire stack frame is traced.
        Also, methods are omitted by default."""
        frame = None
        if label is None:
            label = "current"
        try:
            frame = inspect.currentframe().f_back
        except (AttributeError, KeyError, ValueError):
            trace_fmt(5, "Exception during trace_current_context: {exc}",
                      exc=sys.exc_info())
        trace_fmt(level, "{label} context: {{", label=label)
        prefix = "    "
        if (get_level() - level) > 1:
            trace_object((level + 2), frame, "frame", indentation=prefix,
                         show_all=show_methods_etc)
        else:
            trace_fmt(level, "frame = {f}", f=frame)
            if frame:
                trace_object(level, frame.f_globals, "globals", indentation=prefix,
                             show_all=show_methods_etc)
                trace_object(level, frame.f_locals, "locals", indentation=prefix,
                             show_all=show_methods_etc)
        trace(level, "}")
        return


    ## TODO
    ## def trace_stack(level=VERBOSE):
    ##     """Output stack trace to stderr (if at trace LEVEL or higher)"""
    ##     system.print_full_stack()
    ##     return

    
    def raise_exception(level=1):
        """Raise an exception if debugging (at specified trace LEVEL)"""
        # Note: For producing full stacktrace in except clause when debugging.
        # TODO: elaborate
        if __debug__ and (level <= trace_level):
            raise                       # pylint: disable=misplaced-bare-raise
        return


    ## OLD: def assertion(expression):
    def assertion(expression, message=None):
        """Issue warning if EXPRESSION doesn't hold, along with optional MESSAGE"""
        ## TODO: have streamlined version using sys.write that can be used for trace and trace_fmtd sanity checks about {}'s
        # EX: assertion((2 + 2) != 5)
        if (not expression):
            try:
                # Get source information for failed assertion
                trace_fmtd(9, "Call stack: {st}", st=inspect.stack())
                caller = inspect.stack()[1]
                (_frame, filename, line_number, _function, _context, _index) = caller
                # Read statement in file and extract assertion expression
                # TODO: handle #'s in statement proper (e.g., assertion("#" in text))
                statement = read_line(filename, line_number).strip()
                statement = re.sub("#.*$", "", statement)
                statement = re.sub(r"^(\S*)assertion\(", "", statement)
                expression = re.sub(r"\);?\s*$", "", statement)
                qualification_spec = (": " + message) if message else ""
                # Output information
                trace_fmtd(0, "Assertion failed: {expr} (at {file}:{line}){qual}",
                           expr=expression, file=filename, line=line_number, qual=qualification_spec)
            except:
                trace_fmtd(0, "Exception formatting assertion: {exc}",
                           exc=sys.exc_info())
                trace_object(0, inspect.currentframe(), "caller frame", pretty_print=True)
        return

else:

    def non_debug_stub(*_args, **_kwargs):
        """Non-debug stub"""
        return


    def get_level():
        """Returns tracing level (i.e., 0)"""
        return 0


    def get_output_timestamps():
        """Non-debug stub"""
        return False


    set_output_timestamps = non_debug_stub

    trace = non_debug_stub

    trace_fmtd = non_debug_stub

    trace_object = non_debug_stub

    trace_values = non_debug_stub
    
    trace_expr = non_debug_stub
    
    trace_current_context = non_debug_stub
   
    raise_exception = non_debug_stub
    
    assertion = non_debug_stub

    
# note: adding alias for trace_fmtd to account for common typo
# TODO: alias trace to trace_fmt as well (add something like trace_out if format not desired)
trace_fmt = trace_fmtd

def debug_print(text, level):
    """Wrapper around trace() for backward compatibility
    Note: debug_print will soon be deprecated."""
    return trace(level, text)


def timestamp():
    """Return timestamp for use in logging, etc."""
    return (str(datetime.now()))
    

## OLD: def debugging(level=ERROR):
def debugging(level=USUAL):
    """Whether debugging at specified trace LEVEL (e.g., 3 for usual)"""
    ## BAD: """Whether debugging at specified trace level, which defaults to {l}""".format(l=ERROR)
    ## NOTE: Gotta hate python/pylint (no warning about docstring)
    ## TODO: use level=WARNING (i.e., 2)
    return (get_level() >= level)


def detailed_debugging():
    """Whether debugging with trace level DETAILED (4) or higher"""
    ## BAD: """Whether debugging with trace level at or above {l}""".format(l=DETAILED)
    return (get_level() >= DETAILED)


def verbose_debugging():
    """Whether debugging with trace level VERBOSE (5) or higher"""
    ## BAD: """Whether debugging with trace level at or above {l}""".format(l=VERBOSE)
    return (get_level() >= VERBOSE)


def _getenv_bool(name, default_value):
    """Version of debug.getenv_bool w/o tracing"""
    result = default_value
    if (str(os.environ.get(name) or default_value).upper() in ["1", "TRUE"]):
        result = True
    return result


def xor(value1, value2):
    """Whether VALUE1 and VALUE2 differ when interpretted as booleans"""
    # Note: Used to clarify assertions; same as bool(value1) != bool(value2).
    # See https://stackoverflow.com/questions/432842/how-do-you-get-the-logical-xor-of-two-variables-in-python
    # EX: not(xor(0, 0.0))
    result = (bool(value1) ^ bool(value2))
    trace_fmt(7, "xor({v1}, {v2}) => {r}", v1=value1, v2=value2, r=result)
    return result


def xor3(value1, value2, value3):
    """Whether one and only one of VALUE1, VALUE2, and VALUE3 are true"""
    ## result = (xor(value1, xor(value2m value3))
    ##           and not (bool(value1) and bool(value2) and bool(value3)))
    num_true = sum([int(bool(v)) for v in [value1, value2, value3]])
    result = (num_true == 1)
    trace_fmt(7, "xor3({v1}, {v2}, {v3}) => {r}",
              v1=value1, v2=value2, v3=value3, r=result)
    return result


def init_logging():
    """Enable logging with INFO level by default or with DEBUG if detailed debugging"""
    trace(4, "init_logging()")
    trace_object(6, logging.root, "logging.root")

    # Set the level for the current module
    # TODO: use mapping from symbolic LEVEL user option (e.g., via getenv)
    level = logging.DEBUG if detailed_debugging() else logging.INFO
    trace_fmt(5, "Setting logger level to {ll}", ll=level)
    logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=level)
    logging.debug("init_logging()")

    # Optionally make sure logging level applied globally
    if _getenv_bool("GLOBAL_LOGGING", False):
        old_level = logging.root.level
        trace_fmt(5, "Setting root logger level from {ol} to {nl}", ol=old_level, nl=level)
        logging.root.setLevel(level)
    return


def _print_exception_info(task):
    """Output exception information to stderr regarding TASK (e.g., function)"""
    # Note: version of system.print_exception_info
    sys.stderr.write("Error during {t}: {exc}\n".
                     format(t=task, exc=sys.exc_info()))
    return


def profile_function(frame, event, arg):
    """Function for monitoring function entry and exit (FEE), etc., currently just tracing at level 4. See sys.setprofile.
    # Note: Use a package like viztracer for non-trivial monitoring"""
    # Based on dependency-checking code in PyTorch. See
    #   https://fossies.org/linux/pytorch/torch/package/analyze/trace_dependencies.py.
    # This tries to determine the name of the module that the function is in:
    # 1) Check the global namespace of the frame.
    # 2) Check the local namespace of the frame.
    # 3) To handle class instance method calls, check the attribute named 'name'
    #    of the object in the local namespace corresponding to "self".
    # TODO:
    # - Make tracing level an option (e.g., environment).
    trace_fmt(6, "profile_function(_, {e}, {a})", e=event, a=arg)
    trace_object(7, frame, "frame")

    # Resolve the names for the function (callable) and module
    name = "???"
    module = "???"
    try:
        name = frame.f_code.co_name
        if name in frame.f_globals:
            module = frame.f_globals[name].__module__
        elif name in frame.f_locals:
            module = frame.f_locals[name].__module__
        elif "self" in frame.f_locals:
            method = getattr(frame.f_locals["self"], name, None)
            module = method.__module__ if method else None
        else:
            trace(7, "Unable to resolve module")
    except:
        _print_exception_info("profile_function")

    # Trace out the call (with other information at higher tracing levels)
    if event.endswith("call"):
        trace_fmt(4, "in: {mod}:{func}({a})", mod=module, func=name, a=arg)
    elif event.endswith("return"):
        trace_fmt(4, "out: {mod}:{func} => {a}", mod=module, func=name, a=arg)
    else:
        trace_fmt(5, "profile {mod}:{func} {e}: arg={a}",
                  mod=module, func=name, e=event, a=arg)
    return
    
#-------------------------------------------------------------------------------
# Utility functions useful for debugging (e.g., for trace output)

# TODO: CLIPPED_MAX = system-ish.getenv_int("CLIPPED_MAX", 132)
CLIPPED_MAX = 132
#
def clip_value(value, max_len=CLIPPED_MAX):
    """Return clipped version of VALUE (e.g., first MAX_LEN chars)"""
    # TODO: omit conversion to text if already text [DUH!]
    clipped = "%s" % value
    if (len(clipped) > max_len):
        clipped = clipped[:max_len] + "..."
    return clipped

def read_line(filename, line_number):
    """Returns contents of FILENAME at LINE_NUMBER"""
    # ex: "debugging" in read_line(os.path.join(os.getcwd(), "debug.py"), 3)
    try:
        file_handle = open(filename)
        line_contents = (list(file_handle))[line_number - 1]
        file_handle.close()
    except:
        line_contents = "???"
    return line_contents

#-------------------------------------------------------------------------------

def main(args):
    """Supporting code for command-line processing"""
    trace_expr(4, len(args))
    trace(1, "Warning: Not intended for direct invocation. A simple tracing example follows.")
    #
    trace(0, "date record for now at trace level 1")
    trace_object(1, datetime.now(), label="now")
    #
    # Make sure trace_expr traces at proper tracing level
    trace(0, "level=N         for N from 0..trace_level ({l})".
          format(l=trace_level))
    for level in range(trace_level):
        level_value = level
        trace_expr(level, level_value)
    #
    # Maker sure trace_expr gets all arguments
    trace(0, "n-i=N-i         for N=trace_level ({l}) and i from 1..-1".format(l=trace_level))
    n = trace_level
    i = 1
    ## TODO: for i in range(3, 0, -1):
    trace_expr(1, n+i, n, n+i)
    return

# Do debug-only processing (n.b., for when PYTHONOPTIMIZE not set)
# Note: wrapped in function to keep things clean

if __debug__:

    def debug_init():
        """Debug-only initialization"""
        time_start = time.time()
        trace(4, "in debug_init()")

        # Open external file for copy of trace output
        global debug_file
        debug_filename = os.getenv("DEBUG_FILE")
        if debug_filename is not None:
            debug_file = open(debug_filename, mode="w", encoding="UTF-8")
        
        # Determine whether tracing include time and date
        global output_timestamps
        ## OLD
        ## output_timestamps = (str(os.environ.get("OUTPUT_DEBUG_TIMESTAMPS", False)).upper()
        ##                      in ["1", "TRUE"])
        output_timestamps = _getenv_bool("OUTPUT_DEBUG_TIMESTAMPS", False)
    
        # Show startup time and tracing info
        module_file = __file__
        trace_fmtd(3, "[{f}] loaded at {t}", f=module_file, t=timestamp())
        trace_fmtd(4, "trace_level={l}; output_timestamps={ots}", l=trace_level, ots=output_timestamps)
        trace_fmtd(5, "debug_filename={fn} debug_file={f}",
                   fn=debug_filename, f=debug_file)

        # Show additional information when detailed debugging
        # TODO: sort keys to facilate comparisons of log files
        trace_values(5, dict(os.environ), "environment")

        global use_logging
        use_logging = _getenv_bool("USE_LOGGING", use_logging)
        enable_logging = _getenv_bool("ENABLE_LOGGING", use_logging)
        if enable_logging:
            init_logging()
        monitor_functions = _getenv_bool("MONITOR_FUNCTIONS", False)
        if monitor_functions:
            sys.setprofile(profile_function)

        # Register to show shuttdown time and elapsed seconds
        # TODO: rename to reflect generic-exit nature
        def display_ending_time_etc():
            """Display ending time information"""
            elapsed = round(time.time() - time_start, 3)
            trace_fmtd(4, "[{f}] unloaded at {t}; elapsed={e}s",
                       f=module_file, t=timestamp(), e=elapsed)
            if monitor_functions:
                sys.setprofile(None)
            global debug_file
            if debug_file:
                debug_file.close()
                debug_file = None
        atexit.register(display_ending_time_etc)
        
        return

    
    # Do the initialization
    debug_init()

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    main(sys.argv)
else:
    trace_expr(9, 999)
