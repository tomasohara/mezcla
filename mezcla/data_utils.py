#! /usr/bin/env python
#
# Utility functions for doing data analysis, such as wrappers for functions
# provided by pandas and sklearn.
#
# Note:
# - This started out as way to provide commonly used options for CSV reading
#   with Pandas, along with tracing.
# - It is a little idiosyncratic with a bias towards Unix assumptions
#   (e.g., comments more likely in CSV files).
#
# TODO:
# - Add simple wrapper class for commonly used idioms, sich as len(df.columns) for number of columns.
#

"""Utility functions for work with data (e.g., pandas wrappers)"""

# Standard module
import pandas as pd

# Local modules
## OLD:
## import system
## import debug
from mezcla import debug
from mezcla import system

# Constants
# Note: Delim defaults to None so that dialect inference can be used.
# This is a quirk with Pandas compared to the cvs module.
## OLD: DELIM = system.getenv_text("DELIM", ",",
DELIM = system.getenv_value("DELIM", None,
                            "Delimiter for input and output tables")
COMMENT = 'comment'
DIALECT = 'dialect'
EXCEL = 'excel'

#-------------------------------------------------------------------------------

def read_csv(filename, **in_kw):
    """Wrapper around pandas read_csv"""
    ## TODO: clarify dtype usage
    ## BAD
    ## kw = {'comment': "#", 'delimiter': DELIM, 'dtype': str,
    ##       'error_bad_lines': False, 'escapechar': '\\', 'keep_default_na': False}
    ## OLD:
    ## kw = {'comment': "#", 'delimiter': DELIM, 'dtype': str,
    ##       'error_bad_lines': False, 'keep_default_na': False}
    kw = {'delimiter': DELIM, 'dtype': str,
          'error_bad_lines': False, 'keep_default_na': False}
    kw.update(**in_kw)
    # Add special processing (n.b., a bit idiosyncratic)
    if ((COMMENT not in kw) and (kw.get(DIALECT) != EXCEL)):
        debug.trace_fmt(4, "Enabling comments in read_csv")
        kw[COMMENT] = "#"
    ## OLD:
    ## debug.trace_fmt(5, "read_csv({f}, cmt={comment}, del={delimiter}, dty={dtype},"
    ##                 "ebl={error_bad_lines}, kdn={keep_default_na}, in_kw={ikw})", f=filename, **kw, ikw=in_kw)
    debug.trace_fmt(5, "read_csv({f}, [in_kw={ikw}])", f=filename, ikw=in_kw)
    debug.trace_fmt(6, "\tkw={k}", k=kw)
    df = pd.read_csv(filename, **kw)
    debug.trace(4, f"read_csv({filename}) => {df}")
    return df


def to_csv(filename, data_frame):
    """Output to FILENAME the CSV for DATA_FRAME without index column"""
    result = None
    try:
        result = data_frame.to_csv(filename, index=False)
    except:
        debug.trace(4, f"Exception during write_csv: {system.get_exception()}")
    debug.trace(4, f"to_csv({filename}, {data_frame}) => {result}")
    return result
#
write_csv = to_csv

def lookup_df_value(data_frame, return_field, lookup_field, lookup_value):
    """Return value for DATA_FRAME's RETURN_FIELD given LOOKUP_FIELD value LOOKUP_VALUE"""
    ## TODO: rework in terms of Pandas primitives
    value = None
    try:
        # TODO: trace out index location
        matches = [row[return_field] for index, row in data_frame.iterrows() 
                   if (row[lookup_field] == lookup_value)]
        if matches:
            value = matches[0]
    except:
        debug.trace(4, f"Exception during lookup_df_value: {system.get_exception()}")
    debug.trace(7, f"lookup_df_value(_, {return_field}, {lookup_field}, {lookup_value}) => {value}")
    return value


def main():
    """Entry point for script"""
    ## OLD: debug.trace(2, "Warning: Not intended to being invoked directly")
    system.print_stderr("Error: Not intended to being invoked directly")
    return

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
