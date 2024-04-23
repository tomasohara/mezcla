# Test for the extended_validation.py module

"""
Test for the extended_validation.py module
"""

import pytest
from pydantic import ValidationError, BaseModel, validate_call
import mezcla.extended_validation as ev

# Functions to test

@validate_call
@ev.validate_dictionaries()
def trivial_dict_parameter(some_dict: dict) -> None:
    """Example of simple dictionary validation"""
    assert isinstance(some_dict, dict), "The validation should fail before this"
    print("@custom_validate_call works!")
    return True

class ExpectedDictModel(BaseModel):
    """Expected dictionary model"""
    example_key: str

@validate_call
@ev.validate_dictionaries(some_dict = ExpectedDictModel)
def example_dict_keys_values(some_dict: dict) -> None:
    """Example validating keys and values of a dictionary"""
    assert isinstance(some_dict, dict), "The validation should fail before this"
    assert isinstance(some_dict.get("example_key"), str), "The validation should fail before this"
    print("@custom_validate_call works!")
    return True

class WrongModel:
    """(Not a Pydantic model child)"""
    example_key: str

@validate_call
@ev.validate_dictionaries(some_dict = WrongModel)
def example_wrong_model(some_dict: dict) -> None:
    """Example of wrong model passed to custom_validate_call"""
    raise AssertionError("The validation should fail before this")

# Start of tests

def assert_validation_error(func, *args, **kwargs):
    """Asserts that a function raises a ValidationError"""
    with pytest.raises(ValidationError) as exc_info:
        func(*args, **kwargs)
    assert "For further information visit" in str(exc_info.value)

def test_trivial_dict_parameter():
    """Test for trivial_dict_parameter"""
    assert trivial_dict_parameter({})
    assert trivial_dict_parameter({"a": 1, "b": 2})
    assert_validation_error(trivial_dict_parameter, 12345)
    assert_validation_error(trivial_dict_parameter, True)

def test_dict_key():
    """Test for dictionary key validation"""
    assert example_dict_keys_values({"example_key": "some random string"})
    assert_validation_error(example_dict_keys_values, {})
    assert_validation_error(example_dict_keys_values, {"example_wrong_key": "some random string"})
    assert_validation_error(example_dict_keys_values, 12345)
    assert_validation_error(example_dict_keys_values, True)

def test_dict_value():
    """Test for dictionary value validation"""
    assert example_dict_keys_values({"example_key": "some random string"})
    assert_validation_error(example_dict_keys_values, {"example_key": 12345})
    assert_validation_error(example_dict_keys_values, {"example_key": True})
    assert_validation_error(example_dict_keys_values, {"example_key": False})
    assert_validation_error(example_dict_keys_values, {"example_key": {"a": 1, "b": 2}})

def test_wrong_model():
    """Test for wrong model"""
    with pytest.raises(AssertionError) as exc_info:
        example_wrong_model({})
    assert "must be a pydantic.BaseModel class" in str(exc_info.value)

# Run the tests

if __name__ == "__main__":
    pytest.main()
