#! /usr/bin/env python3
#
# Simple illustration of optional pydantic argument validation.
#

"""Optional pydantic argument validation"""

# Standard modules
import re
from typing import Optional
import importlib.util
import sys

# Installed modules
from pydantic import validate_call

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main
from mezcla import system
from mezcla.my_regex import my_re

def validate_script_args(script_path):
    """Dynamical validation of arguments of functions of the specified script"""
    try:
        spec = importlib.util.spec_from_file_location("script_module", script_path)
        script_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(script_module)
    except Exception as e:
        print(f"Error importing script: {e}")
        return

    functions_to_validate = [
        getattr(script_module, func_name)
        for func_name in dir(script_module)
        if callable(getattr(script_module, func_name))
        and hasattr(getattr(script_module, func_name), "__annotations__")
    ]

    print(functions_to_validate)

    for func in functions_to_validate:
        try:
            validated_func = validate_call(func)
            print(f"Validating arguments for function: {func.__name__}")
            validated_func()
        except Exception as e:
            print(f"Error validating arguments for function {func.__name__}: {e}")

def main():
    """Entry point"""
    if len(sys.argv) < 2:
        print("Usage: python validate_script_arguments.py <path_to_script>")
        sys.exit(1)

    script_path = sys.argv[1]
    validate_script_args(script_path)

if __name__ == '__main__':
    main()


