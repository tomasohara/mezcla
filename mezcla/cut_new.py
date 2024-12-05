#! /usr/bin/env python
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
## OLD: import more_itertools
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
FIELDS = "fields"  # field indices (1-based or symbolic)
F_OPT = "f"  # alias for fields
EXCLUDE_OPT = "exclude"  # fields to exclude (1-based or symbolic)
X_OPT = "x"  # alias for exclude
ENCODE_OPT = "encode"  # use repr for newlines, etc.
FIX = "fix"  # convert runs of spaces into a tab
CSV = "csv"  # comma-separated value format
TSV = "tsv"  # tab-separated value format
OUTPUT_CSV = "output-csv"  # CSV for output
OUTPUT_TSV = "output-tsv"  # TSV for output
CONVERT_DELIM = "convert-delim"  # convert input csv to tsv (or vice versa)
SNIFFER_ARG = "sniffer"  # run CSV sniffer to detect dialect
## TODO
## INPUT_CSV = "input-csv"
## OUTPUT_CSV = "output-csv"
## INPUT_TSV = "input-tsv"
## OUTPUT_TSV = "output-tsv"
DELIM = "delim"  # input delimiter
OUT_DELIM = "output-delim"  # output delimiter if not same for input
ALL_FIELDS = "all-fields"  # use all fields in output (e.g., for delimiter conversion)
TAB = "\t"
SPACE = " "
COMMA = ","
## TODO: make -style suffix optional (e.g., --tab[-style])
EXCEL_STYLE = "excel-style"  # use Excel dialect for CSV (redundant with default)
UNIX_STYLE = "unix-style"  # use Unix dialect for CSV (otherwise Excel is used)
PYSPARK_STYLE = "pyspark-style"  # use PySpark dialect for CSV (otherwise Unix is used)
## TEMP: workaround problem under MacOS
FORCE_SINGLE_LINE = system.getenv_bool(
    "FORCE_SINGLE_LINE",
    False,
    description="Force single line quotedchar handling (i.e., non-strict mode)",
)
TAB_STYLE = "tab-style"  # use (non-Excel) tab dialect
DIALECT = "dialect"  # --dialect option
OUTPUT_DIALECT = "output-dialect"  # --output-dialect option
EXCEL_DIALECT = "excel"  # dialect parameter for Excel style
UNIX_DIALECT = "unix"  # "" for Unix style
PYSPARK_DIALECT = "pyspark"  # "" for Pyspark style
SNIFFER_LOOKAHEAD = 65536  # buffer size for guessing dialect (64k)
TAB_DIALECT = "tab"  # dialect option for TSV
SINGLE_LINE = "single-line"  # collapse multi-line fields into one
MAX_FIELD_LEN = "max-field-len"  # value length before elided
## TODO: TODO_ARG = "TODO-arg"          # TODO: comment
NEW_FIX = system.getenv_bool(
    "NEW_FIX", False, desc="HACK: Fix for --fix bug for whitespace to tabs"
)
NUM_FN_SHORTCUTS = 9
CSV_FORMAT = system.getenv_bool("CSV_FORMAT", False, desc="Use CSV instead of TSV")
MAX_FIELD_SIZE = system.getenv_int(
    "MAX_FIELD_SIZE", -1, desc="Overide for default max field size (128k)"
)

# ...............................................................................

MAX_VALUE_LEN = 128


#
def elide_values(in_list, max_len=MAX_VALUE_LEN):
    """Elide each of the values in IN_LIST (up to MAX_LEN each).
    Note: Returns list of strings"""
    # EX: elide_values(["1234567890", 1234567890, True, False], max_len=4) => ["1234...", "1234...", "True", "Fals..."]
    new_list = []
    for item in in_list:
        new_list.append(gh.elide(system.to_text(item), max_len))
    debug.trace_fmt(
        7, "elide_values({l}, [{m}]) => {r}", l=in_list, m=max_len, r=new_list
    )
    return new_list


