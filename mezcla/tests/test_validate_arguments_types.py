#! /usr/bin/env python3
#
# Tests for validate_arguments_types module
#

"""
Tests for validate_arguments_types module
"""

import sys
import re
from collections import defaultdict
from typing import Any, AnyStr, Dict, List, Optional

import pytest
from pydantic import ValidationError, validate_call, ConfigDict
import mezcla.validate_arguments_types as va

def assert_validation_error(func, *args, **kwargs):
    """Asserts that a function raises a ValidationError"""
    with pytest.raises(ValidationError) as exc_info:
        func(*args, **kwargs)
    assert "For further information visit" in str(exc_info.value)

def test_custom_types():
    """Test for custom types, if they are valid for the current python version"""
    # Function to test
    @validate_call
    def file_to_str(filename: va.FileDescriptorOrPath) -> str:
        """Example of custom types"""
        assert isinstance(filename, (str, bytes, int)), "The validation should fail before this"
        return str(filename)
    # Test
    assert file_to_str("example_file_name.txt") == "example_file_name.txt"
    assert file_to_str(12345) == "12345"
    assert file_to_str(True) == "1" # Interesting behavior
    assert_validation_error(file_to_str, {"a": 1, "b": 2})

#-------------------------------------------------------------------------------
# Spot checks of validate_call against the type hints fleshed out for the main
# modules (debug, html_utils, main, my_regex, system, glue_helpers, template,
# unittest_wrapper). These confirm that the (tightened) annotations are usable
# with pydantic's dynamic type checking, and document cases that aren't (yet).

def test_general_purpose_aliases():
    """Sanity check of new general-purpose aliases added to validate_arguments_types"""
    @validate_call
    def f(a: va.OptStr = None, b: va.OptInt = None, c: va.OptStrOrBytes = None,
          d: va.OptBoolOrStr = None, e: va.OptStrList = None) -> str:
        """Example function exercising the new Opt* aliases"""
        return f"{a}-{b}-{c!r}-{d}-{e}"
    # Defaults and valid values
    assert f() == "None-None-None-None-None"
    assert f(a="x", b=1, c=b"y", d=True, e=["p", "q"]) == "x-1-b'y'-True-['p', 'q']"
    # Invalid values for each alias
    assert_validation_error(f, a=123)          # OptStr: int not a str
    assert_validation_error(f, b="not-an-int") # OptInt
    assert_validation_error(f, c=1.5)          # OptStrOrBytes
    assert_validation_error(f, e="not-a-list") # OptStrList: str not coerced to List[str]


def test_my_regex_types():
    """validate_call against my_regex.regex_wrapper.compile's AnyStr-based signature"""
    from mezcla.my_regex import my_re
    @validate_call
    def compile_pattern(pattern: AnyStr, flags: int = 0) -> re.Pattern:
        """Wrapper mirroring regex_wrapper.compile"""
        return my_re.compile(pattern, flags)
    assert compile_pattern("abc").match("abc")
    assert compile_pattern(b"abc").match(b"abc")
    assert_validation_error(compile_pattern, 123)


def test_debug_types():
    """validate_call against debug.IntOrTraceLevel and the _to_unicode encoding fix"""
    from mezcla import debug
    @validate_call
    def set_level_wrapper(level: debug.IntOrTraceLevel) -> None:
        """Wrapper mirroring debug.set_level"""
        debug.set_level(level)
    set_level_wrapper(3)
    set_level_wrapper(debug.TL.VERBOSE)
    assert_validation_error(set_level_wrapper, "not-a-level")

    # ## BAD fix: _to_unicode's encoding param was Optional[bool] (see debug.py);
    # now OptStr, matching system.to_unicode/from_unicode.
    @validate_call
    def to_unicode_wrapper(text: str, encoding: va.OptStr = None) -> str:
        """Wrapper mirroring debug._to_unicode"""
        return debug._to_unicode(text, encoding)  # pylint: disable=protected-access
    assert to_unicode_wrapper("hi", encoding="UTF-8") == "hi"
    assert_validation_error(to_unicode_wrapper, "hi", encoding=True)

    ## TODO3: debug.profile_function(frame: FrameType, event: str, arg: Any) -> None
    # types.FrameType has no pydantic-known schema, so validate_call needs
    # config=ConfigDict(arbitrary_types_allowed=True) to decorate this directly
    # (PydanticSchemaGenerationError otherwise). Same applies to debug.trace_frame's
    # frame: Optional[FrameType] parameter.
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def profile_function_wrapper(frame: Any, event: str, arg: Any) -> None:
        """Wrapper mirroring debug.profile_function (needs arbitrary_types_allowed)"""
        debug.profile_function(frame, event, arg)
    profile_function_wrapper(sys._getframe(), "call", None)  # pylint: disable=protected-access


