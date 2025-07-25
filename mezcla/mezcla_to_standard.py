#! /usr/bin/env python3
#
# Mezcla to Standard call conversion script
#
# This is a 2to3-like tool for converting scripts using mezcla packages into
# ones based mainly on the Python standard library (PSL) packages. For example,
# calls to file access wrappers are replaced with the os.path equivalent.
# In addition, calls to debug.trace, etc. are replaced with logging statements.
#
# As with 2to3, the goal is achieve the bulk of the transformations needed,
# with warnings indicating cases not supported. The transformations are just
# based on static code analysis, so it is not guaranteed to produce equivalent
# code. The test set includes before and after comparisons using pytest and
# other checks, which can be adapted to testing non-repo scripts.
#
# Not all mezcla packages are supported. For example, this won't convert usages
# of main.py's Script class. Likewise, unit tests with unittest_wrapper.py
# won't be modified. In addition, the focus is on system.py and glue_helpers.py,
# which have the majority of thin wrappers around PSL calls. The debugging
# support in debug.py is also included as a bit idiosyncratic.
#
# TODO4: Try to create a table covering more of system.py and glue_helper.py.
#
# --------------------------------------------------------------------------------
# Sample input and output:
#
# - input
#
#   """Simple file manipulation"""
#   from mezcla import glue_helpers as gh
#   system.write_file("/tmp/fubar.list", ["line1", "line2"])
#   gh.copy_file("/tmp/fubar.list", "/tmp/fubar.list1")
#   gh.delete_file("/tmp/fubar.list")
#   gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")
#   print(gh.form_path("/tmp", "fubar"))
#
# - output
#
#   """Simple file manipulation"""
#   import os
#   from mezcla import glue_helpers as gh
#   # WARNING not supported: system.write_file("/tmp/fubar.list", ["line1", "line2"])
#   # WARNING not supported: gh.copy_file("/tmp/fubar.list", "/tmp/fubar.list1")
#   os.remove("/tmp/fubar.list")
#   os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
#   print(os.path.join("/tmp", "fubar"))
#
#--------------------------------------------------------------------------------
# Note:
# - This uses libCST which in turn is based on Python AST's; see
#   -- https://libcst.readthedocs.io: compromise between an Abstract Syntax Tree (AST)
#      and a traditional Concrete Syntax Tree (CST)
#   -- https://greentreesnakes.readthedocs.io: "field guide" for working with ASTs
# - By the way, lib2to3 is a CST used in Black, see following:
#   https://libcst.readthedocs.io/en/latest/why_libcst.html
# - The code is still very much work in progress.
# --------------------------------------------------------------------------------
# Example illustrating the transformations being made
#
# - Original code
#
#   from mezcla import glue_helpers as gh
#   gh.form_path("/tmp", "fubar")
#
# - The original code is parsed into the following libCST simplified tree
#
#   Module(
#       body=[
#           SimpleStatementLine(
#               body=[
#                   ImportFrom(
#                      module=Name(
#                         value='mezcla',
#                       ),
#                       names=[
#                           ImportAlias(
#                               name=Name(
#                                   value='glue_helpers',
#                               ),
#                               asname=AsName(
#                                   name=Name(
#                                       value='gh',
#                                   ),
#                               ),
#                           ),
#                       ],
#                   ),
#               ],
#           ),
#           SimpleStatementLine(
#               body=[
#                   Expr(
#                       value=Call(
#                           func=Attribute(
#                               value=Name(
#                                   value='gh',
#                               ),
#                               attr=Name(
#                                   value='form_path',
#                               ),
#                           ),
#                           args=[
#                               Arg(
#                                   value=SimpleString(
#                                       value='"/tmp"',
#                                   ),
#                               ),
#                               Arg(
#                                   value=SimpleString(
#                                       value='"fubar"',
#                                   ),
#                               ),
#                           ],
#                       ),
#                   ),
#               ],
#           ),
#       ],
#   )
#
# - Then is transformed into the following libCST simplified tree
#
#    Module(
#       body=[
#           SimpleStatementLine(
#               body=[
#                   Import(
#                       names=[
#                           ImportAlias(
#                               name=Name(
#                                   value='os',
#                               ),
#                           ),
#                       ],
#                   ),
#               ],
#           ),
#           SimpleStatementLine(
#               body=[
#                   ImportFrom(
#                       module=Name(
#                           value='mezcla',
#                       ),
#                       names=[
#                           ImportAlias(
#                               name=Name(
#                                   value='glue_helpers',
#                               ),
#                               asname=AsName(
#                                   name=Name(
#                                       value='gh',
#                                   ),
#                               ),
#                           ),
#                       ],
#                   ),
#               ],
#           ),
#           SimpleStatementLine(
#               body=[
#                   Expr(
#                       value=Call(
#                           func=Attribute(
#                               value=Attribute(
#                                   value=Name(
#                                       value='os',
#                                   ),
#                                   attr=Name(
#                                       value='path',
#                                   ),
#                               ),
#                               attr=Name(
#                                   value='join',
#                               ),
#                           ),
#                           args=[
#                               Arg(
#                                   value=SimpleString(
#                                       value='"/tmp"',
#                                   ),
#                               ),
#                               Arg(
#                                   value=SimpleString(
#                                       value='"fubar"',
#                                   ),
#                               ),
#                           ],
#                       ),
#                   ),
#               ],
#           ),
#       ],
#   )
#
# - Finally the transformed tree is converted back to code and unused imports are removed
#
#   import os
#   os.path.join("/tmp", "fubar")
#
# --------------------------------------------------------------------------------
#
# TODO1:
# - Add a bunch of sanity checks (e.g., via debug.assertion).
# - Use high-level AST tools to validate the transformation. See
#   Exploring the Python AST Ecosystem video by Chase Stevens
#   [https://www.youtube.com/watch?v=Yq3wTWkoaYY].
#
# TODO2:
# - Consolidate ToMezcla and ToStandard because too much duplicated code.
# - Block usage under admin-like users, as in shell-scripts repo's batspp_report.py.
#
# TODO3:
# - Write pretty printer for CST tree for sake of more understandable tracing
#
# TODO4:
#- Move or drop the pylint disable=invalid-name specifications (e.g., via pylint call).
#  Note: comments immediately preceding function defs disrupt flow.
#

"""
Mezcla to Standard call conversion script

Sample usage:
   {script} - <<<"debug.assertion(2 + 2 == 5)"
"""

# Standard modules
import pickle
import datetime
import copy
import io
import time
import sys
import logging
import inspect
import urllib.parse
from typing import (
    Optional, Tuple, List, Union, Callable,
)
import tempfile
from enum import Enum
import collections
# Imports used to convert string to callable
# pylint: disable=unused-import
import os
import json
import ast

# Installed modules
import libcst as cst
## TEMP:
import libcst.tool as cst_tool
## TODO?: import libcst.tool.dump as cst_dump
import spacy as spacy

# Local modules
from mezcla.main import Main
from mezcla import system
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import tpo_common as tpo
from mezcla import misc_utils
from mezcla import spacy_nlp

# Arguments
FILE = "file"
TO_STD = "to-standard"
TO_MEZCLA = "to-mezcla"
METRICS = "metrics"
IN_PLACE = "in-place"
SKIP_WARNINGS = "skip-warnings"

# Types

StrOrCallable = Union[str, Callable]
SingleOrMultipleStrOrCallable = Union[StrOrCallable, List[StrOrCallable], Tuple[StrOrCallable]]

# Other constants (e.g., environment options)
TL = debug.TL
TRACE_DIFF = system.getenv_bool(
    "TRACE_DIFF", False,
    desc="Trace before and after CST trees along with diffs")
VALIDATE_CST = system.getenv_bool(
    "VALIDATE_CST", False,
    desc="Run validation on before and after CST trees")
SKIP_ARG_NAME_MATCHING = system.getenv_bool(
    "SKIP_ARG_NAME_MATCHING", False,
    desc="Omit arg name matching unless eq_params specified")
EQCALL_DATAFILE = system.getenv_value(
    "EQCALL_DATAFILE", None,
    desc="Python data file with EqCall specifications")
#
USER_EQCALL_FIELDS = system.getenv_value(
    "EQCALL_FIELDS", None,
    desc="String list of field names for EqCall matching")
DEFAULT_EQCALL_FIELDS = ["targets", "dests", "condition", "eq_params", "extra_params", "features"]
EQCALL_FIELDS = (misc_utils.extract_string_list(USER_EQCALL_FIELDS) if USER_EQCALL_FIELDS else DEFAULT_EQCALL_FIELDS)
#
USER_IMPORTS = system.getenv_value(
    "EQCALL_IMPORTS", None,
    desc="String names for modules to import")
DEFAULT_EQCALL_IMPORTS = ["debug", "system", "glue_helpers", "tpo_common", "spacy_nlp",
                          "sys", "os", "logging", "time"]
EQCALL_IMPORTS = (misc_utils.extract_string_list(USER_IMPORTS) if USER_IMPORTS else DEFAULT_EQCALL_IMPORTS)

# Globals
global_sandbox = {}
## TODO2: global_sandbox = copy.deepcopy(globals())

#-------------------------------------------------------------------------------

def path_to_callable(path: str) -> Callable:
    """
    Converts a string representing a function into the actual callable function.
    
    Parameters:
    path (str): The string representing the function, e.g., "os.remove".
    
    Returns:
    callable: The actual function.
    """
    components = path.split('.')
    # Get the base module from the global namespace
    module = lambda _x: None            # pylint: disable=unnecessary-lambda-assignment
    try:
        module = global_sandbox[components[0]]
        # Iterate through the components to get the desired attribute
        for component in components[1:]:
            module = getattr(module, component)
    except:
        system.print_exception_info("path_to_callable")
    debug.trace(7, f"path_to_callable(func_string={path}) => {module}")
    return module


ArgsSpecs = collections.namedtuple('Specs',
    'args, kwargs, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, annotations')
"""
Same as `inspect.FullArgSpec`, but separated `args` from `kwargs`
"""
## TODO4: rework using offset of first kwarg (to maintain compatibility with inspect version:
##    ex: class AltFullArgSpec:  spec: FullArgSpec;  kw_offset: int

EmptyArgsSpecs = ArgsSpecs(args=[], kwargs=[], varargs="values", varkw=None,
                           defaults=None, kwonlyargs=None, kwonlydefaults={}, annotations={})