def flatten_list_of_strings(list_of_str):
    """Flatten out LIST_OF_STR"""
    # EX: flatten_list_of_strings([["l1i1", "l1i2"], ["l2i1"]]) => ["l1i1", "l1i2", "l2i1"]
    result = functools.reduce(operator.concat, list_of_str)
    debug.trace(5, f"flatten_list_of_strings({list_of_str}) => {result}")
    return result


# ...............................................................................
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

    delimiter = ","
    quotechar = '"'
    doublequote = False  # uses escaped double quote when embedded
    escapechar = "\\"
    skipinitialspace = False
    lineterminator = "\n"
    quoting = csv.QUOTE_MINIMAL  # only delimiter, double quote or end-of-line


#
csv.register_dialect("pyspark", pyspark_dialect)
#
# note: Uses hive as alias for pyspark.
csv.register_dialect("hive", pyspark_dialect)


class tab_dialect(csv.Dialect):
    """TSV module dialect for tab-separated values (non-Excel)."""

    delimiter = TAB
    ## OLD: quotechar = ''               # default of '"' leads to multiline rows
    quotechar = '"' if not FORCE_SINGLE_LINE else ""
    doublequote = False  # uses escaped double quote when embedded
    # TODO: use special Unicode space-like character
    escapechar = "\\"
    skipinitialspace = False  # keep leaing space afer delimiter
    lineterminator = "\n"
    quoting = csv.QUOTE_NONE  # no special processing for quotes


#
csv.register_dialect("tab", tab_dialect)

# ...............................................................................

