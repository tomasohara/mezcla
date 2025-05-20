#! /usr/bin/env python3
#
# Sanity check for time-tracking report.
#
# Sample input:
#
# Week of Mon 14 Oct 14
# 
# Mon:
# ;; day off
# hours: 0
# 
# Tues:
# 2	3	appserver overview; diagnosing hg update issues on systen repository
# 5	6	re-cloning and reviewing system repository source structure
# 7	8	adding new repository branch; checking old system repository differences (e.g., TODO notes in code)
# 9:30	11:30	exporting related-title code from search prototype into appserver; adding prequisites for running appserver locally (for syntax checking)
# 12	2	trying to get @route-based dispatching for relatedJobs method
# hours: 7
#
# Wed:
# 10    7       [ACME] in-house training for new client
#
#--------------------------------------------------------------------------------
# Notes:
# - The am/pm indicator can be omitted unless ambiguous.
# - The description can start with a tag (e.g., ACME) above for tabulating hours.
#
#-------------------------------------------------------------------------------
# TODO:
# - ** Add edit distance check for 'break' mispellings (e.g., breal) to avoid recording excess time!!
# - Allow _ placeholders in week and total summary if month not complete.
# - Clean up debug_format calls.
# - Make hours line optional (e.g., assume blank line separates days).
# - Make weekly hours optional (e.g., assume repeated day separates week).
# - Have option to output template for current month!
#
#

"""Validates the hour tabulations in a time tracking report"""

# Standard packages
import argparse
from collections import defaultdict
import os
import re
## OLD: import sys

# Local packages
from mezcla import debug
## OLD: import tpo_common as tpo
## OLD: from mezcla import sys_version_info_hack       # pylint: disable=unused-import
from mezcla import system
from mezcla.my_regex import my_re
from mezcla import text_utils

# Note: python 3.6+ format strings are used (n.b., assumes sys_version_info_hack above)
# TODO: See if why to have pylist issue warning about version; that way, there's less
# head scratching about syntax error messages (e.g., for python-3.6+ f-string interpolation).
## TEST:
## assert((sys.version_info.major >= 3) and (sys.version_info.minor >= 6))
## assert(system.python_maj_min_version > 3.6, "Python 3.6+ needed for f-strings")
## if (system.python_maj_min_version > 3.6, "Python 3.6+ needed for f-strings"):
##    assert False, "Python 3.6+ needed for f-strings"
##
## TODO:
## try:
##     debug.trace(4, f"Test of f-strings: major/minor version={system.python_maj_min_version()}")
## except SyntaxError:
##     print("Python 3.6+ needed for f-strings")
## NOTE: effing Python: there should be a from-future style import!
##

WEEKDAYS = ["sunday", "monday", "tuesday", "wednesday", "thursday", "friday", "saturday"]
ABBREVIATED_WEEKDAYS = ["sun", "mon", "tue", "wed", "thu", "fri", "sat"]
## TODO: ALT_ABBREVIATED_WEEKDAYS = ["sun", "mon", "tues", "wed", "thurs", "fri", "sat"]
ALL_WEEKDAYS = WEEKDAYS + ABBREVIATED_WEEKDAYS
REPORT_TAGS = "daily weekly total".split()

#...............................................................................

def show_tagged_hours(tagged_hours_hash, prefix=None):
    """Print report of hours assigned to each task in TAGGED_HOURS_HASH"""
    debug.trace(5, "show_tagged_hours({tagged_hours_hash}, [{prefix}])")
    space = None
    if prefix is None:
        prefix = ""
        space = ""
    else:
        space = " "
    report = ""
    for tag in sorted(tagged_hours_hash):
        if tagged_hours_hash[tag]:
            report += ("\t".join([tag, str(tagged_hours_hash[tag])]) + "\n")
    if report:
        print("{pre}{sp}Hours by tag".format(pre=prefix, sp=space).capitalize())
        print(report.strip("\n"))
    return


