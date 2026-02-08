#! /usr/bin/env python3
#
# Convenience class for regex searching, providing simple wrapper around
# static match results.
#
# Note: This provides tracing for commonly used functions (e.g., search and sub),
# with aliasing used for miscellaneous others (e.g., subn).
#
# Example usage:
#
#    from my_regex import my_re
#    ...
#    if (my_re.search(r"^(\d+)\:?(\d*)\s+(\d+)\:?(\d*)\s+\S.*", line)):
#        (start_hours, start_mins, end_hours, end_mins) = my_re.groups()
#................................................................................
# Regex cheatsheet:
#     (?:regex)               non-capturing group
#     (?<!regex)              negative lookbehind
#     (?!regex)               negative lookahead
#     (?=regex)               positive lookahead
#     *?  and  +?             non-greedy match
#
#--------------------------------------------------------------------------------
# TODO:
# - Flesh out cheatsheet
# - Add examples for group(), groups(), etc.
# - Clean up script (e.g., regex => regex_wrapper).
#

"""Wrapper class for regex match results"""

# Standard packages
import re
from typing import Any, AnyStr, List, Match, Optional, Tuple, Union
## TODO: from re import *

# Type alias for str or bytes
StrOrBytes = Union[str, bytes]

# Installed packages
## OLD: import six

# Local packages
from mezcla import debug
from mezcla import system
## DEBUG: debug.trace(4, "my_regex: {__file__}")

# Expose public symbols from re package, plus the wrapper class and global instance
## OLD:
## # Expose public symbols from re package,
## __all__ = re.__all__
## DEBUG: system.print_error("checking SKIP_RE_ALL")
RE_ALL = (not system.getenv_bool("SKIP_RE_ALL", False,
                                 "Don't use re.__all__: for sake of pylint"))
__all__ = ['regex_wrapper', 'my_re']
if RE_ALL:
    ## TODO: __all__ = re.__all__ + ['regex_wrapper', 'my_re']
    __all__ += re.__all__
    pass
else:
    debug.trace(4, "Omitting use of re __all__")

# Environment options
## OLD
## REGEX_TRACE_LEVEL = system.getenv_int("REGEX_TRACE_LEVEL", debug.QUITE_DETAILED,
##                                       "Trace level for my_regex")
REGEX_DEBUG_LEVEL = system.getenv_int(
    "REGEX_DEBUG_LEVEL", debug.QUITE_DETAILED,
    desc="Alias for REGEX_TRACE_LEVEL")
REGEX_TRACE_LEVEL = system.getenv_int(
    "REGEX_TRACE_LEVEL", REGEX_DEBUG_LEVEL,
    desc="Trace level for my_regex")
REGEX_WARNINGS = system.getenv_bool(
    "REGEX_WARNINGS", debug.debugging(debug.USUAL),
    desc="Include warnings about regex's such as f-string")

## TODO # HACK: make sure regex can be used as plug-in replacement 
## from from re import *

## TEST: Attempts to work around Python enum extension limitation
##
## OLD: class regex_wrapper(object):
## HACK: inherit from RegexFlag, so pylint not confused by attrib copying
## NOTE: Maldito python!
##    class regex_wrapper(re.RegexFlag):
##    => TypeError: Cannot extend enumerations
## via https://stackoverflow.com/questions/33679930/how-to-extend-python-enum:
##    Subclassing an enumeration is allowed only if the enumeration does not define any members.
##
##
## HACK2: try via multiple inheritance
##
## class TraceLevel(object):
##     """Simple class with trace level
##     Note: this is just used to work around issue subclassing enums"""
##     # TODO: rework trace level in debug module to be class based
##     TRACE_LEVEL = debug.QUITE_DETAILED
##
## class regex_wrapper(TraceLevel, re.RegexFlag):
##     ...
##
## 
## class MalditoPython(re.RegexFlag):
##     """Just what it says"""
##     pass
##

