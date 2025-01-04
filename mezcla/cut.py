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
import sys

# Installed modules
## OLD: import more_itertools
import functools
import operator
import pandas as pd

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
PANDAS_OPT = "pandas"
VERBOSE_OPT = "verbose"
## TODO
## INPUT_CSV = "input-csv"
## OUTPUT_CSV = "output-csv"
## INPUT_TSV = "input-tsv"
## OUTPUT_TSV = "output-tsv"
PANDAS = "pandas"
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
EXCEL_TAB_DIALECT = "excel-tab" # dialect parameter for tabbed Excel style
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
## EXPERIMENTAL ENV OPTIONS
DISABLE_QUOTING = system.getenv_bool("DISABLE_QUOTING", False, desc="(Legacy) Force disable double quotes around elements")

USE_PANDAS = system.getenv_bool("USE_PANDAS", False, desc="Use pandas based processing")
ENABLE_SNIFFER = system.getenv_bool("SNIFF_INPUT", False, desc="Enable sniffing of input files")
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

# def return_source_code(function):
#     """Display the code section within a function"""
#     result = inspect.getsource(function)
#     debug.trace(5, f"return_source_code({function}) => {result}")
#     return result


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


class PysparkDialect(csv.Dialect):
    """CSV module dialect for Pyspark CSV files."""
    delimiter = ','
    quotechar = '"'
    doublequote = False          # uses escaped double quote when embedded
    escapechar = '\\'
    skipinitialspace = False
    lineterminator = '\n'
    quoting = csv.QUOTE_MINIMAL  # only delimiter, double quote or end-of-line
#
csv.register_dialect("pyspark", PysparkDialect)
#
# note: Uses hive as alias for pyspark.
csv.register_dialect("hive", PysparkDialect)

class TabDialect(csv.Dialect):
    """TSV module dialect for tab-separated values (non-Excel)."""
    delimiter = TAB
    ## OLD: quotechar = ''               # default of '"' leads to multiline rows
    quotechar = ('"' if not FORCE_SINGLE_LINE else '')
    doublequote = False          # uses escaped double quote when embedded
    # TODO: use special Unicode space-like character
    escapechar = '\\'
    skipinitialspace = False     # keep leaing space afer delimiter
    lineterminator = '\n'
    quoting = csv.QUOTE_NONE     # no special processing for quotes
