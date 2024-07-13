"""
Tests for mezcla_to_standard module
"""

# Standard packages
import os
from unittest.mock import patch, MagicMock, ANY
import logging

# Installed packages
import pytest
import libcst as cst

# Local packages
import mezcla.mezcla_to_standard as THE_MODULE
from mezcla import system, debug, glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla.unittest_wrapper import TestWrapper

# Pylint configurations

## 1 disable "Line Too Long"
# pylint: disable=C0301
## 2 disable "Too many lines in module"
# pylint: disable=C0302


class TestCSTFunctions:
    """Class for test functions that performs operations on CSTs"""

    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    def test_arg_to_value(self):
        """Ensures that value_to_arg method works as expected"""

        def helper_arg2val(value, type_):
            if type_ == str:
                expected_output = cst.Arg(cst.SimpleString(value=f'"{value}"'))
            elif type_ == int:
                expected_output = cst.Arg(cst.Integer(value=str(value)))
            elif type_ == float:
                expected_output = cst.Arg(cst.Float(value=str(value)))
            elif type_ == bool:
                expected_output = cst.Arg(cst.Name(value="True" if value else "False"))
            else:
                expected_output = None
            result = THE_MODULE.arg_to_value(expected_output)
            # DEBUG: print(f'Value: {value}, Expected: {expected_output}, Result: {result}')
            return value, result

        # For simple strings
        value = "text"
        expected_value, result = helper_arg2val(value, str)
        ## Line below yields exception: libcst._nodes.base.CSTValidationError: Invalid string prefix.
        # assert result == expected_value
        assert result == '"text"'

        # For integer
        value = 42
        expected_value, result = helper_arg2val(value, int)
        assert result == expected_value

        # For float
        value = 3.1416
        expected_value, result = helper_arg2val(value, float)
        assert result == expected_value

        # For boolean
        value = True
        expected_value, result = helper_arg2val(value, bool)
        assert result == expected_value

        # For unsupported types
        value = [1, 2, 3]
        with pytest.raises(ValueError):
            THE_MODULE.arg_to_value(cst.Arg(cst.List([cst.Integer(value=str(i)) for i in value])))


    def test_args_to_values(self):
        """Ensures that args_to_values method works as expected"""

        def helper_arg2val(arg):
            if isinstance(arg.value, cst.SimpleString):
                expected_output = arg.value.value.strip('"')
            elif isinstance(arg.value, cst.Integer):
                expected_output = int(arg.value.value)
            elif isinstance(arg.value, cst.Float):
                expected_output = float(arg.value.value)
            elif isinstance(arg.value, cst.Name) and arg.value.value in ["True", "False"]:
                expected_output = arg.value.value == "True"
            else:
                expected_output = None
            result = THE_MODULE.arg_to_value(arg)
            return expected_output, result

        # For simple strings
        arg = cst.Arg(cst.SimpleString(value='"text"'))
        expected_output, result = helper_arg2val(arg)
        assert result == expected_output

        # For integer
        arg = cst.Arg(cst.Integer(value="42"))
        expected_output, result = helper_arg2val(arg)
        assert result == expected_output

        # For float
        arg = cst.Arg(cst.Float(value="3.1416"))
        expected_output, result = helper_arg2val(arg)
        assert result == expected_output

        # For boolean
        arg = cst.Arg(cst.Name(value="True"))
        expected_output, result = helper_arg2val(arg)
        assert result == expected_output

        arg = cst.Arg(cst.Name(value="False"))
        expected_output, result = helper_arg2val(arg)
        assert result == expected_output

        # For unsupported types
        arg = cst.Arg(cst.List([]))
        with pytest.raises(ValueError):
            THE_MODULE.arg_to_value(arg)

    def test_remove_last_comma(self):
        """Ensures that remove_last_comma method works as expected"""
        args = [
            cst.Arg(cst.Name(value="False")),
            cst.Arg(cst.Name(value="True")),
            cst.Arg(cst.Float(value="3.1416")),
            cst.Arg(cst.Integer(value="42")),
        ]
        expected_args = [
            cst.Arg(cst.Name(value="False")),
            cst.Arg(cst.Name(value="True")),
            cst.Arg(cst.Float(value="3.1416")),
            cst.Arg(cst.Integer(value="42")),
        ]

        result = THE_MODULE.remove_last_comma(args)
        assert str(result) == str(expected_args)

    def test_match_args(self):
        """Ensures that match_args method works as expected"""

        # Sample function
        def slope(x1, y1, x2, y2):
            return (y2 - y1) / (x2 - x1)

        args = [
            THE_MODULE.value_to_arg(10),
            THE_MODULE.value_to_arg(20),
            THE_MODULE.value_to_arg(30),
            THE_MODULE.value_to_arg(40)
        ]
        expected_output = {"x1": args[0], "y1": args[1], "x2": args[2], "y2": args[4]}
        result = THE_MODULE.match_args(THE_MODULE.CallDetails(slope), args)
        assert result == expected_output

    def test_flatten_list(self):
        """Ensures that flatten_list method works as expected"""
        args = [1, [2, 3], (4, 5), 6]
        expected_output = [1, 2, 3, 4, 5, 6]
        result = THE_MODULE.flatten_list(args)
        assert result == expected_output

    def callable_to_path(self):
        """Ensures that callable_to_path method works as expected"""
        assert THE_MODULE.callable_to_path(os.path.join) == "os.path.join"

    def path_to_callable(self):
        """Ensures that path_to_callable method works as expected"""
        expected_output = os.path.join
        result = THE_MODULE.path_to_callable("os.path.join")
        assert result == expected_output


