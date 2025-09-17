#! /usr/bin/env python3
#
# Miscellaneous functions not suitable for other modules (e.g., system.py).
#
# TODO:
# - Separate list related functions (e.g., as list_utils.py).
#

"""Misc. utility functions"""

# Standard packages
import datetime
from difflib import ndiff
import inspect
import math
import os
import random
import re
import sys
import time
import json
import yaml
import csv
from types import ModuleType
from typing import Any, Optional
from contextlib import ContextDecorator

# Installed packages
## NOTE: made dynamic due to import issue during shell-script repo tests
## TODO3: import more_itertools

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import dummy_app
from mezcla.my_regex import my_re
from mezcla import system
from mezcla import text_utils

# Constants
ELLIPSIS = "\u2026"                 # Horizontal Ellipsis
TYPICAL_EPSILON = system.getenv_float(
    "TYPICAL_EPSILON", 1e-6,
    description="Traditional floating-point negligible difference")
VALUE_EPSILON = system.getenv_float(
    "VALUE_EPSILON", 1e-3,
    description="Epsilon for informal floating-point comparison")
debug.assertion(TYPICAL_EPSILON < VALUE_EPSILON)
RANDOM_SEED = system.getenv_integer(
    "RANDOM_SEED", 15485863,
    ## TEST: "RANDOM_SEED", 15485863 ** 2 - 1,
    description="Integral seed for random number generation: 0 for default")


def transitive_closure(edge_list):
    """Computes transitive close for graph given by EDGE_LIST (i.e., makes indirect links explicit)"""
    # ex: transitive_closure([(1,2),(2,3),(3,4)]) => set([(1, 2), (1, 3), (1, 4), (2, 3), (3, 4), (2, 4)])
    # notes; based on https://stackoverflow.com/questions/8673482/transitive-closure-python-tuples
    closure = set(edge_list)
    while True:
        new_relations = set((x, w) for x, y in closure for q, w in closure if q == y)

        closure_until_now = closure | new_relations
        if closure_until_now == closure:
            break

        closure = closure_until_now

    return closure


def read_tabular_data(filename):
    """Reads table with (unique) key and tab-separated value. 
    Note: key made lowercase"""
    debug.trace_fmtd(4, "read_tabular_file({f})", f=filename)
    table = {}
    with system.open_file(filename) as f:
        for (i, line) in enumerate(f):
            line = system.from_utf8(line)
            items = line.split("\t")
            if len(items) == 2:
                debug.assertion(items[0].lower() not in table)
                table[items[0].lower()] = items[1]
            else:
                debug.trace_fmtd(4, "Ignoring item w/ unexpected format at line {num}",
                                 num=(i + 1))
    ## debug.trace_fmtd(7, "table={t}", t=table)
    debug.trace_values(7, table, "table")
    return table


def extract_string_list(text, strip_empty=False, allow_numeric_ranges=False):
    """Extract a list of values from text using whitespace and/or commas as delimiters.
    With STRIP_EMPTY, empty-string items are ignored.
    """
    # EX: extract_string_list("1  2,3") => ["1", "2", "3"]
    # TODO: Add support for quoted values to allow for embedded spaces
    trimmed_text = my_re.sub(r"\s+", " ", text.strip())
    ## OLD: values = trimmed_text.replace(" ", ",").split(",")
    trimmed_text = my_re.sub(r"([^,]) ", r"\1,", trimmed_text)
    values = my_re.split(", ?", trimmed_text) if trimmed_text else []
    #
    if allow_numeric_ranges:
        new_values = []
        for value in values:
            if my_re.search(r"^(\d+)-(\d+)", value):
                new_values += list(str(v) for v in
                                   range(int(my_re.group(1)), int(my_re.group(2))+ 1))
            else:
                new_values.append(value)
        values = new_values
    #
    if strip_empty:
        values = [v for v in values if v]
    debug.trace_fmtd(5, "extract_string_list({t!r}) => {v!r}", t=text, v=values)
    return values
#
# EX: extract_string_list("1,", strip_empty=True) => ["1"]
# EX: extract_string_list("1-3") => ["1", "2", "3"]