def get_func_specs(func: callable) -> ArgsSpecs:
    """
    Get the function signature
    """
    ## TODO3: change callable => StrOrCallable in type hint above
    if isinstance(func, str):
        func = path_to_callable(func)
    result = None
    ## DEBUG: debug.trace_object(5, func)
    if not hasattr(func, "__module__"):
        debug.trace(5, f"Warning: unexpected condition in get_func_specs: {func=}")
    elif func.__module__ == "builtins":
        # Workaround for builtins
        # Note: inspect.getfullargspec(print) yields error:
        #     ValueError: no signature found for builtin <built-in function print>
        # See https://stackoverflow.com/questions/11343191/python-inspect-getargspec-with-built-in-function.
        if func.__name__ == "print":
            result = ArgsSpecs(
                args=[],
                kwargs=["sep", "end", "file", "flush"],
                ## TODO4: varargs="value",
                varargs="values",
                varkw=None,
                defaults=[],
                kwonlyargs=[],
                kwonlydefaults={},
                annotations={}
            )
        ## NOTE: Add here more workarounds for builtins if needed
    elif ((func.__module__ == "time") and (func.__name__ == "sleep")):
        # Uses empty ArgsSpecs (to avoid need for special cases)
        result = EmptyArgsSpecs
    else:
        func_specs = inspect.getfullargspec(func)
        # Separate args from kwargs, based on defaults
        new_args = func_specs.args
        new_kwargs = []
        if func_specs.defaults:
            args_count = len(func_specs.args) - len(func_specs.defaults)
            new_args = func_specs.args[0: args_count]
            new_kwargs = func_specs.args[args_count:]
        result = ArgsSpecs(
            args=new_args,
            kwargs=new_kwargs,
            varargs=func_specs.varargs,
            varkw=func_specs.varkw,
            defaults=func_specs.defaults,
            kwonlyargs=func_specs.kwonlyargs,
            kwonlydefaults=func_specs.kwonlydefaults,
            annotations=func_specs.annotations
        )
    debug.trace(7, f"get_func_specs(func={func}) => {result}")
    return result

def callable_to_path(func: Callable) -> str:
    """
    Get the path from callable object
    ```
    import some_module
    callable_to_path(some_module.foo) => "some_module.foo"
    ```
    """
    result = ""
    if isinstance(func, str):
        result = func
    elif not hasattr(func, "__module__"):
        debug.trace(5, f"Warning: unexpected condition in callable_to_path: {func=}")
        ## DEBUG: debug.trace_stack(7)
    elif func.__module__ == "builtins":
        result = func.__name__
    else:
        result = f"{func.__module__}.{func.__name__}"
    debug.trace(7, f"callable_to_path(func={func}) => {result}")
    return result


def trace_node(node: cst.CSTNode, level: int = 6,
               label: Optional[str] = None, diff_node: Optional[cst.CSTNode] = None):
    """Output pretty printed NODE to stderr if at debug LEVEL or higher using LABEL
    Note: if DIFF_NODE included than a diff is also output to stderr.
    """
    ## TODO: cst_dump = cst.tool.dump
    cst_dump = cst_tool.dump
    if not label:
        label = "CSTNode"
    if debug.debugging(level):
        dump = cst_dump(node)
        debug.trace(1, f"{label}:\n{gh.indent_lines(dump)}")
        if diff_node:
            other_dump = cst_dump(diff_node)
            dump_diff = misc_utils.string_diff(dump, other_dump)
            debug.trace(1, f"CST diff:\n{gh.indent_lines(dump_diff)}")

#-------------------------------------------------------------------------------

class CallDetails:
    """
    Class with details of a call, this is useful to
    store `callable`, func as `path` and `specs` of a function
    and avoid recalculating them every time
    """
    imported_modules = {}

    def __init__(self, func: StrOrCallable) -> None:
        debug.trace(7, f"CallDetails.__init__({func!r})")
        self.func = func
        # Import any modules needed to resolve EqCall details
        for module in EQCALL_IMPORTS:
            try:
                if not self.imported_modules.get(module):
                    # pylint: disable=eval-used,exec-used
                    debug.trace(6, f"FYI: importing {module}")
                    exec(f"import {module}", global_sandbox)
                    debug.trace(6, f"{module}={eval(module, global_sandbox)}")
                    debug.assertion(module in global_sandbox)
                else:
                    self.imported_modules[module] = True
            except:
                system.print_exception_info("EqCall imports")
        ## HACK: manually resolve aliases
        if not USER_IMPORTS:
            global_sandbox["gh"] = global_sandbox["glue_helpers"]
            global_sandbox["tpo"] = global_sandbox["tpo_common"]
        # Some local functions as lambda in parameters
        # cannot be converted to path or callable
        # but also is not required, so we ignore them
        self.callable = None
        try:
            self.callable = path_to_callable(func) if isinstance(func, str) else func
        except:
            ## DEBUG: debug.raise_exception(6)
            debug.trace(4, f"FYI: Exception deriving callable from {func!r}: {sys.exc_info()}")
        self.path = None
        try:
            self.path = func if isinstance(func, str) else callable_to_path(func) if func else None
        except:
            ## DEBUG: debug.raise_exception(6)
            debug.trace(4, f"FYI: Exception deriving module path from {func!r}: {sys.exc_info()}")
        self.specs = None
        try:
            self.specs = get_func_specs(func) if func else None
        except:
            ## DEBUG: debug.raise_exception(6)
            debug.trace(4, f"FYI: Exception deriving function specification from {func!r}: {sys.exc_info()}")
            debug.trace_stack(7)
        debug.trace_object(6, self, label="CallDetails instance")

    @staticmethod
    def to_list_of_call_details(funcs: SingleOrMultipleStrOrCallable) -> List['CallDetails']:
        """
        Convert a list of functions to a list of CallDetails objects
        """
        # Convert to list
        if isinstance(funcs, list):
            pass
        elif isinstance(funcs, tuple):
            funcs = list(funcs)
        else:
            funcs = [funcs]
        # Process
        result = []
        for func in funcs:
            details = None
            if isinstance(func, CallDetails):
                details = func
            elif func:
                details = CallDetails(func)
            else:
                details = CallDetails(None)
                debug.trace(6, "FYI: using degenerate CallDetails; {func=}")
            if details:
                result.append(details)
        return result

    def equals_to(self, path: str) -> bool:
        """Compare if the path is equal to the call details path"""
        ## TODO4: use debug.assertion unless critical (likewise below)
        assert self.path, "CallDetails => path is None"
        return self.path == path

    def ends_equals_to(self, path: str) -> bool:
        """
        Compare if the path ends with the call details path
        ```
        "glue_helpers.basename" == "os.path.basename"
        ```
        """
        assert self.path, "CallDetails => path is None"
        return self.path.endswith("." + path)

    def __call__(self, *args, **kwargs):
        debug.trace(9, f"CallDetails.__call__(); self={self}")
        debug.assertion(self.callable, "CallDetails => callable is None")
        return (self.callable(*args, **kwargs) if self.callable else None)

    def __repr__(self) -> str:
        return f"CallDetails: path={self.path!r} callable={self.callable!r} specs={self.specs!r}"

class Features(Enum):
    """Features to be used in the EqCall"""

    FORMAT_STRING = "format_string"
    """
    Convert arguments to format string

    ```
        debug.trace_fmt(
            7,
            "register_env_option({v}, {dsc}, {dft})",
            v=var,
            dsc=description,
            dft=default
        )
    ```
    to
    ```
        logging.debug(
            "register_env_option({v}, {dsc}, {dft})".format(v=var, dsc=description, dft=default)
        )
    ```
    """

    COPY_DEST_SOURCE = "copy_dest_source"
    """
    Copy source code equivalent to a Mezcla call,

    this only works when converting Mezcla => Standard

    ```
    debug.assertion(condition, ...) => "if condition: ..."
    ```
    """

## TODO: separate EqCall into different data classes ???
##       to avoid ambiguity about targets and dests. ???
##       e.g. MultipleTargetsSingleDest, SingleTargetMultipleDests ???
##            ToSourceDest ???
class EqCall:
    """
    Mezcla to standard equivalent call class
    """

    def __init__(
            self,
            targets: SingleOrMultipleStrOrCallable,
            dests: SingleOrMultipleStrOrCallable,
            condition: Optional[StrOrCallable] = None,
            eq_params: Optional[dict] = None,
            extra_params: Optional[dict] = None,
            features: List[Features] = None
        ) -> None:
        self.targets = CallDetails.to_list_of_call_details(targets)
        """
        Mezcla method to be replaced.
        ```
        targets = gh.get_temp_file
        ```
        """

        self.dests = CallDetails.to_list_of_call_details(dests)
        """
        Standard method to be replaced.
        ```
        dests = tempfile.NamedTemporaryFile
        ```
        NOTE: some standard modules like `os` are loaded as `posix`,
        or `os.path` as `posixpath`, to fix this, you can set dest as string:
        ```
        dests = 'os.path.getsize'
        ```
        """
        ## TODO2: change all EqCall specs to use strings; besides the posix issue,
        ## the conversion should be sandboxed to avoid using this script's global space.

        self.condition = (condition if isinstance(condition, CallDetails)
                          else CallDetails(condition) if condition else None)
        """
        Evaluation function to determine if the replacement should be made.
        ```
        condition = lambda level: level > 3
        ```
        """

        self.eq_params = eq_params
        """
        Equivalent parameters names, used to match the
        arguments between the Mezcla and standard calls.
        ```
        def foo(a, b, c):
            ...
        def replacement_for_foo(x, y, z):
            ...
        eq_params = {
            "a": "z",
            "b": "x",
            "c": "y"
        }
        ```
        """

        self.extra_params = extra_params
        """
        Extra parameters to be added when the replacement
        require more arguments than the original call.
        ```
        def logging_error(msg):
            ...
        def replacement_for_logging(level, msg):
            ...
        extra_params = {
            "level": 1
        }
        > logging_error("message") => replacement_for_logging(1, "message")
        ```
        """

        self.features = features if features else []
        """
        Extra features to be used in the replacement
        """

        self.permutations = []
        """
        Memoization of the permutations to avoid recalculating them
        """
        debug.trace_object(7, self, label="EqCall instance")

    def get_permutations(self) -> List['EqCall']:
        """
        Get all permutations of the equivalent call

        This is useful when dealing with multiple targets or destinations
        """
        # Return previous permutations
        if len(self.permutations) > 0:
            debug.trace(7, "[early exit] EqCall.get_permutations() => memoized")
            return self.permutations

        # Otherwise calculate the permutations and store them:

        # Create all permutations
        result = []
        for target in self.targets:
            for dest in self.dests:
                result.append(EqCall(
                    targets=target.func,
                    dests=dest.func,
                    condition=(self.condition.func if self.condition else None),
                    eq_params=self.eq_params,
                    extra_params=self.extra_params,
                    features=self.features
                ))
        self.permutations = result
        debug.trace(7, f"EqCall.get_permutations() => {result}")
        return result

    def __repr__(self) -> str:
        target_paths = [t.path for t in self.targets] if len(self.targets) > 1 else self.targets[0]
        dest_paths = [d.path for d in self.dests] if len(self.dests) > 1 else self.dests[0]
        return f"EqCall: {target_paths} => {dest_paths}"