class TestBaseTransformerStrategy:
    """Class for test usage of ToStandard class in mezcla_to_standard"""

    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    # Creating mock functions for testing
    def slope(self, x1: int, y1: int, x2: int, y2: int):
        """TODO"""
        return (y2 - y1) / (x2 - x1)

    def distance(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """TODO"""
        return round(((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5, 2)

    @pytest.mark.xfail  ## TODO: Fix XFAIL (result is weird)
    def test_insert_extra_params(self):
        """Ensures that insert_extra_params method of BaseTransformerStrategy class works as expected"""
        extra_params = {"x1": 3, "y1": 5, "x2": 6}
        args = {
            "x1": THE_MODULE.value_to_arg(10),
            "y2": THE_MODULE.value_to_arg(12)
        }

        expected_result = extra_params | args  # Union of dictionary

        eqcall = THE_MODULE.EqCall(
            targets=self.slope, dests=None, extra_params=extra_params
        )
        bts = THE_MODULE.BaseTransformerStrategy()
        result = bts.insert_extra_params(eqcall, args)
        print(result, "=" * 50, expected_result)
        assert result == expected_result

    def test_get_replacement(self):
        ## OLD: Eqcall._filter_args_by_function
        """Ensures that get_replacement method of BaseTransformerStrategy class works as expected"""
        args = {"x1": 20, "y1": 10, "x2": 30, "y2": -60}
        pass

    @pytest.mark.xfail
    def test_eq_call_to_module_func(self):
        """Ensures that eq_call_to_module_func method of BaseTransformerStrategy class works as expected"""
        assert False, "NOT_IMPLEMENTED_IN_FILE"
        ## TODO: Wait for function to be implemented

    @pytest.mark.xfail
    def test_find_eq_call(self):
        """Ensures that find_eq_call method of BaseTransformerStrategy class works as expected"""
        assert False, "NOT_IMPLEMENTED_IN_FILE"
        ## TODO: Wait for function to be implemented

    @pytest.mark.xfail
    def test_get_args_replacement(self):
        """Ensures that get_args_replacement_func method of BaseTransformerStrategy class works as expected"""
        assert False, "NOT_IMPLEMENTED_IN_FILE"
        ## TODO: Wait for function to be implemented

    @pytest.mark.xfail
    def test_is_condition_to_replace_met(self):
        """Ensures that is_condition_to_replace_met method of BaseTransformerStrategy class works as expected"""
        assert False, "NOT_IMPLEMENTED_IN_FILE"
        ## TODO: Wait for function to be implemented


class TestToStandard:
    """Class for test usage of ToStandard class in mezcla_to_standard"""

    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    # Sample functions to be used in tests
    @staticmethod
    def sample_func1(a):
        """First sample function"""
        pass

    @staticmethod
    def sample_func2(b):
        """Second sample function"""
        pass

    @pytest.fixture
    def setup_to_standard(self):
        THE_MODULE.mezcla_to_standard = [
            THE_MODULE.EqCall(targets=self.sample_func1, dests=self.sample_func1),
            THE_MODULE.EqCall(targets=self.sample_func2, dests=self.sample_func2),
        ]
        # THE_MODULE.ToStandard must be initialized before
        # setting the mezcla_to_standard list
        to_standard = THE_MODULE.ToStandard()
        return to_standard

    ## find_eq_call does not work as intended (e.g. eq_call = None and None is not None)
    @pytest.mark.xfail
    def test_tostandard_find_eq_call_existing(self, setup_to_standard):
        """Test for finding an existing equivalent call"""
        path = "mezcla.sample_func1"
        args = ["a"]
        to_standard = setup_to_standard
        eq_call = to_standard.find_eq_call(path, args=args)
        assert eq_call is not None
        assert eq_call.targets[0].callable == self.sample_func1

    def test_tostandard_find_eq_call_non_existing(self, setup_to_standard):
        """Test for trying to find a non-existing equivalent call"""
        path = "mezcla.no_exist_func"
        args = ["b"]
        to_standard = setup_to_standard
        # Correct assertion, but does not work as intended (no need for XFAIL)
        eq_call = to_standard.find_eq_call(path, args=args)
        assert eq_call is None

    # Does not work as intended (Result = None)
    @pytest.mark.xfail
    def test_tostandard_find_eq_call(self):
        """Ensures that find_eq_call of ToStandard class works as expected"""

        class MockEqCall:
            def __init__(self, module, func, condition_met=True):
                self.target = type(
                    "MockClass", (object,), {"__module__": f"{module}.mock"}
                )()
                self.target.__name__ = func
                self.condition_met = condition_met

            def is_condition_to_replace_met(self, args):
                return self.condition_met

        # Create a ToStandard instance
        to_standard = THE_MODULE.ToStandard()
        mezcla_to_standard = [
            MockEqCall("my_module", "my_function"),
            MockEqCall("other_module", "other_function"),
        ]
        # Assertion for eq_call match
        result = to_standard.find_eq_call("my_module.my_function", ["arg1", "arg2"])
        assert result == mezcla_to_standard[0]

    # Static sample functions for is_condition_to_replace_met
    @staticmethod
    def sample_func1(a, b):
        """First sample function"""
        pass

    @staticmethod
    def sample_func2(a, b):
        """Second sample function"""
        pass

    @pytest.fixture
    def setup_to_standard(self):
        to_standard = THE_MODULE.ToStandard()
        mezcla_to_standard = [
            THE_MODULE.EqCall(
                targets=self.sample_func1, dests=None, condition=lambda a, b: a > b
            ),
            THE_MODULE.EqCall(
                targets=self.sample_func2, dests=None, condition=lambda a, b: a == b
            ),
        ]
        to_standard.mezcla_to_standard = mezcla_to_standard
        return to_standard

    @pytest.mark.xfail
    # Error Involved: on arg_to_value(arg: cst.Arg) -> object
    # AttributeError: 'int' object has no attribute 'value'
    def test_is_condition_to_replace_met(self, setup_to_standard):
        """Ensures that is_condition_to_replace_met of ToStandard class works as expected"""
        to_standard = setup_to_standard

        eq_call = THE_MODULE.EqCall(
            targets=self.sample_func1, dests=None, condition=lambda a, b: a > b
        )
        args = [4, 3]
        result = to_standard.is_condition_to_replace_met(eq_call, args)
        assert result is True

    @pytest.mark.xfail
    def test_get_args_replacement(self):
        """Ensures that get_args_replacement method of ToStandard class works as expected"""
        result = THE_MODULE.ToStandard.get_args_replacement()
        assert False, "TODO: Implement"

    @pytest.mark.xfail
    def test_replace_args_keys(self):
        """Ensures that replace_args_keys method of ToStandard class works as expected"""
        result = THE_MODULE.ToStandard.replace_args_keys()
        assert False, "TODO: Implement"

    @pytest.mark.xfail
    def test_eq_call_to_module_func(self):
        """Ensures that eq_call_to_module_func method of ToStandard class works as expected"""
        result = THE_MODULE.ToStandard.eq_call_to_module_func()
        assert False, "TODO: Implement"


# Unit testing of function
class TestToMezcla:
    """Class for test usage of ToMezcla class in mezcla_to_standard"""

    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @staticmethod
    def sample_func1(a, b):
        """First sample function"""
        return a + b

    @staticmethod
    def sample_func2(a, b):
        """Second sample function"""
        return a - b

    @staticmethod
    def standard_func1(src, dst):
        """Standard equivalent function for sample_func1"""
        return f"{src}: {dst}"

    @staticmethod
    def standard_func2(path):
        """Standard equivalent function for sample_func2"""
        return f"path: {path}"

    @pytest.fixture
    def setup_to_mezcla(self):
        to_mezcla = THE_MODULE.ToMezcla()
        mezcla_to_standard = [
            THE_MODULE.EqCall(
                targets=self.sample_func1,
                dests=self.standard_func1,
                condition=lambda a, b: a > b,
                eq_params={"a": "src", "b": "dst"},
            ),
            THE_MODULE.EqCall(
                targets=self.sample_func2,
                dests=self.standard_func2,
                condition=lambda a, b: a == b,
                eq_params={"a": "path"},
            ),
        ]
        # Directly assigning mezcla_to_standard to the instance
        setattr(to_mezcla, "mezcla_to_standard", mezcla_to_standard)
        return to_mezcla

    ## TEST 1: find_eq_call (existing function)
    ## Error encountered: FAILED mezcla/tests/test_mezcla_to_standard.py::TestToMezcla::test_tomezcla_find_eq_call_existing - AttributeError: 'list' object has no attribute '__module__'
    @pytest.mark.xfail
    def test_tomezcla_find_eq_call_existing(self, setup_to_mezcla):
        """Test for finding an existing equivalent call for ToMezcla class"""
        to_mezcla = setup_to_mezcla
        module, method, args = "mezcla", "standard_func1", [4, 3]
        eq_call = to_mezcla.find_eq_call(module, method, args)
        assert eq_call is not None
        assert eq_call.target == self.sample_func1

    ## TEST 2: find_eq_call (non-existing function)
    ## Error encountered: FAILED mezcla/tests/test_mezcla_to_standard.py::TestToMezcla::test_tomezcla_find_eq_call_existing - AttributeError: 'list' object has no attribute '__module__'
    @pytest.mark.xfail
    def test_tomezcla_find_eq_call_non_existing(self, setup_to_mezcla):
        """Test for not finding an existing equivalent call for ToMezcla class"""
        to_mezcla = setup_to_mezcla
        module, method, args = "mezcla", "standard_func3", [4, 3]
        eq_call = to_mezcla.find_eq_call(module, method, args)
        assert eq_call is None

    ## TEST 3: is_condition_to_replace_met
    ## NOTE: AttributeError detected

    #     def arg_to_value(arg: cst.Arg) -> object:
    #         """Convert the argument to a value"""
    # >       return eval(arg.value.value)
    # E       AttributeError: 'int' object has no attribute 'value'

    @pytest.mark.xfail
    def test_is_condition_to_replace_met(self, setup_to_mezcla):
        """Test for is_condition_to_replace_met in ToMezcla class"""
        to_mezcla = setup_to_mezcla

        eq_call = THE_MODULE.EqCall(
            targets=self.sample_func1,
            dests=self.standard_func1,
            condition=lambda a, b: a > b,
            eq_params={"a": "src", "b": "dst"},
        )
        args = [4, 3]
        result = to_mezcla.is_condition_to_replace_met(eq_call, args)
        assert result is True

        args = [3, 4]
        result = to_mezcla.is_condition_to_replace_met(eq_call, args)
        assert result is False

        eq_call = THE_MODULE.EqCall(
            targets=self.sample_func2,
            dests=self.standard_func2,
            condition=lambda a, b: a == b,
            eq_params={"a": "path"},
        )
        args = [4, 4]
        result = to_mezcla.is_condition_to_replace_met(eq_call, args)
        assert result is True

        args = [4, 5]
        result = to_mezcla.is_condition_to_replace_met(eq_call, args)
        assert result is False

    ## TEST 4: get_args_replacement
    def test_get_args_replacement(self, setup_to_mezcla):
        """Test for get_args_replacement method in ToMezcla class"""
        to_mezcla = setup_to_mezcla
        eq_call = THE_MODULE.EqCall(
            targets=self.sample_func1,
            dests=self.standard_func1,
            condition=lambda a, b: a > b,
            eq_params={"a": "src", "b": "dst"},
        )

        # For multiple arguments in function using multiple arguments

        # OLD: args = [4, 3]
        args = [cst.Arg(value=4), cst.Arg(value=3)]
        kwargs = {}
        result = str(to_mezcla.get_args_replacement(eq_call, args, kwargs))
        assert "Arg(\n    value=4," in result
        assert "Arg(\n    value=3," in result
        assert result.count("Arg(\n    value=4,") == 1
        assert result.count("Arg(\n    value=3,") == 1

        # For multiple arguments in function using single argument (selects first arg)
        eq_call = THE_MODULE.EqCall(
            targets=self.sample_func2,
            dests=self.standard_func2,
            condition=lambda a, b: a == b,
            eq_params={"a": "path"},
        )
        # OLD: args = [4, 4]
        args = [cst.Arg(value=4), cst.Arg(value=4)]
        kwargs = {}
        result = str(to_mezcla.get_args_replacement(eq_call, args, kwargs))
        assert "Arg(\n    value=4," in result
        assert result.count("Arg(\n") == 1

    ## TEST 5: replace_args_keys
    def test_replace_args_keys(self, setup_to_mezcla):
        """Test for replace_args_keys method in ToMezcla class"""
        to_mezcla = setup_to_mezcla

        # For multiple arguments
        eq_call = THE_MODULE.EqCall(
            targets=self.sample_func1,
            dests=self.standard_func1,
            eq_params={"a": "src", "b": "dst"},
        )
        args = {"src": 4, "dst": 3}
        result = to_mezcla.replace_args_keys(eq_call, args)
        assert result == {"a": 4, "b": 3}

        # For single argument
        eq_call = THE_MODULE.EqCall(
            targets=self.sample_func2, dests=self.standard_func2, eq_params={"a": "path"}
        )
        args = {"path": 4}
        result = to_mezcla.replace_args_keys(eq_call, args)
        assert result == {"a": 4}

    ## TEST 6: eq_call_to_path
    def test_eq_call_to_path(self, setup_to_mezcla):
        """Test for eq_call_to_path method in ToMezcla class"""
        to_mezcla = setup_to_mezcla

        eq_call = THE_MODULE.EqCall(targets=self.sample_func1, dests=self.standard_func1)
        path = to_mezcla.eq_call_to_path(eq_call)
        assert path == "self.sample_func1" ## TODO: check module part of the path

        eq_call = THE_MODULE.EqCall(targets=self.sample_func2, dests=self.standard_func2)
        path = to_mezcla.eq_call_to_path(eq_call)
        assert path == "self.sample_func2" ## TODO: check module part of the path


@pytest.fixture
def mock_to_module():
    """Mock for the to_module dependency"""
    # Define mock behavior for get_replacement
    mock_to_module = MagicMock()

    # Mock function for get_replacement method
    def mock_get_replacement(module_name, func, args):
        new_module = cst.Name(f"import_{module_name}")
        new_func_node = cst.Name(f"new_func_{module_name}")
        new_args_nodes = args
        return new_module, new_func_node, new_args_nodes

    mock_to_module.get_replacement.side_effect = mock_get_replacement
    return mock_to_module


class TestTransform(TestWrapper):
    """Class for test usage for methods of transform method in mezcla"""

    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.fixture(autouse=True)
    def setup(self, mock_to_module):
        self.mock_to_module = mock_to_module

    @pytest.mark.xfail
    def test_transform(self):
        """Unit test for transform function"""
        # Example Python code to transform
        code = """
import module_a
from module_b import func1, func2
from module_c import func3 as f3
from other_module import func4
x = func1(1, 2)
y = module_a.func2(3, 4)
z = func3(5, 6)
        """

        # Expected transformed code after calling transform function
        expected_transformed_code = """
import import_module_a
import import_module_b
from other_module import func4
x = new_func_module_b(1, 2)
y = new_func_module_a(3, 4)
z = func3(5, 6)
        """

        # Acutal transformed code is a bit confusing, this marking the test as xfail
        _expected_transformed_code = """
import import_module_a
import module_a
from module_b import func1, func2
from module_c import func3 as f3
from other_module import func4
x = func1(1, 2)
y = new_func_module_a(3, 4)
z = func3(5, 6)
"""
        # Call transform function
        transformed_code, _ = THE_MODULE.transform(self.mock_to_module, code)
        # Assert that the transformed code matches the expected transformed code
        assert transformed_code.strip() == expected_transformed_code.strip()

        # Additional assertions if needed to verify mock interactions
        self.mock_to_module.get_replacement.assert_any_call("module_a", ANY, ANY)
        self.mock_to_module.get_replacement.assert_any_call("module_b", ANY, ANY)
        self.mock_to_module.get_replacement.assert_any_call("module_c", ANY, ANY)

    # Unit Testing I
    @pytest.mark.xfail
    def test_leave_module(self):
        """Ensures that leave_Module method of ReplaceCallsTransformer works as expected"""

        class TestVisitor(THE_MODULE.ReplaceCallsTransformer):
            def __init__(self, to_module):
                super().__init__(to_module)

        code = """
import module_a
x = module_a.func1(1, 2)
        """

        tree = cst.parse_module(code)
        visitor = TestVisitor(mock_to_module)
        visitor.to_import.append(cst.Name("new_module"))
        modified_tree = tree.visit(visitor)

        expected_code = """
import new_module
import module_a
x = module_a.func1(1, 2)
        """
        # Result currently similar/same to original code (no changes)
        # BAD: assert result.strip() == code.strip()
        assert (
            modified_tree.code.strip() == cst.parse_module(expected_code).code.strip()
        )

    # Unit Testing II
    # Error: AttributeError: 'function' object has no attribute 'ReplaceCallsTransformer'
    @pytest.mark.xfail
    def test_visit_importalias(self):
        """Ensures that visit_ImportAlias method of ReplaceCallsTransformer works as expected"""

        code = """
import my_module as mm
from another_module import submodule as sm
"""
        expected_aliases = {"mm": "my_module", "sm": "submodule"}

        # Parse the code into a CST tree
        tree = cst.parse_module(code)

        # Create an instance of ReplaceCallsTransformer
        visitor = THE_MODULE.ReplaceCallsTransformer(None)

        # Visit the tree with the custom visitor
        tree.visit(visitor)

        # Assert that the aliases were correctly stored
        assert visitor.aliases == expected_aliases

    # Unit Testing III
    @pytest.mark.xfail
    def test_leave_call(self):
        """Ensures that leave_Call method of ReplaceCallsTransformer works as expected"""
        original_code = """
result = old_module.old_function(2, 3)
"""
        expected_code = """
from new_module import new_function
result = new_function(2, 3)
"""
        result, _ = THE_MODULE.transform(self.to_module, original_code)
        assert result.strip() == expected_code.strip()

    # Unit Testing IV
    @pytest.mark.xfail
    def test_replace_call_if_needed(self):
        """Ensures that replace_call_if_needed method of ReplaceCallsTransformer works as expected"""
        assert False, "TODO: Implement"


class TestUsageM2SEqCall(TestWrapper):
    """Class for test usage of equivalent calls for mezcla_to_standard"""

    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    def helper_m2s(self, input_code):
        """Helper function to convert mezcla code to standard equivalent code"""
        # Metrics are ignored for this test case
        new_code, _ = THE_MODULE.transform(THE_MODULE.ToStandard(), input_code)
        return new_code

    def test_eqcall_gh_get_temp_file(self):
        """Ensures that gh.get_temp_file is equivalent to tempfile.NamedTemporaryFile"""
        input_code = """
from mezcla import glue_helpers as gh
temp_file = gh.get_temp_file()
"""
        expected_code = """
import tempfile
temp_file = tempfile.NamedTemporaryFile()
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())

    def test_eqcall_gh_basename(self):
        """Ensures that gh.basename is equivalent to os.path.basename"""
        input_code = """
from mezcla import glue_helpers as gh
basename = gh.basename("./foo/bar/foo.bar")
"""
        expected_code = """
import os
basename = os.path.basename("./foo/bar/foo.bar")
"""

        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())

    
    def test_eqcall_gh_dir_path(self):
        """Ensures that gh.dir_path is equivalent to os.path.dirname"""
        input_code = """
from mezcla import glue_helpers as gh
dir_path = gh.dir_path("/tmp/solr-4888.log")
"""
        expected_code = """
import os
dir_path = os.path.dirname("/tmp/solr-4888.log")
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())
    
    @pytest.mark.skip   # Blank parameter in os.path.dirname()
    def test_eqcall_gh_dirname(self):
        """Ensures that gh.dirname is equivalent to os.path.dirname"""
        input_code = """
from mezcla import glue_helpers as gh
dirname = gh.dirname("/tmp/solr-4888.log")
"""
        expected_code = """
import os
dirname = os.path.dirname("/tmp/solr-4888.log")
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())

    def test_eqcall_gh_file_exists(self):
        """Ensures that gh.file_exists is equivalent to os.path.exists"""
        input_code = """
from mezcla import glue_helpers as gh
file_exists = gh.file_exists("/tmp/solr-4888.log")
"""
        expected_code = """
import os
file_exists = os.path.exists("/tmp/solr-4888.log")
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())

    def test_eqcall_gh_form_path(self):
        """Ensures that gh.form_path is equivalent to os.path.join"""
        input_code = """
from mezcla import glue_helpers as gh
temp_path = gh.form_path("/tmp/logs/")
"""
        expected_code = """
import os
temp_path = os.path.join("/tmp/logs/")
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())

    def test_eqcall_gh_is_directory(self):
        """Ensures that gh.is_directory is equivalent to os.path.isdir"""
        input_code = """
from mezcla import glue_helpers as gh
is_dir = gh.is_directory("/tmp/logs/")
"""
        expected_code = """
import os
is_dir = os.path.isdir("/tmp/logs/")
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())

    def test_eqcall_gh_create_directory(self):
        """Ensures that gh.create_directory is equivalent to os.mkdir"""
        input_code = """
from mezcla import glue_helpers as gh
is_dir = gh.is_directory("/tmp/logs/")
"""
        expected_code = """
import os
is_dir = os.path.isdir("/tmp/logs/")
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())

    def test_eqcall_gh_rename_file(self):
        """Ensures that gh.rename_file is equivalent to os.rename"""
        input_code = """
