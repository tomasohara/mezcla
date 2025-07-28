## Test TODO notes

An optional priority is indicated by [Pn]

- [P1] Use @pytest.mark.xfail to add new tests rather than an empty tets with a TODO note.
- [P2] Make sure path wrappers used instead of using / (e.g., "a/b" => gh.format_path("a", "b").
- [P2] Use mkdir wrapper (e.g., system.create_directory or glue_helpers.full_mkdir).
- [P3] Remove unused boiterplate from template.py (e.g., setup methods).
- [P4] Keep the tests in sync with package upgrades.
- [P4] Track down exceptions in passing tests (e.g., test_to_csv).
- [P3] Make sure tests run in optimized code (i.e., __debug__=False) and likewise with DEBUG_LEVEL lower than default (2).
- [P3] Check for tests not making assertions, as in old version of test_safe_int
       "THE_MODULE.safe_int(2.0) == 2" => "assert THE_MODULE.safe_int(2.0) == 2"
- [P2] Make pass to cut down on xfail usage (e.g., remove if passed for past few months unless special case)!