class EqCallParser:
    """
    EqCallParser is responsible for reading a configuration file and creating
    instances of the EqCall defined within it.
    Attributes:
        config_path (str): The path to the configuration file.
        eq_classes (list): A list to store instances of EqCall.
    Methods:
        parse_config(): Reads the configuration file and creates EQclass instances.
    """

    config_path: str = ""
    eq_classes: list = []

    def __init__(self, config_path: str) -> None:
        assert system.file_exists(config_path), f"Config file not found: {config_path}"
        self.config_path = config_path
        self.parse_config()

    def parse_config(self) -> None:
        """
        Parses the config file in `config_path` and creates instences of EqCall for each element in it
        """
        ## TODO3: use with system.open_file(self.config_path): ...
        with open(self.config_path, "r", encoding="UTF-8") as file:
            with json.load(file) as config:
                for eq_call in config:
                    targets = eq_call.get("targets")
                    # if lambda in dest, compile and check
                    # for co.names
                    dests = eq_call.get("dests")
                    dests = self._parse_dests(dests)
                    # compile only if lambda,
                    # eval without locals, globals or builtins
                    condition = eq_call.get("condition", None)
                    if condition is not None:
                        condition = self._parse_condition(condition)
                    eq_params = eq_call.get("eq_params", None)
                    extra_params = eq_call.get("extra_params", None)
                    # parse list and add features
                    features = eq_call.get("features", None)
                    features = self._parse_features(features)
                    self.eq_classes.append(
                        EqCall(
                            targets, dests, condition, eq_params, extra_params, features
                        )
                    )
        return

    def _parse_dests(self, dests:SingleOrMultipleStrOrCallable ) -> SingleOrMultipleStrOrCallable:
        """
        Parse the destination list and return a list of CallDetails objects
        """
        allowed_names = {"os.environ.get": os.environ.get}
        results = []
        def _parse_dest(dest:StrOrCallable) -> StrOrCallable:
            result = dest
            if isinstance(dest, str) and "lambda" in dest:
                code = compile(dest, "<string>", "eval")
                for name in code.co_names:
                    if name not in allowed_names:
                        raise NameError(f"Use of {name} not allowed")
                # TODO3: why are builtins disabled? (likewise in other eval call)
                # pylint: disable=eval-used
                result = eval(code, {"__builtins__": {}}, allowed_names)
            return result

        if isinstance(dests, (list, tuple)):
            for dest in dests:
                results.append(_parse_dest(dest))
        else:
            results.append(_parse_dest(dests))
        debug.trace(7, "_parse_dests({dests!r}) => {results!r}")
        return results

    def _parse_condition(self, condition:StrOrCallable) -> StrOrCallable:
        """
        Parse the condition and return a CallDetails object
        """
        result = condition
        if isinstance(condition, str) and "lambda" in condition:
            code = compile(condition, "<string>", "eval")
            if len(code.co_names) > 0:
                raise NameError(f"Use of {code.co_names[0]} not allowed")
            # pylint: disable=eval-used
            result = eval(code, {"__builtins__": {}}, {})
        return result
    
    def _parse_features(self, features:List[str]) -> List[Features]:
        """
        Parse the features list and return a list of Features objects
        """
        results = []
        for feature in features:
            ## TODO4: use dict lookup for better maintenance
            ##    ex: feature_name_to_value = {"Features.FORMAT_STRING": Features.FORMAT_STRING, ...}
            if feature.endswith("FORMAT_STRING"):
                results.append(Features.FORMAT_STRING)
            elif feature.endswith("COPY_DEST_SOURCE"):
                results.append(Features.COPY_DEST_SOURCE)
            else:
                raise ValueError(f"Unsupported feature: {feature}")
        return results
        

# Custom Function replacements

def assertion_replacement(expression, message=None, assert_level=None):   # pylint: disable=missing-function-docstring
    ## TODO2: """Replacement for debug.assertion"""
    ##  NOTE: The above comment breaks replacement which assumes single line of code
    ## TODO3: Encode directly via lambda in the EqCall
    ##    ex: dests=lambda expression, message=None, assert_level=None: (debug.trace(assert_level, message) if expression else None)
    if expression:
        debug.trace(assert_level, message)

# Add equivalent calls between Mezcla and standard
# Note: put new additions at the end (see comments undew NEW CALLS).
## TODO4: drop support for multiple targets (i.e., at expense of a little redundancy);
##    ex: EqCall(targets=(fu, bar), dests=fubar) => EqCall(targets=fu, dests=fubar) & EqCall(targets=bar, dests=fubar)

