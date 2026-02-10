#! /usr/bin/env python3
#
# show-dependency-chain.bash: shows chain of dependencies given output from pip install's
# --report option. Specifically, it extract package names and requires_dist blocks from
# a pip report JSON file and emit a valid YAML dependency listing.
#
# NOTES:
# - Based on ChatGpt.
# - This automates the following Perl-based snippet:
#     $ perl -pe 's/^\s+"name":.*/\n$&\n/; s/^\s+"requires_dist":/\n$&/; s/\],?\s*/$&\n/;' "$report" |
#         perl-grep -para '^\s*"name|requires_dist":' |
#         perl -0777 -pe 's/\n(\s*"requires_dist":)/$1/g;' > "$report".dependencies
# - The Python version parses JSON properly instead of relying on regexes.

"""
Extract package names and their requires_dist entries from a pip --report JSON
and emit VALID YAML.

Output format:

    ---

    - name: PACKAGE
      requires_dist:
        - dep1
        - dep2

    - name: OTHER

Sample usage:
    {script} pip-report.json > pip-report-dependencies.yaml
"""

# Standard modules
import json
from typing import Iterable, List

# Installed modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main, FILENAME
from mezcla import system

# ---------------------------------------------------------------------------

TL = debug.TL

# ---------------------------------------------------------------------------

class Helper:
    """Process a pip --report JSON structure and emit YAML dependencies."""

    def __init__(self) -> None:
        debug.trace_object(5, self, label=f"{self.__class__.__name__} instance")

    def _iter_requires(self, meta: dict) -> List[str]:
        """Gets module requirements from METAdata"""
        reqs = meta.get("requires_dist")
        if not reqs:
            return []
        return [str(r) for r in reqs]

    def process(self, report: dict) -> None:
        """Extracts module dependencies from pip report"""
        installs: Iterable[dict] = report.get("install", [])

        print("---")
        for entry in installs:
            meta = entry.get("metadata", {})
            name = meta.get("name")
            if not name:
                continue

            print()
            print(f"- name: {name}")

            reqs = self._iter_requires(meta)
            if reqs:
                print("  requires_dist:")
                for r in reqs:
                    print(f"    - {r}")

# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point."""
    debug.trace(TL.DETAILED, f"main(): script={system.real_path(__file__)}")

    main_app = Main(
        description=__doc__.format(script=gh.basename(__file__)),
    )

    report_file = main_app.get_parsed_option(FILENAME)
    debug.assertion(report_file)

    with system.open_file(report_file) as fh:
        report = json.load(fh)

    helper = Helper()
    helper.process(report)

# ---------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    main()