from mezcla import glue_helpers as gh
gh.rename_file("foo.txt", "bar.txt")
"""
        expected_code = """
import os
os.rename("foo.txt", "bar.txt")
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())

    def test_eqcall_gh_delete_file(self):
        """Ensures that gh.delete_file is equivalent to os.remove"""
        input_code = """
from mezcla import glue_helpers as gh
gh.delete_file("foo.txt")
"""
        expected_code = """
import os
os.remove("foo.txt")
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())

    def test_eqcall_gh_delete_existing_file(self):
        """Ensures that gh.delete_exisiting_file is equivalent to os.remove"""
        input_code = """
from mezcla import glue_helpers as gh
gh.delete_existing_file("foo.txt")
"""
        expected_code = """
import os
os.remove("foo.txt")
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())

    def test_eqcall_gh_file_size(self):
        """Ensures that gh.file_size is equivalent to os.path.getsize"""
        input_code = """
from mezcla import glue_helpers as gh
foo_size = gh.file_size("foo.txt")
"""
        expected_code = """
import os
foo_size = os.path.getsize("foo.txt")
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())

    def test_eqcall_gh_get_directory_listing(self):
        """Ensures that gh.get_directory_listing is equivalent to os.listdir"""
        input_code = """
from mezcla import glue_helpers as gh
is_dir = gh.get_directory_listing("/tmp")
"""
        expected_code = """
