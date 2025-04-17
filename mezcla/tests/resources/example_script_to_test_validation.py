#! /usr/bin/env python3
#
# note: Not used in any test.
#

"""
Illustration script to test validation of most used functions from:
- html_utils.py
- debug.py
- system.py

List of most used functions in Mezcla package (✓ == tested on this script, x == not tested):

✓ trace(...) -> called 32 times
x get_exception(...) -> called 21 times
✓ val(...) -> called 17 times
✓ get_url_param(...) -> called 16 times
x trace_fmt(...) -> called 15 times
x code(...) -> called 12 times
x debugging(...) -> called 12 times
x assertion(...) -> called 12 times
✓ get_url_parameter(...) -> called 12 times
x getenv(...) -> called 12 times
x get_url_parameter_value(...) -> called 11 times
x call(...) -> called 9 times
x trace_fmtd(...) -> called 9 times
x format_value(...) -> called 9 times
✓ escape_html_text(...) -> called 9 times
x trace_expr(...) -> called 8 times
x download_web_document(...) -> called 8 times
✓ escape_html_value(...) -> called 8 times
x trace_object(...) -> called 7 times
✓ get_level(...) -> called 7 times
x print_stderr(...) -> called 7 times
x getenv_int(...) -> called 7 times
x _to_utf8(...) -> called 6 times
x get_param_dict(...) -> called 6 times
x getenv_value(...) -> called 6 times
x profile_function(...) -> called 5 times
x timestamp(...) -> called 5 times
x docstring_parameter(...) -> called 5 times
x main(...) -> called 5 times
x get_browser(...) -> called 5 times
✓ open_file(...) -> called 5 times
✓ file_exists(...) -> called 5 times
x to_utf8(...) -> called 5 times
x to_float(...) -> called 5 times
x _getenv_bool(...) -> called 4 times
x _print_exception_info(...) -> called 4 times
x open_debug_file(...) -> called 4 times
x trace_values(...) -> called 4 times
x init_BeautifulSoup(...) -> called 4 times
✓ unescape_html_text(...) -> called 4 times
✓ round_num(...) -> called 4 times
x init(...) -> called 4 times
x register_env_option(...) -> called 4 times
x getenv_number(...) -> called 4 times
x to_int(...) -> called 4 times
x print_error(...) -> called 4 times
x print_full_stack(...) -> called 4 times
✓ write_file(...) -> called 4 times
x to_str(...) -> called 4 times
x to_string(...) -> called 4 times
"""

# Standard packages
import tempfile

# Installed packages
from mezcla.main import Main
from mezcla import system
from mezcla import debug
from mezcla import html_utils

# Command-line labels and
# enviroment variables constants
WRONG = 'wrong'
GOOD = 'good'

class ExampleValidationScript(Main):
    """Argument processing class"""

    # Class-level member variables for arguments
    # (avoids need for class constructor)
    wrong = False
    good = True

    def setup(self) -> None:
        """Process arguments"""
        self.wrong = self.get_parsed_option(WRONG, self.wrong)
        self.good = self.get_parsed_option(GOOD, self.good)

    def run_main_step(self) -> None:
        """Process main script"""
        if self.good:
            print("With GOOD parameter types:")
            print(f"\t{'✓' if self.is_debug_working() else 'x'} mezcla.debug")
            print(f"\t{'✓' if self.is_html_utils_working() else 'x'} mezcla.html_utils")
            print(f"\t{'✓' if self.is_system_working() else 'x'} mezcla.system")
        if self.wrong:
            print("With WRONG parameter types:")
            print(f"\t{'✓' if self.is_debug_failing() else 'x'} mezcla.debug")
            print(f"\t{'✓' if self.is_html_utils_failing() else 'x'} mezcla.html_utils")
            print(f"\t{'✓' if self.is_system_failing() else 'x'} mezcla.system")

    def is_debug_working(self) -> bool:
        """Check if debug functions work with good types"""
        debug.trace(7, 'Works as expected!')
        debug.trace(debug.TraceLevel.QUITE_VERBOSE, 'Works as expected!')
        assert debug.val(debug.get_level(), 'Hello, world!') == 'Hello, world!'
        return True

    def is_html_utils_working(self) -> bool:
        """Check if html_utils functions work with good types"""
        html_utils.get_url_param(
            "some-key",
            "some-value",
            { "some-key": "foobar" },
        )
        html_utils.escape_html_text("<2/")
        html_utils.escape_html_text("Joe's hat")
        return True

    def is_system_working(self) -> bool:
        """Check if system functions work with good types"""
        temp_file = tempfile.NamedTemporaryFile().name
        system.write_file(temp_file, 'Hello, world!')
        assert system.file_exists(temp_file)
        file = system.open_file(temp_file, 'w')
        assert file is not None
        file.close()
        assert system.round_num(1.6789, 2) == 1.68
        return True

    def fails_successfully(self, func, *args, **kwargs) -> bool:
        """Check if function fails as expected"""
        try:
            func(*args, **kwargs)
            return False
        except TypeError: ## TODO: change to specific exception
            return True
        except Exception:
            return False

    def is_debug_failing(self) -> bool:
        """Check if debug functions fail with wrong types"""
        to_check = [
            self.fails_successfully(debug.trace, None, 'foo'),
            self.fails_successfully(debug.trace, "7", 'foo'),
            self.fails_successfully(debug.trace, debug.TraceLevel.QUITE_VERBOSE, {'a': 1, 'b': 2}),
            self.fails_successfully(debug.val, None, 'Hello, world!'),
        ]
        return all(to_check)

    def is_html_utils_failing(self) -> bool:
        """Check if html_utils functions fail with wrong types"""
        to_check = [
            self.fails_successfully(html_utils.get_url_param, "some-key", "some-value", True),
            self.fails_successfully(html_utils.escape_html_text, True),
            self.fails_successfully(html_utils.escape_html_text, 7),
        ]
        return all(to_check)

    def is_system_failing(self) -> bool:
        """Check if system functions fail with wrong types"""
        to_check = [
            self.fails_successfully(system.write_file, None, 'Hello, world!'),
            self.fails_successfully(system.file_exists, None),
            self.fails_successfully(system.write_file, 7, 'Hello, world!'),
            self.fails_successfully(system.file_exists, 7),
            self.fails_successfully(system.round_num, None, 2),
            self.fails_successfully(system.round_num, 1.6789, '2'),
        ]
        return all(to_check)


if __name__ == '__main__':

    app = ExampleValidationScript(
        description = __doc__,
        boolean_options = [
            (WRONG, 'Run methods with wrong types'),
            (GOOD, 'Run methods with good types'),
        ],
        manual_input = True,
    )

    app.run()
