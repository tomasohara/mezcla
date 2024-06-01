#! /usr/bin/env python

"""
Tests for mezcla_to_standard module
"""

# Standard packages
## NOTE: this is empty for now
from unittest.mock import patch, MagicMock

# Installed packages
import pytest

# Local packages
import mezcla.mezcla_to_standard as THE_MODULE
from mezcla import system, debug, glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla.unittest_wrapper import TestWrapper

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    
    # XPASS
    @pytest.mark.xfail
    def test_eqcall_same_target(self):
        """Make sure that same_target function of EqCall class works as usual"""
        
        # Creating mock functions for testing
        def mock_rename_file(source, target):
            pass
        
        def another_function(source, target):
            pass

        eqcall = THE_MODULE.EqCall(target=mock_rename_file, dest=None)
        assert eqcall.same_target(mock_rename_file) == True
        assert eqcall.same_target(another_function) == False

    # XPASS
    @pytest.mark.xfail
    def test_eqcall_same_dest(self):
        """Make sure that same_dest function of EqCall class works as usual"""
        # Creating mock functions for testing
        def mock_function(source, target):
            pass

        def another_function(source, target):
            pass

        eqcall = THE_MODULE.EqCall(target=None, dest=mock_function)
        assert eqcall.same_dest(mock_function) == True
        assert eqcall.same_dest(another_function) == False 

    # XPASS
    @pytest.mark.xfail
    def test_eqcall__to_dest_args(self):
        """Make sure that _to_dest_args function of EqCall class works as usual"""
        
        # Creating mock functions for testing
        def add(a:int, b:int):
            return a+b

        def power(a:int, b:int):
            return a**b
        
        eqcall_add = THE_MODULE.EqCall(add, dest=None)
        eqcall_power = THE_MODULE.EqCall(power, dest=None)

        # Testing without keyword args
        result_add = eqcall_add._to_dest_args(100, 2)
        expected_add = {"a": 100, "b": 2}
        assert result_add == expected_add, f"Expected {expected_add}, but got {result_add}"
   
        result_power = eqcall_power._to_dest_args(17, 38)
        expected_power = {"a": 17, "b": 38}
        assert result_power == expected_power

        # Testing with keyword args
        result_add = eqcall_add._to_dest_args(a=100, b=2)
        expected_add = {"a": 100, "b": 2}
        assert result_add == expected_add, f"Expected {expected_add}, but got {result_add}"
        
        result_power = eqcall_power._to_dest_args(17, 38)
        expected_power = {"a": 17, "b": 38}
        assert result_power == expected_power

    # XPASS
    @pytest.mark.xfail
    def test_eqcall__to_target_args(self):
        """Make sure that _to_target_args function of EqCall class works as usual"""
        
        # Creating mock functions for testing
        def add(a:int, b:int):
            return a+b

        def power(a:int, b:int):
            return a**b

        eqcall_add = THE_MODULE.EqCall(target=None, dest=add)
        eqcall_power = THE_MODULE.EqCall(target=None, dest=power)

        # Testing without keyword args
        result_add = eqcall_add._to_target_args(100, 2)
        expected_add = {"a": 100, "b": 2}
        assert result_add == expected_add, f"Expected {expected_add}, but got {result_add}"
   
        result_power = eqcall_power._to_target_args(17, 38)
        expected_power = {"a": 17, "b": 38}
        assert result_power == expected_power

        # Testing with keyword args
        result_add = eqcall_add._to_target_args(a=100, b=2)
        expected_add = {"a": 100, "b": 2}
        assert result_add == expected_add, f"Expected {expected_add}, but got {result_add}"
        
        result_power = eqcall_power._to_target_args(17, 38)
        expected_power = {"a": 17, "b": 38}
        assert result_power == expected_power

    # XPASS
    @pytest.mark.xfail
    def test_eqcall__filter_args_by_function(self):
        """Make sure that _filter_args_by_function of EqCall class works as usual"""
        # Creating mock functions for testing
        def add(a:int, b:int):
            return a+b

        def cube(x:int):
            return x**3
        
        def volume(l:int, b:int, h:int):
            return l*b*h
        
        # Testing "add" method
        eqcall = THE_MODULE.EqCall(target=add, dest=None)
        args_add = {"a": 23, "b": 322, "c": -54}
        expected_add = {"a": 23, "b": 322}
        result_add = eqcall._filter_args_by_function(add, args_add)
        assert result_add == expected_add
        
        # Testing "cube" method       
        eqcall = THE_MODULE.EqCall(target=cube, dest=None)
        args_cube = {"x": 9, "y": 38}
        expected_cube = {"x": 9}
        result_cube = eqcall._filter_args_by_function(cube, args_cube)
        assert result_cube == expected_cube
        
        # Testing "volume" method
        eqcall = THE_MODULE.EqCall(target=volume, dest=None)
        args_volume = {"l": 10, "b": 2, "h": 6, "alpha": 0.25}
        expected_volume = {"l": 10, "b": 2, "h": 6}
        result_volume = eqcall._filter_args_by_function(volume, args_volume)     
        # In this method, the result value is sorted according to the key of dictionary
        assert result_volume == expected_volume

        # Testing "add" method with empty dictionary (no-args)
        eqcall = THE_MODULE.EqCall(target=add, dest=None)
        result_volume_empty = eqcall._filter_args_by_function(add, {})
        assert result_volume_empty == {}

        # Testing "add" method with incorrect dictionary
        eqcall = THE_MODULE.EqCall(target=add, dest=None)
        args_add = {"aa": 23, "bb": 322}
        result_volume_empty = eqcall._filter_args_by_function(add, args_add)
        assert result_volume_empty == {}

    # XPASS
    @pytest.mark.xfail
    def test_eqcall_is_dest_condition_met(self):
        """Make sure that is_dest_condition_met of EqCall class works as usual"""
        # Creating mock functions for testing        
        def volume(l:int, b:int, h:int):
            return l*b*h
        
        def volume_valid_condition(l:int, b:int, h:int, extra):
            return l > 0 and b > 0 and h > 0 and extra == "value"
        
        args = {"l": 10, "b": 5, "h": 255, "extra": "value"}
        eqcall = THE_MODULE.EqCall(dest=volume, target=volume, condition=volume_valid_condition)
        result = eqcall.is_dest_condition_met(**args)
        assert result == True
        
        args = {"l": -10, "b": 5, "h": 255, "extra": "value"}
        eqcall = THE_MODULE.EqCall(dest=volume, target=volume, condition=volume_valid_condition)
        result_fail = eqcall.is_dest_condition_met(**args)
        assert result_fail == False

    # XPASS
    @pytest.mark.xfail
    def test_eqcall_is_target_condition_met(self):
        """Make sure that is_target_condition_met of EqCall class works as usual"""
        # Creating mock functions for testing        
        def volume(l:int, b:int, h:int):
            return l*b*h
        
        def volume_valid_condition(l:int, b:int, h:int, extra):
            return l > 0 and b > 0 and h > 0 and extra == "value"
        
        args = {"l": 10, "b": 5, "h": 255, "extra": "value"}
        eqcall = THE_MODULE.EqCall(dest=volume, target=volume, condition=volume_valid_condition)
        result = eqcall.is_target_condition_met(**args)
        assert result == True
        
        args = {"l": -10, "b": -5, "h": 255, "extra": "value"}
        eqcall = THE_MODULE.EqCall(dest=volume, target=volume, condition=volume_valid_condition)
        result_fail = eqcall.is_target_condition_met(**args)
        assert result_fail == False

    # XPASS
    @pytest.mark.xfail
    def test_eqcall__to_dest_args_keys(self):
        """Make sure that _to_dest_args_keys of EqCall class works as usual"""
        
        # Creating mock functions for testing        
        def volume(l:int, b:int, h:int):
            return l*b*h
        
        def pressure(d:int, h:int, g:int):
            return d*h*g
        
        args = {"l": 60, "b": 400, "h": 50}
        eq_params = {"l": "length", "b": "breadth", "h": "height"}
        expected_result = {"length": 60, "breadth": 400, "height": 50}

        eqcall = THE_MODULE.EqCall(target=volume, dest=pressure, eq_params=eq_params)
        result = eqcall._to_dest_args_keys(args)
        assert result == expected_result
    
    # XPASS
    @pytest.mark.xfail
    def test_eqcall__to_target_args_keys(self):
        """Make sure that _to_target_args_keys of EqCall class works as usual"""
        
        # Creating mock functions for testing        
        def volume(l:int, b:int, h:int):
            return l*b*h
        
        def pressure(d:int, h:int, g:int):
            return d*h*g
        
        args = {"d": 790, "h": 100, "g": 10}
        eq_params = {"d": "density", "h": "depth", "g": "acceleration_due_to_gravity"}
        expected_result = {"density": 790, "depth": 100, "acceleration_due_to_gravity": 10}

        eqcall = THE_MODULE.EqCall(target=volume, dest=pressure, eq_params=eq_params)
        result = eqcall._to_dest_args_keys(args)
        assert result == expected_result

    # XPASS
    @pytest.mark.xfail
    def test_eqcall__insert_extra_params(self):
        """Make sure that _insert_extra_paramas of EqCall class works as usual"""
        
        # Creating mock functions for testing        
        def slope(x1:int, y1:int, x2:int, y2:int):
            return (y2 - y1)/(x2 - x1)
        
        extra_params = {"x1": 3, "y1": 5, "x2": 6}
        args = {"x1": 10, "y2": 12}

        # Union of dictionary
        expected_result = extra_params|args

        eqcall = THE_MODULE.EqCall(target=slope, dest=None, extra_params=extra_params)
        result = eqcall._insert_extra_params(args)
        assert result == expected_result

    # XPASS
    @pytest.mark.xfail
    def test_eqcall_run_target(self):
        """Make sure that run_target of EqCall class works as usual"""
        def slope(x1:int, y1:int, x2:int, y2:int) -> float:
            return round((y2 - y1)/(x2 - x1), 2)
        
        def distance(x1:int, y1:int, x2:int, y2:int) -> float:
            return round(( (x2 - x1) ** 2 + (y2 - y1) ** 2 ) ** 0.5, 2)
        
        args = {"x1": 4, "y1": 5, "x2": 6, "y2": 10}
        expected_result = 2.5

        eqcall = THE_MODULE.EqCall(target=slope, dest=distance)
        result = eqcall.run_target(**args)
        assert result == expected_result

    # XPASS
    @pytest.mark.xfail
    def test_eqcall_run_dest(self):
        """Make sure that run_dest of EqCall class works as usual"""
        def slope(x1:int, y1:int, x2:int, y2:int) -> float:
            return round((y2 - y1)/(x2 - x1), 2)
        
        def distance(x1:int, y1:int, x2:int, y2:int) -> float:
            return round(( (x2 - x1) ** 2 + (y2 - y1) ** 2 ) ** 0.5, 2)
        
        args = {"x1": 4, "y1": 5, "x2": 6, "y2": 10}
        expected_result = 5.39

        eqcall = THE_MODULE.EqCall(target=slope, dest=distance)
        result = eqcall.run_dest(**args)
        assert result == expected_result

    # XPASS
    @pytest.mark.xfail
    def test_use_standard_equivalent(self):
        """Make sure that use_standard_equivalent works as usual"""

        class MockCall:
            def __init__(self, target_func, dest_func, condition_met) -> None:
                self.target_func = target_func
                self.dest_func = dest_func
                self.condition_met = condition_met

            def same_target(self, func):
                return self.target_func == func
            
            def is_dest_condition_met(self, *args, **kwargs):
                return self.condition_met(*args, **kwargs)
            
            def run_dest(self, *args, **kwargs):
                return self.dest_func(*args, **kwargs)
            
        def mock_target_func(*args, **kwargs):
            return "target"
        
        def mock_dest_func(*args, **kwargs):
            return "destination"
        
        def always_true(*args, **kwargs):
            return True

        def always_false(*args, **kwargs):
            return False
        
        # Mock mezcla_to_standard to verify mock_target_func
        THE_MODULE.mezcla_to_standard = [
            MockCall(target_func=mock_target_func, condition_met=always_true, dest_func=mock_dest_func),
            MockCall(target_func=mock_target_func, condition_met=always_false, dest_func=mock_dest_func)
        ]

        # Apply the decorator
        decorated_func = THE_MODULE.use_standard_equivalent(mock_target_func)
        assert decorated_func() == "destination"

        # Re-mock mezcla_to_standard to verify mock_dest_func
        THE_MODULE.mezcla_to_standard = [
            MockCall(target_func=mock_dest_func, condition_met=always_false, dest_func=mock_target_func),
            MockCall(target_func=mock_dest_func, condition_met=always_true, dest_func=mock_target_func)
        ]

        decorated_func = THE_MODULE.use_standard_equivalent(mock_dest_func)
        assert decorated_func() == "target"

    # XPASS
    @pytest.mark.xfail
    def test_use_mezcla_equivalent(self):
        """Make sure that use_mezcla_equivalent works as usual"""

        class MockCall:
            def __init__(self, dest_func, target_func, condition_met) -> None:
                self.dest_func = dest_func
                self.target_func = target_func
                self.condition_met = condition_met

            def same_dest(self, func):
                return self.dest_func == func

            def is_target_condition_met(self, *args, **kwargs):
                return self.condition_met(*args, **kwargs)

            def run_target(self, *args, **kwargs):
                return self.target_func(*args, **kwargs)

        def mock_dest_func(*args, **kwargs):
            return "destination"

        def mock_target_func(*args, **kwargs):
            return "target"

        def always_true(*args, **kwargs):
            return True

        def always_false(*args, **kwargs):
            return False

        # Mock mezcla_to_standard in THE_MODULE
        THE_MODULE.mezcla_to_standard = [
            MockCall(dest_func=mock_dest_func, target_func=mock_target_func, condition_met=always_true),
            MockCall(dest_func=mock_dest_func, target_func=mock_target_func, condition_met=always_false)
        ]

        # Apply the decorator
        decorated_func = THE_MODULE.use_mezcla_equivalent(mock_dest_func)
        assert decorated_func() == "target"

        # Re-mock mezcla_to_standard to verify mock_target_func
        THE_MODULE.mezcla_to_standard = [
            MockCall(dest_func=mock_target_func, target_func=mock_dest_func, condition_met=always_true),
            MockCall(dest_func=mock_target_func, target_func=mock_dest_func, condition_met=always_false)
        ]

        decorated_func = THE_MODULE.use_mezcla_equivalent(mock_target_func)
        assert decorated_func() == "destination"

    # XPASS
    @pytest.mark.xfail
    def test_insert_decorator_to_functions(self):
        """Make sure that insert_decorator_to_functions works as expected"""

        def sample_decorator(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper

        original_code = '''
def foo():
    print("Hello, World!")
    
def bar(x):
    return x * 2
'''
        # Expected modified code (uses the format of the decorator)
        _expected_code = '''
from mezcla.mezcla_to_standard import sample_decorator

@sample_decorator
def foo():
    print("Hello, World!")
    
@sample_decorator
def bar(x):
    return x * 2
'''         
        # Sample decorator is wrapped arround print
        # Avoid double codes within the sample code
        expected_code = '''
from mezcla.mezcla_to_standard import sample_decorator

def foo():
    sample_decorator(print)('Hello, World!')

def bar(x):
    return x * 2
'''
            # Run the function to insert the decorator
        result = THE_MODULE.insert_decorator_to_functions(sample_decorator, original_code)
        # Normalize whitespace for comparison
        def normalize_whitespace(s):
            return ''.join(s.split())
        normalized_result = normalize_whitespace(result)
        normalized_expected_code = normalize_whitespace(expected_code)
        # Assert that the result matches the expected code
        assert repr(normalized_result) == repr(normalized_expected_code)

    
    # XPASS
    @pytest.mark.xfail
    def test_to_standard(self):
        """Make sure that to_standard works as usual"""
        original_code = '''
def foo():
    print("Hello, World!")
    
def bar(x):
    return x * 2
'''
        to_assert = ["from mezcla.mezcla_to_standard import use_standard_equivalent", "use_standard_equivalent(print)"]
        result = THE_MODULE.to_standard(original_code)
        assert result.startswith(to_assert[0]+ "\n") == True
        assert to_assert[1] in result
    
    # XPASS
    @pytest.mark.xfail
    def test_to_mezcla(self):
        """Make sure that to_mezcla works as usual"""
        original_code = '''
from mezcla import glue_helpers as gh

def foo():
    gh.create_temp_file('temp1.tmp')
    
def bar(x):
    x = gh.run('echo $PWD')
    return x
'''

        to_assert = ["from mezcla.mezcla_to_standard import use_mezcla_equivalent", "use_mezcla_equivalent(gh.create_temp_file)", "use_mezcla_equivalent(gh.run)"]
        result = THE_MODULE.to_mezcla(original_code)
        assert result.startswith(to_assert[0]+ "\n") == True
        assert to_assert[1] in result
        assert to_assert[2] in result

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])