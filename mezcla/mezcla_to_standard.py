#! /usr/bin/env python
#
# Mezcla to Standard call conversion script
#
# TODO1: Add tracing throughout.
# TODO2: Add examples illustrating the transformations being made (e.g., AST).
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


"""
Mezcla to Standard call conversion script
"""

# Standard modules
import time
import os
import sys
import logging
import inspect
from typing import (
    Optional, Tuple,
)
import tempfile

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

class EqCall:
    """Mezcla to standard equivalent call class"""

    def __init__(
            self,
            target: callable,
            dest: callable,
            condition: callable = lambda: True,
            eq_params: Optional[dict] = None,
            extra_params: Optional[dict] = None
        ) -> None:
        self.target = target
        self.dest = dest
        self.condition = condition
        self.eq_params = eq_params
        self.extra_params = extra_params

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
        gh.file_exists,
        "os.path.exists",
        eq_params={ "filename": "path" }
    ),
    EqCall(
        gh.form_path,
        "os.path.join",
        eq_params = { "filenames": "a" }
    ),
    EqCall(
        gh.is_directory,
        "os.path.isdir",
        eq_params = { "path": "s" }
    ),
    EqCall(
        gh.create_directory,
        "os.mkdir",
    ),
    EqCall(
        gh.rename_file,
        "os.rename",
        eq_params = { "source": "src", "target": "dst" }
    ),
    EqCall(
        gh.delete_file,
        "os.remove",
        eq_params = { "filename": "path" }
    ),
    EqCall(
        gh.delete_existing_file,
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
        debug.trace,
        logging.debug,
        condition = lambda level: level > 3,
        eq_params = { "text": "msg" },
        extra_params = { "level": 4 }
    ),
    EqCall(
        debug.trace,
        logging.info,
        condition = lambda level: 2 < level <= 3,
        eq_params = { "text": "msg" },
        extra_params = { "level": 3 }
    ),
    EqCall(
        debug.trace,
        logging.warning,
        condition = lambda level: 1 < level <= 2,
        eq_params = { "text": "msg" },
        extra_params = { "level": 2 }
    ),
    EqCall(
        debug.trace,
        logging.error,
        condition = lambda level: 0 < level <= 1,
        eq_params = { "text": "msg" },
        extra_params  = { "level": 1 }
    ),
    EqCall(
        system.get_exception,
        sys.exc_info,
    ),
    EqCall(
        system.get_exception,
        sys.exc_info,
    ),
    EqCall(
        system.print_error,
        print,
        extra_params={ "file": sys.stderr },
    ),
    EqCall(
        system.exit,
        sys.exit,
        eq_params={ "message": "status" }
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
        system.form_path,
        "os.path.join",
        eq_params = { "filenames": "a" }
    ),
    EqCall(
        system.is_directory,
        "os.path.isdir",
        eq_params = { "path": "s" }
    ),
    EqCall(
        system.is_regular_file,
        "os.path.isfile",
    ),
    EqCall(
        system.create_directory,
        "os.mkdir",
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
        system.get_args,
        sys.argv,
    ),
]

def value_to_arg(value: object) -> cst.Arg:
    """Convert the value to an argument"""
    if isinstance(value, str):
        return cst.Arg(cst.SimpleString(value=value))
    if isinstance(value, int):
        return cst.Arg(cst.Integer(value=str(value)))
    if isinstance(value, float):
        return cst.Arg(cst.Float(value=str(value)))
    if isinstance(value, bool):
        return cst.Arg(cst.Name(value=str(value)))
    raise ValueError(f"Unsupported value type: {type(value)}")

def arg_to_value(arg: cst.Arg) -> object:
    """Convert the argument to a value"""
    return eval(arg.value.value)

def args_to_values(args: list) -> list:
    """Convert the arguments to values"""
    return [arg_to_value(arg) for arg in args]

def match_args(func: callable, args: list, kwargs: dict) -> dict:
    """Match the arguments to the function signature"""
    target_spec = inspect.getfullargspec(func)
    # Extract arguments
    arguments = dict(zip(target_spec.args, args))
    # Extract *arguments
    if target_spec.varargs:
        arguments[target_spec.varargs] = args[len(target_spec.args):]
    # Extract **arguments
    if target_spec.varkw:
        arguments[target_spec.varkw] = kwargs
    return arguments

def flatten_list(list_to_flatten: list) -> list:
    """Flatten a list"""
    result = []
    for arg in list_to_flatten:
        if isinstance(arg, list):
            result += arg
        elif isinstance(arg, tuple):
            result += list(arg)
        else:
            result.append(arg)
    return result

