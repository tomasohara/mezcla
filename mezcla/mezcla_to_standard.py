#! /usr/bin/env python
#
# Mezcla to Standard call conversion script
#
# TODO3: Look into making this table driven. Can't eval() be used to generate the EqCall specifications?
# TODO4: Try to create a table covering more of system.py and glue_helper.py.  
#
#--------------------------------------------------------------------------------
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
#--------------------------------------------------------------------------------
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
#--------------------------------------------------------------------------------
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
    Optional, Tuple,
)
import tempfile
from enum import Enum
# Imports used to convert string to callable
# pylint: disable=unused-import
import os

# Installed module
import libcst as cst

# Local modules
from mezcla.main import Main
from mezcla import system
from mezcla import debug
from mezcla import glue_helpers as gh

# Arguments
FILE = "file"
TO_STD = "to_standard"
TO_MEZCLA = "to_mezcla"
METRICS = "metrics"

class EqCall:
    """
    Mezcla to standard equivalent call class
    """

    def __init__(
            self,
            target: callable,
            dest: callable,
            condition: Optional[callable] = None,
            eq_params: Optional[dict] = None,
            extra_params: Optional[dict] = None,
            features: list = []
        ) -> None:
        self.target = target
        """
        Mezcla method to be replaced.
        ```
        target = gh.get_temp_file
        ```
        """

        self.dest = dest
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

        self.condition = condition
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

        self.features = features
        """
        Extra features to be used in the replacement
        """

    def get_permutations(self) -> list:
        """
        Get all permutations of the equivalent call,

        This is useful when dealing with multiple targets or destinations
        """
        # Group all targets
        targets = []
        if isinstance(self.target, tuple):
            targets = list(self.target)
        elif isinstance(self.target, list):
            targets = self.target
        else:
            targets = [self.target]
        # Group all destinations
        dests = []
        if isinstance(self.dest, tuple):
            dests += list(self.dest)
        elif isinstance(self.dest, list):
            dests += self.dest
        else:
            dests.append(self.dest)
        # Create all permutations
        result = []
        for target in targets:
            for dest in dests:
                result.append(EqCall(
                    target=target,
                    dest=dest,
                    condition=self.condition,
                    eq_params=self.eq_params,
                    extra_params=self.extra_params,
                    features=self.features
                ))
        debug.trace(7, f"EqCall.get_permutations() => {result}")
        return result

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