#
csv.register_dialect("tab", TabDialect)

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
    use_pandas = False
    verbose = False

    def setup(self):
        """Centralized setup method."""
        debug.trace_fmtd(5, "Script.setup(): self={s}", s=self)

        # Process individual configuration options
        self._process_csv_dialect_options()
        self._process_delimiter_options()
        self._process_field_options()
                
        attributes = {
            "filename": self.filename,
            # "delimiter": self.delimiter or COMMA,
            "delimiter": self.delimiter,
            # "output_delimiter": self.output_delimiter or self.delimiter or COMMA,
            "output_delimiter": self.output_delimiter or self.delimiter or COMMA,
            "max_field_len": self.max_field_len,
            "dialect": self.dialect,
            "output_dialect": self.output_dialect,
            "run_sniffer": self.run_sniffer,
        }
        
        self.cut_logic = self._initialize_logic_object(PandasCutLogic, attributes) if self.use_pandas else self._initialize_logic_object(CutLogic, attributes)     

        # Trace final instance state
        self._trace_instance()

    def _initialize_logic_object(self, logic_class, attributes:dict):
        """Dynamically initialize and assign attributes to a logic object."""
        logic_object = logic_class()
        for key, value in attributes.items():
            setattr(logic_object, key, value)
        return logic_object

    def _process_field_options(self):
        """Processes field-related command-line options."""
        debug.trace_fmtd(5, "Processing field options.")
        
        # Process inclusion fields
        for i in range(NUM_FN_SHORTCUTS):
            if self.get_parsed_option(f"F{i + 1}"):
                self.fields.append(str(i + 1))
        
        fields_default = ",".join(self.fields)
        ## OLD: self.inclusion_spec = self.get_parsed_option(FIELDS, fields_default)
        self.inclusion_spec = self.get_parsed_option(FIELDS, fields_default) or self.get_parsed_option(F_OPT, fields_default)

        # Process exclusion fields
        exclude_default = ",".join(self.exclude_fields)
        self.exclusion_spec = self.get_parsed_option(EXCLUDE_OPT, exclude_default) or self.get_parsed_option(X_OPT, exclude_default)

        if self.inclusion_spec and self.exclusion_spec:
            raise ValueError("Cannot specify both inclusion and exclusion fields.")

        # Other field-related options
        self.encode_values = self.get_parsed_option(ENCODE_OPT, self.encode_values)
        self.all_fields = self.get_parsed_option(ALL_FIELDS, not self.fields)
        self.fix = self.get_parsed_option(FIX, self.fix)
        self.use_pandas = self.get_parsed_option(PANDAS_OPT, self.use_pandas)
        self.verbose = self.get_parsed_option(VERBOSE_OPT, self.verbose)

    def _process_delimiter_options(self):
        """Processes delimiter-related options."""
        self.csv = self.get_parsed_option(CSV, self.csv)
        if self.csv:
            self.delimiter = COMMA

        tsv = self.get_parsed_option(TSV, not self.csv)
        if tsv:
            self.delimiter = TAB

        explicit_delim = self.get_parsed_option(DELIM, self.delimiter)
        if explicit_delim:
            self.delimiter = explicit_delim
            self.csv = False  
            
        self.output_delimiter = self.get_parsed_option(OUT_DELIM, None)
        if self.output_delimiter is None:  
            if self.get_parsed_option(OUTPUT_TSV):
                self.output_delimiter = TAB
                debug.trace_expr(5, "OUTPUT_TSV set: Output Delimiter is TAB")
            elif self.get_parsed_option(OUTPUT_CSV):
                self.output_delimiter = COMMA 
            elif self.get_parsed_option(CONVERT_DELIM):
                self.output_delimiter = TAB if self.delimiter == COMMA else COMMA
            else:
                self.output_delimiter = self.delimiter
        else:
            debug.trace_expr(5, self.output_delimiter, label="Output Delimiter")

        debug.trace_expr(5, self.delimiter, label="Input Delimiter")
        debug.trace_expr(5, self.output_delimiter, label="Output Delimiter")

        self.run_sniffer = self.get_parsed_option(SNIFFER_ARG, self.run_sniffer)

        debug.assertion(not (self.csv and (self.delimiter != COMMA)))
        self.single_line = self.get_parsed_option(SINGLE_LINE, self.single_line)
        self.max_field_len = self.get_parsed_option(MAX_FIELD_LEN, self.max_field_len)
        
    def _process_csv_dialect_options(self):
        """Processes CSV dialect options."""
        debug.trace_fmtd(5, "Processing CSV dialect options.")

        self.run_sniffer = self.get_parsed_option(SNIFFER_ARG, self.run_sniffer)
        dialects = [DIALECT, EXCEL_DIALECT, UNIX_DIALECT, PYSPARK_DIALECT, TAB_DIALECT, EXCEL_TAB_DIALECT]
        
        debug.assertion(
            system.just_one_non_null(
                [self.get_parsed_option(o, None) for o in dialects]
            )
        )

        if not self.dialect:
            if self.get_parsed_option(EXCEL_STYLE):
                self.dialect = EXCEL_DIALECT
            elif self.get_parsed_option(PYSPARK_STYLE):
                self.dialect = PYSPARK_DIALECT
            elif self.get_parsed_option(UNIX_STYLE) or self.delimiter == COMMA:
                self.dialect = UNIX_DIALECT
            elif self.get_parsed_option(TAB_STYLE) or self.delimiter == TAB:
                self.dialect = TAB_DIALECT

        ## NOTE: Execute when no output delimiter is specified
        if not self.get_parsed_option(OUT_DELIM, None):
            ## OLD: self.output_dialect = self.get_parsed_option(OUTPUT_DIALECT, self.dialect or UNIX_DIALECT)
            self.output_dialect = self.get_parsed_option(OUTPUT_DIALECT, self.dialect)
            if self.output_dialect == EXCEL_DIALECT:
                self.output_delimiter = COMMA
            elif self.output_dialect == TAB_DIALECT or self.output_dialect == 'excel-tab':
                self.output_delimiter = TAB
            else:
                self.output_delimiter = COMMA
        else:
            self.output_dialect = None

        debug.trace_expr(5, self.dialect, label="Dialect")
        debug.trace_expr(5, self.output_dialect, label="Output Dialect")
        debug.trace_expr(5, self.output_delimiter, label="Output Delimiter")

    def _trace_instance(self):
        """Logs the current state of the instance for debugging."""
        debug.trace_object(5, self, label="\nScript instance")

    def _main_step_cut_logic(self):
        if not hasattr(self, 'cut_logic'):
            raise RuntimeError("CutLogic is not initialized. Call setup() first.")

        self.cut_logic.override_field_size(MAX_FIELD_SIZE)
        self.cut_logic.initialize_io_processing()
        debug.trace(5, "About to call determine_dialect")
        self.cut_logic.determine_dialect(self.run_sniffer, SNIFFER_LOOKAHEAD)

        # Ensure Sniffer results are applied
        debug.trace_expr(5, self.cut_logic.delimiter, label="Detected Delimiter")
        if self.run_sniffer:
            debug.trace(5, "Applying Sniffer detected delimiter to CSV reader.")
            self.cut_logic.csv_reader = csv.reader(
                self.cut_logic.input_stream, delimiter=self.cut_logic.delimiter
            )
        else:
            debug.trace(5, "Using predefined delimiter.")

        if self.fix:
            self.cut_logic.fix_input(self.temp_file)

        num_rows = 0
        num_cols = None
        last_row_length = None

        for i, row in enumerate(self.cut_logic.csv_reader):
            
            # Handle rows that might not be split correctly
            if isinstance(row, list) and len(row) == 1:
                debug.trace(5, f"Row before splitting: {row}")
                row = row[0].split(self.cut_logic.delimiter)
                debug.trace(5, f"Row after splitting: {row}")

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

            try:
                debug.trace(5, f"Output Rows at run_main_step = {output_row}")
                self.cut_logic.csv_writer.writerow(output_row)
            except csv.Error as e:
                system.print_exception_info(f"Row Output Error: {e}")

        self.cut_logic.perform_sanity_checks(self.cut_logic.filename, num_rows, num_cols)
        debug.trace_expr(5, self.cut_logic.run_sniffer, label="run_sniffer")
        debug.trace_expr(5, self.cut_logic.delimiter, label="delimiter")
        debug.trace_expr(5, self.cut_logic.output_delimiter, label="output_delimiter")
        debug.trace_expr(5, self.cut_logic.dialect, label="dialect")
        debug.trace_expr(5, self.cut_logic.output_dialect, label="output_dialect")

    def _main_step_pandas_cut_logic(self):
        if not hasattr(self, 'cut_logic'):
            raise RuntimeError("PandasCutLogic is not initialized. Call setup() first.")

        self.cut_logic.determine_dialect(self.run_sniffer, SNIFFER_LOOKAHEAD)
        self.cut_logic.initialize_io_processing()
        self.cut_logic.initialize_fields(self.inclusion_spec, self.exclusion_spec)

        try:
            extracted_df = self.cut_logic.extract_fields()
            result = self.cut_logic.return_formatted_output(extracted_df)
            print(result, end="")
            # debug.trace(3, f"Verbose Code: {self.cut_logic.simplified_code}")
            if self.verbose:
                print(f"\nVerbose Code\n{'='*15}")
                for x in self.cut_logic.simplified_code:
                    print(x)
            debug.trace_expr(5, extracted_df.shape, label="Extracted DataFrame Shape")
        except Exception as e:
            system.print_exception_info(f"Field Extraction: {e}")
            raise e
        
    def run_main_step(self):
        """Main processing step."""
        debug.trace_fmtd(4, "run_main_step()")
        if self.use_pandas:
            self._main_step_pandas_cut_logic()
        else:
            self._main_step_cut_logic()
        
