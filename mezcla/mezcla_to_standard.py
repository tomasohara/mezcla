#! /usr/bin/env python

"""
Mezcla to Standard call conversion script
"""

# Standard modules
import os
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

class BaseTransformerStrategy:
    """Transformer base class"""

    def insert_extra_params(self, eq_call: EqCall, args: dict) -> dict:
        """Insert extra parameters, if not already present"""
        if eq_call.extra_params is None:
            return args
        for key, value in eq_call.extra_params.items():
            if key not in args:
                ## TODO: convert value to tree
                ## args[key] = value
                pass
        return args

    def filter_args_by_function(self, func: callable, args: dict) -> dict:
        """Filter the arguments to match the standard function signature"""
        result = {}
        for key, value in args.items():
            if key in inspect.getfullargspec(func).args:
                result[key] = value
        return result

class ToStandard(BaseTransformerStrategy):
    """Mezcla to standard call conversion class"""

    def find_eq_call(self, module, method) -> Optional[EqCall]:
        """Find the equivalent call"""
        for eq_call in mezcla_to_standard:
            if (module == eq_call.target.__module__.split('.')[-1]
                and method == eq_call.target.__name__):
                return eq_call
        return None

    def is_condition_to_replace_met(self) -> bool:
        """Return if the condition to replace is met"""
        return True

    def get_args_replacement(self, eq_call: EqCall, args: list, kwargs: list) -> dict:
        """Transform every argument to the standard equivalent argument"""
        arguments = dict(zip(inspect.getfullargspec(eq_call.target).args, args))
        arguments.update(kwargs)
        arguments = self.insert_extra_params(eq_call, arguments)
        arguments = self.replace_args_keys(eq_call, arguments)
        arguments = self.filter_args_by_function(eq_call.dest, arguments)
        return list(arguments.values())

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

    def get_matching_call(self, module, method) -> Optional[EqCall]:
        """Get the matching call"""
        eq_call = self.find_eq_call(module, method)
        if eq_call is None:
            return None, None
        if not self.is_condition_to_replace_met():
            return None, None
        module = eq_call.dest.__module__
        method = eq_call.dest.__name__
        return module, method, eq_call

class ToMezcla(BaseTransformerStrategy):
    """Standard to Mezcla call conversion class"""

    def find_eq_call(self, module, method) -> Optional[EqCall]:
        """Find the equivalent call"""
        for eq_call in mezcla_to_standard:
            if (module == eq_call.dest.__module__.split('.')[-1]
                and method == eq_call.dest.__name__):
                return eq_call
        return None

    def is_condition_to_replace_met(self) -> bool:
        """Return if the condition to replace is met"""
        return True

    def get_args_replacement(self, eq_call: EqCall, args: list, kwargs: list) -> dict:
        """Transform every argument to the Mezcla equivalent argument"""
        arguments = dict(zip(inspect.getfullargspec(eq_call.target).args, args))
        arguments.update(kwargs)
        arguments = self.replace_args_keys(eq_call, arguments)
        arguments = self.insert_extra_params(eq_call, arguments)
        arguments = self.filter_args_by_function(eq_call.target, arguments)
        return list(arguments.values())

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

    def get_matching_call(self, module, method) -> Optional[EqCall]:
        """Get the matching call"""
        eq_call = self.find_eq_call(module, method)
        if eq_call is None:
            return None, None
        if not self.is_condition_to_replace_met():
            return None, None
        module = eq_call.target.__module__
        method = eq_call.target.__name__
        return module, method, eq_call

def transform(to_module, code: str) -> str:
    """Transform the code"""
    # Parse the code into a CST tree
    tree = cst.parse_module(code)

    # Traverse the CST and modify function calls
    class CustomVisitor(cst.CSTTransformer):
        """Custom visitor to modify the CST"""

        def __init__(self, to_module) -> None:
            super().__init__()
            self.to_module = to_module
            self.aliases = {}
            self.to_import = []

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
                            names=[cst.ImportAlias(name=cst.Name(module), asname=None)]
                        )
                    ]
                )
                new_body = [new_import_node] + new_body
            return updated_node.with_changes(body=new_body)

        # pylint: disable=invalid-name
        def visit_ImportAlias(self, node: cst.ImportAlias) -> None:
            """Visit an ImportAlias node"""
            if isinstance(node.name, cst.Attribute):
                name = node.name.attr.value
            elif isinstance(node.name, cst.Name):
                name = node.name.value
            asname = node.asname.name.value
            # Store the alias
            self.aliases[asname] = name

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
            func_name = original_node.func.attr.value
            # Get replacement
            new_module, new_func, eq_call = self.to_module.get_matching_call(
                module_name, func_name
            )
            if not new_module or not new_func:
                return updated_node
            # Replace
            updated_node = updated_node.with_changes(
                func=cst.Attribute(value=cst.Name(new_module), attr=cst.Name(new_func)),
                args=self.replace_args_if_needed(eq_call, original_node.args)
            )
            # Add pending import to add
            self.to_import.append(new_module)
            return updated_node

        def replace_args_if_needed(self, eq_call: EqCall, old_args: list) -> cst.Call:
            """Adapt the arguments"""
            return self.to_module.get_args_replacement(eq_call, old_args, [])

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
            to_module = ToMezcla()
        else:
            to_module = ToStandard()
        modified_code = transform(to_module, code)
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