def test_system_types():
    """validate_call against system.ListOrSet and the defaultdict[...] generics"""
    from mezcla import system
    @validate_call
    def intersection_wrapper(list1: List[Any], list2: List[Any], as_set: bool = False) -> system.ListOrSet:
        """Wrapper mirroring system.intersection"""
        return system.intersection(list1, list2, as_set)
    assert sorted(intersection_wrapper([1, 2, 3], [2, 3, 4])) == [2, 3]
    assert intersection_wrapper([1, 2], [2, 3], as_set=True) == {2}
    assert_validation_error(intersection_wrapper, "not-a-list", [1])

    # defaultdict[str, str] / defaultdict[str, bool]: pydantic coerces a plain
    # dict into the proper defaultdict (with the right default_factory), so
    # missing-key lookups still work as in read_lookup_table/lookup_entry.
    @validate_call
    def lookup_entry_wrapper(hash_table: "defaultdict[str, str]", entry: str) -> str:
        """Wrapper mirroring system.lookup_entry"""
        return system.lookup_entry(hash_table, entry)
    assert lookup_entry_wrapper({"fu": "bar"}, "fu") == "bar"
    assert lookup_entry_wrapper({"fu": "bar"}, "missing") == ""

    ## TODO3: system.to_unicode/to_string/from_unicode/to_utf8 are documented as
    # no-ops that return their input unchanged, but typed as (text: str, ...) -> str.
    # html_utils.get_url_param can return a list (StrOrStrList) and passes it
    # through system.to_unicode; if validate_call were applied to to_unicode,
    # such a call would raise ValidationError where today it silently passes
    # the list through. Restructuring (e.g., a TypeVar-based AnyStr/T -> T
    # signature) would be needed before adding validate_call there.
    @validate_call
    def to_unicode_wrapper(text: str, encoding: va.OptStr = None) -> str:
        """Wrapper mirroring system.to_unicode"""
        return system.to_unicode(text, encoding)
    assert to_unicode_wrapper("abc") == "abc"
    assert_validation_error(to_unicode_wrapper, ["a", "b"])


def test_glue_helpers_types():
    """validate_call against the count_it Optional[bool] fix and MatchResult(List) types"""
    from mezcla import glue_helpers as gh
    @validate_call
    def count_it_wrapper(pattern: str, text: str, field: int = 1,
                          multiple: Optional[bool] = None) -> Dict[str, int]:
        """Wrapper mirroring gh.count_it (## BAD fix: multiple was Optional[None])"""
        return dict(gh.count_it(pattern, text, field, multiple))
    assert count_it_wrapper("[a-z]", "Panama") == {"a": 3, "n": 1, "m": 1}
    # A non-bool, non-coercible value for multiple should fail validation
    assert_validation_error(count_it_wrapper, "[a-z]", "Panama", multiple=["x"])

    @validate_call
    def extract_matches_wrapper(pattern: str, lines: List[str]) -> gh.MatchResultList:
        """Wrapper mirroring gh.extract_matches"""
        return gh.extract_matches(pattern, lines)
    assert extract_matches_wrapper(r"^(\S+) \S+", ["John D.", "Plato"]) == ["John"]