mezcla_to_standard = []
if not EQCALL_DATAFILE:
    mezcla_to_standard = [
        EqCall(
            ## TODO4: use full name (glue_helpers)
            gh.get_temp_file,
            tempfile.NamedTemporaryFile,
        ),
        EqCall(
            gh.basename,
            "os.path.basename",
            eq_params={ "filename": "p" },
        ),
        EqCall(
            gh.dir_path,
            "os.path.dirname",
            eq_params={ "filename": "p" },
        ),
        EqCall(
            gh.dirname,
            "os.path.dirname",
            eq_params={ "file_path": "filename" }
        ),
        EqCall(
            ## TODO4: treat targets separately
            (gh.file_exists, system.file_exists),
            "os.path.exists",
            eq_params={ "filename": "path" }
        ),
        EqCall(
            (gh.form_path, system.form_path),
            "os.path.join",
            ## TODO3: condition=lambda: not create [for gh.form_path]
            ##    where extra_params = { "create": False },
            eq_params = { "filenames": "a" }
        ),
        EqCall(
            (gh.is_directory, system.is_directory),
            "os.path.isdir",
            eq_params = { "path": "s" }
        ),
        EqCall(
            (gh.create_directory, system.create_directory),
            "os.mkdir",
        ),
        EqCall(
            gh.rename_file,
            "os.rename",
            eq_params = { "source": "src", "target": "dst" }
        ),
        EqCall(
            (gh.delete_file, gh.delete_existing_file),
            "os.remove",
            eq_params = { "filename": "path" }
        ),
        EqCall(
            gh.file_size,
            "os.path.getsize",
        ),
        EqCall(
            gh.get_directory_listing,
            "os.listdir",
            eq_params = { "dir_name": "path" }
        ),
        EqCall(
            ## TODO4: drop tpo as obsolete; -or- use full name (tpo_common)
            tpo.debug_print,
            logging.debug,
            ## TODO4: condition = lambda level: level > 3,
            eq_params = { "text": "msg" },
            extra_params = { "level": 1 },
        ),
        EqCall(
            (debug.trace, "debug.trace_fmt", debug.trace_fmtd),
            logging.debug,
            condition = lambda level: level > 3,
            eq_params = { "text": "msg" },
            extra_params = { "level": 4 },
            features=[Features.FORMAT_STRING]
        ),
        EqCall(
            (debug.trace, "debug.trace_fmt", debug.trace_fmtd),
            logging.info,
            condition = lambda level: 2 < level <= 3,
            eq_params = { "text": "msg" },
            extra_params = { "level": 3 },
            features=[Features.FORMAT_STRING],
        ),
        EqCall(
            (debug.trace, "debug.trace_fmt", debug.trace_fmtd),
            logging.warning,
            condition = lambda level: 1 < level <= 2,
            eq_params = { "text": "msg" },
            extra_params = { "level": 2 },
            features=[Features.FORMAT_STRING],
        ),
        EqCall(
            (debug.trace, "debug.trace_fmt", debug.trace_fmtd),
            logging.error,
            condition = lambda level: 0 < level <= 1,
            eq_params = { "text": "msg" },
            extra_params  = { "level": 1 },
            features=[Features.FORMAT_STRING],
        ),
        EqCall(
            (system.print_error, system.print_stderr, system.print_stderr_fmt, tpo.print_stderr),
            print,
            eq_params={ "text": "values" },
            extra_params={ "file": sys.stderr },
            features=[Features.FORMAT_STRING],
        ),
        EqCall(
            debug.trace_expr,
            # should we use Icrecream.ic() here?
            dests= print,
            eq_params={ "values": "values" },
            extra_params={ "file": sys.stderr },
            ),
        EqCall(
            system.exit,
            sys.exit,
            eq_params={ "message": "status" }
        ),
        EqCall(
            system.open_file,
            open,
            ## TODO4: extra_params={ "encoding": "UTF-8" },
            eq_params={ "filename": "file" }
        ),
        EqCall(
            system.read_directory,
            "os.listdir",
            eq_params={ "directory": "path" }
        ),
        EqCall(
            system.is_regular_file,
            "os.path.isfile",
        ),
        EqCall(
            system.get_current_directory,
            "os.getcwd",
        ),
        EqCall(
            system.set_current_directory,
            "os.chdir",
            ## TEST:
            ## eq_params={ "directory": "path" }
        ),
        EqCall(
            system.absolute_path,
            "os.path.abspath",
        ),
        EqCall(
            system.real_path,
            "os.path.realpath",
        ),
        EqCall(
            system.get_args,
            ## TODO: "sys.argv", w/ [Features.non-function]
            dests=lambda: sys.argv,
            features=[Features.COPY_DEST_SOURCE]        
        ),
        EqCall(
            system.round_num,
            round,
            eq_params={ 
                       "value": "number",
                       "precision": "ndigits"},
            extra_params={ "ndigits": 6 }
        ),
        EqCall(
            system.round3,
            round,
            eq_params={ 
                       "value": "number",
                       "precision": "ndigits"},
            extra_params={ "ndigits": 3 }
        ),
        EqCall(
            tpo.round_num,
            round,
            eq_params={ 
                       "value": "number",
                       "precision": "ndigits"},
            extra_params={ "ndigits": 3 }
        ),
        EqCall(
            "system.sleep",
            "time.sleep",
        ),
        EqCall(
            ## TODO3: separate: get_exception just returns tuple
            (system.print_exception_info, system.get_exception),
            sys.exc_info,
        ),
        EqCall(
            (
                system.to_string, system.to_str, system.to_unicode,
                tpo.normalize_unicode, tpo.ensure_unicode, system.to_utf8,
                system.from_utf8
            ),
            str,
        ),
        EqCall(
            (system.to_float, system.safe_float),
            ## TODO4: dest=lambda: try: ... except: ...???
            float,
        ),
        EqCall(
            (system.to_int, system.safe_int),
            int,
        ),
        EqCall(
            (debug.assertion, gh.assertion),
            dests=assertion_replacement,
            extra_params={ "assert_level": 1, "message": "debug assertion failed" },
            features=[Features.COPY_DEST_SOURCE]
        ),
        EqCall(
            (system.getenv, system.getenv_value),
            dests=lambda var, default_value: os.environ.get(var) or default_value,
            eq_params={"var": "var", "default": "default_value"},
            features=[Features.COPY_DEST_SOURCE]
        ),
        EqCall(
            (system.getenv_int, system.getenv_integer),
            dests=lambda var, default_value: int(os.environ.get(var)) or default_value,
            eq_params={"var": "var", "default": "default_value"},
            features=[Features.COPY_DEST_SOURCE]
        ),
        EqCall(
            (system.getenv_bool, system.getenv_boolean),
            dests=lambda var, default_value: bool(os.environ.get(var)) or default_value,
            eq_params={"var": "var", "default": "default_value"},
            features=[Features.COPY_DEST_SOURCE]
        ),
        EqCall(
            system.getenv_text,
            dests=lambda var, default_value: str(os.environ.get(var)) or default_value,
            eq_params={"var": "var", "default": "default_value"},
            features=[Features.COPY_DEST_SOURCE]
        ),
        EqCall(
            (system.getenv_number, system.getenv_float),
            dests=lambda var, default_value: float(os.environ.get(var)) or default_value,
            eq_params={"var": "var", "default": "default_value"},
            features=[Features.COPY_DEST_SOURCE]
        ),
        # 
        # NEW CALLS
        #
        # Note:
        # - The goal is to provide coverage for the most commonly used functions,
        #   not all of mezcla. This would mostly include debug.py, system.py, and
        #   glue_helpers.py.
        # - Exceptions would be the deprecated tpo_common.py and the complex main.py.
        # - In addition, testing support is not included (e.g., unittest_wrapper.py).
        #
        EqCall(
            system.quote_url_text,
            dests=urllib.parse.quote_plus
        ),
        EqCall(
            system.unquote_url_text,
            dests=urllib.parse.unquote_plus
        ),
        EqCall(
            (system.non_empty_file, gh.non_empty_file),
            dests=lambda path: os.path.exists(path) and os.path.getsize(path) > 0,
            features=[Features.COPY_DEST_SOURCE]
        ),
        EqCall(
            (system.read_file, system.read_entire_file),
            dests=lambda path: open(path, encoding="UTF-8").read(),
            features=[Features.COPY_DEST_SOURCE]
        ),
        EqCall(
            system.write_file,
            dests=lambda path, text: open(path, "w", encoding="UTF-8").write(text),
            eq_params={ "filename": "path", "text": "text" },
            features=[Features.COPY_DEST_SOURCE]
        ),
        EqCall(
            gh.full_mkdir,
            dests=os.makedirs,
        ),
        EqCall(
            gh.elide,
            dests=lambda text, max_length: text[:max_length] + "..." if len(text) > max_length else text,
            features=[Features.COPY_DEST_SOURCE]
        ),
        EqCall(
            debug.reference_var,
            dests=lambda var: ...,
            features=[Features.COPY_DEST_SOURCE]
        ),
        EqCall(
            (debug.debugging, debug.detailed_debugging, debug.verbose_debugging),
            dests=lambda : False,
            features=[Features.COPY_DEST_SOURCE]
        ),
        EqCall(
            system.chomp,
            dests=lambda text: text.rstrip(os.linesep),
            features=[Features.COPY_DEST_SOURCE]
        ),
        EqCall(
            system.save_object,
            dests=lambda obj,filename: pickle.dump(obj, open(filename, "wb")),
            eq_params={ "obj": "obj", "file_name": "filename" },
            features=[Features.COPY_DEST_SOURCE]
        ),
        EqCall(
            system.load_object,
            dests=lambda filename: pickle.load(open(filename, "rb")),
            features=[Features.COPY_DEST_SOURCE]
        ),
        EqCall(
            system.round_as_str,
            dests=lambda value: str(round(value)),
            features=[Features.COPY_DEST_SOURCE],
            extra_params={ "precision": 6 }
        ),
        EqCall(
            misc_utils.sort_weighted_hash,
            dests=lambda hash: sorted(hash.items(), key=lambda x: x[1], reverse=True),
            features=[Features.COPY_DEST_SOURCE]
        ),
        EqCall(
            gh.resolve_path,
            dests=os.path.realpath,
        ),
        EqCall(
            debug.timestamp,
            dests=datetime.datetime.now,
        ),
        EqCall(
            spacy_nlp.Chunker,
            dests=spacy.load,
            eq_params={"model": "name"},
        ),
        EqCall(
            targets="system.setenv",
            dests="os.putenv",
        ),
        ## TODO2: Make sure new additions are for commonly used functions.
        ## For tips, see header comments and notes above under "NEW CALLS".
    ]

#-------------------------------------------------------------------------------

def cst_to_path(tree: cst.CSTNode) -> str:
    """
    Convert CST Tree Node to a string path.
    ```
    code = "foo.bar.baz(arg1, arg2)"
    tree = libcst.parse_expression(code)
    cst_to_path(tree) =>"foo.bar.baz"
    ```
    """
    ## TODO3: restructure w/ result = ... result = ... return result
    # pylint: disable=no-else-return
    if isinstance(tree, cst.Attribute):
        return f"{cst_to_path(tree.value)}.{tree.attr.value}"
    elif isinstance(tree, cst.Call):
        return f"{cst_to_path(tree.func)}"
    elif isinstance(tree, cst.Name):
        return tree.value
    elif isinstance(tree, cst.SimpleString):
        return tree.value
    elif isinstance(tree, cst.ImportAlias):
        return cst_to_path(tree.name)
    elif isinstance(tree, cst.Subscript):
        return cst_to_path(tree.value)
    elif isinstance(tree, cst.Param):
        return cst_to_path(tree.name)
    raise ValueError(f"Unsupported node type: {type(tree)}")


def cst_to_paths(tree: cst.CSTNode) -> List[str]:
    """
    Convert CST Tree Node to a list of string paths.
    ```
    code = "from os import path, remove"
    tree = libcst.parse_statement(code)
    cst_to_paths(tree) => ["os.path", "os.remove"]
    ```
    """
    ## TODO3: restructure final return using result var
    # pylint: disable=no-else-return
    if isinstance(tree, (cst.Import, cst.ImportFrom)):
        return [cst_to_path(alias) for alias in tree.names]
    elif isinstance(tree, cst.Parameters):
        return [cst_to_path(alias) for alias in tree.params]
    raise ValueError(f"Unsupported node type: {type(tree)}")


def path_to_cst(path: str) -> cst.CSTNode:
    """
    Convert a string path to CST Tree Node.
    ```
    convert_path_to_cst("foo.bar.baz") => cst.Attribute(value=...)
    ```
    """
    parts = path.split(".")
    if len(parts) == 1:
        return cst.Name(parts[0])
    return cst.Attribute(
        value=path_to_cst(".".join(parts[:-1])),
        attr=cst.Name(parts[-1])
    )


def value_to_arg(value: object) -> cst.Arg:
    """
    Convert the value object to an CST tree argument node

    ```
    value_to_arg('text') => cst.Arg(cst.SimpleString(value='text'))
    ```
    """
    result = None
    if isinstance(value, str):
        # OLD: result = cst.Arg(cst.SimpleString(value=value))
        ## TODO3: (value=f'"{value!r}"')?
        result = cst.Arg(cst.SimpleString(value=f'"{value}"'))
    elif isinstance(value, int):
        result = cst.Arg(cst.Integer(value=str(value)))
    elif isinstance(value, float):
        result = cst.Arg(cst.Float(value=str(value)))
    elif isinstance(value, bool):
        # OLD: result = cst.Arg(cst.Name(value=str(value)))
        result = cst.Arg(cst.Name(value='True' if value else 'False'))
    elif isinstance(value, io.TextIOWrapper):
        ## TODO3: what about sys.stdin and sys.stdout?
        result = cst.Arg(cst.Attribute(
            value=cst.Name(value='sys'),
            attr=cst.Name(value='stderr')
        ))
    else:
        raise ValueError(f"Unsupported value type: {type(value)}")
    debug.trace(7, f"value_to_arg({value}) => {result}")
    return result


def arg_to_value(arg: cst.Arg) -> object:
    """
    Convert a CST tree argument node to a value object

    ```
    arg = cst.Arg(cst.SimpleString(value=r'"text"'))
    arg_to_value(arg) => '"text"'
    ```
    """
    result = None
    if isinstance(arg.value, cst.SimpleString):
        result = str(arg.value.value)
    elif isinstance(arg.value, cst.Integer):
        result = int(arg.value.value)
    elif isinstance(arg.value, cst.Float):
        result = float(arg.value.value)
    elif isinstance(arg.value, cst.Name):
        # Check if is Boolean
        ## TODO3: handle None, sys, etc.
        if isinstance(arg.value.value, str):
            result = system.to_bool(arg.value.value)
    if result is None:
        raise ValueError(f"Unsupported CST Argument child node type: {type(arg.value)}")
    debug.trace(7, f"arg_to_value({arg}) => {result}")
    return result


def has_fixed_value(arg: cst.Arg) -> bool:
    """Check if an CST argument node has a fixed value"""
    result = isinstance(arg.value, (cst.SimpleString, cst.Integer, cst.Float, cst.Name))
    debug.trace(7, f"has_fixed_value(arg={arg}) => {result}")
    return result


