## Development TODO notes

An optional priority is indicated by [Pn]

- [P2] Straighten out `TEMP_BASE` and `TEMP_FILE` usages.
- [P3] Add way to convert EX-comments into doctests for use with other tools.
  See https://docs.pytest.org/en/7.1.x/how-to/doctest.html
- [P4] Weed out debug.trace_fmt usages.
- [P1] Weed out lingering tpo_common usages.
- [P3] make sure try/except blocks issue warnings instead of swallowing errors (e.g., during test imports).
- [P4] Avoid use of atexit for deleting temporary files: by default they are
  put under /tmp, which gets cleaned up by the system!
- [P4] Avoid using tempfile directly: use glue_helper.get_temp_file instead.