class CutLogic:
    """Class for implementation of Cut Logic"""
    def __init__(self):
        # Initialization code for CutLogic
        self.fields = []
        self.exclude_fields = []
        self.delimiter = None
        self.output_delimiter = None
        self.dialect = None
        self.output_dialect = None
        self.filename = ""
        self.input_stream = None
        self.csv_reader = None
        self.csv_writer = None
        self.single_line = False
        self.max_field_len = None
        self.encode_values = False
        self.run_sniffer = False

    def parse_field_spec(self, field_spec, columns):
        """
        Convert the FIELD_SPEC from string to a list of integers.
        Supports numeric ranges (e.g., "3-5"), comma-separated values (e.g., "7,9,11"),
        and symbolic names (e.g., "sepal_width,petal_width").
        """
        debug.trace(5, f"parse_field_spec({field_spec}, {columns}); self={self}")
        field_spec = self._replace_field_names_with_indices(field_spec, columns)
        field_spec = self._normalize_field_spec(field_spec, len(columns))
        field_spec = self._expand_field_ranges(field_spec)
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
        debug.assertion(not my_re.search(r"[0-9] [0-9]", field_spec))
        field_spec = field_spec.replace(SPACE, "")
        debug.assertion(",," not in field_spec)
        field_spec = my_re.sub(r",,+", ",", field_spec)
        field_spec = my_re.sub(r"(^,)|(,$)", "", field_spec)
        debug.trace_fmtd(5, "Normalized field_spec: {fs}", fs=field_spec)

        # Handle edge cases with ranges missing bounds
        field_spec = my_re.sub(r"^\-", "1-", field_spec)  # "-N" -> "1-N"
        field_spec = my_re.sub(
            r"\-$", f"-{num_columns}", field_spec
        )  # "N-" -> "N-num_columns"

        return field_spec

    def _expand_field_ranges(self, field_spec):
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
        ## OLD: return field_list
        result = sorted(field_list)
        return list(set(result))
    
    def override_field_size(self, max_field_size):
        """Override maximum field size if specified."""
        if max_field_size > -1:
            old_limit = csv.field_size_limit()
            if max_field_size > old_limit:
                csv.field_size_limit(max_field_size)
                debug.trace(4, f"Set max field size to {max_field_size}; was {old_limit}")
            else:
                debug.trace(4, f"Field size limit ({max_field_size}) is not greater than the current limit ({old_limit}). Skipping.")

    def determine_dialect(self, run_sniffer, lookahead):
        """Determine dialect for CSV input."""
        debug.trace(5, f"determine_dialect.run_sniffer: {run_sniffer}")
        
        if not run_sniffer:
            debug.trace(5, "Sniffer is disabled. Skipping dialect determination.")
            return

        debug.trace(3, f"Sniffing the dialect with a lookahead of {lookahead} bytes.")
        try:

            sample = self.input_stream.read(lookahead)
            self.input_stream.seek(0)

            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample)

            self.dialect = dialect
            self.delimiter = dialect.delimiter
            self.output_dialect = dialect

            debug.trace(5, f"Sniffer detected delimiter: {self.delimiter}")
        except csv.Error as e:
            debug.trace(5, f"Sniffer failed: {e}")
            if not self.delimiter:
                raise ValueError(f"Sniffer failed to detect delimiter, and no fallback delimiter is provided: {e}") from e
            debug.trace(5, f"Using fallback delimiter: {self.delimiter}.")

    def fix_input(self, row):
        """Fix up sloppy input (e.g., multiple spaces into tab) --csv fixup not yet supported."""
        debug.trace(4, "Fixing up sloppy input.")

        # Replace multiple spaces with a single tab
        row = my_re.sub(r"\s+", TAB, row)

        debug.trace_expr(5, row, label="Fixed Input Row")
        return row

    def initialize_io_processing(self):
        """
        Initialize input/output processing for CSV or raw line processing.
        - Opens the input file or uses standard input if specified.
        - Initializes CSV reader and writer if a delimiter is set.
        - Returns file contents as lines if no delimiter is set.
        """
        debug.trace(5, f"initialize_io_processing: Filename before opening: {self.filename}")

        if not self.filename:
            raise ValueError(
                "Filename is not set. Please provide a valid input file or use standard input."
            )

        # Open input stream
        if self.filename == "-":
            debug.trace(4, "initialize_io_processing: Using standard input as the data source.")
            import io
            self.input_stream = io.StringIO(sys.stdin.read())
        else:
            try:
                debug.trace(5, f"initialize_io_processing: Opening file '{self.filename}'")
                self.input_stream = system.open_file(self.filename, newline="")
            except FileNotFoundError as e:
                raise FileNotFoundError(f"initialize_io_processing: File '{self.filename}' does not exist.") from e


        # Initialize CSV reader
        debug.trace(5, "initialize_io_processing: Initializing CSV reader.")
        self.csv_reader = csv.reader(
            self.input_stream, delimiter=self.delimiter, dialect=self.dialect
        )
        debug.trace_object(5, self.csv_reader, "initialize_io_processing: csv_reader")

        # Initialize CSV writer
        debug.trace(5, "initialize_io_processing: Initializing CSV writer.")

        writer_args = {}
        if self.output_dialect:
            debug.trace(5, f"initialize_io_processing: Using output_dialect: {self.output_dialect}")
            writer_args["dialect"] = self.output_dialect
        elif self.output_delimiter:
            debug.trace(5, f"initialize_io_processing: Using output_delimiter: {self.output_delimiter}")
            writer_args["delimiter"] = self.output_delimiter

        # Apply DISABLE_QUOTING logic
        writer_args["quoting"] = csv.QUOTE_NONE if DISABLE_QUOTING else csv.QUOTE_MINIMAL

        self.csv_writer = csv.writer(sys.stdout, **writer_args)

        debug.trace_object(5, self.csv_writer, "initialize_io_processing: csv_writer")
        debug.trace_object(5, self.csv_writer.dialect, "initialize_io_processing: csv_writer.dialect")

        debug.trace(5, "initialize_io_processing: I/O processing initialization complete.")
      
    def sanitize_row(self, row):
        """Sanitize row data."""
        line = TAB.join(row)
        line = my_re.sub("^ +", "", line)
        line = my_re.sub(" +", TAB, line)
        return line.split(TAB)

    def initialize_fields(self, row, inclusion_spec=None, exclusion_spec=None):
        """Initialize fields and exclusions based on the header row."""
        columns = row
        BOM = "\ufeff"
        if columns and columns[0].startswith(BOM):
            columns[0] = columns[0][len(BOM):]

        # Process inclusion specification
        if inclusion_spec:
            self.fields = self.parse_field_spec(inclusion_spec, columns)

        # Process exclusion specification
        if exclusion_spec:
            self.exclude_fields = self.parse_field_spec(exclusion_spec, columns)

        # Adjust self.fields based on exclusions if both are provided
        if self.exclude_fields:
            if not self.fields:
                self.fields = list(range(1, len(columns) + 1))
            self.fields = [f for f in self.fields if f not in self.exclude_fields]

    def extract_fields(self, row):
        """
        Extract specified fields from a row or truncate the entire row if max_field_len is provided.
        """
        debug.trace_expr(5, self.fields, label="Fields before processing")
        debug.trace_expr(5, len(row), label="Row length")
        debug.trace_expr(5, row, label="Row content")

        # Apply truncation to the entire row if max_field_len is set
        if self.max_field_len:
            debug.trace(4, f"Applying truncation with max_field_len={self.max_field_len}")
            row = elide_values(row, self.max_field_len)
            debug.trace_expr(5, row, label="Row after truncation")

        if not self.fields:
            return row

        # Extract and return specified fields
        fields = [int(f) for f in self.fields]
        debug.trace_expr(4, fields, label="Parsed fields")
        output_row = [row[f - 1] if 1 <= f <= len(row) else "" for f in fields]
        debug.trace_expr(6, output_row, label="Output Row")
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

