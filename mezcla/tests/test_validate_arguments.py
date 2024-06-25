#! /usr/bin/env python
#
# Tests for validate_arguments module
#

"""
Tests for validate_arguments module
"""

# Standard modules
import os

# Installed packages
import pytest
from pydantic import ValidationError, BaseModel, validate_call

# Local packages
from mezcla import system
import mezcla.validate_arguments as va
from mezcla.unittest_wrapper import TestWrapper
from mezcla import glue_helpers as gh

# Constants
THIS_DIR = os.path.dirname(os.path.abspath(__file__))
RESOURCES_DIR = os.path.join(THIS_DIR, "resources")
SIMPLE_SCRIPT = os.path.join(RESOURCES_DIR, "simple_script.py")
SIMPLE_SCRIPT_DECORATED = os.path.join(RESOURCES_DIR, "simple_script_decorated.py")
SIMPLE_WRONG_SCRIPT = os.path.join(RESOURCES_DIR, "simple_script_with_wrong_types.py")

def assert_validation_error(func, *args, **kwargs):
    """Asserts that a function raises a ValidationError"""
    with pytest.raises(ValidationError) as exc_info:
        func(*args, **kwargs)
    assert "For further information visit" in str(exc_info.value)

class ExpectedDictModel(BaseModel):
    """Expected dictionary model"""
    example_key: str

@validate_call
@va.validate_dictionaries(some_dict = ExpectedDictModel)
def example_dict_keys_values(some_dict: dict) -> bool:
    """Example validating keys and values of a dictionary"""
    assert isinstance(some_dict, dict), "The validation should fail before this"
    assert isinstance(some_dict.get("example_key"), str), "The validation should fail before this"
    print("@custom_validate_call works!")
    return True

def test_trivial_dict_parameter():
    """Test for trivial_dict_parameter"""
    # Function to test
    @validate_call
    @va.validate_dictionaries()
    def trivial_dict_parameter(some_dict: dict) -> bool:
        """Example of simple dictionary validation"""
        assert isinstance(some_dict, dict), "The validation should fail before this"
        print("@custom_validate_call works!")
        return True
    # Tests
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
    # Class model to test
    class WrongModel:
        """(Not a Pydantic model child)"""
        example_key: str
    # Function to test
    @validate_call
    @va.validate_dictionaries(some_dict = WrongModel)
    def example_wrong_model(some_dict: dict) -> None:
        """Example of wrong model passed to custom_validate_call"""
        raise AssertionError("The validation should fail before this")
    # Test
    with pytest.raises(AssertionError) as exc_info:
        example_wrong_model({})
    assert "must be a pydantic.BaseModel class" in str(exc_info.value)

def test_add_validate_call_decorator():
    """Test for add_validate_call_decorator"""
    code = system.read_file(SIMPLE_SCRIPT)
    expected_output_code = system.read_file(SIMPLE_SCRIPT_DECORATED)
    assert va.add_validate_call_decorator(code) == expected_output_code

class TestValidateArgument(TestWrapper):
    """Class for testcase definition"""
    script_file = TestWrapper.get_module_file_path(__file__)
    script_module = TestWrapper.get_testing_module_name(__file__)

    def test_simple_script(self):
        """Run validate arguments on a simple script"""
        script_output = self.run_script(
            options=f"--output {self.temp_file}",
            data_file=SIMPLE_SCRIPT,
        )
        # Check script output
        assert script_output, 'script output is empty'
        assert "Hello, World!" in script_output
        # Check decorated script output
        expected_output = system.read_file(SIMPLE_SCRIPT_DECORATED)
        current_output = system.read_file(self.temp_file)
        assert current_output, 'current output is empty'
        assert current_output == expected_output

    def test_wrong_script(self):
        """Run validate arguments on a wrong script"""
        script_output = self.run_script(
            data_file=SIMPLE_WRONG_SCRIPT,
        )
        assert script_output, 'script output is empty'
        assert "further information visit" in script_output

if __name__ == "__main__":
    pytest.main()