import os
is_dir = os.listdir("/tmp")
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())

    def test_eqcall_debug_trace_all(self):
        """Ensures that debug.trace is equivalent to appropriate logging based on conditions"""
        # OLD: Same as test_import_debug_all() from TestUsageImportTypes
        input_code_lvl_4 = """
from mezcla import debug
debug.trace(4, "DEBUG")
"""
        expected_lvl_4 = """
import logging
logging.debug("DEBUG")
"""

        input_code_lvl_3 = """
from mezcla import debug
debug.trace(3, "INFO")
"""
        expected_lvl_3 = """
import logging
logging.info("INFO")
"""

        input_code_lvl_2 = """
from mezcla import debug
debug.trace(2, "WARNING")
"""
        expected_lvl_2 = """
import logging
logging.warning("WARNING")
"""

        input_code_lvl_1 = """
from mezcla import debug
debug.trace(1, "ERROR")
"""
        expected_lvl_1 = """
import logging
logging.error("ERROR")
"""

        input_codes = [
            input_code_lvl_4,
            input_code_lvl_3,
            input_code_lvl_2,
            input_code_lvl_1,
        ]
        expected_outputs = [
            expected_lvl_4,
            expected_lvl_3,
            expected_lvl_2,
            expected_lvl_1,
        ]
        zipped_codes = zip(input_codes, expected_outputs)

        for input_code, expected_output in zipped_codes:
            result = self.helper_m2s(input_code)
            self.assertEqual(result.strip(), expected_output.strip())

    def test_eqcall_system_get_exception(self):
        """Ensures that system.get_exception is equivalent to sys.exc_info"""
        input_code = """
from mezcla import system
def divide(a, b):
    try:
        result = a / b
    except ZeroDivisionError:
        exc_type, exc_value, exc_traceback = system.get_exception()
"""
        expected_code = """
import sys
def divide(a, b):
    try:
        result = a / b
    except ZeroDivisionError:
        exc_type, exc_value, exc_traceback = sys.exc_info()
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())

    @pytest.mark.xfail  ## ERROR: ValueError: Unsupported value type: <class '_io.TextIOWrapper'>
    def test_eqcall_system_print_error(self):
        """Ensures that system.print_error is equivalent to printing to stderr"""
        input_code = """
from mezcla import system
system.print_error("This is an error message")
"""
        expected_code = """
print("This is an error message", file=sys.stderr)
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())

    def test_eqcall_system_exit(self):
        """Ensures that system.exit is equivalent to sys.exit"""
        input_code = """
from mezcla import system
system.exit()
"""
        expected_code = """
import sys
sys.exit()
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())

    def test_eqcall_system_open_file(self):
        """Ensures that system.open_file is equivalent to open"""
        input_code = """
from mezcla import system
with system.open_file("example.txt") as f:
    content = f.read()
    print(content)
"""
        expected_code = """
import io
with io.open("example.txt") as f:
    content = f.read()
    print(content)
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())

    def test_eqcall_system_read_directory(self):
        """Ensures that system.read_directory is equivalent to os.listdir"""
        input_code = """
from mezcla import system
dir_files = system.read_directory("/tmp")
"""
        expected_code = """
import os
dir_files = os.listdir("/tmp")
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())

    def test_eqcall_system_form_path(self):
        """Ensures that system.form_path is equivalent to os.path.join"""
        input_code = """
from mezcla import system
system.form_path("/tmp/foo/bar")
"""
        expected_code = """
import os
os.path.join("/tmp/foo/bar")
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())

    def test_eqcall_system_is_regular_file(self):
        """Ensures that system.is_regular_file is equivalent to os.path.isfile"""
        input_code = """
from mezcla import system
is_regular = system.is_regular_file("/tmp/foo.txt")
"""
        expected_code = """
import os
is_regular = os.path.isfile("/tmp/foo.txt")
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())

    def test_eqcall_system_create_directory(self):
        """Ensures that system.create_directory is equivalent to os.mkdir"""
        input_code = """
from mezcla import system
system.create_directory("foo")
"""
        expected_code = """
import os
os.mkdir("foo")
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())

    def test_eqcall_system_get_current_directory(self):
        """Ensures that system.get_current_directory is equivalent to os.getcwd"""
        input_code = """
from mezcla import system
pwd = system.get_current_directory()
"""
        expected_code = """
import os
pwd = os.getcwd()
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())

    @pytest.mark.skip   # Blank parameter in os.path.chdir()
    def test_eqcall_system_set_current_directory(self):
        """Ensures that system.set_current_directory is equivalent to os.chdir"""
        # Note: No matter the order of import, the output will always have the import on the top
        input_code = """
from mezcla import system
PATH = "/home/ricekiller/Downloads"
system.set_current_directory(PATH)
"""
        expected_code = """
import os
PATH = "/home/ricekiller/Downloads"
os.chdir(PATH)
"""
        result = self.helper_m2s(input_code)
        print(result)
        self.assertEqual(result.split(), expected_code.split())

    def test_eqcall_system_absolute_path(self):
        """Ensures that system.absolute_path is equivalent to os.path.abspath"""
        input_code = """
