#! /usr/bin/env python
#
# Simple illustration of optional pydantic argument validation.
#

"""Optional pydantic argument validation"""

# Standard modules
## TODO: import json
import re
from functools import wraps
from pydantic import BaseModel

# Installed module
from pydantic import validate_call
from pydantic import BaseModel

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main
from mezcla import system
from mezcla.my_regex import my_re

# Constants
VALIDATE_ARGUMENTS = True
TL = debug.TL
OUTPUT_PATH = "/tmp/temp_"
LINE_IMPORT_PYDANTIC = "from pydantic import validate_call\n"

# Arguments for Validate Arguments Script
FILE = "file"
ARG_INPUT_SCRIPT = "input"
ARG_NO_TRANSFORM = "no-transform"

# pylint: disable=unused-argument
def validate_dictionaries(*decorator_args, **decorator_kwargs):
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
                return func(*func_args, **func_kwargs)
            # Validate the dictionary keys and values,
            # specified in the decorator parameters
            for key, decorator_model in decorator_kwargs.items():
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

def transform_file(input_file_path):
    global output_filename
    content = system.read_file(input_file_path)
    content = my_re.sub(r"^def", r'@validate_call\n\g<0>', content, flags=re.MULTILINE)
    content = LINE_IMPORT_PYDANTIC + content
    output_filename = OUTPUT_PATH + gh.basename(input_file_path)
    system.write_file(
        filename=output_filename,
        text=content
    )
    return output_filename

def validate_arguments(file_path):
    # Perform validation of arguments here
    command = f"python3 {file_path}"
    try:
        validation_output = gh.run(command)
        return validation_output
    except Exception as e:
        raise f"Exception: {e}"

class ValidateArgumentsScript(Main):
    """Argument processing class to Validate Arguments"""

    # Class-level member variables for arguments
    # (avoids need for class constructor)
    file = ""

    def setup(self) -> None:
        """Process arguments"""
        self.file = self.get_parsed_argument(FILE, self.file)

    def run_main_step(self) -> None:
        """Process main script"""
        debug.trace(TL.USUAL, f"main(): script={system.real_path(__file__)}")
        output_file = transform_file(self.file)
        print(validate_arguments(output_file))

if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    app = ValidateArgumentsScript(
        description = __doc__,
        positional_arguments = [
            (FILE, 'Python script to run with argument validation')
        ],
        manual_input = True,
    )
    app.run()
