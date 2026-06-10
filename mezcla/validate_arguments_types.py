# Common types used in multiple modules
#
# These types are the same as those used in builtins.pyi,
# but we need to copy them here because they are protected
# and cannot be imported directly.
#
# We need to separate the types used in several functions
# in this module to avoid circular imports.

# TODO: reduce redundancy
"""
Common types used in multiple modules

These types are the same as those used in builtins.pyi,
but we need to copy them here because they are protected
and cannot be imported directly.

We need to separate the types used in several functions
in this module to avoid circular imports.
"""

from os import PathLike
from types import TracebackType
from typing import Union, Tuple, Optional, List, Dict, Callable

# Types
StrOrBytesPath = Union[str, bytes, PathLike]  # stable
FileDescriptorOrPath = Union[int, StrOrBytesPath]
ExcInfo = Tuple[BaseException, TracebackType]
OptExcInfo = Union[ExcInfo, Tuple[None, None, None]]

# General-purpose optional/disjunctive aliases
## NOTE: Added so that modules can avoid repeating Union[..., None] and
# similar disjunctions inline (see "TODO: reduce redundancy" above).
OptStr = Optional[str]                         # stable
OptInt = Optional[int]                         # stable
OptFloat = Optional[float]                     # stable
OptBool = Optional[bool]                       # stable
StrOrBytes = Union[str, bytes]                 # stable
OptStrOrBytes = Optional[StrOrBytes]           # stable
OptBoolOrStr = Optional[Union[bool, str]]      # stable
OptCallable = Optional[Callable]               # stable
OptDict = Optional[Dict]                       # stable
StrList = List[str]                            # stable
OptStrList = Optional[StrList]                 # stable