class CutArgsProcessing(Main):
    """Input processing class"""

    # Initialization of variables
    inclusion_spec = ""
    exclusion_spec = ""
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
    filename = None

    def setup(self):
        """Centralized setup method."""
        debug.trace_fmtd(5, "Script.setup(): self={s}", s=self)

        # Process individual configuration options
        self._process_field_options()
        self._process_delimiter_options()
        self._process_csv_dialect_options()

        # Initialize CutLogic object
        self.cut_logic = CutLogic()
        self.cut_logic.filename = self.filename
        self.cut_logic.delimiter = self.delimiter or COMMA  # Default to comma if not set
        self.cut_logic.output_delimiter = self.output_delimiter or self.cut_logic.delimiter

        # Trace final instance state
        self._trace_instance()

    def _process_field_options(self):
        """Processes field-related command-line options."""
        debug.trace_fmtd(5, "Processing field options.")
        
        # Process inclusion fields
        for i in range(NUM_FN_SHORTCUTS):
            if self.get_parsed_option(f"F{i + 1}"):
                self.fields.append(str(i + 1))
        
        fields_default = ",".join(self.fields)
        self.inclusion_spec = self.get_parsed_option(FIELDS, fields_default)

        # Process exclusion fields
        exclude_default = ",".join(self.exclude_fields)
        self.exclusion_spec = self.get_parsed_option(EXCLUDE_OPT, exclude_default)

        # Validate inclusion and exclusion options
        if self.inclusion_spec and self.exclusion_spec:
            raise ValueError("Cannot specify both inclusion and exclusion fields.")

        # Other field-related options
        self.encode_values = self.get_parsed_option(ENCODE_OPT, self.encode_values)
        self.all_fields = self.get_parsed_option(ALL_FIELDS, not self.fields)
        self.fix = self.get_parsed_option(FIX, self.fix)

    def _process_delimiter_options(self):
        """Processes delimiter-related options."""
        debug.trace_expr(5, self.delimiter, label="Parsed delimiter")

        # Explicitly set delimiter
        explicit_delim = self.get_parsed_option(DELIM, None)
        if explicit_delim:
            self.delimiter = explicit_delim
        else:
            # Default to CSV/TSV style based on options
            if self.get_parsed_option(CSV, self.csv):
                self.delimiter = COMMA
            elif self.get_parsed_option(TSV, False):
                self.delimiter = TAB

        # Output delimiter fallback
        self.output_delimiter = self.get_parsed_option(OUT_DELIM, self.delimiter or COMMA)

        # Other delimiter-related options
        self.run_sniffer = self.get_parsed_option(SNIFFER_ARG, self.run_sniffer)
        self.single_line = self.get_parsed_option(SINGLE_LINE, self.single_line)
        self.max_field_len = self.get_parsed_option(MAX_FIELD_LEN, self.max_field_len)

    def _process_csv_dialect_options(self):
        """Processes CSV dialect options."""
        debug.trace_fmtd(5, "Processing CSV dialect options.")

        # Check for exclusive dialect options
        dialects = [DIALECT, EXCEL_DIALECT, UNIX_DIALECT, PYSPARK_DIALECT, TAB_DIALECT]
        debug.assertion(
            system.just_one_non_null(
                [self.get_parsed_option(o, None) for o in dialects]
            )
        )

        # Set dialect based on options
        pyspark_style = self.get_parsed_option(PYSPARK_STYLE)
        if self.get_parsed_option(EXCEL_STYLE):
            self.dialect = EXCEL_DIALECT
        elif pyspark_style:
            self.dialect = PYSPARK_DIALECT
        elif self.get_parsed_option(UNIX_STYLE) or self.delimiter == COMMA:
            self.dialect = UNIX_DIALECT
        elif self.get_parsed_option(TAB_STYLE) or self.delimiter == TAB:
            self.dialect = TAB_DIALECT

        # Output dialect defaults
        self.output_dialect = self.get_parsed_option(
            OUTPUT_DIALECT, self.dialect or UNIX_DIALECT
        )

    def _trace_instance(self):
        """Logs the current state of the instance for debugging."""
        debug.trace_object(5, self, label="Script instance")

    def run_main_step(self):
        """Main processing step."""
        debug.trace_fmtd(4, "run_main_step()")

        # Ensure CutLogic is set up
        if not hasattr(self, 'cut_logic'):
            raise RuntimeError("CutLogic is not initialized. Call setup() first.")

        # Override field size
        self.cut_logic.override_field_size(MAX_FIELD_SIZE)

        # Initialize CSV processing
        self.cut_logic.initialize_csv_processing()

        # Fallback for no processing options
        if not any([self.inclusion_spec, self.exclusion_spec, self.fix]):
            debug.trace(3, "No processing options provided. Echoing file content.")
            if self.cut_logic.csv_reader is not None:
                for row in self.cut_logic.csv_reader:
                    print(self.cut_logic.delimiter.join(row))
            return

        # Normal CSV processing
        self.cut_logic.determine_dialect(self.run_sniffer, SNIFFER_LOOKAHEAD)

        if self.fix:
            self.cut_logic.fix_input(self.temp_file)

        num_rows = 0
        num_cols = None
        last_row_length = None

        for i, row in enumerate(self.cut_logic.csv_reader):
            if NEW_FIX and self.cut_logic.delimiter == TAB:
                row = self.cut_logic.sanitize_row(row)
            if i == 0:
                self.cut_logic.initialize_fields(row, self.inclusion_spec, self.exclusion_spec)

            # Ensure row consistency
            if last_row_length is not None and len(row) != last_row_length:
                raise ValueError(f"Inconsistent row length at row {i}: {row}")

            last_row_length = len(row)
            num_rows += 1
            num_cols = num_cols or last_row_length

            output_row = self.cut_logic.extract_fields(row)
            self.cut_logic.csv_writer.writerow(output_row)

        self.cut_logic.perform_sanity_checks(self.cut_logic.filename, num_rows, num_cols)
        debug.trace_expr(5, self.cut_logic.delimiter, label="Parsed Delimiter")