def get_module_func(func) -> Tuple:
    """Get the module and function from the function"""
    if isinstance(func, str):
        return func.rsplit('.', 1)
    return func.__module__, func.__name__

class BaseTransformerStrategy:
    """Transformer base class"""

    def insert_extra_params(self, eq_call: EqCall, args: dict) -> dict:
        """Insert extra parameters, if not already present"""
        if eq_call.extra_params is None:
            return args
        for key, value in eq_call.extra_params.items():
            if key not in args:
                args[key] = value_to_arg(value)
        return args

    def filter_args_by_function(self, func: callable, args: dict) -> dict:
        """Filter the arguments to match the standard function signature"""
        try:
            result = {}
            for key in inspect.getfullargspec(func).args:
                if key in args:
                    result[key] = args[key]
            return result
        except TypeError:
            return args
        except ValueError:
            return args

    def get_replacement(self, module, func, args) -> Tuple:
        """Get the function replacement"""
        eq_call = self.find_eq_call(module, func, args)
        if eq_call is None:
            return None, None, []
        new_module, new_func = self.eq_call_to_module_func(eq_call)
        # Create the new module node
        if "." in new_module:
            new_import_node = cst.Name(new_module.split('.')[0])
            new_value_node = cst.Attribute(
                value=new_import_node,
                attr=cst.Name(new_module.split('.')[1])
            )
        else:
            new_import_node = cst.Name(new_module)
            new_value_node = new_import_node
        # Create the new function node
        new_func_node = cst.Attribute(value=new_value_node, attr=cst.Name(new_func))
        # Create the new arguments nodes
        new_args_nodes = self.get_args_replacement(eq_call, args, []) ## TODO: add kwargs
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
        """Transform every argument to the standard equivalent argument"""
        raise NotImplementedError

    def is_condition_to_replace_met(self, eq_call: EqCall, args: list) -> bool:
        """Return if the condition to replace is met"""
        # NOTE: must be implemented by the subclass
        raise NotImplementedError

class ToStandard(BaseTransformerStrategy):
    """Mezcla to standard call conversion class"""

    def find_eq_call(self, module: str, func: str, args: list) -> Optional[EqCall]:
        """Find the equivalent call"""
        for eq_call in mezcla_to_standard:
            target_module, target_func = get_module_func(eq_call.target)
            if (module in target_module
                and func in target_func
                and self.is_condition_to_replace_met(eq_call, args)):
                return eq_call
        return None

    def is_condition_to_replace_met(self, eq_call: EqCall, args: list) -> bool:
        """Return if the condition to replace is met"""
        arguments = match_args(eq_call.target, args, {})
        arguments = self.filter_args_by_function(eq_call.condition, arguments)
        arguments = args_to_values(arguments.values())
        try:
            return eq_call.condition(*arguments)
        except Exception as exc:
            return False

    def get_args_replacement(self, eq_call: EqCall, args: list, kwargs: dict) -> dict:
        """Transform every argument to the standard equivalent argument"""
        arguments = match_args(eq_call.target, args, kwargs)
        arguments = self.insert_extra_params(eq_call, arguments)
        arguments = self.replace_args_keys(eq_call, arguments)
        arguments = self.filter_args_by_function(eq_call.dest, arguments)
        return flatten_list(list(arguments.values()))

    def replace_args_keys(self, eq_call: EqCall, args: dict) -> dict:
        """Replace argument keys with the equivalent ones"""
        if eq_call.eq_params is None:
            return args
        result = {}
        for key, value in args.items():
            if key in eq_call.eq_params:
                result[eq_call.eq_params[key]] = value
            else:
                result[key] = value
        return result

    def eq_call_to_module_func(self, eq_call: EqCall) -> Tuple:
        """Get the module and function from the equivalent call"""
        return get_module_func(eq_call.dest)