def main():
    """Entry point for script"""
    ## OLD: debug.trace(4, f"main(): argv={sys.argv}")
    debug.trace(4, f"main(): argv={system.get_args()}")

    # Check command-line arguments
    # TODO: Switch over to argument processing via Main class in main.py.
    # TODO: Add example illustrating DEBUG_LEVEL and to show check-time-tracking alias;
    # also, add option to output blank template for the month.
    parser = argparse.ArgumentParser(description="Validates time tracking reports")
    parser.add_argument("--strict", default=False, action='store_true', help="strict parsing of the time tracking report")
    parser.add_argument("--ignore-comments", default=False, action='store_true', help="ignore comments in the time tracking report")
    parser.add_argument("--verbose", default=True, action='store_true', help="verbose output mode (e.g., summary of weekly hours)")
    parser.add_argument("--quiet", dest='verbose', action='store_false', help="non-verbose mode")
    ## OLD: parser.add_argument("--weekly", dest='weekly', default=False, action='store_true', help="show weekly summary of hours")
    parser.add_argument("--weekly", default=False, action='store_true', help="show weekly summary of hours")
    parser.add_argument("--report", default=False, action='store_true', help="Output time sheet report including computed hours")
    ## OLD: parser.add_argument("--heuristics", default=False, dest='heuristics', action='store_true', help="use heuristics such as ignoring time slots labelled as 'break' (n.b., can be confusing without --quiet or debugging enabled)")
    ## OLD: parser.add_argument("--heuristics", default=False, action='store_true', help="use heuristics such as ignoring time slots labelled as 'break' (n.b., can be confusing without --quiet or debugging enabled)")
    parser.add_argument("--heuristics", default=True, action='store_true', help="use heuristics such as ignoring time slots labelled as 'break' (n.b., can be confusing without --quiet or debugging enabled)")
    parser.add_argument("--skip-heuristics", dest='heuristics', action='store_false', help="don't use heuristics for time slot interpretation")
    parser.add_argument("--skip-hours-check", default=False, action='store_true', help="Omits warning discrepancies in hour specified vs. tabulated")
    parser.add_argument("--extra-normalization", default=False, action='store_true', help="Extra normalization (e.g., stripping am/pm")
    # TODO: --tags => --tabulate-tags
    parser.add_argument("--tags", default=False, action='store_true', help="Tabulate hours according to tags (e.g., [ACME] review)")
    parser.add_argument("--tag-filter", default="", help="Filter out specified tags")
    parser.add_argument("--tag-report", default="daily,weekly,total", help="Show tag report types: {{{rt}}}".format(rt=", ".join(REPORT_TAGS)))
    parser.add_argument("--omit-time", default=False, action='store_true', help="Omit timespec from report")
    parser.add_argument("--omit-tags", default=False, action='store_true', help="Omit tag from report (n.b., requires --omit-time")
    ## TODO: parser.add_argument("--xyz", default=False, action='store_true', help="TODO: does xyz, ...")
    ## -or- parser.add_argument("--not-xyz", dest='xyz', action='store_false', help="TODO: does not xyz, ...")
    parser.add_argument("filename", help="input filename")
    args = vars(parser.parse_args())
    debug.trace(5, f"args = {args}")
    filename = args['filename']
    debug.assertion(os.path.exists(filename))
    strict = args['strict']
    ignore_comments = args['ignore_comments'] or (not strict)
    use_heuristics = args['heuristics']
    verbose = args['verbose']
    ## TODO: verbose = args['verbose'] or use_heuristics
    show_weekly = args['weekly']
    skip_hours_check = args['skip_hours_check']
    extra_normalization = args['extra_normalization']
    tabulate_tags = args['tags']
    filter_tags = args['tag_filter']
    report_tags = args['tag_report'].lower()
    debug.assertion(not system.difference(re.split("[, ]+", report_tags),
                                          REPORT_TAGS))
    output_report = args['report']
    filter_regex = None
    omit_timespec = args["omit_time"]
    omit_tags = args["omit_tags"]
    debug.assertion(not (omit_tags and not omit_timespec))

    # Format optional regex for tag filtering
    if filter_tags:
        tag_list = text_utils.extract_string_list(filter_tags)
        if not tag_list:
            system.print_stderr(f"Error extracting tags from '{filter_tags}'")
        else:
            # ex: "\[TPO|OTHER\]
            tag_spec="|".join(tag_list)
            filter_regex = r"\[{spec}\]".format(spec=tag_spec)
            debug.trace(2, f"Filter regex: {filter_regex}")

    # Print header for weekly summary and initialize associated record keeping
    if show_weekly or verbose:
        print("\t".join(ABBREVIATED_WEEKDAYS))
    weekday_hours = defaultdict(str)
    day_of_week = ""
    
    # Scan time listing keeping track of hours running totals
    daily_tagged_hours = defaultdict(int)
    weekly_tagged_hours = defaultdict(int)
    total_tagged_hours = defaultdict(int)
    hours = 0
    last_hours = 0
    weekly_hours = 0
    last_weekly_hours = 0
    total_hours = 0
    line_num = 0
    num_weeks = 0
    for original_line in system.open_file(filename):
        original_line = original_line.strip("\n")
        filtered_original_line = original_line
        line = original_line.lower()
        line_num += 1
        debug.trace(6, f"L{line_num}:\n\t{line}")

        # HACK: Standardize the weekday
        line_save = line
        line = re.sub(r"^(sun|mon|tues|wednes|thurs|fri|satur)day:", r"\1:", line)
        line = re.sub(r"^(tues):", r"tue:", line)
        line = re.sub(r"^(wednes):", r"wed:", line)
        line = re.sub(r"^(thurs):", r"thu:", line)
        line = re.sub(r"^(satur):", r"sat:", line)
        if ((line != line_save) or verbose):
            debug.trace_fmt(6, "After day-of-week normalization for L{n}:\n\t{l}", n=line_num, l=line)

        # Normalize line to facilitate extraction:
        # - treat whitespace delimiters as tabs after start and end time
        # - remove surrounding whitespace, make lowercase
        # - convert tabs to spaces
        # TODO: convert "T1-T2<tab>..." to "T1<tab>T2<tab>..."
        line = line.strip()
        line_save = line
        line = re.sub("\t", " ", line)
        if (re.search(r"^(\d+\S*)\s+(\d+\S*)\s+", line)):
            line = re.sub(r"^(\S+)\s+(\S+)\s+", r"\1\t\2\t", line)
            debug.assertion(not line.endswith("\t"))
            debug.assertion(not re.search(r"\t.*\t.*\t", line))
        if ((line != line_save) or verbose):
            debug.trace_fmt(6, "After normalized time spec. for L{n}:\n\t{l}", n=line_num, l=line)

        # Normalize time specification:
        # - remove am/pm suffixes in time specification
        #   -- done when prior to tab (\t), dash (-) or ": " (colon-space sequence)
        ## OLD: line = re.sub(r"(am|pm)\t", r"\t", line)
        if extra_normalization:
            line_save = line
            line = re.sub(r"([0-9])(am|pm)((-)|(:?\t)|(: ))", r"\1\3", line)
            if ((line != line_save) or verbose):
                debug.trace_fmt(6, "After extra normalization for L{n}:\n\t{l}", n=line_num, l=line)

        # Ignore comment lines (starting either w/ '#' or ';' ignoring leading space)
        if (ignore_comments and re.search(r"^\s*[#;]", line)):
            debug.trace(6, f"Ignoring comment in L{line_num}: {line}")
            continue

        # Replace ": " w/ "<TAB>" prior to task description
        # ex: "4-5: cleaning code" => "4-5<TAB>cleaning code"
        # Note: requires am/pm stripping
        # TODO: fix processing over bad-time-tracking-may21.list
        line_save = line
        line = re.sub(r"^([-:\t 0-9]+[0-9]): ", r"\1\t", line)
        if ((line != line_save) or verbose):
            debug.trace_fmt(6, "After misc. normalized for L{n}:\n\t{l}", n=line_num, l=line)
        
        # Strip trailing comments
        # ex: "Fri:	    ;; 28" => "Fri:"
        # Note: double-comment now required, unless two or more preceding spaces
        if ignore_comments:
            line_save = line
            ## OLD: line = re.sub(r"\s*[#;]).*", "", line)
            ## OLD: line = re.sub(r"\s\s\s([#;]).*", "", line)
            line = re.sub(r"\s\s([#;]).*", "", line)
            line = re.sub(r"([#;])\1.*", "", line)
            if ((line != line_save) or verbose):
                debug.trace(6, f"After trailing comment removal L{line_num}:\n\t{line}")
            if re.search(r"\s[#;]", line):
                debug.trace(4, f"Warning: potential comment at line {line_num}: {line}")
                debug.trace(4, "Precede by 2+ spaces or double the comment char")

        # Trace end version of line
        if verbose:
            debug.trace(6, f"Final normalized L{line_num}:\n\t{line}")

        # Flag ???'s as items to flesh out
        if (verbose and line.find("???") != -1):
            print("TODO: flesh out line %d: %s" % (line_num, line))

        # Apply heuristics for entries to ignore, etc. (e.g., ignore time-slots listed as break's).
        ## OLD: if use_heuristics and re.search(r"\tbreak\s*$", line):
        if use_heuristics and re.search(r"\t\s*break\s*$", line):
            message = "Ignoring break at line {n}: {t}".format(n=line_num, t=line)
            if verbose:
                print(message)
            debug.trace(5, f"Warning: {message}")
            continue
            
        # TEMP HACK: first Check for daily hours (redundant with old code below)
        # TODO: See why not handled properly in time-tracking-mmmYY.template
        # ex: "hours: 8.5"
        if (my_re.search(r"^hours:\s*(\S*)", line)):
            ## OLD: debug.trace(5, "redundant hours check")
            debug.trace_fmt(5, "redundant hours check: day_of_week={dw}", dw=day_of_week)
            specified_hours = system.safe_float(my_re.group(1), 0.0) if my_re.group(1) else 0.0
            ## OLD: if (specified_hours != hours):
            if ((specified_hours != hours) and (not skip_hours_check)):
                system.print_stderr("Error: Discrepancy in hours at line {n}: change {spec} => {calc}?".format(n=line_num, spec=specified_hours, calc=hours))
            else:
                # HACK: pretend user specified tabulated hours (TODO: use 'hours' in weekly_hours update below for clarity)
                ## OLD: specified_hours = hours
                pass
            ## OLD: weekly_hours += specified_hours
            weekly_hours += hours
            debug.assertion((weekday_hours[day_of_week] == ""), f"Missing weekly-hours lines (near line {line_num})?")
            ## OLD: weekday_hours[day_of_week] = specified_hours
            ## OLD2: weekday_hours[day_of_week] = hours
            weekday_hours[day_of_week] += ("" if not weekday_hours[day_of_week] else "-or-")
            weekday_hours[day_of_week] += str(hours)
            last_hours = hours
            hours = 0
            debug.trace_fmt(7, "spec_hours={sh} daily_hours={h} weekly_hours={wh} total_hours={th}, weekday_hours={wdh}", 
                            sh=specified_hours, h=hours, wh=weekly_hours, th=total_hours, wdh=weekday_hours)

            # Show tagged breakdown
            if tabulate_tags:
                if "daily" in report_tags:
                    show_tagged_hours(daily_tagged_hours, "Daily")
                for tag in daily_tagged_hours:
                    weekly_tagged_hours[tag] += daily_tagged_hours[tag]
                    daily_tagged_hours[tag] = 0

        # Check for day of week
        # NOTE: 'day' now stripped above.
        # TODO: make sure 'day' not included in first regex group
        ## if (my_re.search(r"^(\S+)(day)?:\s*$", line)):
        ## OLD: if (my_re.search(r"^(\S+)(day)?:\s*$", line)):
        elif (my_re.search(r"^(\S+)(day)?:\s*$", line)):
            day_of_week = my_re.group(1)
            debug.assertion(len(day_of_week) == 3, f"Bad day of week at line {line_num}")
            debug.trace(6, f"day of week check: day={day_of_week}")
            ## TODO: handle Saturday and Wednesday
            ## TODO: day_of_week = re.sub(r"(ur|nes)?day$", "", my_re.group(1))
            if (day_of_week in ALL_WEEKDAYS):
                if (hours > 0):
                    system.print_stderr("Error: missing 'hours:' line at line {n}".format(n=line_num))
            else:
                system.print_stderr("Error: Invalid day '{d}' at line {n}", d=day_of_week, n=line_num)

        # Check for hours specification
        # ex: "2:30pm	4:30	debugging check_time_tracking.py"
        # ex: "7-9	trying to get SpaCy NER via Anaconda under edgenode and win10
        # Notes:
        # - The am or pm suffix is optional.
        # - If start time is greater than end time, the latter is assumed to be afternoon.
        # - The start and end time can optionally be separate by a dash (e.g, 8-10pm), without intervening spaces (e.g., not 8 - 10pm)
        #
        # TODO: (my_re.search(r"^(\d+)\:?(\d*)(am|pm)?\s+(\d+)\:?(\d*)\s+\S.*", line))
        ## OLD:
        ## elif (my_re.search(r"^(\d+)\:?(\d*)\s+(\d+)\:?(\d*)\s+\S.*", line) or
        ##      my_re.search(r"^(\d+)\:?(\d*)\-(\d+)\:?(\d*)\s+\S.*", line)):
        elif (my_re.search(r"^(\d+)\:?(\d*)\s+(\d+)\:?(\d*)\s+(\S.*)", line) or
              my_re.search(r"^(\d+)\:?(\d*)\-(\d+)\:?(\d*)\s+(\S.*)", line)):
            debug.trace(6, "time check")
            # TODO: (start_hours, start_mins, start_ampm, end_hours, end_mins, start_ampm) = my_re.groups()
            ## OLD: (start_hours, start_mins, end_hours, end_mins) = my_re.groups()
            (start_hours, start_mins, end_hours, end_mins, desc) = my_re.groups()
            debug.trace(6, f"sh={start_hours} sm={start_mins} eh={end_hours} em={end_mins} desc={desc}")
            start_time = float(start_hours) + float(start_mins or 0)/60.0
            end_time = float(end_hours) + float(end_mins or 0)/60.0
            if (end_time < start_time):
                end_time += 12
            new_hours = (end_time - start_time)
            if (not (0 < new_hours <= 24)):
                system.print_stderr("Error: Invalid hour specification at line {n}: calculated as more than a day ({new})!".format(n=line_num, new=new_hours))
            ## OLD:
            ## hours += new_hours
            ## debug.trace(6, f"{new_hours} new hours; hours={hours}")

            # Checked for tagged tasks and record hours separately
            # EX: "[XYZ] proposal revision"
            tag = "n/a"
            if my_re.search(r"\[([a-z0-9_/-]+)\]", desc):
                tag = my_re.group(1)
                debug.trace_fmt(5, "found tag {t} at line {n}", t=tag, n=line_num)
            elif my_re.search(r"\[(\S+)\]", desc):
                debug.trace(4, f"Warning: unrecognizable tag '{my_re.group(1)}' at line {line_num}")
            daily_tagged_hours[tag] += new_hours

            # Ignore specified tags
            if filter_regex and re.search(filter_regex, line, re.IGNORECASE):
                filtered_original_line = None
                debug.trace(2, "Filtered out line {n}: {l}".
                            format(n=line_num, l=original_line))
                debug.trace(4, f"{new_hours} ignored hours; hours={hours}")
            else:
                hours += new_hours
                debug.trace(5, f"{new_hours} new hours; hours={hours}")
                if verbose:
                    filtered_original_line += f" [{new_hours}]"
                
        # Check for daily hours
        # HACK: keep in synch with (temp) hack above
        elif (my_re.search(r"^hours:\s*(\S*)", line)):
            ## OLD: debug.trace(6, "hours check")
            debug.trace_fmt(5, "hours check: day_of_week={dw}", dw=day_of_week)
            specified_hours = system.safe_float(my_re.group(1), 0.0) if my_re.group(1) else 0.0
            ## OLD: if (specified_hours != hours):
            if ((specified_hours != hours) and (not skip_hours_check)):
                system.print_stderr("Error: Discrepancy in hours at line {n}: change {spec} => {calc}?".format(n=line_num, spec=specified_hours, calc=hours))
            else:
                # HACK: pretend user specified tabulated hours (TODO: use 'hours' below for clarify)
                ## specified_hours = hours
                pass
            ## OLD: weekly_hours += specified_hours
            weekly_hours += hours
            debug.assertion(weekday_hours[day_of_week] == "", f"Day of week already used at line {line_num}")
            ## OLD: weekday_hours[day_of_week] = specified_hours
            ## OLD2: weekday_hours[day_of_week] = hours
            weekday_hours[day_of_week] += ("" if not weekday_hours[day_of_week] else "-or-")
            weekday_hours[day_of_week] += str(hours)
            last_hours = hours
            hours = 0
            debug.trace_fmt(7, "spec_hours={sh} daily_hours={h} weekly_hours={wh} total_hours={th}, weekday_hours={wdh}", 
                            sh=specified_hours, h=hours, wh=weekly_hours, th=total_hours, wdh=weekday_hours)

            # Show tagged breakdown
            if tabulate_tags:
                if "daily" in report_tags:
                    show_tagged_hours(daily_tagged_hours, "Daily")
                for tag in daily_tagged_hours:
                    weekly_tagged_hours[tag] += daily_tagged_hours[tag]
                    daily_tagged_hours[tag] = 0
            
        # Validate and reset weekly hours
        elif (my_re.search(r"^weekly hours:\s*(\S*)", line)):
            debug.trace(6, "weekly hours check")
            specified_hours = system.safe_float(my_re.group(1), 0.0) if my_re.group(1) else 0.0
            ## OLD: if (specified_hours != weekly_hours):
            if ((specified_hours != weekly_hours) and (not skip_hours_check)):
                system.print_stderr("Error: Discrepancy in weekly hours at line {n}: change {spec} => {calc}?".format(n=line_num, spec=specified_hours, calc=weekly_hours))
            num_weeks += 1

            # Show hours and reset
            if verbose:
                print("Week %d hours: %s" % (num_weeks, weekly_hours))
            total_hours += weekly_hours
            last_weekly_hours = weekly_hours
            weekly_hours = 0

            # Show hours by task and reset
            if tabulate_tags:
                if "weekly" in report_tags:
                    show_tagged_hours(weekly_tagged_hours, "Weekly")
                for tag in weekly_tagged_hours:
                    total_tagged_hours[tag] += weekly_tagged_hours[tag]
                    weekly_tagged_hours[tag] = 0

            # Show hours by day of week and then reset associated record keeping
            # TODO: use map in place of simple list comprehensions
            if show_weekly or verbose:
                debug.assertion(not system.difference(list(weekday_hours.keys()), ABBREVIATED_WEEKDAYS))
                hour_per_day = [weekday_hours.get(d, "0") for d in ABBREVIATED_WEEKDAYS]
                print("\t".join([system.to_string(h) for h in hour_per_day]))
            weekday_hours = defaultdict(str)
            day_of_week = ""

        # Validate total hours
        elif (my_re.search(r"^total hours:\s*(\S*)", line)):
            debug.trace(6, "total hours check")
            if (weekly_hours != 0):
                system.print_stderr("Error: Missing weekly hours prior to total at line {n}".format(n=line_num))
            specified_hours = system.safe_float(my_re.group(1), 0.0) if my_re.group(1) else 0.0
            ## OLD: if (specified_hours != total_hours):
            if ((specified_hours != total_hours) and (not skip_hours_check)):
                system.print_stderr("Error: Discrepancy in total hours at line {n}: change {spec} => {calc}?".format(n=line_num, spec=specified_hours, calc=total_hours))

        # Ignore miscellaneous line: starts with 5 or more dashes (e.g., "------------------...-----")
        elif (my_re.search(r"^\-\-\-\-\-+", line) or my_re.search(r"^week of", line)):
            debug.trace(6, "miscellaenous line check")

        # Check for blank line without hours specification
        elif (line == ""):
            debug.trace(6, "blank line check")
            if (hours > 0):
                system.print_stderr("Warning: Unexpected blank line at line %d" % line_num)

        # Report lines not recognized
        else:
            system.print_stderr("Warning: Unexpected format at line %d: %s" % (line_num, line))

        # Output report with task details
        if output_report and (filtered_original_line is not None):
            report_line = filtered_original_line.strip()
            if omit_timespec:
                time_regex = r"\d*(:\d*)?(am|pm)?"
                timespec_regex = (time_regex + "-" + time_regex + r"(:|\s)\s*")
                report_line = re.sub(timespec_regex, "- ", report_line)
            if omit_tags:
                report_line = re.sub(r"^- \[\S+\] *", "- ", report_line)
            if re.search(r"^Hours:$", report_line, re.IGNORECASE):
                report_line += f" {last_hours}"
            if re.search(r"^Weekly Hours:$", report_line, re.IGNORECASE):
                report_line += f" {last_weekly_hours}"
            if re.search(r"^Total Hours:$", report_line, re.IGNORECASE):
                if (not verbose):
                    report_line += f" {total_hours}"
            debug.trace(7, f"report_line: {report_line}")
            print(report_line)

    # Do some sanity checks
    if (hours > 0):
        system.print_stderr("Warning: Missing weekly total for last week")
        debug.assertion(not system.difference(list(weekday_hours.keys()), ABBREVIATED_WEEKDAYS))

    # Print summary
    if verbose:
        print("Total hours:  %s" % total_hours)
        weekly_average = (total_hours / num_weeks) if (num_weeks > 0) else total_hours
        print("Average per week: %s" % system.round_num(weekly_average))
        proto_average = (total_hours / (52 / 12.0))
        print("Proto average (i.e., 52/12): %s" % system.round_num(proto_average))

    # Show hours by task
    if tabulate_tags:
        if "total" in report_tags:
            show_tagged_hours(total_tagged_hours, "Total")
    return

#------------------------------------------------------------------------

if __name__ == '__main__':
    main()
