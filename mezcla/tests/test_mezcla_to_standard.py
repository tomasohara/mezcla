"""
Tests for mezcla_to_standard module
"""

# Standard packages
## NOTE: this is empty for now
from unittest.mock import patch, MagicMock
import os
import logging

# Installed packages
import pytest
import libcst

# Local packages
import mezcla.mezcla_to_standard as THE_MODULE
from mezcla import system, debug, glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla.unittest_wrapper import TestWrapper

class TestEqCall(TestWrapper):
    """Class for test usage of EqCall class in mezcla_to_standard"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    # @pytest.mark.parametrize(
    #     "eq_call, params, expected_dest_arguments", 
    #     [
    #         (THE_MODULE[0], {"source": "src_file", "target": "dst_file"}, ("src_file", "dst_file")),
    #         (THE_MODULE[1], {"filename": "file.txt"}, ("file.txt",)),
    #         (THE_MODULE[2], {"filenames": ["dir", "file.txt"]}, (["dir", "file.txt"],)),
    #         (THE_MODULE[3], {"text": "debug message"}, ("debug message",)),
    #         (THE_MODULE[4], {"text": "info message"}, ("info message",)),
    #         (THE_MODULE[5], {"text": "warning message"}, ("warning message",)),
    #         (THE_MODULE[6], {"text": "error message"}, ("error message",))
    #     ]
    # )
    # @patch('os.rename')         # Equivalent: gh.rename_file
    # @patch('os.remove')         # Equivalent: gh.delete_file
    # @patch('os.path.join')      # Equivalent: gh.form_path
    # @patch('logging.debug')     # Equivalent: debug.trace level=4
    # @patch('logging.info')      # Equivalent: debug.trace level=3
    # @patch('logging.warning')   # Equivalent: debug.trace level=2
    # @patch('logging.error')     # Equivalent: debug.trace level=1

    # def test_eq_calls(
    #     mock_rename,
    #     mock_remove,
    #     mock_join,
    #     mock_debug,
    #     mock_info,
    #     mock_warning,
    #     mock_error,
    #     eq_call, params, expected_dest_args
    # ):
    #     eq_call = THE_MODULE.EqCall()
    #     # Choose a mock based on the destination function
    #     mock_dest = {
    #     os.rename: mock_rename,
    #     os.remove: mock_remove,
    #     os.path.join: mock_join,
    #     logging.debug: mock_debug,
    #     logging.info: mock_info,
    #     logging.warning: mock_warning,
    #     logging.error: mock_error
    # }[eq_call.dest]
        
    #     # Ensure condition is met
    #     if "level" in params:
    #         condition_met = eq_call.condition(params["level"])
    #     else:
    #         condition_met = eq_call.condition()

    #     if condition_met:
    #         # Translate eq_params to standard
    #         standard_params = {
    #             val: params[key] for key, val in (eq_call.eq_params or {}).items()
    #         }
    #         if eq_call.extra_params:
    #             standard_params.update(eq_call.extra_params)
            
    #         # Call the destination function with translated params
    #         eq_call.dest(**standard_params)

    #         # Assert the destination function was called with expected params
    #         mock_dest.assert_called_once_with(*expected_params)
    
    def helper_get_eqcall(self, func):
        """Helper function for obtaining all equivalent calls for a function"""
        return next(
            call\
            for call in THE_MODULE.mezcla_to_standard\
            if call.target is func
        )
    
    def test_rename_file(self):
        """Tests for equivalence of gh.rename_file to os.rename"""
        eq_call = self.helper_get_eqcall(gh.rename_file)
        self.assertEqual(eq_call.dest, os.rename)
        self.assertEqual(eq_call.eq_params, {"source": "src", "target": "dst"})

    def test_delete_file(self):
        """Tests for equivalence of gh.delete_file to os.remove"""
        eq_call = self.helper_get_eqcall(gh.delete_file)
        self.assertEqual(eq_call.dest, os.remove)
        self.assertEqual(eq_call.eq_params, {"filename": "path"})

    def test_form_path(self):
        """Tests for equivalence of gh.form_path to os.path.join"""
        eq_call = self.helper_get_eqcall(gh.form_path)
        self.assertEqual(eq_call.dest, os.path.join)
        self.assertEqual(eq_call.eq_params, {"filenames": "a"})

    def test_trace_logging_levels(self):
        """Tests for equivalence of debug (mezcla) to logging module"""
        for level, log_func in \
            [(4, logging.debug), (3, logging.info), (2, logging.warning), (1, logging.error)]:
            eq_call = next((call for call in THE_MODULE.mezcla_to_standard if call.target is debug.trace and call.condition(level)), None)
            self.assertIsNotNone(eq_call)
            self.assertEqual(eq_call.dest, log_func)
            self.assertEqual(eq_call.eq_params, {"text": "msg"})
            self.assertEqual(eq_call.extra_params, {"level": int(level)})

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
        to_standard = THE_MODULE.ToStandard()
        mezcla_to_standard = [
            THE_MODULE.EqCall(target=self.sample_func1, dest=None),
            THE_MODULE.EqCall(target=self.sample_func2, dest=None)
        ]
        to_standard.mezcla_to_standard = mezcla_to_standard
        return to_standard

    @pytest.mark.xfail
    def test_find_eq_call_existing(self):
        """Test for finding an existing equivalent call"""
        module = "mezcla"
        method = "sample_func1"
        args = ['a']
        eq_call = THE_MODULE.ToStandard.find_eq_call(self, module=module, func=method, args=args)
        
        ## Not working as intended, shall be fixed soon
        assert eq_call is not None
        assert eq_call.target == self.sample_func1

    def test_find_eq_call_non_existing(self, setup_to_standard):
        """Test for trying to find a non-existing equivalent call"""
        to_standard = setup_to_standard
        module = "mezcla"
        method = "no_exist_func"
        args = ['b']
        
        # Correct assertion, but does not work as intended (no need for XFAIL)
        eq_call = to_standard.find_eq_call(module, method, args)
        assert eq_call is None

    # Does not work as intended (Result = None)
    @pytest.mark.xfail
    def test_find_eq_call(self):
        """Ensures that find_eq_call of ToStandard class works as expected"""
        
        class MockEqCall:
            def __init__(self, module, func, condition_met=True):
                self.target = type(
                'MockClass', (object,), {'__module__': f'{module}.mock'}
                )()
                self.target.__name__ = func
                self.condition_met = condition_met

            def is_condition_to_replace_met(self, args):
                return self.condition_met
        # Create a ToStandard instance
        to_standard = THE_MODULE.ToStandard()
        mezcla_to_standard = [
            MockEqCall('my_module', 'my_function'),
            MockEqCall('other_module', 'other_function')
        ]
        print("M2S:", mezcla_to_standard)
        # Assertion for eq_call match
        result = to_standard.find_eq_call("my_module", "my_function", ['arg1', 'arg2'])
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
            THE_MODULE.EqCall(target=self.sample_func1, dest=None, condition=lambda a, b: a > b),
            THE_MODULE.EqCall(target=self.sample_func2, dest=None, condition=lambda a, b: a == b)
        ]
        to_standard.mezcla_to_standard = mezcla_to_standard
        return to_standard

    @pytest.mark.xfail
    # Error Involved: on arg_to_value(arg: cst.Arg) -> object
    # AttributeError: 'int' object has no attribute 'value'
    def test_is_condition_to_replace_met(self, setup_to_standard):
        """Ensures that is_condition_to_replace_met of ToStandard class works as expected"""
        to_standard = setup_to_standard

        eq_call = THE_MODULE.EqCall(target=self.sample_func1, dest=None, condition=lambda a, b: a > b)
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

    ## Sample Static Methods for Testing
    @staticmethod
    def sample_func1(a, b):
        """First sample function"""
        pass

    @staticmethod
    def sample_func2(a, b):
        """Second sample function"""
        pass

    @staticmethod
    def standard_func1(src, dst):
        """Standard equivalent function for sample_func1"""
        pass

    @staticmethod
    def standard_func2(path):
        """Standard equivalent function for sample_func2"""
        pass

    ## Setup for ToMezcla Class
    @pytest.fixture
    def setup_to_mezcla(self):
        to_mezcla = THE_MODULE.ToMezcla()
        mezcla_to_standard = [
            THE_MODULE.EqCall(target=self.sample_func1, dest=self.standard_func1, condition=lambda a, b: a > b, eq_params={"a": "src", "b": "dst"}),
            THE_MODULE.EqCall(target=self.sample_func2, dest=self.standard_func2, condition=lambda a, b: a == b, eq_params={"a": "path"})
        ]
        to_mezcla.mezcla_to_standard = mezcla_to_standard
        return to_mezcla
    
    ## TEST 1: find_eq_call (existing function)
    ## NOTE: eq_call not working as expected
    @pytest.mark.xfail
    def test_find_eq_call_existing(self, setup_to_mezcla):
        """Test for finding an existing equivalent call for ToMezcla class"""
        to_mezcla = setup_to_mezcla
        module, method, args = "mezcla", "standard_func1", [4, 3]
        # Using setup_to_mezcla to mock the working of ToMezcla class
        eq_call = to_mezcla.find_eq_call(module, method, args)
        assert eq_call is not None
        assert eq_call.target == self.sample_func1
    
    ## TEST 2: find_eq_call (non-existing function)
    def test_find_eq_call_non_existing(self, setup_to_mezcla):
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
        
        eq_call = THE_MODULE.EqCall(target=self.sample_func1, dest=self.standard_func1, condition=lambda a, b: a > b, eq_params={"a": "src", "b": "dst"})
        args = [4, 3]
        result = to_mezcla.is_condition_to_replace_met(eq_call, args)
        assert result is True

        args = [3, 4]
        result = to_mezcla.is_condition_to_replace_met(eq_call, args)
        assert result is False

        eq_call = THE_MODULE.EqCall(target=self.sample_func2, dest=self.standard_func2, condition=lambda a, b: a == b, eq_params={"a": "path"})
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
        eq_call = THE_MODULE.EqCall(target=self.sample_func1, dest=self.standard_func1, condition=lambda a, b: a > b, eq_params={"a": "src", "b": "dst"})

        # For multiple arguments in function using multiple arguments
        args = [4, 3]
        kwargs = {}
        result = to_mezcla.get_args_replacement(eq_call, args, kwargs)
        assert result == [4, 3]

        # For multiple arguments in function using single argument (selects first arg)
        eq_call = THE_MODULE.EqCall(target=self.sample_func2, dest=self.standard_func2, condition=lambda a, b: a == b, eq_params={"a": "path"})
        args = [4, 4]
        kwargs = {}
        result = to_mezcla.get_args_replacement(eq_call, args, kwargs)
        assert result == [4]

    ## TEST 5: replace_args_keys
    def test_replace_args_keys(self, setup_to_mezcla):
        """Test for replace_args_keys method in ToMezcla class"""
        to_mezcla = setup_to_mezcla
        
        # For multiple arguments
        eq_call = THE_MODULE.EqCall(target=self.sample_func1, dest=self.standard_func1, eq_params={"a": "src", "b": "dst"})
        args = {"src": 4, "dst": 3}
        result = to_mezcla.replace_args_keys(eq_call, args)
        assert result == {"a": 4, "b": 3}

        # For single argument
        eq_call = THE_MODULE.EqCall(target=self.sample_func2, dest=self.standard_func2, eq_params={"a": "path"})
        args = {"path": 4}
        result = to_mezcla.replace_args_keys(eq_call, args)
        assert result == {"a": 4}

    ## TEST 6: eq_call_to_module_func
    def test_eq_call_to_module_func(self, setup_to_mezcla):
        """Test for eq_call_to_module_func method in ToMezcla class"""
        to_mezcla = setup_to_mezcla

        eq_call = THE_MODULE.EqCall(target=self.sample_func1, dest=self.standard_func1)
        module, func = to_mezcla.eq_call_to_module_func(eq_call)
        assert module == self.sample_func1.__module__
        assert func == self.sample_func1.__name__

        eq_call = THE_MODULE.EqCall(target=self.sample_func2, dest=self.standard_func2)
        module, func = to_mezcla.eq_call_to_module_func(eq_call)
        assert module == self.sample_func2.__module__
        assert func == self.sample_func2.__name__

class TestTransform(TestWrapper):
    """Class for test usage for methods of transform method in mezcla"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    # Usage test
    ## TODO: Assertion not working as expected
    @pytest.mark.xfail
    def test_simple_transform(self):
        class SimpleModule:
            """Defining a simple module to test transform method"""    
            
            def get_replacement(self, module_name, func_node, args_nodes):
                if module_name == "old_module" and func_node.attr.value == "old_function":
                    return "new_module", libcst.Name("new_function"), args_nodes
                else:
                    return None, None, args_nodes
                
        original_code = """
from old_module import old_function
result = old_function(2, 3)
        """
        expected_code = """
from new_module import new_function
result = new_function(2, 3)
        """
        to_module = SimpleModule()
        result = THE_MODULE.transform(to_module, original_code)
        # Result currently similar to original code (no changes)
        self.assertEqual(result.strip(), expected_code.strip())

    # Unit Testing
    @pytest.mark.xfail
    def test_leave_module(self):
        """Ensures that leave_Module method of CustomVisitor works as expected"""
        assert False, "TODO: Implement"

