#! /usr/bin/env python

"""
Tests for mezcla_to_standard module
"""

# Standard packages
## NOTE: this is empty for now

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

if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])