def is_prime(num):
    """Moderately efficient function for testing whether a number is prime
    Notes:
    - Based on https://en.wikipedia.org/wiki/Primality_test.
    - The intuition is that primes > 3 are of form (6k +/- 1).
    """
    ## EX: FIRST_100_PRIMES = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151, 157, 163, 167, 173, 179, 181, 191, 193, 197, 199, 211, 223, 227, 229, 233, 239, 241, 251, 257, 263, 269, 271, 277, 281, 283, 293, 307, 311, 313, 317, 331, 337, 347, 349, 353, 359, 367, 373, 379, 383, 389, 397, 401, 409, 419, 421, 431, 433, 439, 443, 449, 457, 461, 463, 467, 479, 487, 491, 499, 503, 509, 521, 523, 541]; (len(FIRST_100_PRIMES) == 100)
    ## EX: all([is_prime(n) for n in FIRST_100_PRIMES])
    ## EX: all([(not is_prime(n)) for n in range(FIRST_100_PRIMES[-1])  if n not in FIRST_100_PRIMES])
    ##
    debug.trace_fmt(5, "in is_prime({n})", n=num)
    is_prime_num = True

    # First, check primes below 4 (only 2)
    if (num <= 3):
        is_prime_num = (num > 1)
        if not is_prime_num:
            debug.trace_fmt(4, "{n} not prime as less than 3 and not 2.", n=num)
        return is_prime_num

    # Next, make sure not divisible by 2 or 3
    if ((num % 2 == 0) or (num % 3 == 0)):
        debug.trace_fmt(4, "{n} not prime as divisible by 2 or 3.", n=num)
        return False

    # Otherwise, check (6k +/- 1) values to see if divisible by 2 or 3,
    # stopping when value exceeds sqrt(n).
    last_possible = math.ceil(math.sqrt(num))
    i = 5
    while (i <= last_possible):
        if (((num % i) == 0) or ((num % (i + 2)) == 0)):
            debug.trace_fmt(4, "{n} not prime as (6k +/- 1) divisible by 2 or 3 for some k.", n=num)
            is_prime_num = False
            break
        i += 6

    debug.trace_fmt(5, "is_prime({n}) => {ip}", n=num, ip=is_prime_num)
    return is_prime_num


def prime_factorization(num):
    """Return list of primne factors for NUM"""
    ## EX: prime_factors(123) => [3, 41]
    ## EX: prime_factors(127) => [127]
    i = 2
    factors = []
    while i * i <= num:
        if num % i:
            i += 1
        else:
            num //= i
            factors.append(i)
    if num > 1:
        factors.append(num)
    debug.trace(6, f"prime_factorization({num}) => factors")
    return factors


def fibonacci(max_num):
    """Returns Fibonacci sequence with numbers less than MAX_NUM"""
    # EX: fibonacci(10) => [0, 1, 1, 2, 3, 5, 8]
    a, b = 0, 1
    sequence = []
    while (a < max_num):
        sequence.append(a)
        a, b = b, (a + b)
    debug.trace_fmt(9, "fibonacci({m}) => {s}", m=max_num, s=sequence)
    return sequence


def sort_weighted_hash(weights, max_num=None, reverse=None):
    """sorts the entries in WEIGHTS hash, returns list of (key, freq) tuples.
    Note: sorted in REVERSE order by default"""
    if max_num is None:
        max_num = len(weights)
    if reverse is None:
        reverse = True
    sorted_keys = sorted(weights.keys(), reverse=reverse, 
                         key=lambda k: weights[k])
    top_values = [(k, weights[k]) for k in sorted_keys[:max_num]]
    debug.trace_fmt(5, "sort_weighted_hash(_, [max={m}], [rev={r}) => {t}",
                    m=max_num, r=reverse, t=top_values)
    return top_values


def unzip(iterable, num=None):
    """"Inverse of zip operation: returns n lists of i-th elements of input list of tuples. The optional NUM argument ensures that that many values returned (in case of empty input lists)"""
    # See https://stackoverflow.com/questions/19339/transpose-unzip-function-inverse-of-zip.
    # EX: unzip(zip([1, 2, 3], ['a', 'b', 'c'])) => [[1, 2, 3], ['a', 'b', 'c']]
    # EX: unzip(zip([], []), 2) => [[], []]
    result = [list(tupl) for tupl in zip(*iterable)]
    if not result and num:
        result = [[] for _i in range(num)]
    return result


