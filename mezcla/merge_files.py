#! /usr/bin/env python
# 
# Merges two versions of the same file, using an earlier version as a baseline
# (i.e., 3-way merge). If the baseline version is not supplied it is determined
# as the most recent backup older than both versions.
#
# Notes:
# - The merge process can easily get confused is there are parallel changes to
#   the same sections.
# - Use a visual merge script to help with manual reconciliation (e.g., via kdiff3).
#
# TODO:
# - Make stdout the default.
# - Integrate merge heuristics for common issues.
#   -- For example, accounting for changes flagged with comments:
#      ## OLD: from regex import my_re
#      from my_regex import my_re
#   -- Accounting for changes elsewhere.
#

"""Perform 3-way merge with baseline from backup dir"""

# Standard packages
import re

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main
from mezcla import system

# Constants for switches omitting leading dashes (e.g., DEBUG_MODE = "debug-mode")
BASENAME = "basename"
BACKUP_DIR = "backup-dir"
BACKUP_FILENAME = "backup-filename"
FILENAME1 = "filename1"
FILENAME2 = "filename2"
QUIET = "quiet"
USE_STDOUT = "stdout"
SKIP_BASELINE = "skip-baseline"
UPDATE_FILE1 = "update-file1"
IGNORE_ERRORS = "ignore-errors"
MERGE = system.getenv_text("MERGE", "/usr/bin/merge -p",
                           description="Command line for merge with output piping arg (e.g., -p)")

#...............................................................................

def get_timestamp(filename):
    """Returns timestamp for FILENAME as string value"""
    # EX: get_timestamp("/vmlinuz") => "2021-04-15 04:24:54"
    result = system.get_file_modification_time(filename, as_float=False)
    debug.assertion(isinstance(result, str))
    return result


def get_numeric_timestamp(filename):
    """Returns timestamp for FILENAME as floating point value"""
    # EX: get_numeric_timestamp("/vmlinuz") => 1618478694.0
    result = system.get_file_modification_time(filename, as_float=True)
    debug.assertion(isinstance(result, float))
    return result

#...............................................................................

class Script(Main):
    """Adhoc script processing class"""
    filename1 = ""
    filename2 = ""
    backup_filename = ""
    backup_dir = "./backup"
    basename = ""
    update_file1 = False
    skip_baseline = False
    quiet = False
    use_stdout = False
    ignore_errors = False

    def setup(self):
        """Check results of command line processing"""
        debug.trace_fmtd(5, "Script.setup(): self={s}", s=self)
        self.filename1 = self.get_parsed_argument(FILENAME1)
        self.filename2 = self.get_parsed_argument(FILENAME2)
        self.backup_filename = self.get_parsed_option(BACKUP_FILENAME)
        self.backup_dir = self.get_parsed_option(BACKUP_DIR, self.backup_dir)
        self.basename = self.get_parsed_option(BASENAME, self.filename1)
        self.update_file1 = self.get_parsed_option(UPDATE_FILE1, self.update_file1)
        self.skip_baseline = self.get_parsed_option(SKIP_BASELINE, self.skip_baseline)
        self.quiet = self.get_parsed_option(QUIET)
        self.use_stdout = self.get_parsed_option(USE_STDOUT)
        self.ignore_errors = self.get_parsed_option(IGNORE_ERRORS)
        ## self.x = self.get_parsed_option(X)
        debug.trace_object(5, self, label="Script instance")

    def check_regular_file(self, filename):
        """Make sure regular file exists; otherwise, issue error and exit"""
        ok = (system.file_exists(filename) and system.is_regular_file(filename))
        if not ok and not self.ignore_errors:
            system.exit(f"Error: expecting regular file for '{filename}'")
        return ok
        
    def run_main_step(self):
        """Main processing step"""
        debug.trace_fmtd(5, "Script.run_main_step(): self={s}", s=self)

        # Validate input files
        self.check_regular_file(self.filename1)
        # TODO: if .../is_dir(self.filename2): self.filename2 = .../form_path(filename2, basename(filename2))
        self.check_regular_file(self.filename2)

        # Find the backup baseline if not specified
        if not self.backup_filename:
            EPSILON = 1e-6
            timestamp1 = get_numeric_timestamp(self.filename1)
            timestamp2 = get_numeric_timestamp(self.filename2)
            min_timestamp = min(timestamp1, timestamp2) - EPSILON

            # Find most recent backup older than two files
            SEP = "\t"
            backup_files = gh.get_files_matching_specs("{d}/{b}{SEP}{d}/{b}.*~*".
                                                       format(d=self.backup_dir, b=self.basename, SEP=SEP)
                                                       .split(SEP))
            timestamped_backups = [(f, ts) for (f, ts) in sorted(zip(backup_files,
                                                                     map(get_numeric_timestamp, backup_files)),
                                                                 key=lambda f_ts: f_ts[1], reverse=True)
                                   if (ts <= min_timestamp)]
            if timestamped_backups:
                self.backup_filename = timestamped_backups[0][0]

            # If no suitable backup, use the older of the two files
            if ((not self.backup_filename) and self.skip_baseline):
                self.backup_filename = self.filename1 if (timestamp1 < timestamp2) else self.filename2
        if not self.backup_filename:
            system.exit("Error: Unable to find baseline backup for {f1} ({ts1}) and {f2} ({ts2}) ",
                        f1=self.filename1, ts1=get_timestamp(self.filename1),
                        f2=self.filename2, ts2=get_timestamp(self.filename2))
        self.check_regular_file(self.backup_filename)

        # Do the merge and check for conflicts
        # TODO: produce report including diff listings of old vs. new
        system.create_directory(self.temp_base)
        temp_new_file = gh.form_path(self.temp_base, self.basename)
        result = gh.run("{m} {f1} {b} {f2} > {new}", m=MERGE, f1=self.filename1,
                        b=self.backup_filename, f2=self.filename2, new=temp_new_file)
        if re.search(r"conflict in merge", result):
            system.print_stderr("Error in merge:\n\t{r}", r=gh.indent_lines(result))
        elif self.update_file1:
            if not self.quiet:
                print("Updating {f1}", f1=self.filename1)
            gh.rename_file(self.filename1, (self.filename1 + ".backup"))
            gh.copy_file(temp_new_file, self.filename1)
        elif self.use_stdout:
            print(system.read_entire_file(temp_new_file))
        else:
            if not self.quiet:
                print("Merge result:\n\t{r}".format(r=result))
                debug.trace(4, f"See {temp_new_file}")
        return

#-------------------------------------------------------------------------------
    
if __name__ == '__main__':
    debug.trace_current_context(level=debug.QUITE_DETAILED)
    # TODO: add examples (especially with consolidated backup directory)
    app = Script(
        description=__doc__,
        skip_input=True,
        manual_input=True,
        boolean_options=[(IGNORE_ERRORS, "Ignore errors in processing"),
                         (UPDATE_FILE1, "Replace file1 with merged result"),
                         (USE_STDOUT, "Use standard output for result"),
                         ## TODO: (X, "..."),
                         (QUIET, "Omit status messages")],
        positional_arguments=[FILENAME1, FILENAME2],
        text_options=[(BACKUP_FILENAME, "Backup file for baseline"),
                      (BACKUP_DIR, "Backup directory"),
                      (BASENAME, "Basename for backup check (if not filename1)")])
    app.run()