class CutLogic:
    def __init__(self):
        # Initialization code for CutLogic
        self.fields = []
        self.exclude_fields = []
        self.delimiter = COMMA
        self.output_delimiter = COMMA
        self.dialect = None
        self.output_dialect = None
        self.filename = ""
        self.input_stream = None
        self.csv_reader = None
        self.csv_writer = None
        self.single_line = False
        self.max_field_len = None
        self.encode_values = False

    def parse_field_spec(self, field_spec, columns):
        """
        Convert the FIELD_SPEC from string to a list of integers.
        Supports numeric ranges (e.g., "3-5"), comma-separated values (e.g., "7,9,11"),
        and symbolic names (e.g., "sepal_width,petal_width").
        """
        debug.trace(5, f"parse_field_spec({field_spec}, {columns}); self={self}")
        field_spec = self._replace_field_names_with_indices(field_spec, columns)
        field_spec = self._normalize_field_spec(field_spec, len(columns))
        field_spec = self._expand_field_ranges(field_spec, len(columns))
        return self._convert_field_spec_to_list(field_spec)

    def _replace_field_names_with_indices(self, field_spec, columns):
        """
        Replace symbolic field names with their corresponding indices.
        """
        original_spec = field_spec
        while my_re.search(r"([a-z][a-z0-9_]+)", field_spec, flags=my_re.IGNORECASE):
            field_name = my_re.group(1)
            if field_name not in columns:
                system.print_error(
                    f"Error: Unable to resolve field {field_name!r}: original_spec={original_spec}"
                )
                break
            field_pos = 1 + columns.index(field_name)  # 1-based index
            field_spec = my_re.pre_match() + str(field_pos) + my_re.post_match()
            debug.trace(4, f"Replaced {field_name!r} with {field_pos}")
        return field_spec

    def _normalize_field_spec(self, field_spec, num_columns):
        """
        Normalize the FIELD_SPEC to remove unnecessary spaces, commas, and invalid patterns.
        """
        debug.assertion(not re.search(r"[0-9] [0-9]", field_spec))
        field_spec = field_spec.replace(SPACE, "")
        debug.assertion(",," not in field_spec)
        field_spec = re.sub(r",,+", ",", field_spec)
        field_spec = re.sub(r"(^,)|(,$)", "", field_spec)
        debug.trace_fmtd(5, "Normalized field_spec: {fs}", fs=field_spec)

        # Handle edge cases with ranges missing bounds
        field_spec = my_re.sub(r"^\-", "1-", field_spec)  # "-N" -> "1-N"
        field_spec = my_re.sub(
            r"\-$", f"-{num_columns}", field_spec
        )  # "N-" -> "N-num_columns"

        return field_spec

    def _expand_field_ranges(self, field_spec, num_columns):
        """
        Expand numeric ranges (e.g., "3-5") into comma-separated values (e.g., "3,4,5").
        """
        while my_re.search(r"([0-9]+)\-([0-9]+)", field_spec):
            range_spec = my_re.group(0)
            start, end = int(my_re.group(1)), int(my_re.group(2))
            debug.assertion(start < end, f"Invalid range: {range_spec}")
            expanded_range = ",".join(map(str, range(start, end + 1)))
            field_spec = field_spec.replace(range_spec, expanded_range, 1)
            debug.trace_fmtd(
                4, "Expanded range: {rs} => {er}", rs=range_spec, er=expanded_range
            )

        debug.trace_fmtd(5, "Expanded field_spec: {fs}", fs=field_spec)
        return field_spec

    def _convert_field_spec_to_list(self, field_spec):
        """
        Convert the normalized and expanded FIELD_SPEC string into a list of integers.
        """
        field_list = [int(f) for f in field_spec.split(",")] if field_spec else []
        debug.assertion(field_list, "Field specification resulted in an empty list.")
        debug.trace_fmtd(4, "parse_field_spec() => {fl}", fl=field_list)
        return field_list

    def override_field_size(self, max_field_size):
        """Override maximum field size if specified."""
        if max_field_size > -1:
            old_limit = csv.field_size_limit()
            debug.assertion(max_field_size > old_limit)
            csv.field_size_limit(max_field_size)
            debug.trace(4, f"Set max field size to {max_field_size}; was {old_limit}")

    def determine_dialect(self, run_sniffer, lookahead):
        """Determine dialect for CSV input."""
        if (self.delimiter == COMMA) and (not self.dialect) and run_sniffer:
            debug.assertion(self.input_stream != sys.stdin)
            self.dialect = csv.Sniffer().sniff(self.input_stream.read(lookahead))
            debug.trace_object(4, self.dialect, "csv sniffer")
            self.input_stream.seek(0)
            if self.output_dialect is None:
                self.output_dialect = self.dialect

    def fix_input(self, temp_file, fix_delimiter=TAB):
        """Fix input data if specified."""
        if not self.input_stream:
            raise ValueError("Input stream is not initialized.")
        debug.assertion(self.delimiter == fix_delimiter)

        temp_file_stream = system.open_file(temp_file, mode="w")
        num_fixed = 0
        for line in self.input_stream.readlines():
            new_line = re.sub(r" +", fix_delimiter, line)
            if new_line != line:
                num_fixed += 1
            debug.assertion(SPACE not in new_line)
            temp_file_stream.write(new_line)
        debug.trace(4, f"Fixed {num_fixed} lines")
        temp_file_stream.close()
        self.input_stream = system.open_file(temp_file, mode="r")
        sys.stdin = self.input_stream

    def initialize_csv_processing(self):
        """Initialize CSV reader and writer, or return file contents as lines if no delimiter is set."""
        debug.trace(3, f"Filename before opening: {self.filename}")

        if not self.filename:
            raise ValueError(
                "Filename is not set. Please provide a valid input file or use standard input."
            )

        if self.filename == "-": 
            debug.trace(3, "Using standard input as the data source.")
            self.input_stream = sys.stdin
        else:
            try:
                self.input_stream = system.open_file(self.filename, newline="")
            except FileNotFoundError:
                raise FileNotFoundError(f"File '{self.filename}' does not exist.")

        if self.delimiter is None:
            # Read the contents of the file as lines and return them
            debug.trace(3, "No delimiter set. Returning file contents as lines.")
            lines = self.input_stream.readlines()
            self.input_stream.seek(0)  # Reset the stream for potential further use
            return lines  # Return the file contents as a list of lines

        # Proceed with CSV processing if a delimiter is set
        debug.trace(3, f"Using delimiter: {self.delimiter}")
        debug.trace(3, f"Output delimiter: {self.output_delimiter}")

        self.csv_reader = csv.reader(
            self.input_stream, delimiter=self.delimiter, dialect=self.dialect
        )
        self.csv_writer = csv.writer(
            sys.stdout, delimiter=self.output_delimiter, dialect=self.output_dialect
        )

        debug.trace_object(5, self.csv_reader, "csv_reader")
        debug.trace_object(5, self.csv_reader.dialect, "csv_reader.dialect")
        debug.trace_object(5, self.csv_writer, "csv_writer")
        debug.trace_object(5, self.csv_writer.dialect, "csv_writer.dialect")

    def sanitize_row(self, row):
        """Sanitize row data."""
        line = TAB.join(row)
        line = re.sub("^ +", "", line)
        line = re.sub(" +", TAB, line)
        return line.split(TAB)

    def initialize_fields(self, row, inclusion_spec=None, exclusion_spec=None):
        """Initialize fields and exclusions based on the header row."""
        columns = row
        BOM = "\ufeff"
        if columns and columns[0].startswith(BOM):
            columns[0] = columns[0][len(BOM) :]
        if inclusion_spec:
            self.fields = self.parse_field_spec(inclusion_spec, columns)
        if exclusion_spec:
            self.exclude_fields = self.parse_field_spec(exclusion_spec, columns)

    def extract_fields(self, row):
        """Extract specified fields from a row."""

        debug.trace_expr(5, self.fields, label="Fields before processing")
        debug.trace_expr(5, len(row), label="Row length")
        debug.trace_expr(5, row, label="Row content")

        # Sanitize the row
        row = [col.strip() for col in row if col.strip()]

        # Convert fields into integers
        fields = [int(f) for f in self.fields]

        # Return entire row if no fields specified
        if not fields:
            return row

        output_row = []
        for f in fields:
            if not (1 <= f <= len(row)):
                debug.trace(
                    3, f"Invalid field {f} for row with length {len(row)}: {row}"
                )
                raise ValueError(f"Field {f} out of range for row: {row}")
            column = row[f - 1]
            if self.single_line:
                column = re.sub(r"\s", SPACE, column)
            if self.max_field_len:
                column = gh.elide(column, max_len=self.max_field_len)
            if self.encode_values:
                column = repr(column).strip("'")
            output_row.append(column)

        return output_row

    def perform_sanity_checks(self, filename, num_rows, num_cols):
        """Perform sanity checks on the processed data."""
        if debug.debugging() and (self.input_stream != sys.stdin):
            debug.trace(4, "note: csv vs. pandas row count sanity check")
            dataframe = du.read_csv(
                filename, delimiter=self.delimiter, dialect=self.dialect
            )
            valid_dataframe = dataframe is not None
            debug.assertion(valid_dataframe)
            if valid_dataframe:
                df_num_rows = 1 + len(dataframe)
                df_num_cols = len(dataframe.columns)
                debug.trace_fmt(
                    4, "csv dimensions: {nr}x{nc}", nr=num_rows, nc=num_cols
                )
                debug.trace_fmt(
                    4, "pandas dimensions: {nr}x{nc}", nr=df_num_rows, nc=df_num_cols
                )
                debug.assertion(num_rows == df_num_rows)
                debug.assertion(num_cols == df_num_cols)