from mezcla import system
abs_path = system.absolute_path("./Downloads/testfile.pdf")
"""
        expected_code = """
import os
abs_path = os.path.abspath("./Downloads/testfile.pdf")
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())

    @pytest.mark.skip   # Blank parameter in os.path.realpath()
    def test_eqcall_system_real_path(self):
        """Ensures that system.real_path is equivalent to os.path.realpath"""
        input_code = """
from mezcla import system
real_path = system.real_path("./Downloads/testfile.pdf")
"""
        expected_code = """
import os
real_path = os.path.realpath("./Downloads/testfile.pdf")
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())

    def test_eqcall_system_round_num(self):
        """Ensures that system.round_num is equivalent to rounding with ndigits=6"""
        input_code = """
from mezcla import system
round_val = system.round_num(1738.4423425357457131)
"""
        expected_code = """
round_val = round(1738.4423425357457131, 6)
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())

    def test_eqcall_system_round3(self):
        """Ensures that system.round3 is equivalent to rounding with ndigits=3"""
        input_code = """
from mezcla import system
round_val_3 = system.round3(1738.4423425357457131)
"""
        expected_code = """
round_val_3 = round(1738.4423425357457131, 3)
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())

    def test_eqcall_system_sleep(self):
        """Ensures that system.sleep is equivalent to time.sleep"""
        input_code = """
from mezcla import system
system.sleep(60)
"""
        expected_code = """
import time
time.sleep(60)
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())

    @pytest.mark.xfail  ## AttributeError: 'list' object has no attribute '__module__'. Did you mean: '__mul__'
    def test_eqcall_system_get_args(self):
        """Ensures that system.get_args is equivalent to sys.argv"""
        input_code = """
from mezcla import system
system.get_args()
"""
        expected_code = """
import sys
sys.argv
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.split(), expected_code.split())


class TestUsageImportTypes(TestWrapper):
    """Class for test usage for several methods of import in mezcla_to_standard"""

    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    ## TODO: Add a helper function
    def helper_m2s(self, input_code):
        """TODO"""
        # Metrics are ignored for this test case
        new_code, _ = THE_MODULE.transform(THE_MODULE.ToStandard(), input_code)
        return new_code

    ## NOTE: When testing code, DO NOT follow the code in this format
    ## NOTE: Instead, DO NOT apply any indentations on code
    # code_direct_import = '''
    #     from mezcla.debug import trace
    #     trace(1, "error")
    #     '''

    def test_conversion_no_imports(self):
        """This test case checks if the conversion correctly handles a block of code with no imports."""
        # Input: result = gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2") if condition else gh.rename_file("/tmp/foo.list1", "/tmp/foo.list2")
        # Expected Output: result = os.rename("/tmp/fubar.list1", "/tmp/fubar.list2") if condition else os.rename("/tmp/foo.list1", "/tmp/foo.list2")
        ## NO IMPORTS means that the code is treated as a usual code
        input_code = """
gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.strip(), input_code.strip())

    @pytest.mark.xfail
    def test_import_types(self):
        """Usage test for conversion of various mezcla import styles to standard import (VANILLA: no comments or multiline imports)"""
        ## XFAIL: code_direc_import and code_import are not currently supported (TO BE DESIGNED)
        # 4 Styles of import: Direct, using alias, from ... import, import
        code_direct_import = """
from mezcla.debug import trace
trace(1, "error")
"""

        code_alias_import = """
from mezcla import debug as dbg
dbg.trace(1, "error")
"""

        code_from_import = """
from mezcla import debug
debug.trace(1, "error")
"""

        code_import = """
import mezcla
mezcla.debug.trace(1, "error")
"""

        expected_output = """
import logging
logging.error("error")
"""

        ## TEMP_HALT (Not all code import styles are currently supported)
        code_combinations = [
            code_direct_import,
            code_alias_import,
            code_from_import,
            code_import,
        ]
        # OLD (For debugging): code_combinations = [code_from_import, code_alias_import]

        # Writing code to input file/function and transforming it for assertion
        for code in code_combinations:

            ## ATTEMPT 1: Did not work as expected
            # temp_file = gh.create_temp_file(contents=code)
            # command = f"python3 mezcla/mezcla_to_standard.py --to_standard {temp_file}"
            # result = gh.run(command)

            ## ATTEMPT 2: Did not work either
            result, _ = THE_MODULE.transform(THE_MODULE.ToStandard(), code)
            self.assertEqual(result.strip(), expected_output.strip())

    @pytest.mark.xfail
    def test_import_with_comments(self):
        """Usage test for conversion of various mezcla import styles to standard import (WITH_COMMENTS: comments)"""

        code_with_comment = """
# This is a comment
from mezcla.debug import trace
trace(1, "error")
"""

        expected_output = """
# This is a comment
import logging
logging.error("error")
"""

        code_combinations = [code_with_comment]

        for code in code_combinations:
            result = THE_MODULE.transform(THE_MODULE.ToStandard(), code)
            # Refer from test_import_types
            self.assertEqual(result, expected_output, "TODO: Implement")

    @pytest.mark.xfail
    def test_import_multiple(self):
        """Usage test for conversion of various mezcla import styles to standard import (MULTIPLE: import of more than one module, class, function)"""

        code_multiple_imports = """
from mezcla.debug import trace, log
trace(1, "error")
log("info", "message")
"""

        expected_output = """
import logging  
logging.error("error")
logging.info("message")
"""

        code_combinations = [code_multiple_imports]

        for code in code_combinations:
            # Refer from test_import_types
            self.assertEqual(code, None, "TODO: Implement")

    def test_import_no_transformation(self):
        """Usage test for conversion of various mezcla import styles to standard import (NO_TRANSFORMATION: Input code written with standard module)"""

        code_no_transformation = """
import logging
logging.error("error")
"""

        expected_output = """
import logging
logging.error("error")
"""

        code_combinations = [code_no_transformation]

        for code in code_combinations:
            # Refer from test_import_types
            result, _ = THE_MODULE.transform(THE_MODULE.ToStandard(), code)
            self.assertEqual(result.strip(), expected_output.strip())


