#! /usr/bin/env python3
#
# Tests for validate_arguments_types module
#

"""
Tests for validate_arguments_types module
"""

import pytest
from pydantic import ValidationError, validate_call
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

if __name__ == "__main__":
    pytest.main()
