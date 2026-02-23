#! /usr/bin/env python3
#
# Filters large log file to allow for convenient sharing (e.g., AI agents).
# This applies the following transformations:
# - Collapses progress bars (\r)
# - Substitutes frequent long paths with tokens
# - Substitutes frequent general substrings with tokens (e.g., compiler flags)
# - Samples head, tail, and error lines to fit token budgets
#
# Note:
# - Initial version produced with Gemini-3-Pro.
# - It was in the context of filtering Android deployment logs
#

"""
Refines Android deployment logs for AI analysis.

Sample usage:
   {script} --collapse --adaptive --substr --sample _android_deploy.log
"""

# Standard modules
from typing import Optional, List, Dict
import collections
import os

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
SUBSTR_OPT = "substr"

# Environment options
MIN_PATH_LEN = system.getenv_bool(
     "MIN_PATH_LEN", 40,
     description="Mininum path length for filtering")
MAX_PATHS = system.getenv_bool(
     "MAX_PATH", 10,
     description="Maxmium number of paths length to filter")
MIN_SUBSTR_LEN = system.getenv_int(
     "MIN_SUBSTR_LEN", 30,
     description="Minimum substring length for general text substitution")
MIN_SUBSTR_FREQ = system.getenv_int(
     "MIN_SUBSTR_FREQ", 5,
     description="Minimum frequency for general text substitution")
MAX_SUBSTRS = system.getenv_int(
     "MAX_SUBSTRS", 10,
     description="Maximum number of general text substitutions")

#-------------------------------------------------------------------------------