def all_has_fixed_value(args: List[cst.Arg]) -> bool:
    """Check if any CST argument node has a fixed value"""
    ## TODO4:   ^^^ each
    result = all(has_fixed_value(arg) for arg in args)
    debug.trace(7, f"any_has_fixed_value(args={args}) => {result}")
    return result


def args_to_values(args: List[cst.Arg]) -> list:
    """Convert a list of CST arguments nodes to a list of values objects"""
    debug.trace(7, "args_to_values(args) => list")
    return [arg_to_value(arg) for arg in args]


def remove_last_comma(args: List[cst.Arg]) -> List[cst.Arg]:
    """
    Remove the last comma node from a list CST arguments nodes
    ```
    args = [
        cst.Arg(...),
        cst.Arg(...),
        ...
        cst.Arg(...), # remove comma from last item
    ]
    ```
    """
    if not args:
        return args
    args[-1] = args[-1].with_changes(comma=cst.MaybeSentinel.DEFAULT)
    debug.trace(7, "remove_last_comma(args) => list")
    return args

def match_args(func: CallDetails, cst_arguments: List[cst.Arg]) -> dict:
    """
    Match the arguments to the function signature
    ```
    def foo(a, b, c):
        ...
    match_args(foo, [Arg(1), Arg(2), Arg(3)], {}) => {
        "a": Arg(1),
        "b": Arg(2),
        "c": Arg(3)
    }
    ```
    """
    # Extract function signature
    func_specs = func.specs
    if func_specs is None:
        debug.trace(7, f"[early exit] match_args(func={func}, cst_arguments={cst_arguments}) => {func_specs}")
        return func_specs
    arg_names = func_specs.args # name
    varargs_name = func_specs.varargs # *name
    kwarg_names = func_specs.kwargs # name = "value"

    # Separate between args and kwargs
    args, kwargs = [], []
    for idx, arg in enumerate(cst_arguments):
        if not isinstance(arg, cst.Arg):
            raise ValueError(f"Unsupported argument type: {type(arg)}")
            
        if arg.keyword:
            kwargs.append(arg)
        else:
            # Check for positional arguments
            if len(args) >= len(arg_names) and not varargs_name:
                if not kwarg_names:
                    debug.trace(6, f"FYI: Ignoring arg {idx + 1}: {arg!r}")
                    continue
                arg = arg.with_changes(keyword=cst.Name(value=(arg_names+kwarg_names)[idx]))
                kwargs.append(arg)
            else:
                args.append(arg)

    # Match positional arguments
    matched_args = {}
    excess_args = []
    for i, arg in enumerate(args):
        if i < len(arg_names):
            matched_args[arg_names[i]] = arg
        else:
            excess_args.append(arg)

    # Handle *args
    if varargs_name:
        matched_args[varargs_name] = excess_args

    # Match keyword arguments
    for kwarg in kwargs:
        if kwarg.keyword and kwarg.keyword.value in kwarg_names:
            matched_args[kwarg.keyword.value] = kwarg
        else:
            debug.trace(6, f"FYI: Ignoring kwarg {kwarg!r}")      

    debug.trace(7, f"match_args(func={func!r}, cst_arguments={cst_arguments!r}) => {matched_args!r}")
    return matched_args


def dict_to_func_args_list(func: CallDetails, args_dict: dict,
                           eq_call: EqCall, other_func: Optional[CallDetails] = None) -> List[cst.Arg]:
    """
    Convert a dictionary to a list of CST arguments nodes, this is the opposite of match_args(...).
    This uses the FUNC specification and the ARGS_DICT of matching arguments. The EQ_CALL argument 
    correspondence is just used to determine whether certain hueristics apply (e.g., only if empty).
    It is also used to help determine whether function argument matching should be skipped, which
    alleviates need for such correspondence specifications, which can be tedious. In addition, 
    the optional OTHER_FUNC is used in case the original specification is not available, which
    happens with certain builtin functions (e.g., C-based). 

    Example:
    ```
    def foo(a, b=None):
        ...
    dict_to_func_args_list(
        foo,
        {
            "a": Arg(1),
            "b": Arg(2, keyword="b"),
            "c": Arg(3)
        },
        ...)
    ) => [
        Arg(1),
        Arg(2, keyword="b")
    ]
    ```
    As you can see, this method removes extra arguments.
    """
    debug.trace(7, f"in dict_to_func_args_list({func=}, {args_dict=}, {eq_call=})")
    # Extract function signature
    func_specs = func.specs
    if func_specs is None:
        result = list(args_dict.values())
        debug.trace(7, f"[early exit] dict_to_func_args_list(_) => {result}!r")
        return result
    func_specs_args = func_specs.args
    if (not func_specs_args) and (other_func is not None) and not eq_call.eq_params:
        debug.trace(3, "FYI: Applying func_specs_args reversal")
        func_specs_args = other_func.specs.args
        
    # Match positional arguments
    result = []
    debug.trace_expr(6, func_specs_args)
    skip_arg_name_matching = (SKIP_ARG_NAME_MATCHING and not eq_call.eq_params)
    if not skip_arg_name_matching:
        for arg_name in func_specs_args:
            if arg_name in args_dict:
                result.append(args_dict[arg_name])
            else:
                debug.trace(2, f"Warning: unable to match {arg_name!r} in {func.func!r}: args_dict.keys={list(args_dict.keys())}")
    if func_specs_args and not result:
        debug.trace(3, "FYI: Applying func_specs_args workaround")
        result = list(args_dict.values())

    # Handle *args
    if func_specs.varargs in args_dict:
        varargs = args_dict[func_specs.varargs]
        if isinstance(varargs, list):
            result += varargs
        else:
            result.append(varargs)

    # Match keyword arguments
    for kwarg_name in func_specs.kwargs:
        if kwarg_name in args_dict:
            new_arg = args_dict[kwarg_name].with_changes(keyword=path_to_cst(kwarg_name))
            result.append(new_arg)

    result = flatten_list(result)
    result = remove_last_comma(result)

    debug.trace(6, f"dict_to_func_args_list(_) => {result!r}")
    return result


def flatten_list(list_to_flatten: list[list]) -> list:
    """Flatten a list"""
    result = []
    for item in list_to_flatten:
        if isinstance(item, list):
            result += item
        elif isinstance(item, tuple):
            result += list(item)
        else:
            result.append(item)
    debug.trace(7, f"flatten_list(list_to_flatten={list_to_flatten!r}) => {result!r}")
    return result


def text_to_comments_node(text: str) -> cst.Comment:
    """Convert text into a comment node"""
    # We convert the text into a single line comment,
    # Because using multiline comments can create
    # confusion if those lines are next to other comments
    text = text.replace("\n", " ")
    comment = cst.Comment(value=f"# {text}")
    debug.trace(9, f"text_to_comment_node(text={text!r}) => {comment!r}")
    return comment


def get_format_names_in_string(value: str) -> List[str]:
    """
    Return list of format variables names in a string

    Input:
    ```
        get_format_names_in_string("Hello {user}, welcome to {place}")
    ```

    Output:
    ```
        ["user", "place"]
    ```
    """
    ## TODO4: rework in terms of libcst parsing, given complexity of format strings
    result = []
    for name in value.split("{"):
        if "}" in name:
            ## TODO3: ignore double braces (e.g., "values={{\n...\n}}")
            name = name.split("}")[0].strip()
            name = name.split("!")[0]
            name = name.split(":")[0]
            result.append(name)
    debug.trace(7, f"get_format_names_in_string(value={value!r}) => {result!r}")
    return result


def create_string_dot_format_node(value: str, format_args: List[cst.Arg]) -> cst.Call:
    """
    Create a string.format() node
    """
    format_node = cst.Attribute(
        value=cst.SimpleString(value=value),
        attr=cst.Name("format")
    )
    call_node = cst.Call(
        func=format_node,
        args=format_args
    )
    debug.trace(7, (f"create_string_dot_format_node(value={value!r}, " +
                    f"format_args={format_args!r}) => {call_node!r}"))
    return call_node


def get_keyword_name(arg: cst.Arg) -> Optional[str]:
    """
    Get the keyword name from the argument node
    """
    result = arg.keyword.value if arg.keyword else None
    return result


def filter_kwargs(kwargs: List[cst.Arg], names: List[str]) -> List[cst.Arg]:
    """
    Filter kwargs by the names
    """
    result = []
    for kwarg in kwargs:
        keyword = get_keyword_name(kwarg)
        if keyword and keyword in names:
            result.append(kwarg)
    debug.trace(9, f"filter_kwargs(names={names!r}) => {result!r}")
    return result


def format_strings_in_args(args: List[cst.Arg]) -> dict:
    """
    Convert arguments to format strings

    Usage example, with simplified CST:

    ```
    args = (
        Arg("this is a string with some value {v}"),
        Arg(v=42)
    )
    format_strings_in_args(args) => (
        Arg("this is a string with some value {v}".format(v=42)),
    )
    ```
    """
    if not args:
        debug.trace(7, f"[early exit] format_strings_in_args(args={args}) => {args}")
        return args
    args = list(args)
    result = []
    args_to_skip = []
    for arg in args:
        # Check if argument is already processed
        keyword = get_keyword_name(arg)
        if keyword in args_to_skip:
            continue
        # Process the argument
        arg_content = arg.value
        if isinstance(arg_content, cst.SimpleString):
            format_names = get_format_names_in_string(arg_content.value)
            if format_names:
                format_kwargs = filter_kwargs(args, format_names)
                dot_format_node = create_string_dot_format_node(arg_content.value, format_kwargs)
                new_arg = arg.with_changes(value=dot_format_node)
                result.append(new_arg)
                args_to_skip += format_kwargs
            else:
                result.append(arg)
        else:
            result.append(arg)
    debug.trace(7, f"format_strings_in_args(args={args!r}) => {result!r}")
    return result


def path_to_import(path: str) -> cst.SimpleStatementLine:
    """
    Convert a path to an import node
    ```
    path_to_import("os.path") => cst.SimpleStatementLine(body=cst.ImportFrom(...))
    path_to_import("debug") => cst.SimpleStatementLine(body=cst.Import(...))
    ```
    """
    result = None
    parts = path.split(".")
    if len(parts) == 1:
        result = cst.Import([cst.ImportAlias(cst.Name(parts[0]))])
    elif len(parts) == 2:
        result = cst.ImportFrom(
            module=cst.Name(parts[0]),
            names=[cst.ImportAlias(cst.Name(parts[1]))]
        )
    else:
        raise ValueError(f"Unsupported path: {path}")
    result = cst.SimpleStatementLine(
        body=[result]
    )
    debug.trace(7, f"path_to_import(path={path!r}) => {result!r}")
    return result


