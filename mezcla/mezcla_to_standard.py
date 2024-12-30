#! /usr/bin/env python
#
# Mezcla to Standard call conversion script
#
# TODO3: Look into making this table driven. Can't eval() be used to generate the EqCall specifications?
# TODO4: Try to create a table covering more of system.py and glue_helper.py.
#
# --------------------------------------------------------------------------------
# Sample input and output:
#
# - input
#
#   $ cat _simple_glue_helper_samples.py
#   from mezcla import glue_helpers as gh
#   gh.write_file("/tmp/fubar.list", "fubar.list")
#   gh.copy_file("/tmp/fubar.list", "/tmp/fubar.list1")
#   gh.delete_file("/tmp/fubar.list")
#   gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")
#   gh.form_path("/tmp", "fubar")
#
# - output
#
#   from mezcla import glue_helpers as gh
#   import os
#   # WARNING not supported: gh.write_file("/tmp/fubar.list", "fubar.list")
#   # WARNING not supporte: gh.copy_file("/tmp/fubar.list", "/tmp/fubar.list1")
#   os.remove("/tmp/fubar.list")
#   os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
#   os.path.join("/tmp", "fubar")
#
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

"""
Mezcla to Standard call conversion script
"""

# Standard modules
import io
import time
import sys
import logging
import inspect
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

# Installed module
import libcst as cst

# Local modules
from mezcla.main import Main
from mezcla import system
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import tpo_common as tpo

# Arguments
FILE = "file"
TO_STD = "to_standard"
TO_MEZCLA = "to_mezcla"
METRICS = "metrics"
IN_PLACE = "in_place"
SKIP_WARNINGS = "skip_warnings"

# Types
StrOrCallable = Union[str, Callable]
SingleOrMultipleStrOrCallable = Union[StrOrCallable, List[StrOrCallable], Tuple[StrOrCallable]]

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
    module = globals()[components[0]]
    # Iterate through the components to get the desired attribute
    for component in components[1:]:
        module = getattr(module, component)
    debug.trace(7, f"path_to_callable(func_string={path}) => {module}")
    return module

ArgsSpecs = collections.namedtuple('Specs',
    'args, kwargs, varargs, varkw, defaults, kwonlyargs, kwonlydefaults, annotations')
"""
Same as `inspect.FullArgSpec`, but separated `args` from `kwargs`
"""

def get_func_specs(func: callable) -> ArgsSpecs:
    """
    Get the function signature
    """
    if isinstance(func, str):
        func = path_to_callable(func)
    result = None
    if func.__module__ == "builtins":
        # Workaround for builtins
        if func.__name__ == "print":
            result = ArgsSpecs(
                args=[],
                kwargs=["sep", "end", "file", "flush"],
                varargs="values",
                varkw=None,
                defaults=[],
                kwonlyargs=[],
                kwonlydefaults={},
                annotations={}
            )
        ## NOTE: Add here more workarounds for builtins if needed
    else:
        func_specs = inspect.getfullargspec(func)
        # Separate args from kwargs, based on defaults
        new_args = func_specs.args
        new_kwargs = []
        if func_specs.defaults:
            new_kwargs = func_specs.args[-len(func_specs.defaults):]
            new_args = func_specs.args[:-len(func_specs.defaults)]
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
    elif func.__module__ == "builtins":
        result = func.__name__
    else:
        result = f"{func.__module__}.{func.__name__}"
    debug.trace(7, f"callable_to_path(func={func}) => {result}")
    return result

