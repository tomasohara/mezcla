#! /usr/bin/env python3
#
# randomize-lines.py: randomize lines in a file without reading entirely into memory.
# This creates a temporary file with a random number in the first column and
# the original line contents in the second. Then the temporary file is sorted
# and the random number column removed.
#
# Note:
# - Inspired by examples under Stack Overflow (see below).
#
#------------------------------------------------------------------------
# via http://stackoverflow.com/questions/4618298/randomly-mix-lines-of-3-million-line-file
#
# At the shell, use this.
#   python decorate.py | sort | python undecorate.py
#   
# decorate.py:
#   
#   import sys
#   import random
#   for line in sys.stdin:
#       sys.stdout.write("{0}|{1}".format(random.random(), line))
#   
# undecorate.py:
#   
#   import sys
#   for line in sys.stdin:
#       _, _, data = line.partition("|")
#       sys.stdout.write( line )
#
#------------------------------------------------------------------------
# TODO:
# - Add sanity check for disk space issues.
# - Have streamlined version just using output from sort.
#

## OLD: """Randomize lines from stardard input"""

"""
Randomize lines in a file (without reading entirely into memory).
Note: The default seed is {seed}.

Sample usage:
    {script} --header --percent 10 ./examples/pima-indians-diabetes.csv
"""

# Standard modules
## OLD: import argparse
import os
import random
import sys

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main
from mezcla import system

RANDOM_SEED = system.getenv_int(
    "RANDOM_SEED", 15485863,
    description="Integral seed for random number generation--use 0 for default based on time-of-day")

class Dummy_Main(Main):
    """Class for reading input using Main"""
    ## TODO2: Merge usage with that of regular Main class instance main_app below
    manual_input = True
    
    def __init__(self, input_stream):
        super().__init__(runtime_args=[])
        self.input_stream = input_stream
        ## BAD: self.all_lines = []

    ## OLD:
    ## def process_line(self, line):
    ##     self.all_lines.append(line)
    ##     return
        

def main():
    """Entry point for script"""
    debug.trace(4, "main(): sys.argv=%s" % sys.argv)
    ## TODO: assert is_directory("/usr/bin"), "This requires Unix"
    if ("--ignore-case" not in gh.run("sort --help")):
        system.print_error("Error: This requires a Unix-type version of sort (e.g., GNU).")
        sys.exit()

    # Check command-line arguments
    # TODO3: standardize name of instance (e.g., dummy_app vs app vs. script_app)
    HEADER_OPT = "header"
    SEED_OPT = "seed"
    PERCENT_OPT = "percent"
    main_app = Main(description=__doc__.format(script=gh.basename(__file__), seed=RANDOM_SEED),
                    boolean_options=[(HEADER_OPT, "Keep first line for header columns")],
                    int_options=[(SEED_OPT, "random seed if nonzero (e.g., 122949823, the seven-millionth prime)")],
                    float_options=[(PERCENT_OPT, "Percent of lines to keep")],
                    skip_input=False, manual_input=True)
    debug.assertion(main_app.parsed_args)
    #
    input_stream = sys.stdin
    if (main_app.filename != "-"):
        assert(os.path.exists(main_app.filename))
        input_stream = system.open_file(main_app.filename)
        assert(input_stream)
    else:
        debug.trace(5, "Re-opening stdin w/ UTF-8 support")
        ## TODO: figure out proper way to re-open stdin
        STDIN = 0
        input_stream = system.open_file(STDIN)
    random_seed = main_app.get_parsed_option(SEED_OPT, RANDOM_SEED)
    if random_seed:
        random.seed(random_seed)
    include_header = main_app.get_parsed_option(HEADER_OPT)
    percent_lines = main_app.get_parsed_option(PERCENT_OPT, 100)

    # Initialize seed for optional random number generator
    if RANDOM_SEED:
        random.seed(RANDOM_SEED)

    # Add column with random number to temporary file
    ## OLD: temp_base = system.getenv_text("TEMP_FILE", gh.get_temp_file())
    temp_base = main_app.temp_base
    temp_input_file = temp_base + ".input"
    temp_output_file = temp_base + ".output"
    ## OLD: temp_input_handle = open(temp_input_file, "w")
    temp_input_handle = system.open_file(temp_input_file, mode="w")
    assert(temp_input_handle)
    #
    header = None
    line_num = 0
    # Note: uses main class to allow for reading pages and paragraphs
    main_app = Dummy_Main(input_stream)
    main_app.read_input()
    multi_line_mode = not main_app.is_line_mode()
    #
    ## BAD: for line in main_app.all_lines:
    for line in main_app.read_input():
        line_num += 1
        line = line.strip("\n")
        if multi_line_mode:
            # Encode internal newlines so the sort is not thrown off
            line = line.replace("\n", "\\n")
        if (line_num == 1) and include_header:
            header = line
        else:
            temp_input_handle.write("%s\t%s\n" % (random.random(), line))
    num_input_lines = line_num
    temp_input_handle.close()

    # Sort by random-number column (1) and then remove temporary column
    # NOTES:
    # - This needs to ensure that the unix version of sort is used.
    # - The Win32 version of run() doesn't support pipes. 
    ## TODO: Use another way to bypass Windows sort command (e.g., in case sort
    ## is located in a different directory than /usr/bin).
    gh.delete_existing_file(temp_output_file)
    gh.run("sort -n < {in_file} | cut -f2- > {out_file}",
           in_file=temp_input_file, out_file=temp_output_file)

    # Display result
    # TODO: send output of command above to stdout
    ## OLD: temp_output_handle = open(temp_output_file, "r")
    temp_output_handle = system.open_file(temp_output_file, mode="r")
    assert(temp_output_handle)
    line_num = 0
    IO_error = False
    output_header = bool(include_header and header)
    if output_header:
        print(header)
        line_num += 1
        debug.trace(6, "HL%d: %s" % (line_num, header))
    last_line_num = (num_input_lines if (percent_lines >= 100)
                     else int(round(percent_lines / 100 * num_input_lines, 0)))
    for line in temp_output_handle:
        line_num += 1
        if line_num > last_line_num:
            debug.trace(4, f"Stopping after line# {last_line_num} for {percent_lines}% support")
            break
        line = line.strip("\n")
        if multi_line_mode:
            line = line.replace("\\n", "\n")
        debug.trace(6, "RL%d: %s" % (line_num, line))
        if (include_header and (line == header)):
            debug.trace(5, "Ignoring header at line %d" % (line_num))
            continue
        try:
            print(line)
        except:
            IO_error = True
            debug.trace(4, "Exception printing line %d: %s" % (line_num, str(sys.exc_info())))
            break
    num_output_lines = line_num - int(output_header)
    ## OLD: debug.trace(4, "%s input and %d output lines" % (num_input_lines, num_output_lines))
    debug.trace_expr(4, num_input_lines, last_line_num, num_output_lines, IO_error)
    debug.assertion((last_line_num == num_output_lines) or IO_error)
    temp_output_handle.close()

    ## OLD:
    ## # Cleanup (e.g., removing temporary files)
    ## if not tpo.detailed_debugging():
    ##     gh.run("rm -vfr {base}*", base=temp_base)

    return

#------------------------------------------------------------------------

if __name__ == '__main__':
    main()
