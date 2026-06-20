## Test overview

In addition to pytest-based unit tests, there are command-line tests using
BatsPP (see https://github.com/LimaBD/batspp).

## Style tips

Don't use black without permission: it is too opinionated!

See main README under root dir (../..).

## Warning: Make sure assertions add to placeholder tests

When adding new tests, make sure an assertion is used so that
pytest will flag the case as failed

For example, don't just have comments that work in progress:

    def test_fubar_bad(self):             ## note: bad example
        """Verify fubar--bad example"""
        debug.trace(4, "test_fubar_bad()")
        ## TODO: WORK-IN-PROGRESS

Instead add an explicit assertion:

	@pytest.mark.xfail                   # TODO: remove xfail
    def test_fubar(self):
        """Verify fubar--good example"""
        debug.trace(4, "test_fubar()")
        assert False, "TODO: implement"