class PandasCutLogic(CutLogic):
    """Child class based on CutLogic for pandas based processing"""
    def __init__(self):
        super().__init__()
        self.dataframe = None
        self.simplified_code = []

    def _add_to_verbose_code(self, *code):
        """Initialize simplified code for --verbose"""
        for c in code:
            self.simplified_code.append(c)

    def determine_dialect(self, run_sniffer, lookahead):
        """Determine dialect for CSV input."""
        debug.trace(5, f"determine_dialect.run_sniffer: {run_sniffer}")

        if not run_sniffer:
            debug.trace(5, "Sniffer is disabled. Skipping dialect determination.")
            return

        if self.filename == "-":
            raise ValueError("Filename must be provided for sniffer to work.")

        try:
            sample = system.read_file(self.filename)

            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample)

            self.dialect = dialect
            self.delimiter = dialect.delimiter
            self.output_dialect = dialect

            debug.trace(5, f"Sniffer detected delimiter: {self.delimiter}")

        except csv.Error as e:
            debug.trace(1, f"Sniffer failed: {e}")
            if not self.delimiter:
                raise ValueError(f"Sniffer failed to detect delimiter, no fallback delimiter is provided: {e}") from e 
            debug.trace(5, f"Using fallback delimiter: {self.delimiter}")

    def initialize_io_processing(self):
        """Initialize io processing"""
        debug.trace(5, f"Filename before opening: {self.filename}")

        if not self.filename:
            raise ValueError("Filename is not set. Please provide a valid input file or use standard input.")

        if not self.delimiter:
            raise ValueError("Delimiter is not set. Ensure `determine_dialect` has set it or provide a fallback delimiter.")

        try:
            self.dataframe = pd.read_csv(
                self.filename if self.filename != "-" else sys.stdin,
                delimiter=self.delimiter,
                encoding="utf-8"
            )
            debug.trace(5, f"Loaded DataFrame with shape {self.dataframe.shape}")
            
            # Verbose code to create dataframe
            delimiter_literal = (
                self.delimiter.replace("\t", "\\t") if self.delimiter == "\t" else self.delimiter
            )
            self._add_to_verbose_code(
                "import pandas as pd",
                f"df = pd.read_csv('{self.filename}', delimiter='{delimiter_literal}')"
            )
        
        except FileNotFoundError as e:
            raise FileNotFoundError(f"File '{self.filename}' does not exist.") from e

    #pylint: disable=arguments-differ
    def initialize_fields(self, inclusion_spec=None, exclusion_spec=None):
        """
        Initialize fields and exclusions based on the DataFrame columns.
        Args:
            dataframe (pd.DataFrame): The input DataFrame with column headers.
            inclusion_spec (str): Specification for columns to include.
            exclusion_spec (str): Specification for columns to exclude.
        """

        columns = list(self.dataframe.columns)
        BOM = "\ufeff"
        
        if columns and columns[0].startswith(BOM):
            columns[0] = columns[0][len(BOM):]

        if inclusion_spec:
            self.fields = self.parse_field_spec(inclusion_spec, columns)

        if exclusion_spec:
            self.exclude_fields = self.parse_field_spec(exclusion_spec, columns)

        if self.exclude_fields:
            if not self.fields:
                self.fields = list(range(1, len(columns) + 1))
            self.fields = [f for f in self.fields if f not in self.exclude_fields]

        debug.trace(5, f"Initialized fields: {self.fields}")
        debug.trace(5, f"Excluded fields: {self.exclude_fields}")

    #pylint: disable=arguments-differ
    def extract_fields(self):
        """
        Extracts specified fields from the dataframe, truncates column names and values 
        to the specified maximum length if provided, and returns simplified Pandas code.
        """
        if self.dataframe is None:
            raise ValueError("Dataframe is not initialized. Call initialize_io_processing first.")

        if self.fields:
            selected_columns = [
                self.dataframe.columns[f - 1] for f in self.fields if f - 1 < len(self.dataframe.columns)
            ]

            # Add column selection commands
            self._add_to_verbose_code(
                f"df = df[{selected_columns}]"
            )
            
            ## NOTE: Uncomment to add index based dataframe extraction
            # selected_indices = [f - 1 for f in self.fields if f - 1 < len(self.dataframe.columns)]
            # self._add_to_verbose_code(
            #     f"df = df.iloc[:, {selected_indices}]"
            # )

        else:
            selected_columns = list(self.dataframe.columns)

        result_df = self.dataframe[selected_columns]

        if self.max_field_len:
            truncated_columns = elide_values(list(result_df.columns), self.max_field_len)
            result_df.columns = truncated_columns

            result_df = result_df.map(
                lambda x: elide_values([str(x)], self.max_field_len)[0] if isinstance(x, (str, int, float)) else x
            )
            self._add_to_verbose_code(
                f"df.columns = [(col[:{self.max_field_len}] + '...') if len(col) > {self.max_field_len} else col for col in df.columns]",
                f"df = df.map(lambda x: (str(x)[:{self.max_field_len}] + '...') if isinstance(x, (str, int, float)) and len(str(x)) > {self.max_field_len} else x)"
            )

        debug.trace(5, f"Extracted fields DataFrame with shape {result_df.shape}")

        return result_df

    def return_formatted_output(self, result_df):
        """Returns formatted delimiter with index dropped for output"""
        result_df = result_df.reset_index(drop=True)
        ## NOTE: To overcome printing of \t as whitespace
        output_delimiter_literal = (
        self.output_delimiter.replace("\t", "\\t") if self.output_delimiter == "\t" else self.output_delimiter
        )
        result = result_df.to_csv(sep=self.output_delimiter, index=False)
        self._add_to_verbose_code(
            f"print(df.to_csv(sep='{output_delimiter_literal}', index=False))"
        )
        debug.trace(5, "Formatted DataFrame for output.")
        return result


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
                (OUTPUT_CSV, "Return output in CSV format"),
                (OUTPUT_TSV, "Return output in TSV format"),
                (CONVERT_DELIM, "Convert csv to tsv (or vice versa)"),
                (PANDAS_OPT, "Use pandas based processing"),
                (VERBOSE_OPT, "Use verbose mode"),
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