#! /usr/bin/env python3
# 
# Similar to Unix cut command but with support for CSV files. Also modelled
# after perl script with support for treating runs of whitespace as tab.
#
# Notes:
# - Input processing based on csv example (seee https://docs.python.org/2/library/csv.html).
# - The bulk of the work is parsing the field specification After that,
#   the processing is simple row readidng and column extraction (i.e., subsetting).
# - Have option for setting delim to tab to avoid awkward spec under bash (e.g., --output-delim $'\t').
# - The CSV dialect defaults to Excel as with csv module (see csv.py).
# - Warning: by default quotes are added to all values --csv output (a la QUOTE_ALL) unless Excel dialect used.
#
# TODO:
# - ** Make --csv output default to pyspark dialect.
# - * Isolate csv support from Script class.
# - Add option for specifying output dialect.
# - Add support for selecting by columns instead of fields (e.g., as with -c1-40 with cut command).
#

"""Extracts columns from a file as with Unix cut command"""

# Standard modules
import argparse
import csv
import re
import sys

# Installed modules
import functools
import operator

# Local modules
from mezcla import data_utils as du
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main
from mezcla.my_regex import my_re
from mezcla import system

# Fill out constants for switches omitting leading dashes (e.g., DEBUG_MODE = "debug-mode")
FIELDS = "fields"                       # field indices (1-based or symbolic)
F_OPT = "f"                             # alias for fields
EXCLUDE_OPT = "exclude"                 # fields to exclude (1-based or symbolic)
X_OPT = "x"                             # alias for exclude
ENCODE_OPT = "encode"                   # use repr for newlines, etc.
FIX = "fix"                             # convert runs of spaces into a tab
CSV = "csv"                             # comma-separated value format
TSV = "tsv"                             # tab-separated value format
OUTPUT_CSV = "output-csv"               # CSV for output
OUTPUT_TSV = "output-tsv"               # TSV for output
CONVERT_DELIM = "convert-delim"         # convert input csv to tsv (or vice versa)
SNIFFER_ARG = "sniffer"                 # run CSV sniffer to detect dialect
## TODO
## INPUT_CSV = "input-csv"
## OUTPUT_CSV = "output-csv"
## INPUT_TSV = "input-tsv"
## OUTPUT_TSV = "output-tsv"
DELIM = "delim"                         # input delimiter
OUT_DELIM = "output-delim"              # output delimiter if not same for input
ALL_FIELDS = "all-fields"               # use all fields in output (e.g., for delimiter conversion)
TAB = "\t"
SPACE = " "
COMMA = ","
## TODO: make -style suffix optional (e.g., --tab[-style])
EXCEL_STYLE = "excel-style"             # use Excel dialect for CSV (redundant with default)
UNIX_STYLE = "unix-style"               # use Unix dialect for CSV (otherwise Excel is used)
PYSPARK_STYLE = "pyspark-style"         # use PySpark dialect for CSV (otherwise Unix is used)
## TEMP: workaround problem under MacOS
FORCE_SINGLE_LINE = system.getenv_bool(
    "FORCE_SINGLE_LINE", False,
    description="Force single line quotedchar handling (i.e., non-strict mode)")
TAB_STYLE = "tab-style"                 # use (non-Excel) tab dialect
DIALECT = "dialect"                     # --dialect option
OUTPUT_DIALECT = "output-dialect"       # --output-dialect option
EXCEL_DIALECT = "excel"                 # dialect parameter for Excel style
UNIX_DIALECT = "unix"                   # "" for Unix style
PYSPARK_DIALECT = "pyspark"             # "" for Pyspark style
SNIFFER_LOOKAHEAD = 65536               # buffer size for guessing dialect (64k)
TAB_DIALECT = "tab"                     # dialect option for TSV
SINGLE_LINE = "single-line"             # collapse multi-line fields into one
MAX_FIELD_LEN = "max-field-len"         # value length before elided
## TODO: TODO_ARG = "TODO-arg"          # TODO: comment
NEW_FIX = system.getenv_bool(
    "NEW_FIX", False,
    desc="HACK: Fix for --fix bug for whitespace to tabs")
NUM_FN_SHORTCUTS = 9
CSV_FORMAT = system.getenv_bool(
    "CSV_FORMAT", False,
    desc="Use CSV instead of TSV")
