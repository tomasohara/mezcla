#! /usr/bin/env python
#
# Mezcla to Standard call conversion script
#
# NOTE:
# To convert Mezcla calls with standard calls by manipulating the AST,
# we must do it with decorators at runtime. This is because we cannot
# easily know the origin of the function call in the AST. for example:
#
#       from mezcla import glue_helpers as gh
#       gh.rename_file("old", "new")
#
# If we peek into the AST:
#
#       ast.dump(node.func) =>
#            Attribute(value=Name(id='gh', ctx=Load()), attr='rename_file', ctx=Load())
#
# We cannot see directly that 'rename_file' belongs to 'mezcla.glue_helpers',
# comparing it with another function is difficult. But if we do it at
# runtime with decorators, the comparison is more easy:
#
#       func == glue_helpers.rename_file => True
#

"""
Mezcla to Standard call conversion script
"""

# Standard modules
import os
import ast
import logging
import inspect
from typing import Optional

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
OUTPUT = "output"

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

    def same_target(self, func: callable) -> bool:
        """Check if the function is the same as the target"""
        return self.target == func

    def same_dest(self, func: callable) -> bool:
        """Check if the function is the same as the destination"""
        return self.dest == func

    def _to_dest_args(self, *args, **kwargs) -> dict:
        """Transform the target call arguments to dest call arguments"""
        arguments = dict(zip(inspect.getfullargspec(self.target).args, args))
        arguments.update(kwargs)
        arguments = self._insert_extra_params(arguments)
        arguments = self._to_dest_args_keys(arguments)
        return arguments

    def _to_target_args(self, *args, **kwargs) -> dict:
        """Transform the dest call arguments to target call arguments"""
        arguments = dict(zip(inspect.getfullargspec(self.dest).args, args))
        arguments.update(kwargs)
        arguments = self._to_target_args_keys(arguments)
        arguments = self._insert_extra_params(arguments)
        return arguments

    def _filter_args_by_function(self, func: callable, args: dict) -> dict:
        """Filter the arguments by the function"""
        result = {}
        for key, value in args.items():
            if key in inspect.getfullargspec(func).args:
                result[key] = value
        return result

    def is_dest_condition_met(self, *args, **kwargs) -> bool:
        """Return if the condition is met when running the destination function"""
        arguments = self._to_dest_args(*args, **kwargs)
        arguments = self._filter_args_by_function(self.condition, arguments)
        return self.condition(**arguments)

    def is_target_condition_met(self, *args, **kwargs) -> bool:
        """Return if the condition is met when running the target function"""
        arguments = self._to_target_args(*args, **kwargs)
        arguments = self._filter_args_by_function(self.condition, arguments)
        return self.condition(**arguments)

    def _to_dest_args_keys(self, args: dict) -> dict:
        """Transform the arguments keys from target to dest"""
        if self.eq_params is None:
            return args
        result = {}
        for key, value in args.items():
            if key in self.eq_params:
                result[self.eq_params[key]] = value
            else:
                result[key] = value
        return result

    def _to_target_args_keys(self, args: dict) -> dict:
        """Transform the arguments keys from dest to target"""
        if self.eq_params is None:
            return args
        result = {}
        for key, value in args.items():
            if key in self.eq_params.values():
                result[list(self.eq_params.keys())[list(self.eq_params.values()).index(key)] ] = value
            else:
                result[key] = value
        return result

    def _insert_extra_params(self, args: dict) -> dict:
        """Insert extra parameters, if not already present"""
        if self.extra_params is None:
            return args
        for key, value in self.extra_params.items():
            if key not in args:
                args[key] = value
        return args

    def run_target(self, *args, **kwargs):
        """Run the target function"""
        arguments = self._to_target_args(*args, **kwargs)
        arguments = self._filter_args_by_function(self.target, arguments)
        return self.target(**arguments)

    def run_dest(self, *args, **kwargs):
        """Run the destination function"""
        arguments = self._to_dest_args(*args, **kwargs)
        arguments = self._filter_args_by_function(self.dest, arguments)
        return self.dest(**arguments)

# Add equivalent calls between Mezcla and standard
mezcla_to_standard = []
mezcla_to_standard.append(
    EqCall(
        gh.rename_file,
        os.rename,
        eq_params = { "source": "src", "target": "dst" }
    )
)
mezcla_to_standard.append(
    EqCall(
        gh.delete_file,
        os.remove,
        eq_params = { "filename": "path" }
    )
)
mezcla_to_standard.append(
    EqCall(
        gh.form_path,
        os.path.join,
        eq_params = { "filenames": "a" }
    )
)
mezcla_to_standard.append(
    EqCall(
        debug.trace,
        logging.debug,
        condition = lambda level: level > 3,
        eq_params = { "text": "msg" },
        extra_params = { "level": 4 }
    )
)
mezcla_to_standard.append(
    EqCall(
        debug.trace,
        logging.info,
        condition = lambda level: 2 < level <= 3,
        eq_params = { "text": "msg" },
        extra_params = { "level": 3 }
    )
)
mezcla_to_standard.append(
    EqCall(
        debug.trace,
        logging.warning,
        condition = lambda level: 1 < level <= 2,
        eq_params = { "text": "msg" },
        extra_params = { "level": 2 }
    )
)
mezcla_to_standard.append(
    EqCall(
        debug.trace,
        logging.error,
        condition = lambda level: 0 < level <= 1,
        eq_params = { "text": "msg" },
        extra_params  = { "level": 1 }
    )
)

