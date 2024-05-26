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

# Installed module
import astor

# Local modules
from mezcla.main import Main
from mezcla import system
from mezcla import debug
from mezcla import glue_helpers as gh

# Arguments
FILE = "file"

class EqCall:
    """Mezcla to standard equivalent call class"""

    def __init__(
            self,
            target: callable,
            dest: callable,
            condition: callable = lambda: True
        ) -> None:
        self.target = target
        self.dest = dest
        self.condition = condition

    def equal(self, func: callable) -> bool:
        """Check if the function is the same as the target"""
        return self.target == func

    def run_condition(self, *args, **kwargs) -> bool:
        """Run the condition"""
        ## TODO: implement condition
        return True

# Add equivalent calls between Mezcla and standard
mezcla_to_standard = []
mezcla_to_standard.append(EqCall(gh.rename_file, os.rename))
mezcla_to_standard.append(EqCall(gh.delete_file, os.remove))
mezcla_to_standard.append(EqCall(gh.form_path, os.path.join))
mezcla_to_standard.append(EqCall(debug.trace, logging.debug, lambda args: args.level > 3))
mezcla_to_standard.append(EqCall(debug.trace, logging.info, lambda args: 2 < args.level <= 3))
mezcla_to_standard.append(EqCall(debug.trace, logging.warning, lambda args: 1 < args.level <= 2))
mezcla_to_standard.append(EqCall(debug.trace, logging.error, lambda args: 0 < args.level <= 1))

def use_standard_equivalent(func):
    """
    Decorator to run the equivalent standard call to the Mezcla call
    """
    def wrapper(*args, **kwargs):
        ## TODO: optimize this, avoid iterating over all calls every time a function is called
        for call in mezcla_to_standard:
            if not call.equal(func):
                continue
            if not call.run_condition(*args, **kwargs):
                continue
            return call.dest(*args, **kwargs)
        return func(*args, **kwargs)
    return wrapper

def to_standard(code: str) -> str:
    """
    Add decorator to function definitions in the code, to convert Mezcla calls to standard calls
    """

    # Parse the code into AST
    tree = ast.parse(code)

    # Define an import node
    import_node = ast.ImportFrom(
        module='mezcla.mezcla_to_standard',
        names=[ast.alias(name='use_standard_equivalent', asname=None)],
        level=0
    )

    # Define a decorator node
    to_std_decorator = ast.Name(id='use_standard_equivalent', ctx=ast.Load())

    # Add the import statement to the beginning of the AST
    tree.body.insert(0, import_node)

    # Function to recursively traverse the AST
    # pylint: disable=invalid-name
    def visit_Call(node):
        """Visit a Call node"""
        assert isinstance(node, ast.Call)
        # Functions from external modules are represented as Attribute nodes.
        if not isinstance(node.func, ast.Attribute):
            return node
        # Insert decortator
        node.func = ast.Call(func=to_std_decorator, args=[node.func], keywords=[])
        return node

    # Traverse the AST and modify function definitions
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            node = visit_Call(node)

    # Convert the modified AST back to Python code
    modified_code = astor.to_source(tree)

    return modified_code

class MezclaToStandardScript(Main):
    """Argument processing class to MezclaToStandard"""

    # Class-level member variables for arguments
    # (avoids need for class constructor)
    file = ""

    def setup(self) -> None:
        """Process arguments"""
        self.file = self.get_parsed_argument(FILE, self.file)

    def run_main_step(self) -> None:
        """Process main script"""
        code = system.read_file(self.file)
        if not code:
            raise ValueError(f"File {self.file} is empty")
        modified_code = to_standard(code)
        # pylint: disable=exec-used
        exec(modified_code)

if __name__ == '__main__':
    app = MezclaToStandardScript(
        description = __doc__,
        positional_arguments = [
            (FILE, 'Python script to run with Mezcla-to-Standard conversion')
        ],
        manual_input = True,
    )
    app.run()