# Add equivalent calls between Mezcla and standard
mezcla_to_standard = [
    EqCall(
        gh.get_temp_file,
        tempfile.NamedTemporaryFile,
    ),
    EqCall(
        gh.basename,
        "os.path.basename",
    ),
    EqCall(
        gh.dir_path,
        "os.path.dirname",
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
        (debug.trace, debug.trace_fmt, debug.trace_fmtd),
        logging.debug,
        condition = lambda level: level > 3,
        eq_params = { "text": "msg" },
        extra_params = { "level": 4 },
        features=[Features.FORMAT_STRING]
    ),
    EqCall(
        (debug.trace, debug.trace_fmt, debug.trace_fmtd),
        logging.info,
        condition = lambda level: 2 < level <= 3,
        eq_params = { "text": "msg" },
        extra_params = { "level": 3 }
    ),
    EqCall(
        (debug.trace, debug.trace_fmt, debug.trace_fmtd),
        logging.warning,
        condition = lambda level: 1 < level <= 2,
        eq_params = { "text": "msg" },
        extra_params = { "level": 2 }
    ),
    EqCall(
        (debug.trace, debug.trace_fmt, debug.trace_fmtd),
        logging.error,
        condition = lambda level: 0 < level <= 1,
        eq_params = { "text": "msg" },
        extra_params  = { "level": 1 }
    ),
    EqCall(
        system.print_error,
        print,
        eq_params={ "text": "values" },
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
        extra_params={ "ndigits": 6 }
    ),
    EqCall(
        system.round3,
        round,
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
]

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
        result = bool(arg.value.value)
    else:
        raise ValueError(f"Unsupported CST Argument child node type: {type(arg.value)}")
    debug.trace(7, f"arg_to_value({arg}) => {result}")
    return result

def has_fixed_value(arg: cst.Arg) -> bool:
    """Check if an CST argument node has a fixed value"""
    result = isinstance(arg.value, (cst.SimpleString, cst.Integer, cst.Float, cst.Name))
    debug.trace(7, f"has_fixed_value(arg={arg}) => {result}")
    return result

def all_has_fixed_value(args: list) -> bool:
    """Check if any CST argument node has a fixed value"""
    result = all(has_fixed_value(arg) for arg in args)
    debug.trace(7, f"any_has_fixed_value(args={args}) => {result}")
    return result

def args_to_values(args: list) -> list:
    """Convert a list of CST arguments nodes to a list of values objects"""
    debug.trace(7, "args_to_values(args) => list")
    return [arg_to_value(arg) for arg in args]

def remove_last_comma(args: list) -> list:
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

def string_to_callable(func_string):
    """
    Converts a string representing a function into the actual callable function.
    
    Parameters:
    func_string (str): The string representing the function, e.g., "os.remove".
    
    Returns:
    callable: The actual function.
    """
    components = func_string.split('.')
    # Get the base module from the global namespace
    module = globals()[components[0]]
    # Iterate through the components to get the desired attribute
    for component in components[1:]:
        module = getattr(module, component)
    debug.trace(7, f"string_to_callable(func_string={func_string}) => {module}")
    return module

def match_args(func: callable, args: list, kwargs: dict) -> dict:
    """
    Match the arguments to the function signature
    ```
    def foo(a, b, c):
        ...
    match_args(foo, [1, 2, 3], {}) => {
        "a": 1,
        "b": 2,
        "c": 3
    }
    ```
    """
    if isinstance(func, str):
        func = string_to_callable(func)
    target_spec = inspect.getfullargspec(func)
    # Extract arguments
    arguments = dict(zip(target_spec.args, args))
    # Extract *arguments
    if target_spec.varargs:
        arguments[target_spec.varargs] = args[len(target_spec.args):]
    # Extract **arguments
    if target_spec.varkw:
        arguments[target_spec.varkw] = kwargs
    debug.trace(7, f"match_args(func={func}, args={args}, kwargs={kwargs}) => {arguments}")
    return arguments

def flatten_list(list_to_flatten: list) -> list:
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

def get_module_func(func) -> Tuple:
    """
    Get the module and function from callable object
    ```
    import some_module
    get_module_func(some_module.foo) => ('some_module', 'foo')
    ```
    """
    result = None
    if isinstance(func, str):
        result = func.rsplit('.', 1)
    elif func.__module__ == "builtins":
        result = None, func.__name__
    else:
        result = func.__module__, func.__name__
    debug.trace(7, f"get_module_func(func={func}) => {result}")
    return result

def get_module_node_to_name(module_node) -> str:
    """Get the module name from the module node"""
    if isinstance(module_node, cst.Attribute):
        return get_module_node_to_name(module_node.value)
    if isinstance(module_node, (cst.Name, cst.SimpleString)):
        name = module_node.value
        debug.trace(9, f"StoreAliasesTransformer.module_node_to_name(module_node={module_node}) => {name}")
        return name
    raise ValueError(f"Unsupported module node type: {type(module_node)}")

def text_to_comments_node(text: str) -> cst.Comment:
    """Convert text into a comment node"""
    # We convert the text into a single line comment,
    # Because using multiline comments can create
    # confusion if those lines are next to other comments
    text = text.replace("\n", " ")
    comment = cst.Comment(value=f"# {text}")
    debug.trace(9, f"text_to_comment_node(text={text}) => {comment}")
    return comment

def get_format_names_in_string(value: str) -> list:
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
            result.append(name.split("}")[0].strip())
    debug.trace(9, f"get_format_names_in_string(value={value}) => {result}")
    return result

def create_string_dot_format_node(value: str, format_args: list) -> cst.Call:
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

def filter_kwargs(kwargs: list, names: list) -> list:
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

def format_strings_in_args(args: list) -> dict:
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
    result = remove_last_comma(result)
    debug.trace(7, f"format_strings_in_args(args={args}) => {result}")
    return result

class BaseTransformerStrategy:
    """Transformer base class"""

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

    def filter_args_by_function(self, func: callable, args: dict) -> dict:
        """
        Filter the arguments to match the function signature
        ```
        def foo(a, b, c):
            ...
        args = {
            "a": 1,
            "b": 2,
            "d": 3
        }
        filter_args_by_function(foo, args) => {
            "a": 1,
            "b": 2
        }
        ```
        """
        if isinstance(func, str):
            func = string_to_callable(func)
        result = {}
        try:
            for key in inspect.getfullargspec(func).args:
                if key in args:
                    result[key] = args[key]
        except TypeError:
            result = args
        except ValueError:
            result = args
        debug.trace(6, f"BaseTransformerStrategy.filter_args_by_function(func={func}, args={args}) => {result}")
        return result

    def get_replacement(self, module, func, args) -> Tuple:
        """
        Get the function replacement

        Returns tuple of `(new_module_node, new_func_node, new_args_node)`
        """
        eq_call = self.find_eq_call(module, func, args)
        if eq_call is None:
            return None, None, []
        new_module, new_func = self.eq_call_to_module_func(eq_call)
        # Create the new module node
        if new_module is None:
            new_import_node = None
            new_value_node = None
        elif "." in new_module:
            new_import_node = cst.Name(new_module.split('.')[0])
            new_value_node = cst.Attribute(
                value=new_import_node,
                attr=cst.Name(new_module.split('.')[1])
            )
        else:
            new_import_node = cst.Name(new_module)
            new_value_node = new_import_node
        # Create the new function node
        if new_module is None:
            new_func_node = cst.Name(new_func)
        else:
            new_func_node = cst.Attribute(value=new_value_node, attr=cst.Name(new_func))
        # Create the new arguments nodes
        new_args_nodes = self.get_args_replacement(eq_call, args, []) ## TODO: add kwargs
        debug.trace(5, f"BaseTransformerStrategy.get_replacement(module={module}, func={func}, args={args}) => {new_module}, {new_func_node}, {new_args_nodes}")
        return new_import_node, new_func_node, new_args_nodes

    def eq_call_to_module_func(self, eq_call: EqCall) -> Tuple:
        """Get the module and function from the equivalent call"""
        # NOTE: must be implemented by the subclass
        raise NotImplementedError

    def find_eq_call(self, module: str, func: str, args: list) -> Optional[EqCall]:
        """Find the equivalent call"""
        # NOTE: must be implemented by the subclass
        raise NotImplementedError

    def get_args_replacement(self, eq_call: EqCall, args: list, kwargs: dict) -> dict:
        """Transform every argument to the equivalent argument"""
        raise NotImplementedError

    def is_condition_to_replace_met(self, eq_call: EqCall, args: list) -> bool:
        """Return if the condition to replace is met"""
        # NOTE: must be implemented by the subclass
        raise NotImplementedError

    def replace_args_keys(self, eq_call: EqCall, args: dict) -> dict:
        """Replace argument keys with the equivalent ones"""
        # NOTE: must be implemented by the subclass
        raise NotImplementedError

class ToStandard(BaseTransformerStrategy):
    """Mezcla to standard call conversion class"""

    def find_eq_call(self, module: str, func: str, args: list) -> Optional[EqCall]:
        result = None
        all_eq_calls = [e.get_permutations() for e in mezcla_to_standard]
        all_eq_calls = flatten_list(all_eq_calls)
        for eq_call in all_eq_calls:
            target_module, target_func = get_module_func(eq_call.target)
            if target_module is None:
                pass
            elif module not in target_module:
                continue
            if func in target_func:
                if self.is_condition_to_replace_met(eq_call, args):
                    result = eq_call
                    break
        debug.trace(6, f"ToStandard.find_eq_call(module={module}, func={func}, args={args}) => {result}")
        return result

    def is_condition_to_replace_met(self, eq_call: EqCall, args: list) -> bool:
        if eq_call.condition is None:
            return True
        arguments = match_args(eq_call.target, args, {})
        arguments = self.filter_args_by_function(eq_call.condition, arguments)
        arguments = arguments.values()
        if not all_has_fixed_value(arguments):
            debug.trace(6, f"ToStandard.is_condition_to_replace_met(eq_call={eq_call}, args={args}) => an CST argument node has not fixed or valid value")
            return True
        arguments = args_to_values(arguments)
        result = eq_call.condition(*arguments)
        debug.trace(6, f"ToStandard.is_condition_to_replace_met(eq_call={eq_call}, args={args}) => {result}")
        return result

    def get_args_replacement(self, eq_call: EqCall, args: list, kwargs: dict) -> dict:
        if Features.FORMAT_STRING in eq_call.features:
            args = format_strings_in_args(args)
        arguments = match_args(eq_call.target, args, kwargs)
        arguments = self.insert_extra_params(eq_call, arguments)
        arguments = self.replace_args_keys(eq_call, arguments)
        arguments = self.filter_args_by_function(eq_call.dest, arguments)
        result = flatten_list(list(arguments.values()))
        result = remove_last_comma(result)
        debug.trace(6, f"ToStandard.get_args_replacement(eq_call={eq_call}, args={args}, kwargs={kwargs}) => {result}")
        return result

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

    def eq_call_to_module_func(self, eq_call: EqCall) -> Tuple:
        result = get_module_func(eq_call.dest)
        debug.trace(7, f"ToStandard.eq_call_to_module_func(eq_call={eq_call}) => {result}")
        return result

class ToMezcla(BaseTransformerStrategy):
    """Standard to Mezcla call conversion class"""

    def find_eq_call(self, module: str, func: str, args: list) -> Optional[EqCall]:
        result = None
        all_eq_calls = [e.get_permutations() for e in mezcla_to_standard]
        all_eq_calls = flatten_list(all_eq_calls)
        for eq_call in all_eq_calls:
            dest_module, dest_func = get_module_func(eq_call.dest)
            if dest_module is None:
                pass
            elif module not in dest_module:
                continue
            if func in dest_func:
                if self.is_condition_to_replace_met(eq_call, args):
                    result = eq_call
                    break
        debug.trace(7, f"ToMezcla.find_eq_call(module={module}, func={func}, args={args}) => {result}")
        return result

    def is_condition_to_replace_met(self, eq_call: EqCall, args: list) -> bool:
        if eq_call.condition is None:
            return True
        arguments = match_args(eq_call.dest, args, {})
        arguments = self.insert_extra_params(eq_call, arguments)
        arguments = self.replace_args_keys(eq_call, arguments)
        arguments = self.filter_args_by_function(eq_call.condition, arguments)
        arguments = arguments.values()
        if not all_has_fixed_value(arguments):
            debug.trace(6, f"ToMezcla.is_condition_to_replace_met(eq_call={eq_call}, args={args}) => an CST argument node has not fixed or valid value")
            return True
        arguments = args_to_values(arguments)
        result = eq_call.condition(*arguments)
        debug.trace(7, f"ToMezcla.is_condition_to_replace_met(eq_call={eq_call}, args={args}) => {result}")
        return result

    def get_args_replacement(self, eq_call: EqCall, args: list, kwargs: dict) -> dict:
        arguments = match_args(eq_call.dest, args, kwargs)
        arguments = self.replace_args_keys(eq_call, arguments)
        arguments = self.insert_extra_params(eq_call, arguments)
        arguments = self.filter_args_by_function(eq_call.target, arguments)
        result = flatten_list(list(arguments.values()))
        result = remove_last_comma(result)
        debug.trace(7, f"ToMezcla.get_args_replacement(eq_call={eq_call}, args={args}, kwargs={kwargs}) => {result}")
        return result

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

    def eq_call_to_module_func(self, eq_call: EqCall) -> Tuple:
        return get_module_func(eq_call.target)

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

    def alias_to_module(self, module_name: str) -> str:
        """Get the module name if it is an alias"""
        result = self.aliases.get(module_name, module_name)
        debug.trace(9, f"StoreAliasesTransformer.alias_to_module(module_name={module_name}) => {result}")
        return result

class ReplaceCallsTransformer(StoreAliasesTransformer):
    """Replace calls transformer to modify the CST"""

    def __init__(self, to_module: BaseTransformerStrategy) -> None:
        debug.trace(8, "ReplaceCallsTransformer.__init__()")
        super().__init__()
        self.to_module = to_module
        self.to_import = []
        self.amount_replaced = 0

    def append_import_if_unique(self, new_import: cst.Name) -> None:
        """Append the import if unique"""
        debug.trace(9, f"ReplaceCallsTransformer.append_import_if_unique(new_import={new_import})")
        current_imports = [node.value for node in self.to_import]
        if new_import.value in current_imports:
            return
        self.to_import.append(new_import)

    # pylint: disable=invalid-name
    def leave_Module(
            self,
            original_node: cst.Module,
            updated_node: cst.Module
        ) -> cst.Module:
        """Leave a Module node"""
        new_body = list(updated_node.body)
        for module in self.to_import:
            new_import_node = cst.SimpleStatementLine(
                body=[
                    cst.Import(
                        names=[cst.ImportAlias(name=module, asname=None)]
                    )
                ]
            )
            new_body = [new_import_node] + new_body
        result = updated_node.with_changes(body=new_body)
        debug.trace(8, f"ReplaceCallsTransformer.leave_Module(original_node={original_node}, updated_node={updated_node}) => {result}")
        return result

    # pylint: disable=invalid-name
    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        """Leave a Call node"""
        new_node = updated_node
        if isinstance(original_node.func, cst.Attribute):
            new_node = self.replace_call_if_needed(original_node, updated_node)
        debug.trace(8, f"ReplaceCallsTransformer.leave_Call(original_node={original_node}, updated_node={updated_node}) => {new_node}")
        return new_node

    def replace_call_if_needed(
            self,
            original_node: cst.Call,
            updated_node: cst.Call
        ) -> cst.Call:
        """Replace the call if needed"""
        if not isinstance(original_node.func.value, (cst.Attribute, cst.Name, cst.SimpleString)):
            debug.trace(7, f"ReplaceCallsTransformer.replace_call_if_needed(original_node={original_node}, updated_node={updated_node}) => skipping")
            return updated_node
        # Get module and method names
        module_name = get_module_node_to_name(original_node.func)
        module_name = self.alias_to_module(module_name)
        # Get replacement
        new_module, new_func_node, new_args_nodes = self.to_module.get_replacement(
            module_name, original_node.func.attr.value, original_node.args
        )
        # Replace if replacement found
        if new_func_node:
            self.amount_replaced += 1
            updated_node = updated_node.with_changes(
                func=new_func_node,
                args=new_args_nodes
            )
        if new_module:
            self.append_import_if_unique(new_module)
        debug.trace(7, f"ReplaceCallsTransformer.replace_call_if_needed(original_node={original_node}, updated_node={updated_node}) => {updated_node}")
        return updated_node

class ReplaceMezclaWithWarningTransformer(StoreAliasesTransformer):
    """Modify the CST to insert warnings to Mezcla calls"""

    def __init__(self) -> None:
        super().__init__()
        debug.trace(8, "ReplaceMezclaWithWarningTransformer.__init__()")
        self.mezcla_modules = []
        self.amount_replaced = 0

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
        if isinstance(original_node.func, cst.Attribute):
            new_node = self.replace_with_warning_if_needed(original_node, updated_node)
        debug.trace(8, f"ReplaceMezclaWithWarningTransformer.leave_Call(original_node={original_node}, updated_node={updated_node}) => {new_node}")
        return new_node

    def replace_with_warning_if_needed(
            self,
            original_node: cst.Call,
            updated_node: cst.Call
        ) -> cst.Call:
        """Replace the call if needed"""
        if not isinstance(original_node.func.value, (cst.Attribute, cst.Name, cst.SimpleString)):
            debug.trace(7, f"ReplaceCallsTransformer.replace_call_if_needed(original_node={original_node}, updated_node={updated_node}) => skipping")
            return updated_node
        # Get module and method names
        module_name = get_module_node_to_name(original_node.func)
        module_name = self.alias_to_module(module_name)
        # Check if module is a Mezcla module, and replace call with warning comment
        if module_name in self.mezcla_modules:
            self.amount_replaced += 1
            return text_to_comments_node(f"WARNING not supported: {cst.Module([]).code_for_node(original_node)}")
        debug.trace(7, f"ReplaceMezclaWithWarningTransformer.replace_with_warning_if_needed(original_node={original_node}, updated_node={updated_node}) => {updated_node}")
        return updated_node

def transform(to_module, code: str, with_metrics: bool = False) -> str:
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
    calls_transformer = ReplaceCallsTransformer(to_module)
    tree = tree.visit(calls_transformer)

    # Replace Mezcla calls with warning if not supported
    warning_transformer = ReplaceMezclaWithWarningTransformer()
    if isinstance(to_module, ToStandard):
        tree = tree.visit(warning_transformer)

    # Show metrics
    if with_metrics:
        total = calls_transformer.amount_replaced + warning_transformer.amount_replaced
        perc = (calls_transformer.amount_replaced / total) * 100 if total > 0 else 0
        perc_message = f"\t({perc:.2f} %)" if warning_transformer.amount_replaced > 0 else ""
        print(
            f"Calls replaced:\t{calls_transformer.amount_replaced}{perc_message}",
            file=sys.stderr
        )
        print(
            f"Warnings added:\t{warning_transformer.amount_replaced}",
            file=sys.stderr
        )

    # Convert the tree back to code
    modified_code = tree.code

    # Remove unused imports
    #
    # We need to temporarily store the code in a file to run pycln on
    temp_file = gh.get_temp_file() + "a.py"
    system.write_file(
        filename=temp_file,
        text=modified_code
    )
    gh.run(f"pycln -a {temp_file}")
    modified_code = system.read_file(temp_file)

    debug.trace(5, f"transform(to_module={to_module}, code='{code}') => {modified_code}")
    return modified_code

class MezclaToStandardScript(Main):
    """Argument processing class to MezclaToStandard"""

    # Class-level member variables for arguments
    # (avoids need for class constructor)
    file = ""
    to_std = False
    to_mezcla = False
    metrics = False

    def setup(self) -> None:
        """Process arguments"""
        debug.trace(5, "MezclaToStandardScript.setup()")
        self.file = self.get_parsed_argument(FILE, self.file)
        self.to_std = self.has_parsed_option(TO_STD)
        self.to_mezcla = self.has_parsed_option(TO_MEZCLA)
        self.metrics = self.has_parsed_option(METRICS)

    def run_main_step(self) -> None:
        """Process main script"""
        debug.trace(5, "MezclaToStandardScript.run_main_step()")
        code = system.read_file(self.file)
        if not code:
            raise ValueError(f"File {self.file} is empty")
        if self.to_mezcla:
            to_module = ToMezcla()
        else:
            to_module = ToStandard()
        modified_code = transform(to_module, code, with_metrics=self.metrics)
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
        ],
        manual_input = True,
    )
    app.run()