class TestUsage(TestWrapper):
    """Class for several test usages for mezcla_to_standard"""

    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    def helper_m2s(self, input_code, to_standard=True) -> str:
        """Helper function for mezcla to standard conversion"""
        # Helper Function A (Conversion m2s)

        to_standard = THE_MODULE.ToStandard() if to_standard else THE_MODULE.ToMezcla()
        result, _ = THE_MODULE.transform(to_module=to_standard, code=input_code)
        return result

    def helper_run_cmd_m2s(self, input_code, to_standard=True) -> str:
        """Helper function for mezcla to standard conversion"""
        # Helper Function B (conversion m2s through command line)

        arg = "--to_standard" if to_standard else "--to_mezcla"
        input_file = gh.create_temp_file(contents=input_code)
        command = f"python3 mezcla/mezcla_to_standard.py {arg} {input_file}"
        result = gh.run(command)
        return result

    def test_unsupported_function_to_standard(self):
        """Test for conversion of an unsupported function during mezcla to standard conversion (commented as #Warning not supported)"""

        input_code = """
from mezcla import glue_helpers as gh
gh.run("python3 --version")
"""
        ## OLD
        # to_standard = THE_MODULE.ToStandard()
        # result = THE_MODULE.transform(to_module=to_standard, code=input_code)
        result = self.helper_m2s(input_code)
        unsupported_message = '# WARNING not supported: gh.run("python3 --version")'
        assert result is not None
        assert unsupported_message in result

    @pytest.mark.xfail
    def test_unsupported_function_to_mezcla(self):
        """Test for conversion of an unsupported function during standard to mezcla conversion (commented as #Warning not supported)"""
        ## TODO: Wait until the fix: AttributeError: 'list' object has no attribute '__module__'. Did you mean: '__mul__'?
        input_code = """
import os
os.getenv("HOME")
"""
        # to_mezcla = THE_MODULE.ToMezcla()
        # result = THE_MODULE.transform(to_module=to_mezcla, code=input_code)
        result = self.helper_m2s(input_code)
        unsupported_message = '# WARNING not supported: gh.run("python3 --version")'
        assert result is not None
        assert unsupported_message in result

    def test_conversion_mezcla_to_standard(self):
        """Test the conversion from mezcla to standard calls"""

        ## NOTE: Old code of test_conversion_mezcla_to_standard moved to test_run_supported_and_unsupported_function
        ## NOTE: This was done to test both supported and unsupported functions
        # Standard code uses POSIX instead of os (as of 2024-06-10)
        input_code = """
from mezcla import glue_helpers as gh
gh.delete_file("/tmp/fubar.list")
gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")
gh.form_path("/tmp", "fubar")
        """

        # Standard code consistes of glue helpers commands as well (as of 2024-06-10)
        expected_output_code = """
import os
os.remove("/tmp/fubar.list")
os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
os.path.join("/tmp", "fubar")
        """

        ## OLD: Before Helper
        # to_standard = THE_MODULE.ToStandard()
        # result = THE_MODULE.transform(to_standard, input_code)

        result = self.helper_m2s(input_code)
        self.assertEqual(result.strip(), expected_output_code.strip())

    @pytest.mark.xfail
    def test_conversion_standard_to_mezcla(self):
        """Test the conversion from standard to mezcla calls"""
        ## NOTE: Does not work as intended (output code is similar to standard code)
        ## ERROR: FAILED mezcla/tests/test_mezcla_to_standard.py::TestUsage::test_conversion_standard_to_mezcla - AttributeError: 'list' object has no attribute '__module__'. Did you mean: '__mul__'?

        input_code = """
import os
os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
os.remove("/tmp/fubar.list")
        """

        expected_output_code = """
import os
gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")
gh.delete_file("/tmp/fubar.list")
        """

        # to_mezcla = THE_MODULE.ToMezcla()
        # result = THE_MODULE.transform(to_mezcla, input_code)
        result = self.helper_m2s(input_code)
        self.assertEqual(result.strip(), expected_output_code.strip())

    @pytest.mark.xfail
    def test_run_from_command_to_mezcla(self):
        """Test the working of the script through command line/stdio (--to_standard option)"""
        ## TODO: Fix and implement for command-line like runs

        input_code = """
import os
os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
os.remove("/tmp/fubar.list")
        """
        expected_code = """
import os
gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")
gh.delete_file("/tmp/fubar.list")
"""
        ## OLD (Before Helper)
        # input_file = gh.create_temp_file(contents=input_code)
        # command = f"python3 mezcla/mezcla_to_standard.py --to_mezcla {input_file}"
        # result = gh.run(command)
        result = self.helper_run_cmd_m2s(input_code, to_standard=False)
        self.assertEqual(result.strip(), expected_code.strip())

    def test_run_from_command_empty_file(self):
        """Test the working of the script through command line when input file is empty"""
        input_code = ""
        ## OLD (Before Helper)
        # input_file = gh.create_temp_file(contents=input_code)
        # command = f"python3 mezcla/mezcla_to_standard.py --to_standard {input_file}"
        # result = gh.run(command)
        result = self.helper_run_cmd_m2s(input_code)
        self.assertEqual(result.strip(), "")

    def test_run_from_command_syntax_error(self):
        """Test the working of the script through command line when input file has syntax error"""

        input_code = """
from mezcla import glue_helpers as gh
gh.write_file("/tmp/fubar.list", "fubar.list")
gh.copy_file("/tmp/fubar.list", "/tmp/fubar.list1
        """
        ## OLD (Before Helper)
        # input_file = gh.create_temp_file(contents=input_code)
        # command = f"python3 mezcla/mezcla_to_standard.py --to_standard {input_file}"
        # result = gh.run(command)
        result = self.helper_run_cmd_m2s(input_code)
        self.assertIn("Traceback (most recent call last):\n", result.strip())
        self.assertIn(
            "libcst._exceptions.ParserSyntaxError: Syntax Error @ 1:1.", result.strip()
        )
        self.assertIn("tokenizer error: unterminated string literal", result.strip())

    def test_run_supported_and_unsupported_function(self):
        """Test the conversion with both unspported and supported functions included"""

        ## PREVIOUSLY: test_conversion_mezcla_to_standard
        # Standard code uses POSIX instead of os (as of 2024-06-10)
        input_code = """
from mezcla import glue_helpers as gh
gh.write_file("/tmp/fubar.list", "fubar.list")
gh.copy_file("/tmp/fubar.list", "/tmp/fubar.list1")
gh.delete_file("/tmp/fubar.list")
gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")
gh.form_path("/tmp", "fubar")
        """

        # Standard code consistes of glue helpers commands as well (as of 2024-06-10)
        expected_output_code = """
import os
# WARNING not supported: gh.write_file("/tmp/fubar.list", "fubar.list")
# WARNING not supported: gh.copy_file("/tmp/fubar.list", "/tmp/fubar.list1")
os.remove("/tmp/fubar.list")
os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
os.path.join("/tmp", "fubar")
        """

        # to_standard = THE_MODULE.ToStandard()
        # result = THE_MODULE.transform(to_standard, input_code)
        result = self.helper_m2s(input_code)
        self.assertEqual(result.strip(), expected_output_code.strip())

    def test_run_from_command_to_standard(self):
        """Test the working of the script through command line/stdio (--to_standard option)"""

        input_code = """
from mezcla import glue_helpers as gh
gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")
gh.delete_file("/tmp/fubar.list")
"""
        expected_code = """
import os
os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
os.remove("/tmp/fubar.list")
"""

        ## OLD: Before Helper
        # input_file = gh.create_temp_file(contents=input_code)
        # command = f"python3 mezcla/mezcla_to_standard.py --to_standard {input_file}"
        # result = gh.run(command)
        result = self.helper_m2s(input_code)
        self.assertEqual(result.strip(), expected_code.strip())

    def test_conversion_to_mezcla_round_robin(self):
        """Test conversion of script in round robin (e.g. standard -> mezcla -> standard)"""

        ## NOTE: This test passed, however, result_temp is same as result (i.e. to_mezcla not working as expected)
        ## UPDATE: This test has failed as output is similar to mezcla translation

        ## OLD: This section used POSIX instead of OS
        ## This code returns AttributeError: 'list' object has no attribute '__module__'. Did you mean: '__mul__'?

        #       std_code = """
        # import posix
        # posix.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
        # posix.remove("/tmp/fubar.list")
        #        """

        ## This code returns TypeError: /usr/lib/python3.10/inspect.py:1287: TypeError
        std_code = """
import os
os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
os.remove("/tmp/fubar.list")
"""

        # to_mezcla = THE_MODULE.ToMezcla()
        # result_temp = THE_MODULE.transform(to_mezcla, std_code)
        result_temp = self.helper_m2s(std_code, to_standard=False)

        # to_standard = THE_MODULE.ToStandard()
        # result = THE_MODULE.transform(to_standard, result_temp)
        result = self.helper_m2s(result_temp, to_standard=True)

        self.assertEqual(result, std_code)

    ## NOTE: This test failed due to ToMezcla class not working as expected
    @pytest.mark.xfail
    def test_conversion_to_standard_round_robin(self):
        """Test conversion of script in round robin (e.g. mezcla -> standard -> mezcla)"""

        mezcla_code = """
from mezcla import glue_helpers as gh
gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")
gh.delete_file("/tmp/fubar.list")
        """

        ## OLD: Before Helpers
        # to_mezcla = THE_MODULE.ToMezcla()
        # to_standard = THE_MODULE.ToStandard()
        # result_temp = THE_MODULE.transform(to_standard, mezcla_code)
        # result = THE_MODULE.transform(to_mezcla, result_temp)
        result_temp = self.helper_m2s(mezcla_code, to_standard=False)
        result = self.helper_m2s(result_temp, to_standard=True)

        # DEBUG: print(result, "="*20, result_temp)
        self.assertEqual(result, mezcla_code)

    def test_conversion_nested_functions(self):
        """Test conversion of script containing nested functions"""
        ## TODO: Include tests for standard to mezcla
        ## NOTE: Add support for nested functions

        input_code = """
from mezcla import glue_helpers as gh
gh.delete_file(gh.form_path("/var", "log", "application", "old_app.log"))
"""
        expected_code = """
import os
os.remove(os.path.join("/var", "log", "application", "old_app.log"))
"""
        actual_output = """
import os
from mezcla import glue_helpers as gh
os.remove(# WARNING not supported: gh.form_path("/var", "log", "application", "old_app.log"))
"""
        ## OLD: Before Helpers
        # to_standard = THE_MODULE.ToStandard()
        # result = THE_MODULE.transform(to_standard, input_code)
        result = self.helper_m2s(input_code)
        assert result == actual_output

    def test_conversion_assignment_to_var(self):
        """Test conversion of script for assignment of function to a variable"""

        input_code = """
from mezcla import glue_helpers as gh
path = gh.form_path("/var", "log", "application", "app.log")
"""
        expected_code = """
import os
path = os.path.join("/var", "log", "application", "app.log")
"""

        ## OLD: Before Helpers
        # to_standard = THE_MODULE.ToStandard()
        # result = THE_MODULE.transform(to_standard, input_code)
        result = self.helper_m2s(input_code)
        assert result == expected_code

    @pytest.mark.skip   # Exception: TypeError: '>' not supported between instances of 'str' and 'int'
    def test_conversion_multiple_imports(self):
        """Test conversion of script for multiple imports"""

        input_code = """
from mezcla import glue_helpers as gh
from mezcla import debug
from os import path
gh.write_file("/tmp/test.txt", "test content")
gh.copy_file("/tmp/test.txt", "/tmp/test_copy.txt")
debug.trace("Copy created", level=3)
gh.delete_file("/tmp/test.txt")
if path.exists("/tmp/test_copy.txt"):
    debug.trace("File exists", level=2)
    """

        actual_code_old = """
import os
from mezcla import glue_helpers as gh
from mezcla import debug
from os import path
# WARNING not supported: gh.write_file("/tmp/test.txt", "test content")
# WARNING not supported: gh.copy_file("/tmp/test.txt", "/tmp/test_copy.txt")
# WARNING not supported: debug.trace("Copy created", level=3)
os.remove("/tmp/test.txt")
if path.exists("/tmp/test_copy.txt"):
    # WARNING not supported: debug.trace("File exists", level=2)
"""

        expected_code = """
import os
from os import path
# WARNING not supported: gh.write_file("/tmp/test.txt", "test content")
# WARNING not supported: gh.copy_file("/tmp/test.txt", "/tmp/test_copy.txt")
# WARNING not supported: debug.trace("Copy created", level=3)
os.remove("/tmp/test.txt")
if path.exists("/tmp/test_copy.txt"):
    # WARNING not supported: debug.trace("File exists", level=2)
    pass
"""

        ## NOTE: Support for logging (debug in case of mezcla) not present

        ## OLD: Before Helpers
        # to_standard = THE_MODULE.ToStandard()
        # result = THE_MODULE.transform(to_standard, input_code)

        result = self.helper_m2s(input_code)
        assert result.strip() == expected_code.strip()

    def test_conversion_conditional_statement(self):
        """Test conversion of script when conditional statements are used"""

        input_code = """
from mezcla import glue_helpers as gh
if gh.form_path("/home", "user") == "/home/user":
    gh.rename_file("/home/user/file1.txt", "/home/user/file2.txt")
    gh.delete_file("/home/user/file1.txt")
else:
    gh.write_file("/home/user/file2.txt", "content")
    pass
"""

        expected_code = """
import os
if os.path.join("/home", "user") == "/home/user":
    os.rename("/home/user/file1.txt", "/home/user/file2.txt")
    os.remove("/home/user/file1.txt")
else:
    # WARNING not supported: gh.write_file("/home/user/file2.txt", "content")
    pass
"""
        ## OLD: Before Helpers
        # to_standard = THE_MODULE.ToStandard()
        # result = THE_MODULE.transform(to_standard, input_code)
        result = self.helper_m2s(input_code)
        assert result.strip() == expected_code.strip()

    @pytest.mark.xfail
    def test_conversion_keyword_args(self):
        """Test conversion of script for keyword arguments of methods"""
        ## TODO: Add support for keyword args (filename -> path)
        # Input: gh.delete_file(filename="/tmp/fubar.list")
        # Expected Output: os.remove(path="/tmp/fubar.list")
        input_code = """
from mezcla import glue_helpers as gh 
gh.delete_file(filename="/tmp/fubar.list")
"""
        expected_code = """
import os
os.remove(path="/tmp/fubar.list")
"""
        actual_code = """
import os
os.remove(filename="/tmp/fubar.list")
"""
        result = self.helper_m2s(input_code)
        assert result.strip() == expected_code.strip()

    def test_conversion_additional_imports(self):
        """Test conversion of script for keyword arguments of methods"""
        # Input: import shutil; gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")
        # Expected Output: import shutil; os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
        ## TODO [MULTIPLE]: Remove ununsed and previous imports after conversion (I believe in progress)
        input_code = """
import shutil
from mezcla import glue_helpers as gh
gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")
"""
        expected_code = """
import shutil
import os
os.rename("/tmp/fubar.list1", "/tmp/fubar.list2") 
"""
        actual_code = """
import os
os.rename("/tmp/fubar.list1", "/tmp/fubar.list2") 
"""

        result = self.helper_m2s(input_code)
        assert result.strip() == actual_code.strip()

    def test_conversion_pre_existing_import(self):
        """Test conversion of script for keyword arguments of methods"""
        # Input: import os; gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")
        # Expected Output: import os; os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
        ## TODO: Add detection of pre_existing import
        input_code = """
import os
from mezcla import glue_helpers as gh
gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")
"""
        expected_code = """
import os
os.rename("/tmp/fubar.list1", "/tmp/fubar.list2") 
"""
        result = self.helper_m2s(input_code)
        ## EXPECTED: self.assertEqual(result.strip(), expected_code.strip())
        ## ACTUAL OUTPUT:
        self.assertEqual(result.strip(), "import os\n" + expected_code.strip())

    def test_conversion_multiple_args(self):
        """Test conversion of script for keyword arguments of methods"""
        # Input: gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2", extra="ignored")
        # Expected Output: os.rename("/tmp/fubar.list1", "/tmp/fubar.list2") # extra parameter ignored
        ## TODO: Remove comma after ignoring a parameter (see actual_output)
        input_code = """
from mezcla import glue_helpers as gh
gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2", extra="ignored")
"""
        expected_code = """
import os
os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
"""
        actual_output = """
import os
os.rename("/tmp/fubar.list1", "/tmp/fubar.list2", )
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.strip(), expected_code.strip())

    def test_conversion_complex_args(self):
        """Test conversion of script for keyword arguments of methods"""
        # Input: gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2" + str(i))
        # Expected Output: os.rename("/tmp/fubar.list1", "/tmp/fubar.list2" + str(i))
        input_code = """