def test_html_utils_types():
    """validate_call against html_utils' StrOrStrList and repointed Opt* aliases"""
    from mezcla import html_utils
    # The module's local OptStrBytes/OptBoolStr now alias the shared general
    # types added to validate_arguments_types (see "TODO: reduce redundancy" there)
    assert html_utils.OptStrBytes is va.OptStrOrBytes
    assert html_utils.OptBoolStr is va.OptBoolOrStr

    @validate_call
    def get_url_param_wrapper(name: str, default_value: va.OptStr = None,
                               param_dict: Optional[Dict[str, Any]] = None) -> html_utils.StrOrStrList:
        """Wrapper mirroring html_utils.get_url_param"""
        return html_utils.get_url_param(name, default_value, param_dict)
    assert get_url_param_wrapper("fu", param_dict={"fu": "123"}) == "123"
    assert get_url_param_wrapper("fu", param_dict={"fu": ["123", "321"]}) == ["123", "321"]
    assert_validation_error(get_url_param_wrapper, "fu", param_dict="not-a-dict")


def test_main_types():
    """validate_call against main.ArgValue/OptArgValue and UserArgInfoType/SysArgInfoType"""
    from mezcla import main
    @validate_call
    def convert_option_wrapper(option_spec: main.UserArgInfoType) -> main.UserArgInfoType:
        """Wrapper mirroring main.Main.convert_option's option_spec parameter"""
        return option_spec
    assert convert_option_wrapper("verbose") == "verbose"
    assert convert_option_wrapper(("quiet", "Be quiet")) == ("quiet", "Be quiet")
    assert convert_option_wrapper(("num-eggs", "Number of eggs", 2)) == ("num-eggs", "Number of eggs", 2)
    assert convert_option_wrapper(("files", "File names", ["f1", "f2"], "+")) == ("files", "File names", ["f1", "f2"], "+")
    # An object isn't a valid ArgValue for the tuple's default component
    assert_validation_error(convert_option_wrapper, ("bad", "desc", object()))

    @validate_call
    def convert_option_value_wrapper(_label: str, value: main.ArgValue) -> main.ArgValue:
        """Wrapper mirroring main.Main.convert_option_value"""
        return value
    assert convert_option_value_wrapper("n", "5") == "5"
    assert convert_option_value_wrapper("n", 5) == 5
    assert_validation_error(convert_option_value_wrapper, "n", None)


def test_unittest_wrapper_types(monkeypatch):
    """validate_call against unittest_wrapper's IntOrTraceLevel usage and pytest fixture types"""
    from mezcla import debug
    @validate_call
    def patch_trace_level_wrapper(level: debug.IntOrTraceLevel) -> None:
        """Wrapper mirroring TestWrapper.patch_trace_level"""
        debug.reference_var(level)  # no-op use, just exercises the type
    patch_trace_level_wrapper(debug.VERBOSE)
    assert_validation_error(patch_trace_level_wrapper, "not-a-level")

    ## TODO3: TestWrapper.monkeypatch_fixture/capsys_fixture are typed using
    # pytest.MonkeyPatch/pytest.CaptureFixture, which (like FrameType above) have
    # no pydantic-known schema. validate_call would need
    # config=ConfigDict(arbitrary_types_allowed=True) if applied to these methods.
    @validate_call(config=ConfigDict(arbitrary_types_allowed=True))
    def monkeypatch_type_wrapper(mp: pytest.MonkeyPatch) -> bool:
        """Wrapper mirroring TestWrapper.monkeypatch_fixture (needs arbitrary_types_allowed)"""
        return isinstance(mp, pytest.MonkeyPatch)
    assert monkeypatch_type_wrapper(monkeypatch)


def test_template_types():
    """validate_call against template.Helper's Any-typed placeholder methods"""
    from mezcla import template
    @validate_call
    def helper_process_wrapper(_arg: Any) -> bool:
        """Wrapper mirroring template.Helper.process"""
        return template.Helper().process(_arg)
    # Any accepts arbitrary inputs without validation errors
    assert helper_process_wrapper("text") is False
    assert helper_process_wrapper(123) is False


if __name__ == "__main__":
    pytest.main()