class CallDetails:
    """
    Class with details of a call, this is useful to
    store `callable`, func as `path` and `specs` of a function
    and avoid recalculating them every time
    """

    def __init__(self, func: StrOrCallable) -> None:
        self.func = func
        # Some local functions as lambda in parameters
        # cannot be converted to path or callable
        # but also is not required, so we ignore them
        self.callable = None
        try:
            self.callable = path_to_callable(func) if isinstance(func, str) else func
        except Exception:
            pass
        self.path = None
        try:
            self.path = func if isinstance(func, str) else callable_to_path(func)
        except Exception:
            pass
        self.specs = None
        try:
            self.specs = get_func_specs(func)
        except Exception:
            pass

    @staticmethod
    def to_list_of_call_details(funcs: SingleOrMultipleStrOrCallable) -> List['CallDetails']:
        """
        Convert a list of functions to a list of CallDetails objects
        """
        # Convert to list
        if isinstance(funcs, list):
            funcs = funcs
        elif isinstance(funcs, tuple):
            funcs = list(funcs)
        else:
            funcs = [funcs]
        # Process
        result = []
        for func in funcs:
            if isinstance(func, CallDetails):
                result.append(func)
            else:
                result.append(CallDetails(func))
        return result

    def equals_to(self, path: str) -> bool:
        """Compare if the path is equal to the call details path"""
        assert self.path, "CallDetails => path is None"
        return self.path == path

    def ends_equals_to(self, path: str) -> bool:
        """
        Compare if the path ends with the call details path
        ```
        "glue_helpers.get_temp_file" == "os.path.get_temp_file"
        ```
        """
        assert self.path, "CallDetails => path is None"
        return self.path.endswith("." + path)

    def __call__(self, *args, **kwargs):
        assert self.callable, "CallDetails => callable is None"
        return self.callable(*args, **kwargs)

    def __repr__(self) -> str:
        return f"CallDetails: {self.path}"

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
        target = gh.get_temp_file
        ```
        """

        self.dests = CallDetails.to_list_of_call_details(dests)
        """
        Standard method to be replaced.
        ```
        dest = tempfile.NamedTemporaryFile
        ```
        NOTE: some standard modules like `os` are loaded as `posix`,
        or `os.path` as `posixpath`, to fix this, you can set dest as string:
        ```
        dest = 'os.path.getsize'
        ```
        """

        self.condition = condition if isinstance(condition, CallDetails) else CallDetails(condition)
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

    def get_permutations(self) -> List['EqCall']:
        """
        Get all permutations of the equivalent call

        This is useful when dealing with multiple targets or destinations
        """
        # Return previous permutations
        if len(self.permutations) > 0:
            debug.trace(7, "EqCall.get_permutations() => memoized")
            return self.permutations

        # Otherwise calculate the permutations and store them:

        # Create all permutations
        result = []
        for target in self.targets:
            for dest in self.dests:
                result.append(EqCall(
                    targets=target.func,
                    dests=dest.func,
                    condition=self.condition.func,
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
    instances of the EQclass defined within it.
    Attributes:
        config_path (str): The path to the configuration file.
        eq_classes (list): A list to store instances of EQclass.
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
        Parses the config file in `config_path` and creates instences of EQclass for each element in it
        """
        with open(self.config_path, "r") as file:
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
                result = eval(code, {"__builtins__": {}}, allowed_names)
            return result

        if isinstance(dests, list) or isinstance(dests, tuple):
            for dest in dests:
                results.append(_parse_dest(dest))
        else:
            results.append(_parse_dest(dests))
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
            result = eval(code, {"__builtins__": {}}, {})
        return result
    
    def _parse_features(self, features:List[str]) -> List[Features]:
        """
        Parse the features list and return a list of Features objects
        """
        results = []
        for feature in features:
            if feature.endswith("FORMAT_STRING"):
                results.append(Features.FORMAT_STRING)
            elif feature.endswith("COPY_DEST_SOURCE"):
                results.append(Features.COPY_DEST_SOURCE)
            else:
                raise ValueError(f"Unsupported feature: {feature}")
        return results
        

# Custom Function replacements

def assertion_replacement(expression, message=None, assert_level=None):
    if expression:
        debug.trace(assert_level, message)

# Add equivalent calls between Mezcla and standard
mezcla_to_standard = [
    EqCall(
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
        (gh.file_exists, system.file_exists),
        "os.path.exists",
        eq_params={ "filename": "path" }
    ),
    EqCall(
        (gh.form_path, system.form_path),
        "os.path.join",
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
        tpo.debug_print,
        logging.debug,
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
        system.exit,
        sys.exit,
        eq_params={ "message": "status" }
    ),
    EqCall(
        system.open_file,
        open,
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
        system.round_num,
        round,
        eq_params={ "value": "number" },
        extra_params={ "ndigits": 6 }
    ),
    EqCall(
        system.round3,
        round,
        eq_params={ "num": "number" },
        extra_params={ "ndigits": 3 }
    ),
    EqCall(
        tpo.round_num,
        round,
        eq_params={ "num": "number" },
        extra_params={ "ndigits": 3 }
    ),
    EqCall(
        system.sleep,
        time.sleep,
        eq_params={ "num_seconds": "seconds" }
    ),
    EqCall(
        (system.print_exception_info, system.get_exception),
        sys.exc_info,
    ),
    EqCall(
        (
            system.to_string, system.to_str, system.to_unicode,
            tpo.normalize_unicode, tpo.ensure_unicode,
        ),
        str,
    ),
    EqCall(
        (system.to_float, system.safe_float),
        float,
    ),
    EqCall(
        (system.to_int, system.safe_int),
        int,
    ),
    EqCall(
        debug.assertion,
        dests=assertion_replacement,
        extra_params={ "assert_level": 1, "message": "debug assertion failed" },
        features=[Features.COPY_DEST_SOURCE]
    ),
    EqCall(
        system.getenv,
        dests=lambda var, default_value: os.environ.get(var) or default_value,
        features=[Features.COPY_DEST_SOURCE]
    ),
    EqCall(
        system.getenv_value,
        dests=lambda var, default: os.environ.get(var) or default,
        features=[Features.COPY_DEST_SOURCE]
    ),
    EqCall(
        system.getenv_int,
        dests=lambda var, default: int(os.environ.get(var)) or default,
        features=[Features.COPY_DEST_SOURCE]
    ),
    EqCall(
        system.getenv_bool,
        dests=lambda var, default: bool(os.environ.get(var)) or default,
        features=[Features.COPY_DEST_SOURCE]
    ),
    EqCall(
        system.getenv_text,
        dests=lambda var, default: str(os.environ.get(var)) or default,
        features=[Features.COPY_DEST_SOURCE]
    ),
    EqCall(
        system.getenv_number,
        dests=lambda var, default: float(os.environ.get(var)) or default,
        features=[Features.COPY_DEST_SOURCE]
    ),
]

def cst_to_path(tree: cst.CSTNode) -> str:
    """
    Convert CST Tree Node to a string path.
    ```
    code = "foo.bar.baz(arg1, arg2)"
    tree = libcst.parse_expression(code)
    cst_to_path(tree) =>"foo.bar.baz"
    ```
    """
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
        result = cst.Arg(cst.SimpleString(value=f'"{value}"'))
    elif isinstance(value, int):
        result = cst.Arg(cst.Integer(value=str(value)))
    elif isinstance(value, float):
        result = cst.Arg(cst.Float(value=str(value)))
    elif isinstance(value, bool):
        # OLD: result = cst.Arg(cst.Name(value=str(value)))
        result = cst.Arg(cst.Name(value='True' if value else 'False'))
    elif isinstance(value, io.TextIOWrapper):
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
    arg = cst.Arg(cst.SimpleString(value='text'))
    arg_to_value(arg) => 'text'
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
    func_spec = func.specs
    if func_spec is None:
        debug.trace(7, f"match_args(func={func}, cst_arguments={cst_arguments}) => {func_spec}")
        return {}
    arg_names = func_spec.args # name
    varargs_name = func_spec.varargs # *name
    kwarg_names = func_spec.kwargs # name = "value"

    # Separate between args and kwargs
    args, kwargs = [], []
    for idx, arg in enumerate(cst_arguments):
        if isinstance(arg, cst.Arg):
            if arg.keyword:
                kwargs.append(arg)
            else:
                # Check for positional arguments
                if len(args) >= len(arg_names) and not varargs_name:
                    if not kwarg_names:
                        continue
                    arg = arg.with_changes(keyword=cst.Name(value=(arg_names+kwarg_names)[idx]))
                    kwargs.append(arg)
                else:
                    args.append(arg)
        else:
            raise ValueError(f"Unsupported argument type: {type(arg)}")

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
        if not kwarg.keyword:
            continue
        if kwarg.keyword.value in kwarg_names:
            matched_args[kwarg.keyword.value] = kwarg

    return matched_args

def dict_to_func_args_list(func: CallDetails, args_dict: dict) -> List[cst.Arg]:
    """
    Convert a dictionary to a list of CST arguments nodes, this is the opposite of match_args(...)
    ```
    def foo(a, b=None):
        ...
    dict_to_func_args_list(
        foo,
        {
            "a": Arg(1),
            "b": Arg(2, keyword="b"),
            "c": Arg(3)
        }
    ) => [
        Arg(1),
        Arg(2, keyword="b")
    ]
    ```
    As you can see, this method remove extra arguments
    """
    # Extract function signature
    func_spec = func.specs
    if func_spec is None:
        result = list(args_dict.values())
        debug.trace(7, f"dict_to_func_args_list(func={func}, args_dict={args_dict}) => {result}")
        return result

    # Match positional arguments
    result = []
    for arg_name in func_spec.args:
        if arg_name in args_dict:
            result.append(args_dict[arg_name])
        else:
            break

    # Handle *args
    if func_spec.varargs in args_dict:
        varargs = args_dict[func_spec.varargs]
        if isinstance(varargs, list):
            result += varargs
        else:
            result.append(varargs)

    # Match keyword arguments
    for kwarg_name in func_spec.kwargs:
        if kwarg_name in args_dict:
            new_arg = args_dict[kwarg_name].with_changes(keyword=path_to_cst(kwarg_name))
            result.append(new_arg)

    result = flatten_list(result)
    result = remove_last_comma(result)

    debug.trace(7, f"dict_to_func_args_list(func={func}, args_dict={args_dict}) => {result}")
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
    debug.trace(7, f"flatten_list(list_to_flatten={list_to_flatten}) => {result}")
    return result

def text_to_comments_node(text: str) -> cst.Comment:
    """Convert text into a comment node"""
    # We convert the text into a single line comment,
    # Because using multiline comments can create
    # confusion if those lines are next to other comments
    text = text.replace("\n", " ")
    comment = cst.Comment(value=f"# {text}")
    debug.trace(9, f"text_to_comment_node(text={text}) => {comment}")
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
    result = []
    for name in value.split("{"):
        if "}" in name:
            name = name.split("}")[0].strip()
            name = name.split("!")[0]
            name = name.split(":")[0]
            result.append(name)
    debug.trace(9, f"get_format_names_in_string(value={value}) => {result}")
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
    debug.trace(9, f"create_string_dot_format_node(value={value}, format_args={format_args}) => {call_node}")
    return call_node

def get_keyword_name(arg: cst.Arg) -> Optional[str]:
    """
    Get the keyword name from the argument node
    """
    if arg.keyword:
        return arg.keyword.value
    return None

def filter_kwargs(kwargs: List[cst.Arg], names: List[str]) -> List[cst.Arg]:
    """
    Filter kwargs by the names
    """
    result = []
    for kwarg in kwargs:
        keyword = get_keyword_name(kwarg)
        if not keyword:
            continue
        if keyword in names:
            result.append(kwarg)
    debug.trace(9, f"filter_kwargs(names={names}) => {result}")
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
        return []
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
    debug.trace(7, f"format_strings_in_args(args={args}) => {result}")
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
    debug.trace(7, f"path_to_import(path={path}) => {result}")
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
        return None
    # Store the new names
    result = cst_import.with_changes(names=new_names)
    debug.trace(7, f"remove_paths_from_import_cst(cst_import={cst_import}, paths_to_remove={paths_to_remove}) => {result}")
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
    insert_args_in_source(source, args) => 'f"{1} {2}"'
    ```
    """
    # Get source code of func
    source = inspect.getsource(func)
    source = source.strip()
    source = source[:-1] if source.endswith(",") else source
    # To tree
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
        def leave_Name(self, original_node, updated_node):
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

class BaseTransformerStrategy:
    """Transformer base class"""

    def __init__(self) -> None:
        self.unique_eq_calls: list[EqCall] = []
        """
        List of equivalent calls between Mezcla and standard, with all permutations precalculated
        to avoid recalculating them every time we want to find an equivalent call
        """
        self.unique_eq_calls = flatten_list([e.get_permutations() for e in mezcla_to_standard])

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
        new_args = args.copy()
        if eq_call.extra_params is None:
            return args
        for key, value in eq_call.extra_params.items():
            if key not in args:
                new_args[key] = value_to_arg(value)
        debug.trace(6, f"BaseTransformerStrategy.insert_extra_params(args={args}) => {new_args}")
        return new_args

    ## TODO: refactor this returns two different types of values
    def get_replacement(self, path: str, args: List[cst.Arg]) -> Union[Tuple[str, List[cst.Arg]], cst.CSTNode]:
        """
        Get the function replacement

        Returns tuple of `(func_as_str, new_args_node)`
        """
        # Find the equivalent call
        eq_call = self.find_eq_call(path, args)
        func = ""
        new_args_nodes = []
        if eq_call is None:
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
        if eq_call.condition.callable is None:
            return True
        arguments = match_args(eq_call.targets[0], args)
        arguments = dict_to_func_args_list(eq_call.condition, arguments)
        if not all_has_fixed_value(arguments):
            debug.trace(6, f"ToStandard.is_condition_to_replace_met(eq_call={eq_call}, args={args}) => an CST argument node has not fixed or valid value")
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
        arguments = dict_to_func_args_list(eq_call.dests[0], arguments)
        debug.trace(6, f"ToStandard.get_args_replacement(eq_call={eq_call}, args={args}) => {arguments}")
        return arguments

    def replace_args_keys(self, eq_call: EqCall, args: dict) -> dict:
        result = {}
        if eq_call.eq_params is None:
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
        if eq_call.condition.callable is None:
            return True
        arguments = match_args(eq_call.dests[0], args)
        arguments = self.insert_extra_params(eq_call, arguments)
        arguments = self.replace_args_keys(eq_call, arguments)
        arguments = dict_to_func_args_list(eq_call.condition, arguments)
        if not all_has_fixed_value(arguments):
            debug.trace(6, f"ToMezcla.is_condition_to_replace_met(eq_call={eq_call}, args={args}) => an CST argument node has not fixed or valid value")
            return True
        arguments = args_to_values(arguments)
        result = eq_call.condition(*arguments)
        debug.trace(7, f"ToMezcla.is_condition_to_replace_met(eq_call={eq_call}, args={args}) => {result}")
        return result

    def get_args_replacement(self, eq_call: EqCall, args: List[cst.Arg]) -> dict:
        arguments = match_args(eq_call.dests[0], args)
        arguments = self.replace_args_keys(eq_call, arguments)
        arguments = self.insert_extra_params(eq_call, arguments)
        arguments = dict_to_func_args_list(eq_call.targets[0], arguments)
        debug.trace(7, f"ToMezcla.get_args_replacement(eq_call={eq_call}, args={args}) => {arguments}")
        return arguments

    def replace_args_keys(self, eq_call: EqCall, args: dict) -> dict:
        result = {}
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
            debug.trace(7, f"ReplaceCallsTransformer.replace_call_if_needed(updated_node={updated_node}) => skipping")
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
            debug.trace(7, f"ReplaceCallsTransformer.replace_call_if_needed(updated_node={updated_node}) => skipping")
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
    code = \"\"\"
        from mezcla import glue_helpers as gh
        gh.form_path("/tmp", "fubar")
    \"\"\"
    transform(ToStandard(), code) => \"\"\"
        import os
        os.path.join("/tmp", "fubar")
    \"\"\"
    ```
    """
    # Parse the code into a CST tree
    tree = cst.parse_module(code)

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

    debug.trace(5, f"transform(to_module={to_module}, code='{code}') => {modified_code}")
    return modified_code, metrics