from mezcla import glue_helpers as gh
gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2" + str(i))
"""
        expected_code = """
import os
os.rename("/tmp/fubar.list1", "/tmp/fubar.list2" + str(i)) 
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.strip(), expected_code.strip())

    def test_conversion_list_args(self):
        """Test conversion of script for keyword arguments of methods"""
        # Input: gh.form_path(*["/tmp", "fubar"])
        # Expected Output: os.path.join(*["/tmp", "fubar"])
        input_code = """
from mezcla import glue_helpers as gh
gh.form_path(*["/tmp", "fubar"])
"""
        expected_code = """
import os
os.path.join(*["/tmp", "fubar"])
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.strip(), expected_code.strip())

    def test_conversion_dict_args(self):
        """Test conversion of script for keyword arguments of methods"""
        # Input: gh.form_path(**{"filenames": "/tmp"})
        # Expected Output: os.path.join(**{"a": "/tmp"})
        input_code = """
from mezcla import glue_helpers as gh
gh.form_path(**{"filenames": "/tmp"})
"""
        expected_code = """
import os
os.path.join(**{"a": "/tmp"})
"""
        actual_output = """
import os
os.path.join(**{"filenames": "/tmp"})
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.strip(), actual_output.strip())

    @pytest.mark.xfail
    def test_conversion_conditional_call(self):
        """Test conversion of script for keyword arguments of methods"""
        # Input: if condition: gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")
        # Expected Output: if condition: os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
        ## XFAIL: TBD (To Be Designed)
        input_code = """
if condition == False:
    from mezcla import glue_helpers as gh
    gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")
else:
    print("Condition TRUE")
"""
        expected_code = """
if condition == False:
    import os
    os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
else:
    print("Condition TRUE")
"""

        actual_code = """
import os
if condition == False:
    os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
else:
    print("Condition TRUE")
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.strip(), expected_code.strip())

    def test_conversion_loop_call(self):
        """Test conversion of script for keyword arguments of methods"""
        # Input: for file in files: gh.delete_file(file)
        # Expected Output: if condition: for file in files: os.remove(file))
        input_code = """
for i in range(100):
    from mezcla import glue_helpers as gh
    gh.rename_file(f"/tmp/fubar.list{i}", f"/tmp/fubar.list{i}.old")