def get_current_frame():
    """Return stack frame (i.e., for caller)"""
    frame = inspect.currentframe().f_back
    debug.trace_fmt(6, "get_current_frame() => {f}", f=frame)
    return frame


def eval_expression(expr_text, frame=None):
    """Evaluate EXPRESSION_given_by_TEXT, using FRAME
    Note: Uses caller's frame if not given. This should only be used
    when the expression involve local variables (see extract_matches.py
    in shell-scripts repo).
    """
    # EX: eval_expression("len([123, 321]) == 2")
    result = None
    try:
        if frame is None:
            frame = get_current_frame()
            # Note: need to get caller's frame
            frame = frame.f_back
        # pylint: disable=eval-used
        result = eval(expr_text, frame.f_globals, frame.f_locals)
    except:
        debug.trace_fmt(5, "Exception during eval_expression({expr}): {exc}",
                        expr=expr_text, exc=sys.exc_info())
    debug.trace_fmt(7, "eval_expression({expr}) => {r}",
                    expr=expr_text, r=result)
    return result


def trace_named_object(level, object_name, caller_frame=None):
    """Trace OBJECT_given_by_NAME
    Note: ***use debug.trace_expr instead ***"""
    # EX: trace_named_object(4, "sys.argv")
    if caller_frame is None:
        caller_frame = get_current_frame().f_back
    debug.trace_object(level, eval_expression(object_name,
                                              frame=caller_frame),
                       label=object_name)
    return


def trace_named_objects(level, list_text):
    """Trace objects in LIST_text
    Note: *** use debug.trace_expr instead ***"""
    # EX: trace_named_object(4, "[len(sys.argv), sys.argv]")
    debug.assertion(re.search(r"^\[.*\]$", list_text))
    frame = get_current_frame().f_back
    for name in text_utils.extract_string_list(list_text[1:-1]):
        trace_named_object(level, name, caller_frame=frame)
    return


def exactly1(items):
    """Whether one and only one if ITEMS is true"""
    ## TEMP: does import here to avoid problem with mezcla package install
    import more_itertools               # pylint: disable=import-outside-toplevel
    ok = more_itertools.exactly_n(items, 1)
    debug.trace(4, f"exactly1({items}) => {ok}")
    return ok 


def string_diff(text1, text2):
    """Return diff-style comparison of TEXT1 and TEXT2 with an empty string used for equality"""
    debug.trace(6, f"string_diff({text1}, {text2})")
    # EX: string_diff("one\ntwo\nthree\nfour", "one\ntoo\ntree\nfour") => "  one\n< two\n…  ^\n> too\n…  ^\n< three\n…  -\n> tree\n  four\n"

    # Perform comparison
    diff_result = "n/a"
    try:
        lines1 = (text1 + "\n").splitlines(keepends=True)
        lines2 = (text2 + "\n").splitlines(keepends=True)
        diff_result = "".join(ndiff(lines1, lines2))
    except:
        system.print_exception_info("string_diff compare")

    # Convert to diff-style output, using:
    # < and > instead of - and +
    # … instead of ?
    try:
        diff_result = re.sub(r"^- ", "< ", diff_result, flags=re.MULTILINE)
        diff_result = re.sub(r"^\+ ", "> ", diff_result, flags=re.MULTILINE)
        diff_result = re.sub(r"^\? ", f"{ELLIPSIS} ", diff_result, flags=re.MULTILINE)
    except:
        system.print_exception_info("string_diff postprocess")

    debug.trace(6, f"string_diff() => {diff_result}")
    return diff_result


def elide_string_values(obj, depth=0, max_len=None):
    """Elide the values of all strings in OBJ, which can either be a scalar, a list or a hash"""
    if max_len is None:
        max_len = 32
    MAX_DEPTH = 10
    if isinstance(obj, list) and (depth < MAX_DEPTH):
        obj = [elide_string_values(v, depth=(1 + depth), max_len=max_len) for v in obj]
    elif isinstance(obj, dict) and (depth < MAX_DEPTH):
        obj = {k: elide_string_values(obj[k], depth=(1 + depth), max_len=max_len) for k in obj.keys()}
    elif isinstance(obj, str):
        obj = gh.elide(obj, max_len=max_len)
    else:
        pass
    return obj