class regex_wrapper():
    """Wrapper class over re to implement regex search that saves match results
    note: Allows regex to be used directly in conditions"""
    # TODO: IGNORECASE = re.IGNORECASE, etc.
    # import from RE so other methods supported directly (and above constants)
    TRACE_LEVEL = REGEX_TRACE_LEVEL
    ##
    ## Malditos python & pylint!
    ASCII = re.ASCII
    IGNORECASE = re.IGNORECASE
    LOCALE = re.LOCALE
    MULTILINE = re.MULTILINE
    DOTALL = re.DOTALL
    VERBOSE = re.VERBOSE
    UNICODE = re.UNICODE
    # TODO: add miscellaneous re functions (e.g., subn)
    
    # pylint: disable=super-init-not-called
    #
    def __init__(self) -> None:
        debug.trace_fmtd(4, "my_regex.__init__(): self={s}", s=self)
        self.match_result: Optional[Match[Any]] = None
        self.search_text: Optional[StrOrBytes] = None
        # TODO: self.regex = ""

        # HACK: Import attributes from re class
        # TODO3: see if clean way to do this
        # TODO4: find way to disable pylint no-member warning
        try:
            for var in re.__all__:
                if var not in dir(self):
                    debug.trace(9, f"Copying {var} from re into {self}")
                    setattr(self, var, getattr(re, var))
        except:
            system.print_exception_info("__init__ re.* importation")

    def check_pattern(self, regex: AnyStr) -> None:
        """Apply sanity checks to REGEX when debugging
        Note: Added to account for potential missing f-string prefix"""
        debug.trace(self.TRACE_LEVEL + 1, f"check_pattern({regex})")
        debug.reference_var(self)
        # note: checks for variable reference in braces (e.g., "Hi, {name}!")
        ## BAD: check_regex = r"([^{]|^)\{[^0-9][A-Fa-f0-9]*[^{}]+\}([^}]|$)"
        ## ALT: check_regex = r"([^\{]|^)\{([[A-Z][A-Z0-9]*[^\{\}]+)\}([^\}]|$)"
        check_regex = r"([^{]|^){[A-Z][A-Z0-9]*[^{}]+}([^}]|$)"
        if isinstance(regex, bytes):
            ## OLD: regex = regex.encode()
            check_regex = check_regex.encode()
        if REGEX_WARNINGS:
            debug.trace_expr(self.TRACE_LEVEL + 2, check_regex, delim="\n")
            match = re.search(check_regex, regex, flags=re.IGNORECASE)
            if match:
                # Ignore regex operators within f-string replacement
                re_operator_pattern = r"[\*\+\?]"
                if isinstance(match.string, bytes):
                    re_operator_pattern = re_operator_pattern.encode()
                if re.search(re_operator_pattern, match.string):
                    match = None
            if match:
                system.print_error(f"Warning: potentially unresolved f-string in {regex!r} at {match.start(0)}")

    def search(self, regex: AnyStr, text: AnyStr, flags: int = 0, base_trace_level: Optional[int] = None) -> Optional[Match[AnyStr]]:
        """Search for REGEX in TEXT with optional FLAGS and BASE_TRACE_LEVEL (e.g., 6)"""
        ## TODO: rename as match_anywhere for clarity
        if base_trace_level is None:
            base_trace_level = self.TRACE_LEVEL
        debug.trace_fmtd((1 + base_trace_level), "my_regex.search({r!r}, {t!r}, {f}): self={s}",
                         r=regex, t=text, f=flags, s=self, max_len=2048)
        ## OLD: debug.assertion(isinstance(text, six.string_types))
        debug.assertion(isinstance(text, (str, bytes)) and (isinstance(regex, type(text))))
        self.search_text = text
        self.check_pattern(regex)
        self.match_result = re.search(regex, text, flags)
        if self.match_result:
            debug.trace_fmt(base_trace_level, "match: {m!r}; regex: {r!r}", m=self.grouping(), r=regex)
            debug.trace_object(base_trace_level + 1, self.match_result)
        return self.match_result

    def match(self, regex: AnyStr, text: AnyStr, flags: int = 0, base_trace_level: Optional[int] = None) -> Optional[Match[AnyStr]]:
        """Match REGEX to TEXT with optional FLAGS and BASE_TRACE_LEVEL (e.g., 6)"""
        ## TODO: rename as match_start for clarity; add match_all method (wrapper around fullmatch)
        if base_trace_level is None:
            base_trace_level = self.TRACE_LEVEL
        debug.trace_fmtd((1 + base_trace_level), "my_regex.match({r!r}, {t!r}, {f}): self={s}",
                         r=regex, t=text, f=flags, s=self, max_len=2048)
        self.search_text = text
        self.check_pattern(regex)
        self.match_result = re.match(regex, text, flags)
        if self.match_result:
            debug.trace_fmt(base_trace_level, "match: {m!r}; regex: {r!r}", m=self.grouping(), r=regex)
            debug.trace_object(base_trace_level + 1, self.match_result)
        return self.match_result

    def get_match(self) -> Optional[Match[Any]]:
        """Return match result object for last search or match"""
        result = self.match_result
        debug.trace_fmtd(self.TRACE_LEVEL, "my_regex.get_match() => {r!r}: self={s}",
                         r=result, s=self)
        return result

    def group(self, num: int) -> Optional[StrOrBytes]:
        """Return group NUM from match result from last search"""
        debug.assertion(self.match_result)
        result = self.match_result and self.match_result.group(num)
        debug.trace_fmtd(self.TRACE_LEVEL, "my_regex.group({n}) => {r!r}: self={s}",
                         n=num, r=result, s=self)
        return result

    def groups(self) -> Optional[Tuple[StrOrBytes, ...]]:
        """Return all groups in match result from last search"""
        debug.assertion(self.match_result)
        result = self.match_result and self.match_result.groups()
        debug.trace_fmt(self.TRACE_LEVEL, "my_regex.groups() => {r!r}: self={s}",
                        r=result, s=self)
        return result

    def grouping(self) -> Optional[Union[Tuple[StrOrBytes, ...], StrOrBytes]]:
        """Return groups for match result or entire matching string if no groups defined"""
        # Note: this is intended to facilitate debug tracing; see example in search method above
        result = self.match_result and (self.match_result.groups() or self.match_result.group(0))
        debug.trace_fmt(self.TRACE_LEVEL + 1, "my_regex.grouping() => {r!r}: self={s}", r=result, s=self)
        return result

    def start(self, group: int = 0) -> Optional[int]:
        """Start index for GROUP"""
        result = self.match_result and self.match_result.start(group)
        debug.trace_fmt(self.TRACE_LEVEL + 1, "my_regex.start({g}) => {r!r}: self={s}", r=result, s=self, g=group)
        return result

    def end(self, group: int = 0) -> Optional[int]:
        """End index for GROUP"""
        result = self.match_result and self.match_result.end(group)
        debug.trace_fmt(self.TRACE_LEVEL + 1, "my_regex.end({g}) => {r!r}: self={s}", r=result, s=self, g=group)
        return result

    def sub(self, pattern: AnyStr, replacement: AnyStr, string: AnyStr, *, count: int = 0, flags: int = 0) -> AnyStr:
        """Version of re.sub requiring explicit keyword parameters"""
        # Note: Explicit keywords enforced to avoid confusion
        result = re.sub(pattern, replacement, string, count, flags)
        debug.reference_var(self)
        debug.trace(self.TRACE_LEVEL + 1, f"my_regex.sub({pattern!r}, {replacement!r}, {string!r}, [count=[count]], flags={flags}]) => {result!r}\n")
        self.check_pattern(pattern)
        return result

    def span(self, group: int = 0) -> Optional[Tuple[int, int]]:
        """Tuple with GROUP start and end"""
        return (self.match_result and self.match_result.span(group))

    def split(self, pattern: AnyStr, string: AnyStr, maxsplit: int = 0, flags: int = 0) -> List[AnyStr]:
        """Use PATTERN to split STRING, optionally up to MAXSPLIT with FLAGS"""
        result = re.split(pattern, string, maxsplit, flags)
        debug.trace_fmt(self.TRACE_LEVEL, "split{args} => {r!r}",
                        args=tuple([pattern, string, maxsplit, flags]), r=result, max_len=2048)
        return result
    
    def findall(self, pattern: AnyStr, string: AnyStr, flags: int = 0) -> List[AnyStr]:
        """Use PATTERN to find all matches in STRING, optionally with specified FLAGS"""
        # Note: Docstring says "split" but method does findall (returns list of matches)
        result = re.findall(pattern, string, flags)
        debug.trace_fmt(self.TRACE_LEVEL, "findall{args} => {r!r}",
                        args=tuple([pattern, string, flags]), r=result, max_len=2048)
        return result

    def escape(self, text: AnyStr) -> AnyStr:
        """Escape special characters in TEXT"""
        ## TODO3: make static method
        result = re.escape(text)
        debug.trace(self.TRACE_LEVEL + 1, f"escape({text!r}) => {result!r}")
        return result

    def pre_match(self) -> Optional[StrOrBytes]:
        """Text preceding the match or None if not defined"""
        result: Optional[StrOrBytes] = None
        if self.match_result:
            start = 0
            end = self.match_result.span(0)[0]
            result = self.search_text[start: end]
        debug.trace(self.TRACE_LEVEL, f"pre_match() => {result!r}")
        return result
    
    def post_match(self) -> Optional[StrOrBytes]:
        """Text following the match or None if not defined"""
        result: Optional[StrOrBytes] = None
        if self.match_result:
            start = self.match_result.span(0)[1]
            end = len(self.search_text)
            result = self.search_text[start: end]
        debug.trace(self.TRACE_LEVEL, f"post_match() => {result!r}")
        return result

    def compile(self, pattern, flags=0):
        """Compile a regular expression PATTERN using FLAGS, returning a Pattern object."""
        return re.compile(pattern, flags)

    ## Note: Placeholder for other methods (n.b., to avoid silly errors like forgetting self)
    ##
    ## def TODO(self, ...):
    ##     """TODO: docstring"""
    ##     return re.TODO(...)

#...............................................................................
# Initialization
#
# note: creates global instance for convenience (and backward compatibility)

my_re = regex_wrapper()

if __name__ == '__main__':
    system.print_error("Warning: not intended for command-line use")
    ## Note: truth in advertising:
    ## debug.trace(4, f"mp: {MalditoPython()}")
