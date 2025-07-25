#! /usr/bin/env python3
#
# Simple illustration of optional pydantic argument validation.
#
# TODO2: clarify the use of dict's for validation
# TODO3: add support for @validate_call
#

"""Optional pydantic argument validation"""

# Standard modules
import ast
from functools import wraps
import sys

# Installed modules
try:
    from pydantic import BaseModel
    import astor
except:
    sys.stderr.write("Warning unable to import astor and/or pydantic\n")
    BaseModel = object
    astor = None

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main
from mezcla import system

# Constants
## OLD: VALIDATE_ARGUMENTS = True
SKIP_VALIDATION = system.getenv_bool(
    "SKIP_VALIDATION", False,
    desc="Skip pydantic-based validation")
VALIDATE_ARGUMENTS = not SKIP_VALIDATION
TL = debug.TL
TMP_PATH = gh.get_temp_dir()
## OLD: TMP_PATH = "/tmp/temp_"

# Arguments for Validate Arguments Script
FILE = "file"
ARG_INPUT_SCRIPT = "input"
ARG_NO_TRANSFORM = "no-transform"
OUTPUT = "output"

def validate_dictionaries(*_decorator_args, **decorator_kwargs):
    """
    Decorator to validate dictionaries with Pydantic models,
    but without changing function definition to keep compatibility
    with mypy, pyright and other.

    Context:

    Basically with Pydantic you can validate dictionary keys and
    values with models, for example:

    class ExpectedDictModel(BaseModel):
        example_key: str

    @validate_call
    fun some_function(some_dict: ExpectedDictModel):
        # Some code here

    But this is not compatible with mypy, pyright and other...

    So, what we do to keep compatibility is to use this decorator
    and pass the parameter to validate with the model like this:

    @validate_dictionaries(some_dict = ExpectedDictModel)
    fun some_function(some_dict: dict):
        # Some code here
    """
    def decorator(func):
        @wraps(func)
        def inner(*func_args, **func_kwargs):
            if not VALIDATE_ARGUMENTS:
                debug.trace(4, "FYI: Ignoring validation for {func}")
                return func(*func_args, **func_kwargs)
            # Validate the dictionary keys and values,
            # specified in the decorator parameters
            for key, decorator_model in decorator_kwargs.items():
                # TODO: assert => debug.assertion
                # Check decorator parameters
                assert issubclass(decorator_model, BaseModel), f"Parameter {key} must be a pydantic.BaseModel class"
                # Check for function parameters
                func_model = func.__annotations__.get(key)
                assert func_model, f"Parameter {key} is missing for validation in function {func.__name__}"
                assert issubclass(func_model, dict), f"Parameter {func_model} must be a dict for validation in function {func.__name__}"
                # Validate the dictionary keys and values
                key_index = list(func.__annotations__).index(key)
                if key_index < len(func_args):
                    func_passed_value = func_args[key_index]
                else:
                    func_passed_value = func_kwargs.get(key)
                decorator_model.model_validate(func_passed_value, strict=True)
            return func(*func_args, **func_kwargs)
        return inner
    return decorator


def add_validate_call_decorator(code):
    """Add the validate_call decorator to all function calls in the code"""
    debug.trace_fmt(6, "add_validate_call_decorator({c})", c=code, max_len=256)

    # Parse the code into AST
    tree = ast.parse(code)

    # Define an import node
    import_node = ast.ImportFrom(
        module='pydantic',
        names=[ast.alias(name='validate_call', asname=None)],
        level=0
    )

    # Define a decorator node
    validate_decorator = ast.Name(id='validate_call', ctx=ast.Load())

    # Add the import statement to the beginning of the AST
    ## TODO2: put after module docstring
    tree.body.insert(0, import_node)

    # List of functions to ignore, avoiding infinite recursion
    to_ignore = [
        'isinstance', 'print', 'validate_call',
    ]

    # Function to recursively traverse the AST
    # pylint: disable=invalid-name
    def visit_Call(node):
        """Visit a Call node"""
        # Standalone functions are represented as Name nodes.
        # Functions from external modules are represented as Attribute nodes.
        if not isinstance(node.func, (ast.Name, ast.Attribute)):
            return node
        # Skip functions to ignore
        if isinstance(node.func, ast.Name) and node.func.id in to_ignore:
            return node
        # Add the decorator to the function call
        node.func = ast.Call(func=validate_decorator, args=[node.func], keywords=[])
        return node

    # Traverse the AST and modify function definitions
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            node = visit_Call(node)

    # Convert the modified AST back to Python code
    # TODO2: do this via ast
    modified_code = astor.to_source(tree)
    debug.trace_fmt(5, "add_validate_call_decorator() = {r!r})",
                    r=modified_code, max_len=256)

    return modified_code


class ValidateArgumentsScript(Main):
    """Argument processing class to Validate Arguments"""

    # Class-level member variables for arguments
    # (avoids need for class constructor)
    ## OLD: file = ""
    output = ""

    def setup(self) -> None:
        """Process arguments"""
        ## OLD: self.file = self.get_parsed_argument(FILE, self.file)
        self.output = self.get_parsed_option(OUTPUT, self.output)

    def run_main_step(self) -> None:
        """Process main script"""
        debug.trace(TL.USUAL, f"main(): script={system.real_path(__file__)}")
        ## OLD: code = system.read_file(self.filename)
        filename = (self.filename if (self.filename != "-") else "_stdin_")
        code = self.read_entire_input()
        if not code:
            raise ValueError(f"File {filename} is empty")
        if VALIDATE_ARGUMENTS:
            code = add_validate_call_decorator(code)
        output_filename = self.output if self.output else TMP_PATH + gh.basename(filename)
        system.write_file(
            filename=output_filename,
            text=code
        )
        output = gh.run(f"python3 {output_filename}")
        print(output)


if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    app = ValidateArgumentsScript(
        description=__doc__,
        ## OLD:
        ## positional_arguments = [
        ##     (FILE, 'Python script to run with argument validation')
        ## ],
        text_options=[
            (OUTPUT, 'Output of transformed script'),
        ],
        skip_input=False,
        manual_input=True,
    )
    app.run()