def is_close(value1, value2, epsilon=VALUE_EPSILON):
    """Whether VALUE1 and VALUE2 are close (i.e., absolute difference <= epsilon)"""
    # See https://stackoverflow.com/questions/35324893/using-math-isclose-function-with-values-close-to-0
    ## EX: is_close(1.001, 1.002, epsilon=.005)
    ## EX: (not is_close(1.001, 1.002, epsilon=.0005))
    result = math.isclose(value1, value2, abs_tol=epsilon)
    debug.trace(6, f"is_close({value1}, {value2}, [eps={epsilon}]) => {result}")
    return result


def get_formatted_date(date=None, fmt=None, sep=None, timestamp=None):
    """Return (today's) date in DD MMM YY format (e.g., 10 oct 22)
    Note: uses optional SEP between components or FMT
    Use TIMESTAMP to specify date as integer
    """
    ## EX: get_formatted_date(datetime.datetime.fromtimestamp(0)) => "31 dec 69"
    ## BAD: ## EX: get_formatted_date(datetime.date(0)) => "01 jan 70"
    ## TODO3: rename as get_formatted_date
    in_date = date
    if timestamp is not None:
        debug.assertion(date is None)
        date = datetime.datetime.fromtimestamp(timestamp)
    if date is None:
        date = datetime.date.today()
    if sep is None:
        sep = " "
    if fmt is None:
        fmt = f"%d{sep}%b{sep}%y"
    try:
        result = date.strftime(fmt).lower()
    except:
        system.print_exception_info("get_today_ddmmmyy")
        result = "???"
    debug.trace(6, f"get_formatted_date({in_date}, ts={timestamp}) => {result}")
    return result

def get_date_ddmmmyy(date=None):
    """Return (today's) date in DDMMMYY format (e.g., 10oct22)"""
    ## EX: get_date_ddmmmyy(datetime.datetime.fromtimestamp(0)) => "31dec69"
    ## BAD: ## EX: get_date_ddmmmyy(datetime.date(0)) => "01jan70"
    result = get_formatted_date(date).replace(" ", "")
    debug.trace(6, f"get_date_ddmmmyy({date}) => {result}")
    return result

def parse_timestamp(ts: str, truncate=None, utc=None) -> datetime.datetime:
    """Parse timestamp in ISO 8601 format (e.g., 2023-10-06T04:03:27.1271706Z)
    Note: The timestamp is truncated to micrososeconds unless TRUNCATE is false; and, it is optionally converted to UTC
    """
    # EX: parse_timestamp("2023-10-06T04:03:27.1271706Z") => datetime.datetime(2023, 10, 6, 4, 3, 27, 127170, tzinfo=datetime.timezone.utc)
    # Note: See https://stackoverflow.com/questions/6207365/working-with-high-precision-timestamps-in-python
    # Code based on ChatGPT suggestion

    # Truncate to microsecond precision
    in_ts = ts
    if truncate is None:
        truncate = (len(ts.split(".")[-1]) > 7)
    if truncate:
        ts = ts[:26] + 'Z'

    # Convert result and change to UTC if desired
    result = datetime.datetime.strptime(ts, '%Y-%m-%dT%H:%M:%S.%fZ')
    if utc:
        result = result.replace(tzinfo=datetime.timezone.utc)
    debug.trace(7, f"parse_timestamp({in_ts}, [{truncate}]) =>  {result}")
    
    return result


def add_timestamp_diff(in_filename, out_filename, prefix=False):
    """Add timestamp difference to each occurrence from IN_FILENAME based on previous occurrence, saving to OUT_FILENAME
    If PREFIX, then the difference is added to start of line, otherwise after timestamp
    """
    # TODO3: isolate as separate utility?
    new_lines = []
    last_time = None
    for line in system.read_lines(in_filename):
        # Check for ISO 8601 timestamp (e.g., 2023-10-06T04:02:36.5228822Z)
        new_line = line
        if my_re.search(r"(\d{4}-\d{1,2}-\d{1,2}T\d{2}:\d{2}:\d{2}\.\d{6,}Z)", line):
            timestamp = my_re.group(1)
            try:
                new_time = parse_timestamp(timestamp)
            except:
                new_time = last_time

            # Compute delta in microsseconds
            time_diff = "0"
            microsec = "\u00B5" + "s"        # U+00B5 (µ)
            if last_time:
                time_diff = "+" + str((new_time - last_time).total_seconds() * 1e6) + microsec
            if prefix:
                new_line = time_diff + "\t" + line
            else:
                new_line = line.replace(timestamp, f"{timestamp} [{time_diff}]")
            last_time = new_time
        new_lines.append(new_line)

    # Output revised lines
    system.write_lines(out_filename, new_lines)


