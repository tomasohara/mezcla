#! /usr/bin/env python3
#
# Summarizes results from pytest runs with option to combine xfail results into
# regular ones.
#
# note:
# - Via Claude with manual fixup.
#

"""
Summarize pytest pass/fail results from pytest output

Sample usage:
   grep "===" test_results.log | {script} --treat-xresults --
"""

# Standard modules
from typing import Optional, Dict, List
from dataclasses import dataclass

# Installed modules
## TODO: import numpy as np

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main
from mezcla.my_regex import my_re
from mezcla import system

# Constants
TL = debug.TL
TREAT_XRESULTS_OPT = "treat-xresults"
HEADER_ONLY_OPT = "header-only"
IGNORE_TIMESTAMP_OPT = "ignore-timestamp"
COMBINE_OPT = "combine"

# Environment options
VERBOSE_OUTPUT = system.getenv_bool(
    "VERBOSE_OUTPUT", False,
    description="Verbose output with headers and separators")
COMBINE_RESULTS = system.getenv_bool(
    "COMBINE_RESULTS", False,
    description="Combine results with same timestamp")

# Sanity checks
debug.trace(5, f"global __doc__: {__doc__}")
debug.assertion(__doc__)

#-------------------------------------------------------------------------------

@dataclass
class TestResult:
    """Store pytest result summary information"""
    passed: int = 0
    failed: int = 0
    skipped: int = 0
    xfailed: int = 0
    xpassed: int = 0
    duration: float = 0.0
    timestamp: str = ""

    def total_tests(self, treat_xresults: bool = False) -> int:
        """Return total number of tests, optionally treating xfailed/xpassed as failed/passed"""
        ## TODO: add option for treating skipped as failures
        total = self.passed + self.failed
        if treat_xresults:
            total += (self.xfailed + self.xpassed)
        debug.trace_expr(TL.QUITE_VERBOSE, total)
        return total

    def ok_rate(self, treat_xresults: bool = False) -> float:
        """Calculate OK percent, optionally treating xfailed as passed and xpassed as failed"""
        total = self.total_tests(treat_xresults)
        if total == 0:
            debug.trace(TL.VERBOSE, "No tests found, returning 0% OK rate")
            return 0.0
        
        passed = self.passed
        if treat_xresults:
            passed += self.xpassed
        ok_pct = min(passed * 100.0 / total, 100.0) if total else 0.0
        debug.trace_expr(TL.QUITE_VERBOSE, passed, total, ok_pct)
        return ok_pct

#-------------------------------------------------------------------------------

