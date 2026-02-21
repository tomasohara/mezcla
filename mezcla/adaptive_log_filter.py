#! /usr/bin/env python3
#
# Filters large log file to allow for convenient sharing (e.g., AI agents).
# This applies the following transformations:
# - Collapses progress bars (\r)
# - Substitutes frequent long paths with tokens
# - Samples head, tail, and error lines to fit token budgets
#
# Note:
# - Initial version produced with Gemini-3-Pro.
# - It was in the context of filtering Android deployment logs
#

"""
Refines Android deployment logs for AI analysis.

Sample usage:
   {script} --collapse --adaptive --sample _android_deploy.log
"""

# Standard modules
from typing import Optional, List, Dict
import collections

# Installed modules
## TODO: import numpy as np

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main, FILENAME
from mezcla.my_regex import my_re
from mezcla import system
## TODO:
## from mezcla import data_utils as du

# Constants
TL = debug.TL
## TODO: Constants for switches omitting leading dashes (e.g., DEBUG_MODE = "debug-mode")
COLLAPSE_OPT = "collapse"
ADAPTIVE_OPT = "adaptive"
SAMPLE_OPT = "sample"

# Environment options
MIN_PATH_LEN = system.getenv_bool(
     "MIN_PATH_LEN", 40,
     description="Mininum path length for filtering")
MAX_PATHS = system.getenv_bool(
     "MAX_PATH", 10,
     description="Maxmium number of paths length to filter")

#-------------------------------------------------------------------------------

class LogRefiner:
    """Class for filtering and compressing large build logs."""

    def __init__(self, collapse: bool = False, adaptive: bool = False, sample: bool = False) -> None:
        """Initializer: Set filtering modes"""
        debug.trace_expr(TL.VERBOSE, collapse, adaptive, sample, prefix="in LogRefiner.__init__: ")
        self.collapse = collapse
        self.adaptive = adaptive
        self.sample = sample
        self.path_map: Dict[str, str] = {}
        self.TODO: Optional[bool] = None # TODO: revise
        debug.trace_object(5, self, label=f"{self.__class__.__name__} instance") 

    def _get_common_paths(self, lines: List[str], min_len: int = MIN_PATH_LEN, limit: int = MAX_PATHS) -> List[str]:
        """Identifies the most frequent long directory paths."""
        # Focus on paths containing common build artifacts to avoid replacing small system paths
        # Designed for long paths in python-for-android (e.g., NDK)
        ## TODO2: strip final slash
        path_pattern = r'(/[a-zA-Z0-9\._\-]+(?:/[a-zA-Z0-9\._\-]+){4,}/)'
        all_matches = []
        for line in lines:
            all_matches.extend(my_re.findall(path_pattern, line))
        
        counts = collections.Counter(all_matches)
        # We want the longest paths that appear frequently
        candidates = [p for p, c in counts.items() if len(p) >= min_len and c > 1]
        # Sort by length descending is crucial so sub-paths don't break parent paths
        candidates.sort(key=len, reverse=True)
        return candidates[:limit]

    def process(self, raw_lines: List[str]) -> List[str]:
        """Applies filters to the log lines."""
        processed = raw_lines

        # 1. Collapse progress bars (tqdm style \r)
        if self.collapse:
            debug.trace(TL.VERBOSE, "Filtering: Collapsing carriage returns")
            processed = [my_re.sub(r'.*\r', '', line) for line in processed if line.strip()]

        # 2. Adaptive Path Substitution - Identify paths BEFORE sampling
        if self.adaptive:
            debug.trace(TL.VERBOSE, "Filtering: Identifying common paths")
            common = self._get_common_paths(processed)
            for i, path in enumerate(common, 1):
                token = f"{{path{i}}}"
                self.path_map[path] = token

        # 3. Head/Tail/Grep Sampling
        if self.sample:
            debug.trace(TL.VERBOSE, "Filtering: Sampling log structure")
            head_size = 1000
            tail_size = 2000
            if len(processed) > (head_size + tail_size):
                head = processed[:head_size]
                tail = processed[-tail_size:]
                middle = processed[head_size:-tail_size]
                interest = [l for l in middle if my_re.search(r'error|fail|warning|critical|exception|debug', l, my_re.I)]
                
                msg = f"\n... [SNIP: {len(middle) - len(interest)} lines removed] ...\n"
                processed = head + [msg] + interest + [msg] + tail

        # 4. Final Substitution Pass
        if self.adaptive and self.path_map:
            final_output = []
            for line in processed:
                new_line = line
                for path, token in self.path_map.items():
                    new_line = new_line.replace(path, token)
                final_output.append(new_line)
            processed = final_output

        return processed

#-------------------------------------------------------------------------------

def main() -> None:
    """Entry point"""
    debug.trace(TL.DETAILED, f"main(): script={system.real_path(__file__)}") 

    # Parse command line options
    # TODO: manual_input=True; short_options=True 
    main_app = Main(
        description=__doc__.format(script=gh.basename(__file__)),
        boolean_options=[
            (COLLAPSE_OPT, "Collapse tqdm-style progress updates"),
            (ADAPTIVE_OPT, "Replace long path components with path vars"),
            (SAMPLE_OPT, "Keep head/tail/errors only (10% target)")
        ],
    ) 
    debug.reference_var(FILENAME) 
    debug.assertion(main_app.parsed_args) 

    # Read input lines
    input_data = main_app.read_entire_input().split("\n")

    # Apply filters
    refiner = LogRefiner(
        collapse=main_app.get_parsed_option(COLLAPSE_OPT),
        adaptive=main_app.get_parsed_option(ADAPTIVE_OPT),
        sample=main_app.get_parsed_option(SAMPLE_OPT)
    )
    result = refiner.process(input_data)

    # Output Legend at the top (e.g., for AI context)
    if refiner.path_map:
        print("Path substitution legend:")
        ## TODO2: drop braces from token
        for path, token in refiner.path_map.items():
            print(f"    {token}: {path}")

    # Output transformed lines
    for line in result:
        print(line)

    # TODO: delete check when stable 
    debug.assertion(not any(my_re.search(r"^TODO_", m, my_re.IGNORECASE)
                            for m in dir(main_app))) 
    return

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    debug.trace(5, f"module __doc__: {__doc__}")
    debug.assertion("TODO:" not in __doc__)
    main()