def random_int(min_value=None, max_value=None):
    """Returns random integer in range [MIN_VALUE, MAX_VALUE]
    Note: defaults to [0, sys.maxsize]
    """
    if min_value is None:
        min_value = 0
    if max_value is None:
        max_value = sys.maxsize
    result = random.randint(min_value, max_value)
    debug.trace(6, f"random_int() => {result}")
    return result


def random_float(min_value=None, upper_bound=None):
    """Returns random float in range [min_value, upper_bound)
    Note: defaults to [0, 1).
    """
    if min_value is None:
        min_value = 0
    if upper_bound is None:
        upper_bound = 1
    result = (min_value + (random.random() * (upper_bound - min_value)))
    debug.assertion(result < upper_bound)
    debug.trace(6, f"random_float() => {result}")
    return result


def time_function(func, *args, **kwargs):
    """Time invocation of FUNC, optionally supplied with ARGS and KWARGS"""
    ## EX: is_close(time_function(time.sleep, 5), 5000, epsilon=1)
    start = time.time()
    func(*args, **kwargs)
    end = time.time()
    ms = round(1000.0 * (end - start), 3)
    return ms


def get_class_from_name(class_name, module_name=None):
    """Return class with CLASS_NAME
    Optionally specifies MODULE_NAME containing the class, if not __name__
    """
    # EX: "noun_phrases" in dir(get_class_from_name("TextProc", module_name="mezcla.text_processing"))
    # EX: not  get_class_from_name("TextProc")
    # See https://stackoverflow.com/questions/1176136/convert-string-to-python-class-object
    if module_name is None:
        module_name = __name__
    class_object = getattr(sys.modules[module_name], class_name, None)
    debug.trace(6, f"get_class_from_name({class_name}, [{module_name}])) => {class_object}")
    return class_object


def convert_file_to_instances(input_file, module_name, class_name, field_names,
                              fmt=None):
    """Converts input file with array of records into a list of class instances.
    Note: Supports mezcla_to_standard mapping table loading.
    Warning: Future support will just be in terms of reading and evaluation python
    text-based data, which is the "py-data" format used below.
    
    Args:
        input_file: Path to input file (json, yaml, csv)
        module_name: Module containing the class definition
        class_name: Name of the class to instantiate
        field_names: List of field names to use for class constructor
        fmt: Optional format override ('json', 'yaml', 'csv', 'py-data'). If None, inferred from extension.
    
    Returns:
        List of class instances
    """
    # pylint: disable=exec-used,eval-used

    # Detect format if not specified
    if not fmt:
        ext = input_file.lower().split('.')[-1]
        fmt = ext

    # Initialize class from module
    exec(f"from {module_name} import *")          
    actual_class = get_class_from_name(class_name, module_name)

    # Read data based on format
    data = []
    if fmt == 'json':
        data = json.loads(system.read_file(input_file))
    elif fmt == 'yaml':
        data = yaml.safe_load(system.read_file(input_file))
    elif fmt == 'csv':
        debug.trace(4, "Warning: convert_file_to_instances problematic with CSV files")
        # Use CSV DictReader to get list of dicts
        ## OLD: with system.open_file(input_file, newline='') as f:
        with system.open_file(input_file) as f:
            reader = csv.DictReader(f)
            data = list(reader)    
    elif fmt == 'py-data':
        try:
            data = eval(system.read_file(input_file))
        except:
            system.print_exception_info(f"evaluation of {input_file!r}")
    else:
        raise ValueError(f"Unsupported format: {fmt}")

    # Convert records to instances
    instances = []
    for record in data:
        if fmt == 'py-data':
            ## TODO4: rework to put special case outside of loop
            debug.assertion(isinstance(record, actual_class))
            instances.append(record)
            continue
        class_args = []
        for field in field_names:
            # Handle both dict and object-like records
            value = record.get(field, "None")
            # Only eval non-string values from JSON/YAML
            ## TODO3: clarify intention
            ## TEST: if (fmt == 'csv') and isinstance(value, str):
            if fmt in ('json', 'yaml') and isinstance(value, str):
                try:
                    value = eval(value)
                except:
                    system.print_exception_info(f"evaluation of {field} value {value!r}")
            elif (fmt == 'py-data'):
                pass
            else:
                debug.trace(5, f"FYI: Not evaluating {field} value {value!r}")
            class_args.append(value)
        new_inst = actual_class(*class_args)
        instances.append(new_inst)

    return instances    

