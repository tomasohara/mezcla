#! /usr/bin/env python
#
# Simple illustration of optional pydantic argument validation.
#

"""Optional pydantic argument validation"""

# Standard modules
## TODO: import json
import re

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
TL = debug.TL
OUTPUT_PATH = "/tmp/temp_"
LINE_IMPORT_PYDANTIC = "from pydantic import validate_call\n"

# Arguments
ARG_INPUT_SCRIPT = "input"
ARG_NO_TRANSFORM = "no-transform"

#...............................................................................
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

#...............................................................................
    
def main():
    """Entry point"""
    debug.trace(TL.USUAL, f"main(): script={system.real_path(__file__)}")
    input_file = "spell.py"
    output_file = transform_file(input_file)
    print(validate_arguments(output_file))

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    main()