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
# TODO (lossy):
# - Collapse repeated command templates and emit occurrence counts.
# - Throttle dense DEBUG runs (keep first K and every Nth line per phase).
# - Truncate/hash long argument vectors after preserving one full exemplar.
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

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main, FILENAME
from mezcla.my_regex import my_re
from mezcla import system

# Constants
TL = debug.TL
COLLAPSE_OPT = "collapse"
ADAPTIVE_OPT = "adaptive"
SAMPLE_OPT = "sample"
SUBSTR_OPT = "substr"

# Environment options
## OLD: MIN_PATH_LEN = system.getenv_bool(
MIN_PATH_LEN = system.getenv_int(
     "MIN_PATH_LEN", 40,
     description="Minimum path length for filtering")
## OLD: MAX_PATHS = system.getenv_bool(
MAX_PATHS = system.getenv_int(
     "MAX_PATHS",
     system.getenv_int(
         "MAX_PATH", 10,
         description="Legacy maximum number of paths length to filter"),
     description="Maximum number of paths length to filter")
MIN_SUBSTR_LEN = system.getenv_int(
     "MIN_SUBSTR_LEN", 30,
     description="Minimum substring length for general text substitution")
MIN_SUBSTR_FREQ = system.getenv_int(
     "MIN_SUBSTR_FREQ", 5,
     description="Minimum frequency for general text substitution")
MAX_SUBSTRS = system.getenv_int(
     "MAX_SUBSTRS", 10,
     description="Maximum number of general text substitutions")
SAMPLE_HEAD_SIZE = system.getenv_int(
     "SAMPLE_HEAD_SIZE", 500,
     description="Number of initial lines retained during sampling")
SAMPLE_TAIL_SIZE = system.getenv_int(
     "SAMPLE_TAIL_SIZE", 1000,
     description="Number of trailing lines retained during sampling")
SAMPLE_MAX_INTEREST = system.getenv_int(
     "SAMPLE_MAX_INTEREST", 800,
     description="Maximum number of middle error/warning lines retained during sampling")

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
        # Also count shared path prefixes to avoid overfitting to one-off deep paths.
        # This helps large Android logs where full paths vary at the deepest levels.
        prefix_counts = collections.Counter()
        for path, freq in counts.items():
            parts = [part for part in path.split("/") if part]
            for end in range(5, len(parts) + 1):
                prefix = f"/{'/'.join(parts[:end])}/"
                if len(prefix) >= min_len:
                    prefix_counts[prefix] += freq

        # ## OLD: candidates = [p for p, c in counts.items() if len(p) >= min_len and c > 1]
        candidates = [(p, len(p) * c) for p, c in prefix_counts.items() if c > 1]
        candidates.sort(key=lambda item: (item[1], len(item[0])), reverse=True)
        result = []
        for path, _score in candidates:
            if any(path in existing for existing in result):
                continue
            result.append(path)
            if len(result) >= limit:
                break
        # Keep longest-first substitution order for stable replacement behavior.
        result.sort(key=len, reverse=True)
        return result

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
            ## TODO3: make sure the stripped segments overlap
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
            ## OLD: head_size = 1000
            head_size = SAMPLE_HEAD_SIZE
            ## OLD: tail_size = 2000
            tail_size = SAMPLE_TAIL_SIZE
            max_interest = SAMPLE_MAX_INTEREST
            if len(processed) > (head_size + tail_size):
                head = processed[:head_size]
                tail = processed[-tail_size:]
                middle = processed[head_size:-tail_size]
                ## OLD: interest = [l for l in middle if my_re.search(r'error|fail|warning|critical|exception|debug', l, my_re.I)]
                ## Note: 'debug' removed to avoid retaining every [DEBUG] line in buildozer logs
                interest = [l for l in middle if my_re.search(r'error|fail|warning|critical|exception', l, my_re.I)]
                if len(interest) > max_interest:
                    interest = interest[:max_interest]
                
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
            ordered_subs = sorted(all_subs.items(), key=lambda pair: len(pair[0]), reverse=True)
            for line in processed:
                new_line = line
                ## OLD: for text, token in all_subs.items():
                for text, token in ordered_subs:
                    new_line = new_line.replace(text, token)
                final_output.append(new_line)
            processed = final_output

        return processed

#-------------------------------------------------------------------------------

def main() -> None:
    """Entry point"""
    debug.trace(TL.DETAILED, f"main(): script={system.real_path(__file__)}") 

    # Parse command line options
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

    return

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    debug.trace(5, f"module __doc__: {__doc__}")
    debug.assertion("TODO:" not in __doc__)
    main()