def convert_json_to_instance(json_file, module_name, class_name, field_names):
    """Converts JSON_FILE with array of dicts into a list of instances for CLASS_NAME, where each of FIELD_NAMES is used in the class invocation. The MODULE_NAME is used to import the class definition.
    """
    return convert_file_to_instances(json_file, module_name, class_name, field_names, fmt='json')

def convert_yaml_to_instance(yaml_file, module_name, class_name, field_names):
    """Converts YAML_FILE with array of dicts into a list of instances for CLASS_NAME, where each of FIELD_NAMES is used in the class invocation. The MODULE_NAME is used to import the class definition.
    """
    return convert_file_to_instances(yaml_file, module_name, class_name, field_names, fmt='yaml')

def convert_csv_to_instance(csv_file, module_name, class_name, field_names):
    """Converts CSV_FILE with array of dicts into a list of instances for CLASS_NAME, where each of FIELD_NAMES is used in the class invocation. The MODULE_NAME is used to import the class definition.
    """
    return convert_file_to_instances(csv_file, module_name, class_name, field_names, fmt='csv')


def convert_python_data_to_instance(python_data_file, module_name, class_name, field_names):
    """Converts PYTHON_DATA_FILE into list of instances
    Note: see convert_json_to_instance for details of other arguments"""
    return convert_file_to_instances(python_data_file, module_name, class_name, field_names, fmt='py-data')


def apply_numeric_suffixes(text: str, just_once=False) -> str:
    """Converts numbers in TEXT to use K, M, G, T, etc. suffixes.
    Note: Optionally applies JUST_ONCE per line."""
    # Note: used in shell-scripts tomohara-aliases.bash
    # EX: apply_numeric_suffixes("1024 1572864 1073741824") => "1K 1.5M 1G"
    # TODO2: preserve spacing in text (e.g., splitlines quirks)
    debug.trace(5, f"apply_numeric_suffixes({text!r}, [once={just_once})")
    suffixes = "_KMGTPE"                # _ is placeholder for no suffix
    new_text = ""
    for l, line in enumerate(text.splitlines()):
        max_count = len(line) / 3
        count = 0
        # note: uses negative look ahead to avoid conversion in decimals (e.g., 1023.5);
        # also, uses non-greedy search to support just_once (i.e., target first case even if smaller)
        # TODO3: exclude leading question marks (e.g., ?00000000?)
        while (my_re.search(r"^(.*?)\b(\d{4,19})\b(?!\.)(.*)", line)):
            count += 1
            if count > max_count:
                debug.trace(6, f"max attempt count reached ({max_count})")
                break
            (pre, numeric, post) = my_re.groups()
            (new_num, suffix) = ("", "")
            num = float(numeric)
            if num > 0:
                try:
                    power = int(math.log(num) / math.log(1024))
                    new_num = system.round_as_str(num / (1024 ** power))
                    # note: accounts for quirk in rounding (e.g., stripping N.000)
                    # TODO2: ignore special cases like 0000 (n.b., due to \d{4,N} regex)
                    new_num = my_re.sub(r"\.0+$", "", new_num)
                    # note: drops 0's added to due rounding (e.g., 1.500 => 1.5)
                    new_num = my_re.sub(r"(\.[1-9]+)0+$", r"\1", new_num)
                    suffix = suffixes[power]
                    debug.trace_expr(6, numeric, num, power, line)
                except:
                    # note: restore number and add surrounding ?'s to block regex
                    new_num = f"_{numeric}?_"
                    debug.trace_exception(5, f"apply_numeric_suffixes line {l} ({line!r})")
            else:
                ## TODO3: rework pattern matching to exclude 0000, etc.
                new_num = "0K"
            line = pre + str(new_num) + suffix + post
            if just_once:
                debug.trace(6, f"applied just once ({just_once=})")
                break
        new_text += line + os.linesep
    if new_text.endswith(os.linesep) and not text.endswith(os.linesep):
        new_text = my_re.sub(fr"{os.linesep}$", "", new_text)
    debug.trace(5, f"apply_numeric_suffixes() => {new_text!r}")
    return new_text