class TestUsageImportTypes(TestWrapper):
    """Class for test usage for several methods of import in mezcla_to_standard"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    ## TODO: Add a helper function
    # def helper_import(self, code_combinations, explicit_run = True)

    @pytest.mark.xfail
    def test_import_types(self):
        """Usage test for conversion of various mezcla import styles to standard import (VANILLA: no comments or multiline imports)"""

        # 4 Styles of import: Direct, using alias, from ... import, import
        code_direct_import = '''
        from mezcla.debug import trace
        trace(1, "error")'''
        
        code_alias_import = '''
        from mezcla import debug as dbg
        dbg.trace(1, "error")'''
        
        code_from_import = '''
        from mezcla import debug
        debug.trace(1, "error")'''
        
        code_import = '''
        import mezcla
        mezcla.debug.trace(1, "error")'''

        expected_output = '''
        import logging
        logging.error("error")
        '''

        # Storing all possible code combinations
        code_combinations = [code_direct_import, code_alias_import, code_from_import, code_import]
        
        # Writing code to input file/function and transforming it for assertion
        for code in code_combinations:
            
            ## ATTEMPT 1: Did not work as expected
            # temp_file = gh.create_temp_file(contents=code)
            # command = f"python3 mezcla/mezcla_to_standard.py --to_standard {temp_file}"
            # result = gh.run(command)
            
            ## ATTEMPT 2: Did not work either
            # result = THE_MODULE.transform(THE_MODULE.ToStandard(), code)
            # self.assertEqual(result.strip(), expected_output.strip())
            
            self.assertEqual(code, None, "TODO: Implement")

    @pytest.mark.xfail
    def test_import_with_comments(self):
        """Usage test for conversion of various mezcla import styles to standard import (WITH_COMMENTS: comments)"""
        
        code_with_comment = '''
        # This is a comment
        from mezcla.debug import trace
        trace(1, "error")'''
        
        expected_output = '''
        # This is a comment
        import logging
        
        logging.error("error")
        '''

        code_combinations = [code_with_comment]

        for code in code_combinations:
            # Refer from test_import_types
            self.assertEqual(code, None, "TODO: Implement")
    
    @pytest.mark.xfail
    def test_import_multiple(self):
        """Usage test for conversion of various mezcla import styles to standard import (MULTIPLE: import of more than one module, class, function)"""
        
        code_multiple_imports = '''
        from mezcla.debug import trace, log
        trace(1, "error")
        log("info", "message")'''
        
        expected_output = '''
        import logging
        
        logging.error("error")
        logging.info("message")
        '''

        code_combinations = [code_multiple_imports]

        for code in code_combinations:
            # Refer from test_import_types
            self.assertEqual(code, None, "TODO: Implement")

    @pytest.mark.xfail
    def test_import_no_transformation(self):
        """Usage test for conversion of various mezcla import styles to standard import (NO_TRANSFORMATION: Input code written with standard module)"""

        code_no_transformation = '''
        import logging
        logging.error("error")'''

        expected_output = '''
        import logging
        logging.error("error")'''

        code_combinations = [code_no_transformation]

        for code in code_combinations:
            # Refer from test_import_types
            self.assertEqual(code, None, "TODO: Implement")


class TestUsage(TestWrapper):
    """Class for several test usages for mezcla_to_standard"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    def test_conversion_mezcla_to_standard(self):
        """Test the conversion from mezcla to standard calls"""
        
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
import posixpath
import posix
import posix
from mezcla import glue_helpers as gh
gh.write_file("/tmp/fubar.list", "fubar.list")
gh.copy_file("/tmp/fubar.list", "/tmp/fubar.list1")
posix.remove("/tmp/fubar.list")
posix.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
posixpath.join()
        """
        
        to_standard = THE_MODULE.ToStandard()
        result = THE_MODULE.transform(to_standard, input_code)
        self.assertEqual(result.strip(), expected_output_code.strip())
    
    # NOTE: Does not work as intended (output code is similar to standard code)
    @pytest.mark.xfail
    def test_conversion_standard_to_mezcla(self):
        """Test the conversion from standard to mezcla calls"""

        input_code = """