def use_standard_equivalent(func):
    """
    Decorator to run the equivalent standard call to the Mezcla call
    """
    def wrapper(*args, **kwargs):
        ## TODO: optimize this, avoid iterating over all calls every time a function is called
        for call in mezcla_to_standard:
            if not call.same_target(func):
                continue
            if not call.is_dest_condition_met(*args, **kwargs):
                continue
            return call.run_dest(*args, **kwargs)
        return func(*args, **kwargs)
    return wrapper

def use_mezcla_equivalent(func):
    """
    Decorator to run the equivalent Mezcla call to the standard call
    """
    def wrapper(*args, **kwargs):
        ## TODO: optimize this, avoid iterating over all calls every time a function is called
        for call in mezcla_to_standard:
            if not call.same_dest(func):
                continue
            if not call.is_target_condition_met(*args, **kwargs):
                continue
            return call.run_target(*args, **kwargs)
        return func(*args, **kwargs)
    return wrapper

def insert_decorator_to_functions(decorator: callable, code: str) -> str:
    """
    Insert a decorator to a function definition in the code
    """
    name = decorator.__name__

    # Parse the code into a CST tree
    tree = cst.parse_module(code)

    # Traverse the CST and modify function calls
    class CustomVisitor(cst.CSTTransformer):
        """Custom visitor to modify the CST"""

        def __init__(self):
            super().__init__()
            self.added_import = False

        # pylint: disable=invalid-name
        def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
            """Leave a Module node"""
            if self.added_import:
                return updated_node
            self.added_import = True
            new_import = cst.SimpleStatementLine(
                body=[
                    cst.ImportFrom(
                        module=cst.Attribute(
                            value=cst.Name("mezcla"),
                            attr=cst.Name("mezcla_to_standard")
                        ),
                        names=[cst.ImportAlias(name=cst.Name(name))]
                    )
                ]
            )
            new_body = [new_import] + list(updated_node.body)
            return updated_node.with_changes(body=new_body)

        # pylint: disable=invalid-name
        def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
            """Leave a Call node"""
            if not isinstance(original_node.func, (cst.Name, cst.Attribute)):
                return updated_node
            new_func = cst.Call(
                func=cst.Name(value=name),
                args=[cst.Arg(value=original_node.func)]
            )
            new_call = cst.Call(
                func=new_func,
                args=updated_node.args
            )
            return new_call

    # Apply the custom visitor to the CST
    modified_tree = tree.visit(CustomVisitor())

    # Convert the modified CST back to Python code
    modified_code = modified_tree.code

    return modified_code

def to_standard(code: str) -> str:
    """
    Add decorator to function definitions in the code, to convert Mezcla calls to standard calls
    """
    return insert_decorator_to_functions(use_standard_equivalent, code)

def to_mezcla(code: str) -> str:
    """
    Add decorator to function definitions in the code, to convert standard calls to Mezcla calls
    """
    return insert_decorator_to_functions(use_mezcla_equivalent, code)

class MezclaToStandardScript(Main):
    """Argument processing class to MezclaToStandard"""

    # Class-level member variables for arguments
    # (avoids need for class constructor)
    file = ""
    to_std = False
    to_mezcla = False
    output = ""

    def setup(self) -> None:
        """Process arguments"""
        self.file = self.get_parsed_argument(FILE, self.file)
        self.to_std = self.has_parsed_option(TO_STD)
        self.to_mezcla = self.has_parsed_option(TO_MEZCLA)
        self.output = self.get_parsed_argument(OUTPUT, self.output)

    def run_main_step(self) -> None:
        """Process main script"""
        code = system.read_file(self.file)
        if not code:
            raise ValueError(f"File {self.file} is empty")
        if self.to_mezcla:
            modified_code = to_mezcla(code)
        else:
            modified_code = to_standard(code)
        if self.output:
            system.write_file(
                filename=self.output,
                text=modified_code
            )
        # pylint: disable=exec-used
        exec(modified_code)

if __name__ == '__main__':
    app = MezclaToStandardScript(
        description = __doc__,
        positional_arguments = [
            (FILE, 'Python script to run with Mezcla-to-Standard conversion')
        ],
        boolean_options = [
            (TO_STD, 'Convert Mezcla calls to standard calls'),
            (TO_MEZCLA, 'Convert standard calls to Mezcla calls')
        ],
        text_options = [
            (OUTPUT, 'Output of transformed script'),
        ],
        manual_input = True,
    )
    app.run()