if __name__ == "__main__":
    debug.trace_current_context()
    debug.trace_fmt(
        4,
        "Environment options: {eo}",
        eo=system.formatted_environment_option_descriptions(),
    )
    app = CutArgsProcessing(
        # description=__doc__,
        skip_input=False,
        manual_input=True,
        multiple_files=True,
        boolean_options=(
            [("Fn", "alias for --field n")]
            + [(f"F{i + 1}", argparse.SUPPRESS) for i in range(NUM_FN_SHORTCUTS)]
            + [
                (
                    CSV,
                    "Comma-separated values ({xls} as per csv module)".format(
                        xls=EXCEL_STYLE
                    ),
                ),
                (TSV, "Tab-separated values"),
                OUTPUT_CSV,
                OUTPUT_TSV,
                (CONVERT_DELIM, "Convert csv to tsv (or vice versa)"),
                (SNIFFER_ARG, "Detect csv dialect by lookahead (file-input only)"),
                ## TODO: INPUT_CSV, OUTPUT_CSV, INPUT_TSV, OUTPUT_TSV,
                (
                    FIX,
                    "Fix up sloppy input (e.g., multiple spaces into tab)--csv fixup not yet supported",
                ),
                (ALL_FIELDS, "Alternative to {f} option".format(f=FIELDS)),
                (
                    EXCEL_STYLE,
                    "Use Excel conventions for CSV files (see csv python package docs)",
                ),
                (
                    PYSPARK_STYLE,
                    "Use PySpark conventions for CSV files (see {f} source)".format(
                        f=__file__
                    ),
                ),
                (SINGLE_LINE, "Remove embedded newlines from mult-line fields"),
                (TAB_STYLE, "Non-excel TSV conventions (default)"),
                ## (TODO_ARG, "TODO: arg desc").
                (
                    UNIX_STYLE,
                    "Use Unix conventions for CSV files (see csv python package docs)",
                ),
                (
                    ENCODE_OPT,
                    "Output field encoded via repr (i.e., canonical representation)",
                ),
            ]
        ),
        int_options=[(MAX_FIELD_LEN, "Maximum length per field")],
        text_options=[
            (DELIM, "Input field separator"),
            (
                DIALECT,
                "CSV module dialect: standard (i.e., excel, excel-tab, or unix) or adhoc (e.g., pyspark, hive)",
            ),
            (OUTPUT_DIALECT, "dialect for output--defaults to input one"),
            (
                FIELDS,
                "Field specification (1-based or label): single column, range of columns, or comma-separated columns",
            ),
            (F_OPT, "Alias for --fields"),
            (OUT_DELIM, "Output field separator"),
            (
                EXCLUDE_OPT,
                "Field specification (1-based or label): single column, range of columns, or comma-separated columns",
            ),
            (X_OPT, "Alias for --exclude"),
        ],
    )
    app.run()
