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
OptStr = Optional[str]
OptInt = Optional[int]
OptFloat = Optional[float]
OptBool = Optional[bool]
StrOrBytes = Union[str, bytes]
OptStrOrBytes = Optional[StrOrBytes]
OptBoolOrStr = Optional[Union[bool, str]]
OptCallable = Optional[Callable]
OptDict = Optional[Dict]
StrList = List[str]
OptStrList = Optional[StrList]