def remove_paths_from_import_cst(
        cst_import: cst.SimpleStatementLine,
        paths_to_remove: List[str]
    ) -> cst.SimpleStatementLine:
    """
    Remove paths from an CST Import Node, ignore aliases

    Example with simple Import

    ```
        code = "import os"
        cst_import = libcst.parse_statement(code)
        remove_paths_from_import_cst(cst_import, ["os"]) => None
    ```

    Example with Import From

    ```
        code = "from os import (\n    path,\n    remove,\n)"
        cst_import = libcst.parse_statement(code)
        remove_paths_from_import_cst(cst_import, ["path"]) => cst.ImportFrom(...)
        remove_paths_from_import_cst(cst_import, ["path", "remove"]) => None
    ```
    """
    # Keep names not in paths_to_remove
    new_names = []
    for name in cst_import.names:
        if cst_to_path(name) not in paths_to_remove:
            new_names.append(name)
    #
    if not new_names:
        debug.trace(7, f"[early exit] remove_paths_from_import_cst(cst_import={cst_import}, paths_to_remove={paths_to_remove}) => None")
        return None
    # Store the new names
    result = cst_import.with_changes(names=new_names)
    debug.trace(7, f"remove_paths_from_import_cst(cst_import={cst_import!r}, paths_to_remove={paths_to_remove!r}) => {result!r}")
    return result


def skip_module(tree: cst.Module) -> cst.CSTNode:
    """
    Skip the module node
    """
    assert isinstance(tree, cst.Module), "Expected module node"
    return tree.body[0]


def skip_assign(tree: cst.CSTNode) -> cst.CSTNode:
    """
    Skip the assignment node
    """
    if isinstance(tree, cst.SimpleStatementLine):
        tree = tree.body[0]
    assert isinstance(tree, cst.Assign), "Expected assignment node"
    return tree.value


def extract_replaced_body(func: Callable, args: List[cst.Arg]) -> cst.CSTNode:
    """
    Extract replaced body from the source code
    ```
    func = lambda a, b: f"{a} {b}"
    args = [Arg(1), Arg(2)]
    extract_replaced_body(source, args) => 'f"{1} {2}"'
    ```
    """
    # Get source code of func
    source = inspect.getsource(func)
    source = source.strip()
    source = source[:-1] if source.endswith(",") else source

    # To tree (TODO4: omitting leading module node)
    tree = cst.parse_module(source)
    tree = skip_module(tree)
    # Lambda functions always is assigned to a variable
    if not isinstance(tree, cst.FunctionDef):
        tree = skip_assign(tree)
        assert isinstance(tree, cst.Lambda)
        
    # Extract parameters
    parameters = cst_to_paths(tree.params)
    tree = tree.body
    # Setup arguments
    args = [arg.value for arg in args]
    # Replace arguments
    class ReplaceArgs(cst.CSTTransformer):
        """Class for replacing arguments in function expansions"""
        def leave_Name(self, original_node, updated_node):
            """Replace ORIGINAL_NODE parameter name with UPDATED_NODE argument value"""
            if original_node.value in parameters:
                idx = parameters.index(original_node.value)
                if idx < len(args):
                    return args[idx]
            return updated_node
    tree = tree.visit(ReplaceArgs())

    # Remove indentation
    if isinstance(tree, cst.IndentedBlock):
        tree = tree.body[0]
    if isinstance(tree, cst.If):
        # for some reason, If statements always are inserted with bad indent
        tree = tree.with_changes(leading_lines=[cst.EmptyLine(indent=False)])

    # Return source
    return tree

#-------------------------------------------------------------------------------

class BaseTransformerStrategy:
    """Transformer base class"""

    def __init__(self, eq_call_table: Optional[List[EqCall]] = None) -> None:
        """Initialize BaseTransformerStrategy with optional EQ_CALL_TABLE"""
        if eq_call_table is None:
            eq_call_table = mezcla_to_standard
            if EQCALL_DATAFILE:
                eq_call_table = misc_utils.convert_python_data_to_instance(
                    EQCALL_DATAFILE, "mezcla.mezcla_to_standard", "EqCall",
                    EQCALL_FIELDS)
        self.unique_eq_calls: list[EqCall] = []
        """
        List of equivalent calls between Mezcla and standard, with all permutations precalculated
        to avoid recalculating them every time we want to find an equivalent call
        """
        self.unique_eq_calls = flatten_list([e.get_permutations() for e in eq_call_table])
        debug.trace_object(5, self, label="BaseTransformerStrategy instance")

    def insert_extra_params(self, eq_call: EqCall, args: dict) -> dict:
        """
        Insert extra parameters as CST arguments nodes
        ```
        original_args = { "a": Arg(1), "b": Arg(2) }
        eq_call = EqCall(
            extra_params = { "c": 3 }
        )
        insert_extra_params(eq_call, original_args) => {
            "a": Arg(1),
            "b": Arg(2),
            "c": Arg(3)
        }
        ```
        """
        debug.assertion(args is not None)
        if args is None:
            args = {}
        new_args = args.copy()
        if eq_call.extra_params is None:
            debug.trace(6, f"[early exit] BaseTransformerStrategy.insert_extra_params(args={args}) => {new_args}")
            return args
        for key, value in eq_call.extra_params.items():
            if key not in args:
                new_args[key] = value_to_arg(value)
        debug.trace(6, f"BaseTransformerStrategy.insert_extra_params(args={args}) => {new_args}")
        return new_args

    def get_replacement(self, path: str, args: List[cst.Arg]) -> Union[Tuple[str, List[cst.Arg]], cst.CSTNode]:
        """
        Get the function replacement

        Returns tuple of `(func_as_str, new_args_node)`
        """
        ## TODO: refactor this returns two different types of values
        # Find the equivalent call
        eq_call = self.find_eq_call(path, args)
        func = ""
        new_args_nodes = []
        if eq_call is None:
            debug.trace(5, f"[early exit] BaseTransformerStrategy.get_replacement(path={path}, args={args}) => {func}, {new_args_nodes}")
            return func, new_args_nodes
        # Replace args
        new_args_nodes = self.get_args_replacement(eq_call, args)
        # Replace func
        if Features.COPY_DEST_SOURCE in eq_call.features:
            func = extract_replaced_body(eq_call.dests[0].callable, new_args_nodes)
        else:
            func = self.eq_call_to_path(eq_call)
        #
        debug.trace(5, f"BaseTransformerStrategy.get_replacement(path={path}, args={args}) => {func}, {new_args_nodes}")
        return func, new_args_nodes

    def eq_call_to_path(self, eq_call: EqCall) -> str:
        """Get the path from the equivalent call"""
        # NOTE: must be implemented by the subclass
        raise NotImplementedError

    def find_eq_call(self, path: str, args: List[cst.Arg]) -> Optional[EqCall]:
        """Find the equivalent call"""
        # NOTE: must be implemented by the subclass
        raise NotImplementedError

    def get_args_replacement(self, eq_call: EqCall, args: List[cst.Arg]) -> dict:
        """Transform every argument to the equivalent argument"""
        raise NotImplementedError

    def is_condition_to_replace_met(self, eq_call: EqCall, args: List[cst.Arg]) -> bool:
        """Return if the condition to replace is met"""
        # NOTE: must be implemented by the subclass
        raise NotImplementedError

    def replace_args_keys(self, eq_call: EqCall, args: dict) -> dict:
        """Replace argument keys with the equivalent ones"""
        # NOTE: must be implemented by the subclass
        raise NotImplementedError

class ToStandard(BaseTransformerStrategy):
    """Mezcla to standard call conversion class"""

    def __init__(self, *args, **kwargs):
        debug.trace_expr(TL.VERBOSE, self, args, kwargs, delim="\n\t", prefix="in ToStandard.__init__({a})")
        super().__init__(*args, **kwargs)
    
    def find_eq_call(self, path: str, args: List[cst.Arg]) -> Optional[EqCall]:
        result = None
        for eq_call in self.unique_eq_calls:
            # Unique calls is supposed to have only one target
            target = eq_call.targets[0]
            if target.equals_to(path) or target.ends_equals_to(path):
                if self.is_condition_to_replace_met(eq_call, args):
                    result = eq_call
                    break
        debug.trace(6, f"ToStandard.find_eq_call(path={path}, args={args}) => {result}")
        return result

    def is_condition_to_replace_met(self, eq_call: EqCall, args: List[cst.Arg]) -> bool:
        if (not eq_call.condition) or (eq_call.condition.callable is None):
            debug.trace(6, f"[early exit] ToStandard.is_condition_to_replace_met(eq_call={eq_call}, args={args}) => missing callable condition")
            return True
        arguments = match_args(eq_call.targets[0], args)
        arguments = dict_to_func_args_list(eq_call.condition, arguments, eq_call)
        if not all_has_fixed_value(arguments):
            debug.trace(6, f"[early exit] ToStandard.is_condition_to_replace_met(eq_call={eq_call}, args={args}) => an CST argument node has not fixed or valid value")
            return True
        arguments = args_to_values(arguments)
        arguments = eq_call.condition(*arguments)
        debug.trace(6, f"ToStandard.is_condition_to_replace_met(eq_call={eq_call}, args={args}) => {arguments}")
        return arguments

    def get_args_replacement(self, eq_call: EqCall, args: List[cst.Arg]) -> dict:
        if Features.FORMAT_STRING in eq_call.features:
            args = format_strings_in_args(args)
        arguments = match_args(eq_call.targets[0], args)
        arguments = self.insert_extra_params(eq_call, arguments)
        arguments = self.replace_args_keys(eq_call, arguments)
        arguments = dict_to_func_args_list(eq_call.dests[0], arguments, eq_call, other_func=eq_call.targets[0])
        debug.trace(6, f"ToStandard.get_args_replacement(eq_call={eq_call}, args={args}) => {arguments}")
        return arguments

    def replace_args_keys(self, eq_call: EqCall, args: dict) -> dict:
        ## TODO3: restructure w/ single return call
        # pylint: disable=no-else-return
        result = {}
        ## TEST:
        if eq_call.eq_params is None:
            eq_call.eq_params = {}
        if eq_call.eq_params is None:
            debug.trace(7, f"[early exit] ToStandard.replace_args_keys(eq_call={eq_call}, args={args}) => {args}")
            return args
        else:
            for key, value in args.items():
                if key in eq_call.eq_params:
                    result[eq_call.eq_params[key]] = value
                else:
                    result[key] = value
        debug.trace(7, f"ToStandard.replace_args_keys(eq_call={eq_call}, args={args}) => {result}")
        return result

    def eq_call_to_path(self, eq_call: EqCall) -> str:
        result = eq_call.dests[0].path
        debug.trace(7, f"ToStandard.eq_call_to_path(eq_call={eq_call}) => {result}")
        return result