class ToMezcla(BaseTransformerStrategy):
    """Standard to Mezcla call conversion class"""

    def find_eq_call(self, module: str, func: str, args: list) -> Optional[EqCall]:
        """Find the equivalent call"""
        for eq_call in mezcla_to_standard:
            dest_module, dest_func = get_module_func(eq_call.dest)
            if (module in dest_module
                and func in dest_func
                and self.is_condition_to_replace_met(eq_call, args)):
                return eq_call
        return None

    def is_condition_to_replace_met(self, eq_call: EqCall, args: list) -> bool:
        """Return if the condition to replace is met"""
        arguments = match_args(eq_call.dest, args, {})
        arguments = self.insert_extra_params(eq_call, arguments)
        arguments = self.replace_args_keys(eq_call, arguments)
        arguments = self.filter_args_by_function(eq_call.condition, arguments)
        arguments = args_to_values(arguments.values())
        try:
            return eq_call.condition(*arguments)
        except Exception as exc:
            return False

    def get_args_replacement(self, eq_call: EqCall, args: list, kwargs: dict) -> dict:
        """Transform every argument to the Mezcla equivalent argument"""
        arguments = match_args(eq_call.dest, args, kwargs)
        arguments = self.replace_args_keys(eq_call, arguments)
        arguments = self.insert_extra_params(eq_call, arguments)
        arguments = self.filter_args_by_function(eq_call.target, arguments)
        return flatten_list(list(arguments.values()))

    def replace_args_keys(self, eq_call: EqCall, args: dict) -> dict:
        """Replace argument keys with the equivalent ones"""
        if eq_call.eq_params is None:
            return args
        result = {}
        for key, value in args.items():
            if key in eq_call.eq_params.values():
                result[list(eq_call.eq_params.keys())[list(eq_call.eq_params.values()).index(key)] ] = value
            else:
                result[key] = value
        return result

    def eq_call_to_module_func(self, eq_call: EqCall) -> Tuple:
        """Get the module and function from the equivalent call"""
        return get_module_func(eq_call.target)

class CustomVisitor(cst.CSTTransformer):
    """Custom visitor to modify the CST"""

    def __init__(self, to_module: BaseTransformerStrategy) -> None:
        super().__init__()
        self.to_module = to_module
        self.aliases = {}
        self.to_import = []
        self.mezcla_modules = []

    def append_import_if_unique(self, new_import: cst.Name) -> None:
        """Append the import if unique"""
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
        return updated_node.with_changes(body=new_body)

    # pylint: disable=invalid-name
    def visit_ImportAlias(self, node: cst.ImportAlias) -> None:
        """Visit an ImportAlias node"""
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

    # pylint: disable=invalid-name
    def visit_ImportFrom(self, node: cst.ImportFrom) -> None:
        """Visit an ImportFrom node"""
        if node.module.value == "mezcla":
            for name in node.names:
                self.mezcla_modules.append(name.name.value)

    # pylint: disable=invalid-name
    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        """Leave a Call node"""
        if isinstance(original_node.func, cst.Name):
            # NOTE: we only want to transform standard
            # functions or from the Mezcla module
            pass
        elif isinstance(original_node.func, cst.Attribute):
            return self.replace_call_if_needed(original_node, updated_node)
        return updated_node

    def replace_call_if_needed(
            self,
            original_node: cst.Call,
            updated_node: cst.Call
        ) -> cst.Call:
        """Replace the call if needed"""
        # Get module and method names
        module_name = original_node.func.value.value
        module_name = self.aliases.get(module_name, module_name)
        # Get replacement
        new_module, new_func_node, new_args_nodes = self.to_module.get_replacement(
            module_name, original_node.func.attr.value, original_node.args
        )
        # Replace if replacement found
        if new_module and new_func_node:
            updated_node = updated_node.with_changes(
                func=new_func_node,
                args=new_args_nodes
            )
            self.append_import_if_unique(new_module)
            return updated_node
        # Otherwise, check if the module
        # is a Mezcla module and comment it
        if isinstance(self.to_module, ToStandard) and module_name in self.mezcla_modules:
            return cst.Comment(
                value=f"# WARNING not supported: {cst.Module([]).code_for_node(original_node)}"
            )
        return updated_node

def transform(to_module, code: str) -> str:
    """Transform the code"""
    # Parse the code into a CST tree
    tree = cst.parse_module(code)

    # Traverse the CST and modify function calls
    visitor = CustomVisitor(to_module)

    # Apply the custom visitor to the CST
    modified_tree = tree.visit(visitor)

    # Convert the modified CST back to Python code
    modified_code = modified_tree.code

    return modified_code

class MezclaToStandardScript(Main):
    """Argument processing class to MezclaToStandard"""

    # Class-level member variables for arguments
    # (avoids need for class constructor)
    file = ""
    to_std = False
    to_mezcla = False

    def setup(self) -> None:
        """Process arguments"""
        self.file = self.get_parsed_argument(FILE, self.file)
        self.to_std = self.has_parsed_option(TO_STD)
        self.to_mezcla = self.has_parsed_option(TO_MEZCLA)

    def run_main_step(self) -> None:
        """Process main script"""
        code = system.read_file(self.file)
        if not code:
            raise ValueError(f"File {self.file} is empty")
        if self.to_mezcla:
            to_module = ToMezcla()
        else:
            to_module = ToStandard()
        modified_code = transform(to_module, code)
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
            (TO_MEZCLA, 'Convert standard calls to Mezcla calls')
        ],
        manual_input = True,
    )
    app.run()