def apply_numeric_suffixes_stdin(just_once=False):
    """Invokes apply_numeric_suffixes over stdin
    Note: supports Bash alias (see shell-scripts/tomohara-aliases.bash)
    """
    text = dummy_app.read_entire_input()
    # Note: doesn't add newline as normally stdin ends with one, and users
    # might want stdin preserved if not (e.g., for use with `echo -n`).
    print(apply_numeric_suffixes(text, just_once=just_once), end="")

#-------------------------------------------------------------------------------
# Utility class for setting contexts
# NOTE: Based on Grok3
# TODO3: put in new module like python_utils.py

class GlobalSetter(ContextDecorator):
    """A context manager and decorator to temporarily set a module-level global variable.

    This class allows you to temporarily modify a module-level global variable within
    a `with` block or as a decorator, restoring the original value (or removing the
    attribute if it didn't exist) upon exit.

    Args:
        module (ModuleType): The module containing the global variable (e.g., `debug`).
        name (str): The name of the global variable (e.g., 'trace_level').
        value (Any): The temporary value to set for the global variable.

    Example:
        >>> import debug
        >>> def trace_values():
        ...     print(debug.trace_level)
        >>> debug.trace_level = 3
        >>> trace_values()  # Prints: 3
        >>> with GlobalSetter(debug, 'trace_level', 6):
        ...     trace_values()  # Prints: 6
        >>> trace_values()  # Prints: 3

    Note:
        - This context manager is not thread-safe. Use synchronization mechanisms
          (e.g., locks) if modifying globals in a multithreaded environment.
        - If the module is reloaded during the context, the global variable may be reset.
    """

    def __init__(self, module: ModuleType, name: str, value: Any) -> None:
        """Initialize the GlobalSetter with the module, attribute name, and temporary value.

        Args:
            module (ModuleType): The module containing the global variable.
            name (str): The name of the global variable to modify.
            value (Any): The temporary value to set for the global variable.
        """
        self.module: ModuleType = module
        self.name: str = name
        self.value: Any = value
        self.original_value: Optional[Any] = None

    def __enter__(self) -> 'GlobalSetter':
        """Enter the context, saving the original value and setting the new value.

        Returns:
            GlobalSetter: The context manager instance (for use in `with` blocks).

        Saves the original value of the module attribute (or None if it doesn't exist)
        and sets the attribute to the specified temporary value.
        """
        self.original_value = getattr(self.module, self.name, None)
        setattr(self.module, self.name, self.value)
        return self

    def __exit__(self, exc_type: Optional[type], exc_val: Optional[Exception], 
                 exc_tb: Optional[Any]) -> None:
        """Exit the context, restoring the original value or removing the attribute.

        Args:
            exc_type (Optional[type]): The type of the exception raised, if any.
            exc_val (Optional[Exception]): The exception instance raised, if any.
            exc_tb (Optional[Any]): The traceback of the exception, if any.

        Restores the original value of the module attribute if it existed, or removes
        the attribute if it was newly created during the context.
        """
        if self.original_value is None:
            delattr(self.module, self.name)
        else:
            setattr(self.module, self.name, self.original_value)

#-------------------------------------------------------------------------------

def init():
    """MOdule initialization"""
    if RANDOM_SEED:
        random.seed(RANDOM_SEED)


init()

#-------------------------------------------------------------------------------

def main(args):
    """Supporting code for command-line processing"""
    debug.trace_fmtd(6, "main({a})", a=args)
    system.print_stderr("Warning: not intended for direct invocation")
    return

if __name__ == '__main__':
    main(sys.argv)