MAX_FIELD_SIZE = system.getenv_int(
    "MAX_FIELD_SIZE", -1,
    desc="Overide for default max field size (128k)")

#...............................................................................

MAX_VALUE_LEN = 128
#
def elide_values(in_list, max_len=MAX_VALUE_LEN):
    """Elide each of the values in IN_LIST (up to MAX_LEN each).
    Note: Returns list of strings"""
    # EX: elide_values(["1234567890", 1234567890, True, False], max_len=4) => ["1234...", "1234...", "True", "Fals..."]
    new_list = []
    for item in in_list:
        new_list.append(gh.elide(system.to_text(item), max_len))
    debug.trace_fmt(7, "elide_values({l}, [{m}]) => {r}", l=in_list, m=max_len, r=new_list)
    return new_list

def flatten_list_of_strings(list_of_str):
    """Flatten out LIST_OF_STR"""
    # EX: flatten_list_of_strings([["l1i1", "l1i2"], ["l2i1"]]) => ["l1i1", "l1i2", "l2i1"]
    result = functools.reduce(operator.concat, list_of_str)
    debug.trace(5, f"flatten_list_of_strings({list_of_str}) => {result}")
    return result

#...............................................................................
# TODO: Put following in separate module (e.g., data_utils.py)
#
# Note:
#
# - Dialect definitions from source for the standard CSV module (csv.py)
#
#   class excel(Dialect):
#       """Describe the usual properties of Excel-generated CSV files."""
#       delimiter = ','
#       quotechar = '"'
#       doublequote = True                     [ " => "" if embedded ]
#       skipinitialspace = False
#       lineterminator = '\r\n'
#       quoting = QUOTE_MINIMAL
#   register_dialect("excel", excel)
#   
#   class unix_dialect(Dialect):
#       """Describe the usual properties of Unix-generated CSV files."""
#       delimiter = ','
#       quotechar = '"'
#       doublequote = True
#       skipinitialspace = False
#       lineterminator = '\n'
#       quoting = QUOTE_ALL
#   register_dialect("unix", unix_dialect)
# 
# - Both double a double quote if embedded (e.g., "I said ""Hey!"" then.")
#

class pyspark_dialect(csv.Dialect):
    """CSV module dialect for Pyspark CSV files."""
    delimiter = ','
    quotechar = '"'
    doublequote = False          # uses escaped double quote when embedded
    escapechar = '\\'
    skipinitialspace = False
    lineterminator = '\n'
    quoting = csv.QUOTE_MINIMAL  # only delimiter, double quote or end-of-line
#
csv.register_dialect("pyspark", pyspark_dialect)
#
# note: Uses hive as alias for pyspark.
csv.register_dialect("hive", pyspark_dialect)

class tab_dialect(csv.Dialect):
    """TSV module dialect for tab-separated values (non-Excel)."""
    delimiter = TAB
    quotechar = ('"' if not FORCE_SINGLE_LINE else '')
    doublequote = False          # uses escaped double quote when embedded
    # TODO: use special Unicode space-like character
    escapechar = '\\'
    skipinitialspace = False     # keep leaing space afer delimiter
    lineterminator = '\n'
    quoting = csv.QUOTE_NONE     # no special processing for quotes
#
csv.register_dialect("tab", tab_dialect)

#...............................................................................