class MezclaToStandardScript(Main):
    """Argument processing class to MezclaToStandard"""

    # Class-level member variables for arguments
    # (avoids need for class constructor)
    file = ""
    to_std = False
    to_mezcla = False
    metrics = False
    in_place = False
    skip_warnings = False

    def setup(self) -> None:
        """Process arguments"""
        debug.trace(5, "MezclaToStandardScript.setup()")
        self.file = self.get_parsed_argument(FILE, self.file)
        self.to_std = self.has_parsed_option(TO_STD)
        self.to_mezcla = self.has_parsed_option(TO_MEZCLA)
        self.metrics = self.has_parsed_option(METRICS)
        self.in_place = self.has_parsed_option(IN_PLACE)
        self.skip_warnings = self.has_parsed_option(SKIP_WARNINGS)

    def show_continue_warning(self) -> None:
        """Show warning if user want to continue"""
        print(
            "\033[93m WARNING, THIS OPERATION WILL OVERRIDE:\n",
            f"{self.file}\n",
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
        code = self.read_code(self.file)
        # Process
        if self.to_mezcla:
            to_module = ToMezcla()
        else:
            to_module = ToStandard()
        modified_code, metrics = transform(
            to_module,
            code,
            skip_warnings=self.skip_warnings
        )
        metrics['time'] = time.time() - time_start
        # Output
        if self.metrics:
            self.print_metrics(metrics)
        if self.in_place:
            system.write_file(self.file, modified_code)
        else:
            print(modified_code)

if __name__ == '__main__':
    ## TODO4: use main()
    app = MezclaToStandardScript(
        description = __doc__,
        positional_arguments = [
            (FILE, 'Python script to run with Mezcla-to-Standard conversion')
        ],
        boolean_options = [
            (TO_STD, 'Convert Mezcla calls to standard calls'),
            (TO_MEZCLA, 'Convert standard calls to Mezcla calls'),
            (METRICS, 'Show metrics for the conversion'),
            (IN_PLACE, 'Modify the file in place, useful if you want to compare changes using Git'),
            (SKIP_WARNINGS, 'Skip warnings'),
        ],
        manual_input = True,
    )
    app.run()