import os
os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
os.remove("/tmp/fubar.list")
        """
        
        expected_output_code = """
import os
from mezcla import glue_helpers as gh
gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")
gh.delete_file("/tmp/fubar.list")
        """

        to_mezcla = THE_MODULE.ToMezcla()
        result = THE_MODULE.transform(to_mezcla, input_code)
        self.assertEqual(result.strip(), expected_output_code.strip())

    # TODO: Fix and implement    
    @pytest.mark.xfail
    def test_run_from_command_to_mezcla(self):
        """Test the working of the script through command line/stdio (--to_standard option)"""
        
        input_code = """
import os
os.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
os.remove("/tmp/fubar.list")
        """
        expected_code = """
import os
from mezcla import glue_helpers as gh
gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")
gh.delete_file("/tmp/fubar.list")
"""
        input_file = gh.create_temp_file(contents=input_code)
        command = f"python3 mezcla/mezcla_to_standard.py --to_mezcla {input_file}"
        result = gh.run(command)
        self.assertEqual(result.strip(), expected_code.strip())
    
    # TODO: Fix and implement
    @pytest.mark.xfail
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

        input_file = gh.create_temp_file(contents=input_code)
        command = f"python3 mezcla/mezcla_to_standard.py --to_standard {input_file}"
        result = gh.run(command)
        self.assertEqual(result.strip(), expected_code.strip())


    ## NOTE: This test passed, however, result_temp is same as result (i.e. to_mezcla not working as expected)
    # @pytest.mark.xfail
    def test_conversion_to_mezcla_round_robin(self):
        """Test conversion of script in round robin (e.g. mezcla -> standard -> mezcla)"""
        
        std_code = """