class Script(Main):
    """Input processing class"""
    inclusion_spec = ''
    exclusion_spec = ''
    fields = []
    exclude_fields = []
    encode_values = False
    fix = False
    delimiter = None
    output_delimiter = None
    csv = CSV_FORMAT
    csv_reader = None
    all_fields = False
    dialect = None
    output_dialect = None
    run_sniffer = False
    single_line = False
    max_field_len = None
    ## TODO: todo_arg = ...

    def setup(self):
        """Check results of command line processing"""
        # Note: The defaults above might be changed based on other arguments;
        # but, the user-specified value is normally not overridden.
        debug.trace_fmtd(5, "Script.setup(): self={s}", s=self)

        # Check main options
        # note: several options regarding fields including --Fn aliases
        for i in range(NUM_FN_SHORTCUTS):
            if self.get_parsed_option(f"F{i + 1}"):
                self.fields.append(str(i + 1))
        FIELDS_DEFAULT = ",".join(self.fields)
        debug.trace_expr(4, FIELDS_DEFAULT)
        inclusion_spec = self.get_parsed_option(F_OPT, FIELDS_DEFAULT)
        self.inclusion_spec = self.get_parsed_option(FIELDS, inclusion_spec)
        EXCLUDE_DEFAULT = ",".join(self.exclude_fields)
        exclusion_spec = self.get_parsed_option(F_OPT, EXCLUDE_DEFAULT)
        self.exclusion_spec = self.get_parsed_option(EXCLUDE_OPT, exclusion_spec)
        debug.assertion(not (self.inclusion_spec and self.exclusion_spec))
        self.encode_values = self.get_parsed_option(ENCODE_OPT, self.encode_values)
        ## NOTES: Fields initialization postponed until columns reads to allow ffor symbolic names
        self.all_fields = self.get_parsed_option(ALL_FIELDS, (not self.fields))
        debug.assertion(not (self.fields and self.all_fields))
        #
        self.fix = self.get_parsed_option(FIX, self.fix)

        # Check delimiter options
        # Note: output delimiter defaults to input unless convert specified
        self.csv = self.get_parsed_option(CSV, self.csv)
        if self.csv:
            self.delimiter = COMMA
        tsv = self.get_parsed_option(TSV, not self.csv)
        if tsv:
            self.delimiter = TAB
        self.delimiter = self.get_parsed_option(DELIM, self.delimiter)
        #
        debug.assertion(self.output_delimiter is None)
        if self.get_parsed_option(OUTPUT_CSV):
            self.output_delimiter = COMMA
        if self.get_parsed_option(OUTPUT_TSV):
            self.output_delimiter = TAB
        if self.output_delimiter is None:
            self.output_delimiter = self.delimiter
        if self.get_parsed_option(CONVERT_DELIM):
            self.output_delimiter = TAB if (self.delimiter == COMMA) else COMMA
        if (self.output_delimiter is None):
            self.output_delimiter = self.delimiter
        #
        self.run_sniffer = self.get_parsed_option(SNIFFER_ARG, self.run_sniffer)
        debug.assertion(not (self.csv and (self.delimiter != COMMA)))
        self.output_delimiter = self.get_parsed_option(OUT_DELIM, (self.output_delimiter or self.delimiter))
        self.single_line = self.get_parsed_option(SINGLE_LINE, self.single_line)
        self.max_field_len = self.get_parsed_option(MAX_FIELD_LEN, self.max_field_len)
        # self.todo_arg = self.get_parsed_option(TODO_ARG, self.todo_arg)

        # Check CSV dialet options
        debug.assertion(system.just_one_non_null([self.get_parsed_option(o, None) for o in 
                                                  [DIALECT, EXCEL_DIALECT, UNIX_DIALECT, PYSPARK_DIALECT, TAB_DIALECT]]))
        pyspark_style = self.get_parsed_option(PYSPARK_STYLE)
        if self.get_parsed_option(EXCEL_STYLE):
            self.dialect = EXCEL_DIALECT
        elif pyspark_style:
            self.dialect = PYSPARK_DIALECT
        elif (self.get_parsed_option(UNIX_STYLE) or (self.delimiter == COMMA)):
            self.dialect = UNIX_DIALECT
        elif (self.get_parsed_option(TAB_STYLE) or (self.delimiter == TAB)):
            self.dialect = TAB_DIALECT
        self.dialect = self.get_parsed_option(DIALECT, self.dialect)
        default_output_dialect = (self.output_dialect or self.dialect) if not self.run_sniffer else self.output_dialect
        if (self.output_delimiter == TAB):
            default_output_dialect = TAB_DIALECT
        if (self.output_delimiter == COMMA):
            default_output_dialect = PYSPARK_DIALECT if pyspark_style else UNIX_DIALECT
        self.output_dialect = self.get_parsed_option(OUTPUT_DIALECT, default_output_dialect)
        # TODO: see if there is an option to determine number of fields (before reading data)
        ## if self.all_fields:
        ##    self.fields = range(self.csv_reader.num_fields)

        # Trace instane
        debug.trace_object(5, self, label="Script instance")
        return

    def parse_field_spec(self, field_spec, columns):
        """Convert the FIELD_SPEC from string to list of integers. The specification can contain numeric ranges (e.g., "3-5") or comma-separated values (e.g., "7,9,11").
        Symbolic names can also be used (e.g., "sepal_width,petal_width")
        Note: throws exception if fields are not integers"""
        ## TODO3: decompose using helper functions
        # EX: self.parse_field_spec("1,2,5-8,3,4") => [1, 2, 5, 6, 7, 8, 3, 4]
        debug.trace(5, f"parse_field_spec({field_spec}, {columns}); self={self}")

        # Convert labels to 1-based offsets (TODO3: find CSV spec and clarify label chars)
        # NOTE: dashes in field names not supported (TODO2: subsitute non-ascii dash)
        in_field_spec = field_spec
        if my_re.search(r"[A-Za-z]", field_spec):
            ## TODO4: quote fields that should be used as is; add alternative to dash
            debug.trace(4, "FYI: Fieldnames currently are Python-like Ascii identifiers")
        while my_re.search(r"([a-z][a-z0-9_]+)", field_spec, flags=my_re.IGNORECASE):
            field_name = my_re.group(1)
            if field_name not in columns:
                system.print_error(f"Error: Unable to resolve field {field_name!r}: {in_field_spec=}")
                if field_name.lower() in str(field_spec).lower():
                    debug.trace(4, "Try matching case")
                break
            field_pos = (1 + columns.index(field_name))
            field_spec = my_re.pre_match() + str(field_pos) + my_re.post_match()
            debug.trace(4, f"Replaced {field_name!r} with {field_pos}")
        
        # Normalize the field specification
        debug.assertion(not re.search(r"[0-9] [0-9]", field_spec))
        field_spec = field_spec.replace(SPACE, "")
        debug.assertion(",," not in field_spec)
        field_spec = re.sub(r",,+", ",", field_spec)
        debug.assertion(not (field_spec.startswith(",") or field_spec.endswith(",")))
        field_spec = re.sub(r"(^,)|(,$)", "", field_spec)
        debug.trace_fmtd(5, "normalized field_spec: {fs}", fs=field_spec)

        # Replace ranges with comma-separated cols (e.g., "5-7" => "5,6,7")
        if "-" in field_spec:
            # Supply missing first and last column (e.g., "^-3" => "1-3" and "2-$" => "2-3")
            field_spec = my_re.sub(r"^\-", "1-", field_spec)
            field_spec = my_re.sub(r"\-$", f"-{len(columns)}", field_spec)

            # Replace ranges
            while my_re.search(r"([0-9]+)\-([0-9]+)", field_spec):
                range_spec = my_re.group(0)
                debug.trace_fmtd(4, "Converting range: {r}", r=range_spec)
                start = int(my_re.group(1))
                end = int(my_re.group(2))
                debug.assertion(start < end)

                # Add comma-separated values in range
                subfield_spec = ""
                while (start <= end):
                    subfield_spec += str(start) + ","
                    start += 1
                if subfield_spec.endswith(","):
                    subfield_spec = subfield_spec[:-1]

                # Replace the range specification with the delimited values
                debug.trace_fmtd(5, "subfield_spec: {ss}", ss=subfield_spec)
                field_spec = field_spec.replace(range_spec, subfield_spec, 1)
        debug.trace_fmtd(5, "expanded field_spec: {fs}", fs=field_spec)

        # Convert text field specification into list
        field_list = []
        if field_spec:
            field_list = [int(f) for f in field_spec.split(",")]
        debug.assertion(field_list)
        debug.trace_fmtd(4, "parse_field_spec() => {fl}", fl=field_list)
        return field_list
    
    def run_main_step(self):
        """Main processing step: read each line (i.e. row) and extract specified columns.
        Note: The fields are 1-based (i.e., first column specified 1 not 0)"""
        debug.trace_fmtd(4, "run_main_step()")

        # Overide the maxium field size if specified
        if MAX_FIELD_SIZE > -1:
            old_limit = csv.field_size_limit()
            debug.assertion(MAX_FIELD_SIZE > old_limit)
            csv.field_size_limit(MAX_FIELD_SIZE)
            debug.trace(4, f"Set max field size to {MAX_FIELD_SIZE}; was {old_limit}")
        
        # If unspecified, try to determine dialect for CSV input automatically
        # Notes: doesn't recognize escapes properly, such as \"); and,
        # sniffer doesn't work for stdin due to python limitation with backtracking.
        if ((self.delimiter == COMMA) and (not self.dialect) and self.run_sniffer):
            debug.assertion(self.input_stream != sys.stdin)
            self.dialect = csv.Sniffer().sniff(self.input_stream.read(SNIFFER_LOOKAHEAD))
            debug.trace_object(4, self.dialect, "csv sniffer")
            self.input_stream.seek(0)
            if (self.output_dialect is None):
                self.output_dialect = self.dialect

        # Optionally, fixup input if TSV changing multiple spaces into single tab.
        # Note: makes pass through data, writes to temp file, and then resets input stream to
        # read from the temp file.
        # TODO: have option to distinguish old-style loose fix (3+ spaces) from strict fix (all whitespace)
        if self.fix:
            debug.assertion(self.delimiter == TAB)
            temp_file_stream = system.open_file(self.temp_file, mode="w")
            num_fixed = 0
            for line in self.input_stream.readlines():
                new_line = re.sub(r" +", TAB, line)
                if (new_line != line):
                    num_fixed += 1
                    line = new_line
                debug.assertion(SPACE not in line)
                temp_file_stream.write(line)
            debug.trace(4, f"Fixed {num_fixed} lines")
            temp_file_stream.close()
            self.input_stream = system.open_file(self.temp_file, mode="r")
            ## HACK: pretend reading from stdin
            sys.stdin = self.input_stream

        # Create reader and writer
        debug.trace_expr(4, self.delimiter, self.output_delimiter, self.dialect, self.output_dialect)
        if (self.input_stream != sys.stdin):
            # note: silly csv.reader requirement for newline option to open (TODO, open what?)
            # TODO: add support for multiple filenames
            self.input_stream = system.open_file(self.filename, newline="")
            debug.assertion(not self.other_filenames)
        self.csv_reader = csv.reader(self.input_stream, delimiter=self.delimiter, 
                                     dialect=self.dialect)
        csv_writer = csv.writer(sys.stdout, delimiter=self.output_delimiter, 
                                dialect=self.output_dialect)
        debug.trace_object(5, self.csv_reader, "csv_reader")
        debug.trace_object(5, self.csv_reader.dialect, "csv_reader.dialect")
        debug.trace_object(5, csv_writer, "csv_writer")
        debug.trace_object(5, csv_writer.dialect, "csv_writer.dialect")

        # Iterate through the rows, outputting subset of columns
        last_row_length = None
        num_rows = 0
        num_cols = None
        columns = None
        for i, row in enumerate(self.csv_reader):
            if NEW_FIX and (self.delimiter == TAB):
                # Strip leading spaces and replace other multiple spaces by a tab
                debug.trace_fmt(7, "old R{n}: {r}", n=(i + 1), r=row)
                line = TAB.join(row)
                line = re.sub("^ +", "", line)
                line = re.sub(" +", TAB, line)
                row = line.split(TAB)
                debug.assertion(not any(SPACE in field for field in row))
            if i == 0:
                # note: Byte order mark (BOM) is removed
                # TODO3: warn about delimiter mismatch
                columns = row
                BOM = '\ufeff'
                if columns and columns[0].startswith(BOM):
                    columns[0] = columns[0][len(BOM):]
                if self.inclusion_spec:
                    self.fields = self.parse_field_spec(self.inclusion_spec, columns)
                if self.exclusion_spec:
                    self.exclude_fields = self.parse_field_spec(self.exclusion_spec, columns)
            debug.trace_fmt(6, "R{n}: {r}", n=(i + 1), r=row)
            debug.trace_fmt(5, "R{n}: len(row)={l} [{rspec}]", n=(i + 1), l=len(row), rspec=elide_values(row))
            debug.assertion((len(row) == last_row_length) or (not last_row_length))
            last_row_length = len(row)
            # TODO: rework i references in terms of num_rows
            num_rows += 1
            if num_cols is None:
                num_cols = last_row_length

            # Derive the fields to extract if all to be extracted
            debug.trace_fmt(7, "pre f={f} all={a}", f=self.fields, a=self.all_fields)
            if ((not self.fields) and self.all_fields):
                self.fields = [(c + 1) for c in range(len(row)) if (c + 1) not in self.exclude_fields]
                if not self.fields:
                    system.print_stderr("Error: No items in row at line {l}", l=(i + 1))
            debug.trace_fmt(7, "post f={f}", f=self.fields)
            debug.assertion(self.fields)

            # Output line with fields joined by (output) separator
            output_row = []
            for f in self.fields:
                valid_field_number = (1 <= f <= len(row))
                debug.trace_expr(5, f)
                debug.assertion(valid_field_number, f"field {f}")
                column = row[f - 1] if valid_field_number else ""
                if self.single_line:
                    column = re.sub(r"\s", SPACE, column)
                if self.max_field_len:
                    column = gh.elide(column, max_len=self.max_field_len)
                if self.encode_values:
                    ## TODO4: maxcount of 1 for left and right
                    column = repr(column).strip("'")
                output_row.append(column)
            debug.trace_expr(6, output_row)
            try:
                csv_writer.writerow(output_row)
            except:
                ## TODO2: add ignore-errors option
                system.print_exception_info("row output")

        # Do sanity checks
        # Note: this compares row extraction against Pandas dataframe
        if (debug.debugging() and (self.input_stream != sys.stdin)):
            debug.trace(4, "note: csv vs. pandas row count sanity check")
            dataframe = du.read_csv(self.filename, delimiter=self.delimiter, dialect=self.dialect)
            valid_dataframe = (dataframe is not None)
            debug.assertion(valid_dataframe)
            if valid_dataframe:
                df_num_rows = 1 + len(dataframe)
                df_num_cols = len(dataframe.columns)
                debug.trace_fmt(4, "csv dimensions: {nr}x{nc}", nr=num_rows, nc=num_cols)
                debug.trace_fmt(4, "pandas dimensions: {nr}x{nc}", nr=df_num_rows, nc=df_num_cols)
                debug.assertion(num_rows == df_num_rows)
                debug.assertion(num_cols == df_num_cols)

        return

