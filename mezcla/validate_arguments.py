#! /usr/bin/env python
#
# Simple illustration of optional pydantic argument validation.
#

"""Optional pydantic argument validation"""

# Standard modules
from functools import wraps

# Installed module
from pydantic import BaseModel          # pylint: disable=no-name-in-module
import libcst as cst

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main
from mezcla import system

# Constants
VALIDATE_ARGUMENTS = True
TL = debug.TL
## OLD:
## # TODO: TMP_PATH = gh.get_temp_dir
## TMP_PATH = "/tmp/temp_"
TMP_PATH = gh.get_temp_dir()

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
    def some_function(some_dict: ExpectedDictModel):
        # Some code here

    But this is not compatible with mypy, pyright and other...

    So, what we do to keep compatibility is to use this decorator
    and pass the parameter to validate with the model like this:

    @validate_dictionaries(some_dict = ExpectedDictModel)
    def some_function(some_dict: dict):
        # Some code here
    """
    def decorator(func):
        @wraps(func)
        def inner(*func_args, **func_kwargs):
            if not VALIDATE_ARGUMENTS:
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

    # Parse the code into a CST tree
    tree = cst.parse_module(code)

    # List of functions to ignore, avoiding infinite recursion
    to_ignore = [
        'isinstance', 'print', 'validate_call',
    ]

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
                        module=cst.Name("pydantic"),
                        names=[cst.ImportAlias(name=cst.Name("validate_call"))]
                    )
                ]
            )
            new_body = [new_import] + list(updated_node.body)
            return updated_node.with_changes(body=new_body)

        # pylint: disable=invalid-name
        def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
            """Leave a Call node"""
            if not isinstance(original_node.func, (cst.Attribute, cst.Name)):
                return updated_node
            if original_node.func.value in to_ignore:
                return updated_node
            new_func = cst.Call(
                func=cst.Name(value="validate_call"),
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


class ValidateArgumentsScript(Main):
    """Argument processing class to Validate Arguments"""

    # Class-level member variables for arguments
    # (avoids need for class constructor)
    file = ""
    output = ""

    def setup(self) -> None:
        """Process arguments"""
        self.file = self.get_parsed_argument(FILE, self.file)
        self.output = self.get_parsed_argument(OUTPUT, self.output)

    def run_main_step(self) -> None:
        """Process main script"""
        debug.trace(TL.USUAL, f"main(): script={system.real_path(__file__)}")
        code = system.read_file(self.file)
        if not code:
            raise ValueError(f"File {self.file} is empty")
        code = add_validate_call_decorator(code)
        output_filename = self.output if self.output else TMP_PATH + gh.basename(self.file)
        system.write_file(
            filename=output_filename,
            text=code
        )
        output = gh.run(f"python3 {output_filename}")
        print(output)


if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    app = ValidateArgumentsScript(
        description = __doc__,
        positional_arguments = [
            (FILE, 'Python script to run with argument validation')
        ],
        text_options = [
            (OUTPUT, 'Output of transformed script'),
        ],
        manual_input = True,
    )
    app.run()