class ToMezcla(BaseTransformerStrategy):
    """Standard to Mezcla call conversion class"""

    def __init__(self, *args, **kwargs):
        debug.trace_expr(TL.VERBOSE, self, args, kwargs, delim="\n\t", prefix="in ToStandard.__init__({a})")
        super().__init__(*args, **kwargs)
    
    def find_eq_call(self, path: str, args: List[cst.Arg]) -> Optional[EqCall]:
        result = None
        for eq_call in self.unique_eq_calls:
            # Unique calls is supposed to have only one dest
            dest = eq_call.dests[0]
            if dest.equals_to(path) or dest.ends_equals_to(path):
                if self.is_condition_to_replace_met(eq_call, args):
                    result = eq_call
                    break
        debug.trace(7, f"ToMezcla.find_eq_call(func={path}, args={args}) => {result}")
        return result

    def is_condition_to_replace_met(self, eq_call: EqCall, args: List[cst.Arg]) -> bool:
        if (not eq_call.condition) or (eq_call.condition.callable is None):
            debug.trace(6, f"[early exit] ToMezcla.is_condition_to_replace_met(eq_call={eq_call}, args={args}) => missing condition callable")
            return True
        arguments = match_args(eq_call.dests[0], args)
        arguments = self.insert_extra_params(eq_call, arguments)
        arguments = self.replace_args_keys(eq_call, arguments)
        arguments = dict_to_func_args_list(eq_call.condition, arguments, eq_call)
        if not all_has_fixed_value(arguments):
            debug.trace(6, f"[early exit] ToMezcla.is_condition_to_replace_met(eq_call={eq_call}, args={args}) => an CST argument node has not fixed or valid value")
            return True
        arguments = args_to_values(arguments)
        result = eq_call.condition(*arguments)
        debug.trace(7, f"ToMezcla.is_condition_to_replace_met(eq_call={eq_call}, args={args}) => {result}")
        return result

    def get_args_replacement(self, eq_call: EqCall, args: List[cst.Arg]) -> dict:
        arguments = match_args(eq_call.dests[0], args)
        arguments = self.replace_args_keys(eq_call, arguments)
        arguments = self.insert_extra_params(eq_call, arguments)
        arguments = dict_to_func_args_list(eq_call.targets[0], arguments, eq_call, other_func=eq_call.dests[0])
        debug.trace(7, f"ToMezcla.get_args_replacement(eq_call={eq_call}, args={args}) => {arguments}")
        return arguments

    def replace_args_keys(self, eq_call: EqCall, args: dict) -> dict:
        result = {}
        ## TEST
        if eq_call.eq_params is None:
            eq_call.eq_params = {}
        if eq_call.eq_params is None:
            result = args
        else:
            for key, value in args.items():
                if key in eq_call.eq_params.values():
                    result[list(eq_call.eq_params.keys())[list(eq_call.eq_params.values()).index(key)] ] = value
                else:
                    result[key] = value
        debug.trace(7, f"ToMezcla.replace_args_keys(eq_call={eq_call}, args={args}) => {result}")
        return result

    def eq_call_to_path(self, eq_call: EqCall) -> str:
        return eq_call.targets[0].path

class StoreMetrics:
    """CST Transformer with metrics utilities"""

    def __init__(self) -> None:

        self.history = []
        """
        History of replacements, as strings
        ```
        self.history = [
            "os.remove => os.path.remove",
            "os.path.basename => os.path.basename"
            ...
        ]
        ``` 
        """

    @property
    def unique(self) -> int:
        """Get the number of unique replacements"""
        return len(set(self.history))

    @property
    def total(self) -> int:
        """Get the number of total replacements"""
        return len(self.history)

    def add_to_history(self, from_call: str, to_call: str = None) -> None:
        """Add replacement to metrics"""
        replacement_as_str = f"{from_call} --> {to_call}" if to_call else from_call
        self.history.append(replacement_as_str)

    def get_unique_history(self) -> List[Tuple[str, int]]:
        """Get the sorted history by amount of counts"""
        result = []
        for replacement in set(self.history):
            count = self.history.count(replacement)
            result.append((replacement, count))
        result = sorted(result, key=lambda x: x[1], reverse=True)
        return result

class StoreAliasesTransformer(cst.CSTTransformer):
    """Store aliases visitor"""

    def __init__(self) -> None:
        super().__init__()
        self.aliases = {}

    # pylint: disable=invalid-name
    def visit_ImportAlias(self, node: cst.ImportAlias) -> None:
        """Visit an ImportAlias node"""
        debug.trace(8, f"StoreAliasesTransformer.visit_ImportAlias(node={node})")
        if node.asname is None:
            return
        # Store asname alias for later replacement
        if isinstance(node.name, cst.Attribute):
            name = node.name.attr.value
        elif isinstance(node.name, cst.Name):
            name = node.name.value
        else:
            debug.assertion(False, "Unexpected condition in visit_ImportAlias")
            name = "unknown"
        asname = node.asname.name.value
        # Store the alias
        self.aliases[asname] = name

    def replace_alias_in_path(self, path: str) -> str:
        """Get the module name if it is an alias"""
        first_part = path.split(".")[0]
        result = self.aliases.get(first_part, first_part)
        result = ".".join([result] + path.split(".")[1:])
        debug.trace(9, f"StoreAliasesTransformer.replace_alias_in_path(path={path}) => {result}")
        return result

class ReplaceCallsTransformer(StoreAliasesTransformer, StoreMetrics):
    """Replace calls transformer to modify the CST"""

    def __init__(self, to_module: BaseTransformerStrategy) -> None:
        debug.trace(8, "ReplaceCallsTransformer.__init__()")
        StoreAliasesTransformer.__init__(self)
        StoreMetrics.__init__(self)
        self.to_module = to_module
        self.to_import = []
        self.removed = []
        self.keep = []

    # pylint: disable=invalid-name
    def leave_Module(
            self,
            original_node: cst.Module,
            updated_node: cst.Module
        ) -> cst.Module:
        """Leave a Module node"""
        # Add new imports
        new_body = list(updated_node.body)
        for module in set(self.to_import):
            new_body = [path_to_import(module)] + new_body
        self.to_import = []
        result = updated_node.with_changes(body=new_body)
        # Extract import paths of keep/removed references
        def extract_imports(list_of_paths: str) -> str:
            return [path.split(".")[0] for path in list_of_paths]
        imports_to_keep = extract_imports(self.keep)
        imports_to_remove = extract_imports(self.removed)
        # Substract the removed imports from the keep imports
        unused_removed_imports = []
        for path in imports_to_remove:
            if path not in imports_to_keep:
                unused_removed_imports.append(path)
        # Remove unused imports
        new_body = []
        for node in result.body:
            if not isinstance(node, cst.SimpleStatementLine):
                new_body.append(node)
                continue
            if isinstance(node.body[0], (cst.Import, cst.ImportFrom)):
                new_import_node = remove_paths_from_import_cst(node.body[0], unused_removed_imports)
                if new_import_node is not None:
                    new_node = node.with_changes(body=[new_import_node])
                    new_body.append(new_node)
            else:
                new_body.append(node)
        self.removed = []
        result = result.with_changes(body=new_body)
        #
        debug.trace(8, f"ReplaceCallsTransformer.leave_Module(original_node={original_node}, updated_node={updated_node}) => {result}")
        return result

    # pylint: disable=invalid-name
    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        """Leave a Call node"""
        new_node = updated_node
        if isinstance(updated_node.func, cst.Attribute):
            new_node = self.replace_call_if_needed(updated_node)
        else:
            self.keep.append(cst_to_path(updated_node))
        debug.trace(8, f"ReplaceCallsTransformer.leave_Call(original_node={original_node}, updated_node={updated_node}) => {new_node}")
        return new_node

    def replace_call_if_needed(
            self,
            updated_node: cst.Call
        ) -> cst.Call:
        """Replace the call if needed"""
        if not isinstance(updated_node.func.value, (cst.Attribute, cst.Name, cst.SimpleString)):
            debug.trace(7, f"[early exit 1] ReplaceCallsTransformer.replace_call_if_needed(updated_node={updated_node}) => skipping")
            return updated_node
        # Get module and method names
        path = cst_to_path(updated_node.func)
        path = self.replace_alias_in_path(path)
        # Get replacement
        new_path, new_args_nodes = self.to_module.get_replacement(
            path, updated_node.args
        )
        if not new_path:
            self.keep.append(path)
            debug.trace(7, f"[early exit 2] ReplaceCallsTransformer.replace_call_if_needed(updated_node={updated_node}) => skipping")
            return updated_node
        if isinstance(new_path, str):
            # We use the first components on a path is for
            # the import and the rest is for the function call
            #
            # Example path: "mezcla.debug.trace"
            # New import: from mezcla import debug
            # New call: debug.trace
            #
            if "." in new_path:
                import_path = ".".join(new_path.split(".")[:-1])
                call_path = ".".join(new_path.split(".")[-2:])
            else:
                import_path = ""
                call_path = new_path
            # Replace CST Call
            updated_node = updated_node.with_changes(
                func=path_to_cst(call_path),
                args=new_args_nodes
            )
            # Handle new imports
            if import_path:
                self.to_import.append(import_path)
            self.removed.append(path)
            self.add_to_history(path, new_path)
        elif isinstance(new_path, cst.CSTNode):
            # Replace CST Call directly
            updated_node = new_path
            self.add_to_history(path, "embedded code")
        else:
            raise ValueError(f"Error in replacement: {new_path}")
        debug.trace(7, f"ReplaceCallsTransformer.replace_call_if_needed(updated_node={updated_node}) => {updated_node}")
        return updated_node