if __name__ == '__main__':
    debug.trace_current_context()
    debug.trace_fmt(4, "Environment options: {eo}",
                    eo=system.formatted_environment_option_descriptions())
    app = Script(
        description=__doc__,
        skip_input=False,
        manual_input=True,
        multiple_files=True,
        boolean_options=(
            [("Fn", "alias for --field n")] +
            [(f"F{i + 1}", argparse.SUPPRESS) for i in range(NUM_FN_SHORTCUTS)] +
            [(CSV, "Comma-separated values ({xls} as per csv module)".format(xls=EXCEL_STYLE)),
             (TSV, "Tab-separated values"),
             OUTPUT_CSV, OUTPUT_TSV,
             (CONVERT_DELIM, "Convert csv to tsv (or vice versa)"),
             (SNIFFER_ARG, "Detect csv dialect by lookahead (file-input only)"),
             ## TODO: INPUT_CSV, OUTPUT_CSV, INPUT_TSV, OUTPUT_TSV,
             (FIX, "Fix up sloppy input (e.g., multiple spaces into tab)--csv fixup not yet supported"),
             (ALL_FIELDS, "Alternative to {f} option".format(f=FIELDS)),
             (EXCEL_STYLE, "Use Excel conventions for CSV files (see csv python package docs)"),
             (PYSPARK_STYLE, "Use PySpark conventions for CSV files (see {f} source)".format(f=__file__)),
             (SINGLE_LINE, "Remove embedded newlines from mult-line fields"),
             (TAB_STYLE, "Non-excel TSV conventions (default)"),
             ## (TODO_ARG, "TODO: arg desc").
             (UNIX_STYLE, "Use Unix conventions for CSV files (see csv python package docs)"),
             (ENCODE_OPT, "Output field encoded via repr (i.e., canonical representation)"),
             ]),
        int_options = [(MAX_FIELD_LEN, "Maximum length per field")],
        text_options=[(DELIM, "Input field separator"),
                      (DIALECT, "CSV module dialect: standard (i.e., excel, excel-tab, or unix) or adhoc (e.g., pyspark, hive)"),
                      (OUTPUT_DIALECT, "dialect for output--defaults to input one"),
                      (FIELDS, "Field specification (1-based or label): single column, range of columns, or comma-separated columns"),
                      (F_OPT, "Alias for --fields"),
                      (OUT_DELIM, "Output field separator"),
                      (EXCLUDE_OPT, "Field specification (1-based or label): single column, range of columns, or comma-separated columns"),
                      (X_OPT, "Alias for --exclude"),
                      ])
    app.run()