import posix
posix.rename("/tmp/fubar.list1", "/tmp/fubar.list2")
posix.remove("/tmp/fubar.list")
        """
        
        to_mezcla = THE_MODULE.ToMezcla()
        result_temp = THE_MODULE.transform(to_mezcla, std_code)
        to_standard = THE_MODULE.ToStandard()
        result = THE_MODULE.transform(to_standard, result_temp)
        self.assertEqual(result, std_code)
    
    ## NOTE: This test failed due to ToMezcla class not working as expected
    @pytest.mark.xfail
    def test_conversion_to_standard_round_robin(self):
        """Test conversion of script in round robin (e.g. standard -> mezcla -> standard)"""
        
        mezcla_code = """
from mezcla import glue_helpers as gh
gh.rename_file("/tmp/fubar.list1", "/tmp/fubar.list2")
gh.delete_file("/tmp/fubar.list")
        """
        
        to_mezcla = THE_MODULE.ToMezcla()
        to_standard = THE_MODULE.ToStandard()
        result_temp = THE_MODULE.transform(to_standard, mezcla_code)
        result = THE_MODULE.transform(to_mezcla, result_temp)
        # DEBUG: print(result, "="*20, result_temp)
        self.assertEqual(result, mezcla_code)



if __name__ == '__main__':
    debug.trace_current_context()
    pytest.main([__file__])