class PytestSummarizer:
    """Class for parsing and summarizing pytest results"""

    def __init__(self, **kwargs) -> None:
        """Initializer"""
        debug.trace_expr(TL.VERBOSE, kwargs, prefix="in PytestSummarizer.__init__: ")
        self.treat_xresults: bool = kwargs.get('treat_xresults', False)
        self.combine: bool = kwargs.get('combine', False)
        self.ignore_timestamp: bool = kwargs.get('ignore_timestamp', False)
        self.results_cache: Dict[str, TestResult] = {}
        debug.trace_object(5, self, label=f"{self.__class__.__name__} instance")

    def parse_pytest_line(self, line: str) -> Optional[TestResult]:
        """Parse a pytest summary line and return TestResult object"""
        debug.trace(TL.QUITE_DETAILED, f"parse_pytest_line({line[:50]}...)")
        
        # Check if this is a pytest summary line
        if not my_re.search(r"= .*(passed|failed|skipped).* =", line):
            debug.trace(TL.VERBOSE, "Not a pytest summary line")
            return None
        
        # Extract timestamp with optional revision number
        # example: 09jan25.12
        timestamp = "n/a"
        if not self.ignore_timestamp:
            timestamp_match = my_re.search(r'(\d+\w+\d+(\.\d+)?)', line)
            if timestamp_match:
                timestamp = timestamp_match.group(1)
            else:
                system.print_error(f"Warning: Timestamp not found in {line[:50]}...")
                return None
        debug.trace_expr(TL.VERBOSE, timestamp)
        
        # Get existing result from cache or create new one
        result = self.results_cache.get(timestamp, TestResult(timestamp=timestamp))
        debug.trace_expr(TL.QUITE_VERBOSE, result)
        
        # Parse test counts and duration
        patterns = {
            r'(\d+)\s+passed': 'passed',
            r'(\d+)\s+failed': 'failed',
            r'(\d+)\s+skipped': 'skipped',
            r'(\d+)\s+xfailed': 'xfailed',
            r'(\d+)\s+xpassed': 'xpassed',
            r'in\s+([\d.]+)s': 'duration'
        }
        
        for pattern, attr in patterns.items():
            match = my_re.search(pattern, line)
            if match:
                value = float(match.group(1)) if attr == 'duration' else int(match.group(1))
                if self.combine:
                    # Add to existing value rather than replacing
                    current_value = getattr(result, attr, 0)
                    value += current_value
                setattr(result, attr, value)
                debug.trace_expr(TL.QUITE_VERBOSE, attr, value)
        
        self.results_cache[timestamp] = result
        debug.trace_expr(TL.VERBOSE, result)
        return result

    def process(self, lines) -> List[TestResult]:
        """Process LINES with pytest results"""
        debug.trace(TL.USUAL, f"process: processing {len(lines)} input lines")
        
        lines = lines if isinstance(lines, list) else lines.splitlines()
        
        for line in lines:
            self.parse_pytest_line(line.strip())
        
        # Convert cache to sorted list
        results = list(self.results_cache.values())
        results.sort(key=lambda x: x.timestamp)
        
        debug.trace_expr(TL.VERBOSE, len(results))
        return results

    def format_output(self, results: List[TestResult], header_only: bool = False) -> str:
        """Format the results as a string table"""
        debug.trace(TL.USUAL, f"format_output: formatting {len(results)} results")
        
        if not results:
            debug.trace(TL.USUAL, "No results to format")
            return ""
        
        # Build header
        header = (f"{'Timestamp':12} {'Skip':>7} {'Pass':>7} {'Fail':>7} " +
                  f"{'XFail':>7} {'XPass':>7} {'Total':>7} {'OK-pct':>8} {'Time':>7}")
        
        lines = []
        
        if VERBOSE_OUTPUT and not header_only:
            lines.append("\nTest Results Summary:")
            lines.append("-" * len(header))
        
        lines.append(header)
        
        if not header_only:
            for result in results:
                lines.append(
                    f"{result.timestamp:12} "
                    f"{result.skipped:7d} "
                    f"{result.passed:7d} "
                    f"{result.failed:7d} "
                    f"{result.xfailed:7d} "
                    f"{result.xpassed:7d} "
                    f"{result.total_tests(self.treat_xresults):7d} "
                    f"{result.ok_rate(self.treat_xresults):7.2f}% "
                    f"{result.duration:6.2f}s"
                )
        
        return "\n".join(lines)

#-------------------------------------------------------------------------------

def main() -> None:
    """Entry point"""
    debug.trace(TL.USUAL, f"main(): script={system.real_path(__file__)}")

    # Parse command line options, show usage if --help given
    main_app = Main(
        description=__doc__.format(script=gh.basename(__file__)),
        boolean_options=[
            (TREAT_XRESULTS_OPT, "Treat xfailed as passed and xpassed as failed"),
            (HEADER_ONLY_OPT, "Only show the header line"),
            (IGNORE_TIMESTAMP_OPT, "Don't require timestamp"),
            (COMBINE_OPT, "Combine results with same timestamp"),
        ],
    )
    debug.assertion(main_app.parsed_args)
    
    treat_xresults = main_app.get_parsed_option(TREAT_XRESULTS_OPT, False)
    header_only = main_app.get_parsed_option(HEADER_ONLY_OPT, False)
    ignore_timestamp = main_app.get_parsed_option(IGNORE_TIMESTAMP_OPT, False)
    combine = main_app.get_parsed_option(COMBINE_OPT, COMBINE_RESULTS)

    summarizer = PytestSummarizer(
        treat_xresults=treat_xresults,
        combine=combine,
        ignore_timestamp=ignore_timestamp
    )
    
    # Read and process input
    input_text = main_app.read_entire_input()
    results = summarizer.process(input_text)
    
    # Format and print output
    output = summarizer.format_output(results, header_only=header_only)
    if output:
        print(output)
    
    return

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    debug.trace(5, f"module __doc__: {__doc__}")
    main()