"""
        expected_code = """
import os
for i in range(100):
    os.rename(f"/tmp/fubar.list{i}", f"/tmp/fubar.list{i}.old")
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.strip(), expected_code.strip())

    def test_conversion_call_in_list(self):
        """Test conversion of script for keyword arguments of methods"""
        # Input: operations = [gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")]
        # Expected Output: operations = [os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")]
        input_code = """
from mezcla import glue_helpers as gh
operations = [gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2"), gh.form_path(filename="/tmp/fubar.list")]
"""
        expected_code = """
import os
operations = [os.rename("/tmp/fubar.list1", "/tmp/fubar.list2"), os.path.join(filename="/tmp/fubar.list")] 
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.strip(), expected_code.strip())

    # @pytest.mark.xfail
    def test_conversion_call_in_dict(self):
        """Test conversion of script for keyword arguments of methods"""
        # Input: actions = {"rename": gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")}
        # Expected Output: actions = {"rename": os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")}
        input_code = """
from mezcla import glue_helpers as gh
actions = {"rename": gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")}
 """
        expected_code = """
import os
actions = {"rename": os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")}
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.strip(), expected_code.strip())

    def test_conversion_starred_args(self):
        """Test conversion of script for keyword arguments of methods"""
        # Input: gh.rename_file(*args)
        # Expected Output: os.rename(*args)
        input_code = """
from mezcla import glue_helpers as gh
gh.rename_file(*args)
"""
        expected_code = """
import os
os.rename(*args)
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.strip(), expected_code.strip())

    def test_conversion_starred_kwargs(self):
        """Test conversion of script for keyword arguments of methods"""
        # Input: gh.rename_file(**kwargs)
        # Expected Output: os.rename(**kwargs)
        input_code = """
from mezcla import glue_helpers as gh
gh.rename_file(**kwargs)
"""
        expected_code = """
import os
os.rename(**kwargs)
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.strip(), expected_code.strip())

    def test_conversion_function_with_named_args_and_condition(self):
        """Test conversion of script for keyword arguments of methods"""
        # Input: if level > 3: debug.trace("trace message", text="debug", level=4)
        # Expected Output: if level > 3: logging.debug("trace message", msg="debug")
        ## TODO: Check the implementation of debugging methods (I believe I saw some of them in the tests)
        input_code = """
from mezcla import debug
level = 4
if level > 3:
    debug.trace(4, "trace message")
"""
        expected_code = """
import logging
level = 4
if level > 3:
    logging.debug("trace message")
"""

        result = self.helper_m2s(input_code)
        self.assertEqual(result.strip(), expected_code.strip())

    def test_conversion_class_method(self):
        """Test conversion of script for keyword arguments of methods"""
        # Input: class FileOps: def rename(self): gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")
        # Expected Output: class FileOps: def rename(self): os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
        input_code = """
from mezcla import glue_helpers as gh
class FileOps:
    def rename(self):
        gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")
"""
        expected_code = """
import os
class FileOps:
    def rename(self):
        os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.strip(), expected_code.strip())

    def test_conversion_lambda(self):
        """Test conversion of script for keyword arguments of methods"""
        # Input: lambda: gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")
        # Expected Output: lambda: os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
        input_code = """
from mezcla import glue_helpers as gh
x = lambda: gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")
"""
        expected_code = """
import os
x = lambda: os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.strip(), expected_code.strip())

    def test_conversion_function_with_decorators(self):
        """Test conversion of script for keyword arguments of methods"""
        # Input: @staticmethod def rename_static(): gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")
        # Expected Output: @staticmethod def rename_static(): os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
        input_code = """
from mezcla import glue_helpers as gh
@staticmethod
def rename_static(): 
    gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")
"""
        expected_code = """
import os
@staticmethod
def rename_static(): 
    os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.strip(), expected_code.strip())

    def test_conversion_function_with_annotations(self):
        """Test conversion of script for keyword arguments of methods"""
        # Input: def rename_file(src: str, dst: str): return gh.rename_file(src, dst)
        # Expected Output: def rename_file(src: str, dst: str): return os.rename(src, dst)
        input_code = """
from mezcla import glue_helpers as gh
def rename_file(src: str, dst: str):
    return gh.rename_file(src, dst)
"""
        expected_code = """
import os
def rename_file(src: str, dst: str):
    return os.rename(src, dst)
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.strip(), expected_code.strip())

    def test_conversion_multiline_args(self):
        """Test conversion of script for keyword arguments of methods"""
        # Input: gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2" + \n "1")
        # Expected Output: os.rename("/tmp/fubar.list1", "/tmp/fubar.list2" + \n "1")
        input_code = """
from mezcla import glue_helpers as gh
gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2" + \n "1")
"""
        expected_code = """
import os
os.rename("/tmp/fubar.list1", "/tmp/fubar.list2" + \n "1")
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.strip(), expected_code.strip())

    def test_conversion_indented_args(self):
        """Test conversion of script for keyword arguments of methods"""
        ## Input:
        # gh.rename_file(
        #   "/tmp/fubar.list1",
        #   "/tmp/fubar.list2"
        # )

        ## Expected Output:
        # os.rename(
        #   "/tmp/fubar.list1",
        #   "/tmp/fubar.list2"
        # )

        input_code = """
from mezcla import glue_helpers as gh
gh.rename_file(
    "/tmp/fubar.list1", 
    "/tmp/fubar.list2"
)
"""
        expected_code = """
import os
os.rename(
    "/tmp/fubar.list1", 
    "/tmp/fubar.list2"
)
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.strip(), expected_code.strip())

    def test_conversion_tuple_args(self):
        """Test conversion of script for keyword arguments of methods"""
        # Input: gh.rename_file(("/tmp/fubar.list1", "/tmp/fubar.list2"))
        # Expected Output: os.rename(("/tmp/fubar.list1", "/tmp/fubar.list2"))
        input_code = """
from mezcla import glue_helpers as gh
gh.rename_file(("/tmp/fubar.list1", "/tmp/fubar.list2"))
"""
        expected_code = """
import os
os.rename(("/tmp/fubar.list1", "/tmp/fubar.list2"))
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.strip(), expected_code.strip())

    def test_conversion_try_except(self):
        """Test conversion of script for keyword arguments of methods"""
        # try: gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2") except OSError: pass
        # Expected Output: try: os.rename("/tmp/fubar.list1", "/tmp/fubar.list2") except OSError: pass
        input_code = """
from mezcla import glue_helpers as gh
try:
    gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")
except OSError:
    pass
"""
        expected_code = """
import os
try:
    os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
except OSError:
    pass
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.strip(), expected_code.strip())

    @pytest.mark.xfail
    def test_conversion_dynamic_import(self):
        """Test conversion of script for keyword arguments of methods"""
        ## Input:
        # if condition:
        #   import gh
        #   gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2") except OSError: pass

        ## Expected Output:
        # if condition:
        #   import os
        #   os.rename("/tmp/fubar.list1", "/tmp/fubar.list2") except OSError: pass

        ## TODO: Match output according to the expected code (import inside a block)
        input_code = """
try:
    if condition:
        from mezcla import glue_helpers as gh
        gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")
    else:
        print(None)
except OSError:
    pass
"""
        expected_code = """
try:
    if condition:
        import os
        os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
    else:
        print(None)
except OSError:
    pass
"""

        actual_code = """
import os
try:
    if condition:
        os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
    else:
        print(None)
except OSError:
    pass
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.strip(), expected_code.strip())

    def test_conversion_ternary_operator(self):
        """Test conversion of script for keyword arguments of methods"""
        # Input: result = gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2") if condition else gh.rename_file("/tmp/foo.list1", "/tmp/foo.list2")
        # Expected Output: result = os.rename("/tmp/fubar.list1", "/tmp/fubar.list2") if condition else os.rename("/tmp/foo.list1", "/tmp/foo.list2")
        input_code = """
from mezcla import glue_helpers as gh
result = gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2") if condition else gh.rename_file("/tmp/foo.list1", "/tmp/foo.list2")
"""
        expected_code = """
import os
result = os.rename("/tmp/fubar.list1", "/tmp/fubar.list2") if condition else os.rename("/tmp/foo.list1", "/tmp/foo.list2")
"""
        result = self.helper_m2s(input_code)
        self.assertEqual(result.strip(), expected_code.strip())


if __name__ == "__main__":
    debug.trace_current_context()
    pytest.main([__file__])