class ReplaceMezclaWithWarningTransformer(StoreAliasesTransformer, StoreMetrics):
    """Modify the CST to insert warnings to Mezcla calls"""

    def __init__(self) -> None:
        StoreAliasesTransformer.__init__(self)
        StoreMetrics.__init__(self)
        debug.trace(8, "ReplaceMezclaWithWarningTransformer.__init__()")
        self.mezcla_modules = []

    # pylint: disable=invalid-name
    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        """Visit an ImportFrom node"""
        debug.trace(8, f"ReplaceMezclaWithWarningTransformer.visit_ImportFrom(node={node})")
        if node.module.value == "mezcla":
            for name in node.names:
                self.mezcla_modules.append(name.name.value)

    # pylint: disable=invalid-name
    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        """Leave a Call node"""
        ## TODO3: document better: what is being done? why leave_Call?
        new_node = updated_node
        if isinstance(updated_node.func, cst.Attribute):
            new_node = self.replace_with_warning_if_needed(updated_node)
        debug.trace(8, f"ReplaceMezclaWithWarningTransformer.leave_Call(original_node={original_node}, updated_node={updated_node}) => {new_node}")
        return new_node

    def replace_with_warning_if_needed(
            self,
            updated_node: cst.Call
        ) -> cst.Call:
        """Replace the call if needed"""
        if not isinstance(updated_node.func.value, (cst.Attribute, cst.Name, cst.SimpleString)):
            debug.trace(7, f"ReplaceCallsTransformer.replace_call_if_needed(original_node={updated_node}, updated_node={updated_node}) => skipping")
            return updated_node
        # Get module and method names
        path = cst_to_path(updated_node.func).split(".")[0]
        path = self.replace_alias_in_path(path)
        # Check if module is a Mezcla module, and replace call with warning comment
        if path in self.mezcla_modules:
            self.add_to_history(
                cst_to_path(updated_node),
            )
            return text_to_comments_node(f"WARNING not supported: {cst.Module([]).code_for_node(updated_node)}")
        debug.trace(7, f"ReplaceMezclaWithWarningTransformer.replace_with_warning_if_needed(updated_node={updated_node}) => {updated_node}")
        return updated_node


def transform(to_module, code: str, skip_warnings:bool=False) -> tuple[str,dict]:
    """
    Transform the code

    ```
    >>> code = (
    >>>    '''
    >>>    from mezcla import glue_helpers as gh
    >>>    gh.form_path("/tmp", "fubar")
    >>>    ''')
    >>> transform(ToStandard(), code)
    import os
    os.path.join("/tmp", "fubar")
    ```
    """
    debug.trace(6, f"in transform(to_module={to_module}, code='{code!r}')")
    ## TODO2: put this in a new class (e.g., MezclaToStandard)
    # Parse the code into a CST tree
    tree = cst.parse_module(code)
    input_has_validation_error = False
    if TRACE_DIFF:
        debug.trace(1, f"in code:\n{gh.indent_lines(code)}")
        in_tree = copy.deepcopy(tree)
        trace_node(in_tree, label="input tree", level=1)
    if VALIDATE_CST:
        try:
            in_tree.validate_types_deep()
        except:
            input_has_validation_error = True
            system.print_exception_info("input tree validation")

    # Replace calls in the tree
    # Two passes are needed to replace nested calls
    calls_transformer = ReplaceCallsTransformer(to_module)
    tree = tree.visit(calls_transformer)
    tree = tree.visit(calls_transformer)

    # Replace Mezcla calls with warning if not supported
    warning_transformer = ReplaceMezclaWithWarningTransformer()
    if not skip_warnings and isinstance(to_module, ToStandard):
        tree = tree.visit(warning_transformer)

    # Convert the tree back to code
    modified_code = tree.code
    if TRACE_DIFF:
        trace_node(tree, label="output tree", diff_node=in_tree, level=1)
        debug.trace(1, f"out code:\n{gh.indent_lines(modified_code)}")
        code_diff = misc_utils.string_diff(code, modified_code)
        debug.trace(1, f"code diff:\n{gh.indent_lines(code_diff)}")
    if VALIDATE_CST:
        try:
            tree.validate_types_deep()
        except:
            trace_exception_fn = (system.print_exception_info if input_has_validation_error
                                  else lambda task: debug.trace_exception(5, task))
            trace_exception_fn("output tree validation")

    # Build metrics
    metrics = {}
    # Call metrics
    metrics["number_calls_replaced"] = calls_transformer.total
    metrics["number_unique_calls_replaced"] = calls_transformer.unique
    metrics["calls_replaced"] = calls_transformer.get_unique_history()
    # Warning metrics
    metrics["number_warnings_added"] = warning_transformer.total
    metrics["number_unique_warnings_added"] = warning_transformer.unique
    metrics["warnings_added"] = warning_transformer.get_unique_history()
    # Total metrics
    metrics["total"] = 0 \
        + calls_transformer.total \
        + warning_transformer.total
    metrics["unique_total"] = 0 \
        + calls_transformer.unique \
        + warning_transformer.unique

    debug.trace(5, f"transform(...) => {modified_code!r}")
    return modified_code, metrics

#-------------------------------------------------------------------------------
    
class MezclaToStandardScript(Main):
    """Argument processing class to MezclaToStandard"""
    ## TODO2: Put non-argument processing in a separate class (e.g., MezclaToStandard)

    # Class-level member variables for arguments
    # (avoids need for class constructor)
    to_std = False
    to_mezcla = False
    metrics = False
    in_place = False
    skip_warnings = False

    def setup(self) -> None:
        """Process arguments"""
        debug.trace(5, "MezclaToStandardScript.setup()")
        self.to_std = self.get_parsed_option(TO_STD, self.to_std)
        self.to_mezcla = self.get_parsed_option(TO_MEZCLA, self.to_mezcla)
        self.metrics = self.get_parsed_option(METRICS, self.metrics)
        self.in_place = self.get_parsed_option(IN_PLACE, self.in_place)
        self.skip_warnings = self.get_parsed_option(SKIP_WARNINGS, self.skip_warnings)

    def show_continue_warning(self) -> None:
        """Show warning if user want to continue"""
        print(
            ## TODO3: make ansi escapes optional
            "\033[93m WARNING, THIS OPERATION WILL OVERRIDE:\n",
            f"{self.filename}\n",
            "Make sure you have a backup of the file before proceeding.\n\n",
            "Are you sure you want to continue? (yes/no): \033[0m",
            file=sys.stderr,
            end=""
        )
        want_to_continue = input().lower()
        # NOTE: we don't use single characters "y" as verification,
        #       because could be accidentally pressed
        if want_to_continue != "yes":
            debug.trace(5, "MezclaToStandardScript.run_main_step() => cancelled by user")
            system.exit("Operation cancelled by user")

    def print_metrics(self, metrics: dict) -> None:
        """Print metrics"""
        def print_total_with_perc(title, number, total, unique, total_unique):
            perc = (number / total) * 100 if total > 0 else 0
            unique_perc = (unique / total_unique) * 100 if total_unique > 0 else 0
            system.print_error(
                f"{title}:\t{number}\t({perc:.2f} %);\t{unique} unique ({unique_perc:.2f} %)",
            )
        def print_replacements(title, replacements):
            system.print_error(f"{title}:")
            system.print_error("\tnumber\tcall")
            while len(replacements) < 5:
                replacements.append(("", ""))
            for idx, (name, number) in enumerate(replacements):
                if not number:
                    number = "-"
                if not name:
                    name = "---"
                system.print_error(f"{idx + 1}.\t{number}\t{name}")
        system.print_error("====== Result Metrics ======")
        print_total_with_perc(
            "Total changes",
            metrics["total"],
            metrics["total"],
            metrics["unique_total"],
            metrics["unique_total"],
        )
        print_total_with_perc(
            "Calls replaced",
            metrics["number_calls_replaced"],
            metrics["total"],
            metrics["number_unique_calls_replaced"],
            metrics['unique_total'],
        )
        print_total_with_perc(
            "Warnings added",
            metrics["number_warnings_added"],
            metrics["total"],
            metrics["number_unique_warnings_added"],
            metrics['unique_total'],
        )
        print_replacements(
            "Calls replaced",
            metrics["calls_replaced"]
        )
        print_replacements(
            "Warnings added",
            metrics["warnings_added"]
        )
        system.print_error(f"Total time: {metrics['time']:.2f} seconds")
        system.print_error("============================")

    def read_code(self, filename: str) -> str:
        """Read code from filename, and throw exceptions if is invalid"""
        if not system.file_exists(filename):
            raise ValueError(f"File {filename} does not exist")
        code = system.read_file(filename)
        if not code:
            raise ValueError(f"File {filename} is empty")
        return code

    def run_main_step(self) -> None:
        """Process main script"""
        debug.trace(5, "MezclaToStandardScript.run_main_step()")
        if self.in_place:
            self.show_continue_warning()
        # Read code
        time_start = time.time()
        code = (self.read_code(self.filename) if (self.filename != "-")
                else self.read_entire_input())
        # Process
        if self.to_mezcla:
            to_module = ToMezcla()
        else:
            to_module = ToStandard()
        try:
            modified_code, metrics = transform(to_module, code,
                skip_warnings=self.skip_warnings)
        except:
            modified_code = ""
            metrics = {}
            system.print_exception_info("run_main_step")
        metrics['time'] = time.time() - time_start
        # Output
        if self.metrics:
            self.print_metrics(metrics)
        if self.in_place:
            system.write_file(self.filename, modified_code)
        else:
            print(modified_code)

def main():
    """Entry point"""
    ## TODO4: use main()
    app = MezclaToStandardScript(
        description=__doc__.format(script=gh.basename(__file__)),
        boolean_options = [
            (TO_STD, 'Convert Mezcla calls to standard calls'),
            (TO_MEZCLA, 'Convert standard calls to Mezcla calls'),
            (METRICS, 'Show metrics for the conversion'),
            (IN_PLACE, 'Modify the file in place, useful if you want to compare changes using Git'),
            (SKIP_WARNINGS, 'Skip warnings'),
        ],
        manual_input=True,
        skip_input=False,
    )
    app.run()

#-------------------------------------------------------------------------------
    
if __name__ == '__main__':
    main()