class LogRefiner:
    """Class for filtering and compressing large build logs."""

    def __init__(self, collapse: bool = False, adaptive: bool = False, sample: bool = False, substr: bool = False) -> None:
        """Initializer: Set filtering modes"""
        debug.trace_expr(TL.VERBOSE, collapse, adaptive, sample, substr, prefix="in LogRefiner.__init__: ")
        self.collapse = collapse
        self.adaptive = adaptive
        self.sample = sample
        self.substr = substr
        self.path_map: Dict[str, str] = {}
        self.substr_map: Dict[str, str] = {}
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

    def _get_common_substrings(self, lines: List[str], min_len: int = MIN_SUBSTR_LEN, min_freq: int = MIN_SUBSTR_FREQ, limit: int = MAX_SUBSTRS) -> List[str]:
        """Identifies frequently occurring text substrings for token substitution.
        Uses whitespace-delimited token counting with common-prefix grouping
        to find impactful candidates (e.g., '-I/home/user/path/to/sdk/')."""
        debug.trace(TL.VERBOSE, f"_get_common_substrings(_, #lines={len(lines)}, ml={min_len}, mf={min_freq}, lim={limit})")
        # Count whitespace-delimited tokens
        token_counts: Dict[str, int] = collections.Counter()
        for line in lines:
            for token in line.split():
                if len(token) >= min_len:
                    token_counts[token] += 1

        # Sort ALL long tokens lexicographically for prefix grouping
        all_long_tokens = sorted(token_counts.keys())
        debug.trace_expr(TL.VERBOSE, len(all_long_tokens), prefix="_get_common_substrings: ")

        # Group adjacent sorted tokens by common prefix
        candidates = []
        i = 0
        while i < len(all_long_tokens):
            group = [all_long_tokens[i]]
            j = i + 1
            while j < len(all_long_tokens):
                prefix = os.path.commonprefix([group[0], all_long_tokens[j]])
                if len(prefix) >= min_len:
                    group.append(all_long_tokens[j])
                    j += 1
                else:
                    break

            if len(group) > 1:
                # Use longest common prefix; total freq is sum across group
                prefix = os.path.commonprefix(group)
                if len(prefix) >= min_len:
                    total = sum(token_counts[t] for t in group)
                    if total >= min_freq:
                        candidates.append((prefix, total))

            # Also add individual frequent tokens (may differ from prefix)
            for t in group:
                if token_counts[t] >= min_freq:
                    candidates.append((t, token_counts[t]))

            i = j

        # Sort by impact score (length * frequency)
        candidates.sort(key=lambda x: len(x[0]) * x[1], reverse=True)

        # Deduplicate: skip substrings already covered by a longer selection
        # Also skip candidates covered by existing path_map entries
        existing_paths = set(self.path_map.keys())
        result = []
        for substr, _score in candidates:
            if any(substr in existing for existing in result):
                continue
            if any(substr in path or path in substr for path in existing_paths):
                continue
            result.append(substr)
            if len(result) >= limit:
                break

        # Sort longest first so longer substitutions are applied before shorter ones
        result.sort(key=len, reverse=True)
        debug.trace_expr(TL.VERBOSE, result, prefix="_get_common_substrings => ")
        return result

    def process(self, raw_lines: List[str]) -> List[str]:
        """Applies filters to the log lines."""
        processed = raw_lines

        # 1. Collapse progress bars (tqdm style \r) and strip ANSI escape codes
        if self.collapse:
            debug.trace(TL.VERBOSE, "Filtering: Collapsing carriage returns and ANSI codes")
            processed = [my_re.sub(r'.*\r', '', line) for line in processed if line.strip()]
            ## Note: ANSI codes common in android_deploy/buildozer logs (e.g., colored [DEBUG]/[INFO])
            processed = [my_re.sub(r'\x1b\[[0-9;]*m', '', line) for line in processed]

        # 2. Adaptive Path Substitution - Identify paths BEFORE sampling
        if self.adaptive:
            debug.trace(TL.VERBOSE, "Filtering: Identifying common paths")
            common = self._get_common_paths(processed)
            for i, path in enumerate(common, 1):
                token = f"{{path{i}}}"
                self.path_map[path] = token

        # 2b. General Substring Substitution - Identify frequent substrings
        if self.substr:
            debug.trace(TL.VERBOSE, "Filtering: Identifying common substrings")
            common_substrs = self._get_common_substrings(processed)
            for i, substr in enumerate(common_substrs, 1):
                token = f"{{sub{i}}}"
                self.substr_map[substr] = token

        # 3. Head/Tail/Grep Sampling
        if self.sample:
            debug.trace(TL.VERBOSE, "Filtering: Sampling log structure")
            head_size = 1000
            tail_size = 2000
            if len(processed) > (head_size + tail_size):
                head = processed[:head_size]
                tail = processed[-tail_size:]
                middle = processed[head_size:-tail_size]
                ## OLD: interest = [l for l in middle if my_re.search(r'error|fail|warning|critical|exception|debug', l, my_re.I)]
                ## Note: 'debug' removed to avoid retaining every [DEBUG] line in buildozer logs
                interest = [l for l in middle if my_re.search(r'error|fail|warning|critical|exception', l, my_re.I)]
                
                msg = f"\n... [SNIP: {len(middle) - len(interest)} lines removed] ...\n"
                processed = head + [msg] + interest + [msg] + tail

        # 4. Final Substitution Pass
        all_subs = {}
        if self.adaptive and self.path_map:
            all_subs.update(self.path_map)
        if self.substr and self.substr_map:
            all_subs.update(self.substr_map)
        if all_subs:
            final_output = []
            for line in processed:
                new_line = line
                for text, token in all_subs.items():
                    new_line = new_line.replace(text, token)
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
            ## BAD: (SAMPLE_OPT, "Keep head/tail/errors only (10% target)")
            ## TODO2: check for other issues with argparse option text
            (SAMPLE_OPT, "Keep head/tail/errors only (10%% target)"),
            (SUBSTR_OPT, "Replace frequent substrings with tokens (generalizes --adaptive)")
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
        sample=main_app.get_parsed_option(SAMPLE_OPT),
        substr=main_app.get_parsed_option(SUBSTR_OPT)
    )
    result = refiner.process(input_data)

    # Output Legend at the top (e.g., for AI context)
    if refiner.path_map or refiner.substr_map:
        print("Substitution legend:")
        ## TODO2: drop braces from token
        for path, token in refiner.path_map.items():
            print(f"    {token}: {path}")
        for substr, token in refiner.substr_map.items():
            print(f"    {token}: {substr}")

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
