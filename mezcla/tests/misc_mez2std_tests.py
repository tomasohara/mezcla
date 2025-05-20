#! /usr/bin/env python3
#
# Note:
# - This is work-in-progress code in much need of improvement.
# - For example, the code was adapted from type hinting checks,
#   but not sufficiently updated (see type-hinting-integration repo).
# - To disable caching of pytests, use the PYTEST_ADDOPTS environment variable externally
#   $ export PYTEST_ADDOPTS="--cache-clear"
#
# TODO0:
# - Rework the tests to be less brittle. This might be added to Github actions with
#   other code check scripts to be run once a week or so. Therefore, a single failure
#   should not cause the test suite to fail. Instead, use percentage thresholds.
#
# TODO1:
# - Remember to check for mezcla wrappers before calling functions directly (e.g., for
#   tracing and sanity checks):
#      $ para-grep getsize ~/mezcla/*.py
#   where para-grep defined in tomohara-aliases.bash of companion shell-scripts repo
# - This is good for one's pre-commit checklist (e.g., along with running python-lint).
#
# TODO2:
# - Try to make output easier to review for pytest summary.
#
# TODO3:
# - Keep most comments focused on high-level, covering the intention of the code.
#   Avoid getting into the nitty-gritty details unless it is a tricky algorithm.
#   (Moreover, tricky algorithms in general should be avoided unless critical.)
#
# TODO4:
# - Avoid numbering steps, because it becomes a maintenance issue.
# - Similarly, avoid references like "script 1", etc.
#

"""
Miscellaneous tests for mezcla_to_standard module
"""

# Standard packages
import difflib

# Installed packages
import pytest
from pydantic import BaseModel

# Local packages
from mezcla import system, debug, glue_helpers as gh, misc_utils
from mezcla.my_regex import my_re
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
from mezcla.tests.common_module import RUN_SLOW_TESTS, fix_indent

# Constants, including environment variables
MEZCLA_DIR = gh.form_path(gh.dir_path(__file__), "..")
debug.assertion(system.file_exists(gh.form_path(MEZCLA_DIR, "debug.py")))
MIN_MEZCLA_SCRIPTS_COUNT = 50
LINE_IMPORT_PYDANTIC = "from pydantic import validate_call\n"
TEST_GLOB = system.getenv_value(
    "TEST_GLOB",
    None,
    description="Specify glob pattern for files to test"
)
TEST_FILES = system.getenv_value(
    "TEST_FILES",
    None,
    description="Comma-separated list of files to test"
)
debug.assertion(not (TEST_GLOB and TEST_FILES))
SKIP_WARNINGS = system.getenv_bool(
    "SKIP_WARNINGS", 
    False,
    description="Skip warning comments for tests without standard equivalents"
)
OMIT_SLOW_TESTS = not (RUN_SLOW_TESTS or TEST_GLOB or TEST_FILES)
OMIT_SLOW_REASON = "this will take a while"

## OLD: class ScriptComparison(BaseModel)
class ScriptComparisonMetrics(BaseModel):
    """Pydantic model for tracking script conversion metrics"""
    original_script: str
    converted_script: str
    total_original_lines: int
    total_converted_lines: int
    lines_added: int
    lines_removed: int
    lines_warned: int


class TestM2SBatchConversion(TestWrapper):
    """Class for batch conversion of test usage of equivalent calls for mezcla_to_standard"""

    script_module = "mezcla.mezcla_to_standard"

    def setup_test_directories(self, temp_base):
        """Setup and create required test directories"""
        dirs = {
            'typehint_org': f"{temp_base}-typehint_org",
            'typehint_m2s': f"{temp_base}-typehint_m2s",
            'mezcla_m2s': f"{temp_base}-mezcla_m2s",
            'pytest_org': f"{temp_base}-pytest_org",
            'pytest_m2s': f"{temp_base}-pytest_m2s"
        }
        for dir_path in dirs.values():
            system.create_directory(dir_path)   
        return dirs

    def process_pytest_results(self, pytest_output):
        """Extract pass/fail counts from pytest output"""
        failed = sum(map(int, my_re.findall(r"(\d+) x?failed", pytest_output)))
        passed = sum(map(int, my_re.findall(r"(\d+) x?passed", pytest_output)))
        return passed, failed
    
    def count_methods(self, code_content):
        """
        Count number of method definitions in code.
        
        Args:
            code_content: String containing the code to analyze
            
        Returns:
            Number of method definitions found
        """
        method_pattern = r"^\s*def\s+\w+\s*\(.*\):"
        # return sum(1 for _ in my_re.findall(r"^\s*def\s+\w+\s*\(.*\):", code_content, my_re.MULTILINE))
        return len(my_re.findall(method_pattern, code_content, my_re.MULTILINE))


    def validate_mez2std_conversion(self, script_path, dirs, m2s_path):
        """Process single script conversion and validation"""
        script = gh.basename(script_path)
        
        output, output_file = self.get_mezcla_command_output(
            m2s_path=m2s_path,
            script_path=script_path,
            option="to-standard",
            output_path=dirs['mezcla_m2s']
        )
        
        transformed_org = self.transform_for_validation(script_path)
        script_path_org = gh.form_path(dirs['typehint_org'], script)
        system.write_file(filename=script_path_org, text=transformed_org)
        
        transformed_m2s = self.transform_for_validation(output_file)
        script_path_m2s = gh.form_path(dirs['typehint_m2s'], script)
        system.write_file(filename=script_path_m2s, text=transformed_m2s)
        
        return {
            'script': script,
            'method_count': self.count_methods(output),
            'org_path': script_path_org,
            'm2s_path': script_path_m2s
        }
    
    def calculate_failure_metrics(self, validation_results, num_scripts):
        """Calculate and validate failure metrics"""
        fail_count = 0
        for result in validation_results:
            total_count = sum(result['m2s_passed'])
            if result['m2s_passed'][1] > result['org_passed'][1]:
                fail_count += 1
            bad_pct = round(fail_count * 100 / total_count, 2) if total_count else 0
            debug.assertion(bad_pct < 20)
            
        overall_bad_pct = round(fail_count * 100 / num_scripts, 2) if num_scripts else 0
        return overall_bad_pct
    
    # TEMPORARILY COMMENTED
    def run_validation_tests(self, script_info, dirs):
        """Run and compare validation tests for original and converted code"""
        # Create and run tests for original
        test_file_org = self.create_test_file(script_info['org_path'], dirs['typehint_org'])
        pytest_result_org = gh.run(f"PYTHONPATH='{dirs['typehint_org']}' pytest {test_file_org}")
        
        # Create and run tests for converted
        test_file_m2s = self.create_test_file(script_info['m2s_path'], dirs['typehint_m2s'])
        pytest_result_m2s = gh.run(f"PYTHONPATH='{dirs['typehint_m2s']}' pytest {test_file_m2s}")
        
        # Save test results
        org_result_path = gh.form_path(dirs['pytest_org'], gh.basename(script_info['script'], '.py')) + '.txt'
        m2s_result_path = gh.form_path(dirs['pytest_m2s'], gh.basename(script_info['script'], '.py')) + '.txt'
        # system.write_file(pytest_result_org, org_result_path)
        # system.write_file(pytest_result_m2s, m2s_result_path)
        system.write_file(org_result_path, pytest_result_org)
        system.write_file(m2s_result_path, pytest_result_m2s)
        
        return {
            'org_passed': self.process_pytest_results(pytest_result_org),
            'm2s_passed': self.process_pytest_results(pytest_result_m2s),
            'result_paths': (org_result_path, m2s_result_path)
        }

    def get_mezcla_scripts(self):
        """Returns list of paths for python scripts in MEZCLA_DIR.
        Note: Uses TEST_GLOB or TEST_FILES instead if defined
        """
        file_names = []
        if TEST_GLOB:
            file_names = gh.get_matching_files(TEST_GLOB)
        elif TEST_FILES:
            file_names = misc_utils.extract_string_list(TEST_FILES)
        else:
            file_names = [f for f in system.read_directory(MEZCLA_DIR) if f.endswith(".py")]
        debug.trace_expr(6, file_names)
        result = [(gh.form_path(MEZCLA_DIR, f) if not system.file_exists(f) else f)
                  for f in file_names]
        debug.trace(5, f"get_mezcla_scripts() => {result!r}")
        return result

    # Helper Script: Get the output of the execution of mezcla_to_standard.py (w/ options)
    def get_mezcla_command_output(self, m2s_path, script_path, option, skip_warnings=SKIP_WARNINGS, output_path="/dev/null"):
        """Executes the mezcla script externally (option: to_standard, metrics)"""
        warning_option = ("--skip-warnings" if skip_warnings else "")
        if output_path != "/dev/null":
            output_file = f"{output_path}/_mez2std_{gh.basename(script_path, '.py')}.py"
            command = f"python3 {m2s_path} --{option} {script_path} {warning_option} | tee {output_file}"
        else:
            output_file = output_path
            command = f"python3 {m2s_path} --{option} {script_path} {warning_option} > {output_path}"
        print("\nCommand from get_mezcla_command_output:", command)
        output = gh.run(command)
        return output, output_file

    # Helper Script: Get absolute path of "mezcla_to_standard.py"
    ## OLD_NAME: get_m2s_path
    def get_mezcla_to_standard_script_path(self):
        """Returns the path of mezcla_to_standard.py"""        
        return gh.form_path(MEZCLA_DIR, "mezcla_to_standard.py")

    # Helper Script: Use Pydantic class to find comparison in the script
    ## OLD_NAME: compare_scripts
    def helper_compare_converted_scripts(self, original_script_path: str, converted_script_path: str) -> ScriptComparisonMetrics:
        """Uses Pydantic to compare the contents between the original & converted scripts"""
        original_code = system.read_file(original_script_path)
        converted_code = system.read_file(converted_script_path)
        
        original_lines = original_code.splitlines()
        converted_lines = converted_code.splitlines()

        diff = difflib.unified_diff(original_code.splitlines(), converted_code.splitlines())
        differences = [line for line in diff if line.strip()]

        lines_added = len([line for line in differences if line.startswith("+") and not line.startswith("+++")])
        lines_removed = len([line for line in differences if line.startswith("-") and not line.startswith("---")])
        lines_warned = len([line for line in converted_lines if 'WARNING not supported' in line])

        return ScriptComparisonMetrics(
            original_script=original_script_path,
            converted_script=converted_script_path,
            differences=differences,
            total_original_lines=len(original_lines),
            total_converted_lines=len(converted_lines),
            lines_added=lines_added,
            lines_removed=lines_removed,
            lines_warned=lines_warned
        )
    
    ## OLD_NAME: calculate_score
    def helper_calculate_heuristic_score(
            self, 
            lines_original: int, 
            lines_converted: int,
            lines_added: int,
            lines_removed: int, 
            lines_warned: int,
            epsilon: float = 0.001,
            wt_size_difference: float = 0.40,
            wt_added: float = 0.25,
            wt_removed: float = 0.25,
            wt_warning: float = 0.10
        ):
        """
        Calculates a highly sensitive efficiency score based on the changes made during conversion,
        with increased emphasis on line changes and size differences.
        
        Arguments:
            lines_original: Number of lines in the original script.
            lines_converted: Number of lines in the converted script.
            lines_added: Number of lines added during conversion.
            lines_removed: Number of lines removed during conversion.
            lines_warned: Number of warnings generated.
            epsilon: A small value to prevent division by zero.
            wt_size_difference, wt_added, wt_removed, wt_warning: Weights for each metric.
            
        Returns:
            A normalized efficiency score between 0.0 and 1.0.
        """
        if lines_original == 0 or lines_converted <= 1:
            return 0.0

        size_ratio = min(1.0, abs(lines_converted - lines_original) / (lines_original + epsilon))
        line_add_ratio = min(1.0, lines_added / (lines_original + epsilon))
        line_removed_ratio = min(1.0, lines_removed / (lines_original + epsilon))
        line_warning_ratio = min(1.0, lines_warned / (lines_original + epsilon))

        # Penalize if warnings exceed 10% of original lines
        if lines_warned > lines_original * 0.1:  
            wt_warning += 0.1
            wt_size_difference -= 0.05

        weighted_sum = (
            size_ratio * wt_size_difference +
            line_add_ratio * wt_added +
            line_removed_ratio * wt_removed +
            line_warning_ratio * wt_warning
        )

        minimal_change_bonus = 0.02 if (size_ratio < 0.05 and line_warning_ratio < 0.05) else 0.0
        result = max(0.0, min(1.0, 1.0 - weighted_sum + minimal_change_bonus))
        return round(result, 4)

    def transform_for_validation(self, file_path):
        """Creates a copy of the script for validation of argument calls (using pydantic)"""
        content = system.read_file(file_path)
        content = my_re.sub(r"^def", r"@validate_call\ndef", content, flags=my_re.MULTILINE)
        content = LINE_IMPORT_PYDANTIC + content
        return content

    def create_test_function(self, module_name, function_name):
        """Creates a test function template for a given function name"""
        code = (
            f"""
            def test_{function_name}():
                from {module_name} import {function_name}
                assert callable({function_name})
                # Add appropriate function calls and assertions here
                try:
                    {function_name}()  # Example call, modify as needed
                except Exception as e:
                    assert False, f"Function {function_name} raised an exception: {{e}}"
            """
            )
        result = fix_indent(code)
        debug.trace(6, f"create_test_function({module_name}, {function_name}) => {result!r}")
        return result

    def create_test_file(self, script_path, test_dir):
        """Creates a test file for a given script"""
        script_name = gh.basename(script_path, ".py")
        function_names = self.extract_function_names(script_path)
        test_file_content = "\n".join([self.create_test_function(script_name, fn) for fn in function_names])
        test_file_dir = gh.form_path(test_dir, "tests")
        system.create_directory(test_file_dir)
        test_file_path = gh.form_path(test_file_dir, f"test_{script_name}.py")
        system.write_file(filename=test_file_path, text=test_file_content)
        return test_file_path

    def extract_function_names(self, file_path):
        """Extracts function names from a script"""
        content = system.read_file(file_path)
        return my_re.findall(r"^def (\w+)", content, flags=my_re.MULTILINE)

    ## EXPERIMENTAL: check_mezcla_wrappers in converted
    def check_mez2std_wrappers(self, converted_code: str) -> dict:
        """Check for proper use of mezcla wrappers in converted code"""
        wrapper_stats = {
            'direct_calls': [],
            'wrapper_calls': []
        }
        
        wrapper_patterns = {
            'getsize': r'(?:gh\.file_size|os\.path\.getsize)',
        }
        
        for func, *_ in wrapper_patterns.items():
            direct_calls = my_re.findall(rf'(?<!gh\.){func}\(', converted_code)
            wrapper_calls = my_re.findall(rf'gh\.{func}\(', converted_code)

            if direct_calls:
                wrapper_stats['direct_calls'].extend(direct_calls)
            if wrapper_calls:
                wrapper_stats['wrapper_calls'].extend(wrapper_calls)
                
        return wrapper_stats

    ## TOFIX: TestM2SBatchConversion.test_check_mez2std_wrappers() missing 2 required positional arguments: 'converted_code' and 'expected'
    @pytest.mark.skipif(OMIT_SLOW_TESTS, reason=OMIT_SLOW_REASON)
    @pytest.mark.parametrize("converted_code, expected", [
        (
            """
            import os
            def analyze_file(file_path):
                size = os.path.getsize(file_path)
                return size
            def get_wrapper_size(file_path):
                size = gh.file_size(file_path)
                return size
            """,
            {
                'direct_calls': ['getsize('],
                'wrapper_calls': ['file_size(']
            }
        ),
        (
            """
            def another_function():
                return gh.file_size('/path/to/file')
            """,
            {
                'direct_calls': [],
                'wrapper_calls': ['file_size(']
            }
        ),
        (
            """
            def no_calls_here():
                return "Nothing interesting"
            """,
            {
                'direct_calls': [],
                'wrapper_calls': []
            }
        )
    ])
    def test_check_mez2std_wrappers(self, converted_code, expected):
        """Test for check_mez2std_wrappers function in the test script"""
        result = self.check_mez2std_wrappers(converted_code)
        assert result == expected, f"Failed for input:\n{converted_code}"
    
    @pytest.mark.xfail
    @pytest.mark.skipif(OMIT_SLOW_TESTS, reason=OMIT_SLOW_REASON)
    def test_mez2std_heuristic(self):
        """
        Tests the conversion quality of mezcla scripts using various heuristic metrics.
        
        This test evaluates script conversion efficiency by:
        - Processing multiple scripts
        - Checking individual script efficiency
        - Tracking overall conversion success
        """
        
        scripts = self.get_mezcla_scripts()
        if not scripts:
            pytest.skip("No scripts found to test")
        
        m2s_path = self.get_mezcla_to_standard_script_path()
        output_dir = gh.get_temp_dir()
        
        # Initialize metrics tracking
        metrics = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'efficiency_scores': [],
            'clean_conversions': 0,
            'warned_conversions': 0,
            'failed_scripts': []
        }
        
        print("\nProcessing scripts for heuristic evaluation:")
        
        for script_path in scripts:
            script_name = gh.basename(script_path)
            metrics['processed'] += 1
            print(f"\nScript {metrics['processed']}/{len(scripts)}: {script_name}")
            
            try:
                # Execute mezcla command and generate output
                output, output_file = self.get_mezcla_command_output(
                    m2s_path=m2s_path,
                    script_path=script_path,
                    option="to-standard",
                    output_path=output_dir
                )
                
                # Validate output file generation
                if not gh.file_exists(output_file):
                    raise RuntimeError("Conversion failed - no output file generated")
                
                # Track warning status
                if "WARNING" in output:
                    metrics['warned_conversions'] += 1
                else:
                    metrics['clean_conversions'] += 1
                
                # Compare original and converted scripts
                comparison = self.helper_compare_converted_scripts(script_path, output_file)
                
                # Calculate efficiency score
                efficiency = self.helper_calculate_heuristic_score(
                    lines_original=comparison.total_original_lines,
                    lines_converted=comparison.total_converted_lines,
                    lines_added=comparison.lines_added,
                    lines_removed=comparison.lines_removed,
                    lines_warned=comparison.lines_warned
                )
                
                # Printing script metrics
                print(
                    "\nScript Metrics (Lines):",
                    "\nOriginal:", comparison.total_original_lines,
                    "\nConverted:", comparison.total_converted_lines,
                    "\nAdded:", comparison.lines_added,
                    "\nRemoved:", comparison.lines_removed,
                    "\nWarned:", comparison.lines_warned
                )


                # Assert individual script efficiency
                assert efficiency >= 0.75, (
                    f"Script {script_name} efficiency ({efficiency:.2f}) "
                    "below minimum threshold (0.75)"
                )
                
                metrics['efficiency_scores'].append(efficiency)
                metrics['successful'] += 1
                
                # Print script processing details
                print(f"✓ Processed successfully (Efficiency: {efficiency:.2f})")

            except Exception as e:
                # Track and report failed scripts
                metrics['failed'] += 1
                metrics['failed_scripts'].append((script_name, str(e)))
                print(f"✗ Failed: {str(e)}")
        
        # Print test summary
        self.print_test_summary(metrics)

        # Calculate and validate overall test performance
        success_rate = (metrics['successful'] / metrics['processed']) * 100
        avg_efficiency = (
            sum(metrics['efficiency_scores']) / metrics["processed"] 
            if metrics['efficiency_scores'] else 0
        )

            
        assert success_rate >= 80, (
            f"Success rate ({success_rate:.1f}%) below minimum threshold (80%)"
        )
        assert avg_efficiency >= 0.75, (
            f"Average efficiency ({avg_efficiency:.2f}) below minimum threshold (0.75)"
        )
    
    # Check that 50+ scripts are collected
    def test_get_mezcla_scripts(self):
        """Tests if all Python3 scripts are in MEZCLA_DIR"""
        min_mezcla_scripts_count = (MIN_MEZCLA_SCRIPTS_COUNT
                                    if not (TEST_GLOB or TEST_FILES) else 1)
        assert len(self.get_mezcla_scripts()) >= min_mezcla_scripts_count    

    ## OLD_NAME: test_mezcla_scripts_batch_conversion(self):
    @pytest.mark.xfail
    @pytest.mark.skipif(OMIT_SLOW_TESTS, reason=OMIT_SLOW_REASON)
    def test_mez2std_batch_conversion(self):
        """Test for batch conversion of mezcla scripts to standard scripts."""
        print("\n=== Starting Batch Conversion Test (mez2std) ===\n")
        scripts = self.get_mezcla_scripts()
        if not scripts:
            print("[ERROR] No mezcla scripts found for conversion.")
            return
        
        print(f"[DEBUG] Found {len(scripts)} mezcla scripts to process.")
        
        m2s_path = self.get_mezcla_to_standard_script_path()
        if not m2s_path:
            print("[ERROR] Conversion script path is not set.")
            return

        print(f"[DEBUG] Conversion script path: {m2s_path}")
        
        output_path = gh.get_temp_dir()
        if not output_path:
            print("[ERROR] Temporary directory for output is not available.")
            return

        print(f"[DEBUG] Output directory: {output_path}\n")

        ## NEW: Added stats for tracking successful conversions 
        successful_conversions = 0
        total_scripts = len(scripts)

        for idx, script_path in enumerate(scripts, start=1):
            script_name = gh.basename(script_path)
            print(f"\n# [DEBUG {idx}/{len(scripts)}] Processing script: {script_name}")

            # Attempt to run the conversion command
            try:
                ## OLD: Unused variable 'output'
                # output, output_file = self.get_mezcla_command_output(
                #     m2s_path=m2s_path, 
                #     script_path=script_path, 
                #     option="to-standard", 
                #     output_path=output_path
                # )
                output_file = self.get_mezcla_command_output(
                    m2s_path=m2s_path, 
                    script_path=script_path, 
                    option="to-standard", 
                    output_path=output_path
                )[1]

                print(f"[DEBUG] Command output file: {output_file}")
            except Exception as e:
                print(f"[ERROR] Failed to run conversion command for {script_name}: {e}")
                continue

            # Check if the output file was created
            if not gh.file_exists(output_file):
                print(f"[ERROR] Output file not generated for {script_name}.")
                continue

            try:
                original_size = gh.file_size(script_path)
                converted_size = gh.file_size(output_file)
                print(f"[DEBUG] Original size: {original_size} bytes, Converted size: {converted_size} bytes")

                assert 0.8 * original_size <= converted_size <= 1.2 * original_size, (
                    f"\n[ERROR] Converted size {converted_size} bytes is not within 20% of the original size {original_size} bytes"
                )
            except Exception as e:
                print(f"[ERROR] File size comparison failed for {script_name}: {e}")
                continue

             # Check content integrity
            try:
                converted_content = system.read_file(output_file)
                if not converted_content.strip():
                    print(f"[ERROR] Converted file {output_file} is empty.")
                else:
                    line_count = len(converted_content.splitlines())
                    print(f"[DEBUG] Converted file {output_file} contains {line_count} lines.")
                    successful_conversions += 1
            except Exception as e:
                print(f"[ERROR] Failed to read converted file {output_file}: {e}")
                continue

        # Validate the output directory contents
        try:
            converted_files = gh.get_matching_files(gh.form_path(output_path, "*.py"))
            print(f"[DEBUG] Converted files in output directory: {len(converted_files)}")
            assert len(converted_files) == len(scripts), (
                f"[ERROR] Mismatch in expected ({len(scripts)}) and actual converted files ({len(converted_files)})."
            )
        except Exception as e:
            print(f"[ERROR] Final directory verification failed: {e}")

        print("\n=== Batch Conversion Test Completed ===\n")

        # Assert that at least 80% of scripts were converted successfully
        success_percentage = (successful_conversions / total_scripts) * 100
        assert success_percentage >= 80, (
            f"[ERROR] Only {success_percentage:.2f}% of scripts converted successfully. "
            f"Expected at least 80%. Successful conversions: {successful_conversions}/{total_scripts}"
        )
        print(f"[SUCCESS]: {successful_conversions} out of {total_scripts} passed (Efficiency: {success_percentage}% >= 80%)")


    ## COMMENTED: Activities performed by test_mez2std_heuristic
    ## NOTE: Could be seen as an alternative to calculate detailed efficiency
    ## OLD_NAME: def test_mezcla_scripts_metrics
    # @pytest.mark.xfail
    # @pytest.mark.skipif(OMIT_SLOW_TESTS, reason=OMIT_SLOW_REASON)   
    # def test_mez2std_conversion_efficiency(self, threshold=25):
    #     """Tests external scripts through mezcla using metrics option (TODO: Write better description)
    #     Note: Provides alternative "conversion efficiency" to test_mezcla_scripts_compare
    #     """
    #     ## TODO2: better motivate the use of the "efficiency" metric and use a better threshold
    #     debug.trace(6, f"test_exteral_scripts({self})")
        
    #     print(f"\nEfficiency Scores (out of 100 / threshold={threshold}):\n")
    #     # Run conversion
    #     scripts = self.get_mezcla_scripts()[0]
    #     m2s_path = self.get_m2s_path()
    #     option = "metrics"
    #     output_path = "/dev/null"

    #     for idx, script_path in enumerate(scripts, start=1):
    #         script = gh.basename(script_path)
    #         output, _output_file = self.get_mezcla_command_output(m2s_path, script_path, option, output_path)

    #         # Use regex to search calls replaced and warnings added
    #         calls_replaced = my_re.search(r"Calls replaced:\t(\d+)", output)
    #         warnings_added = my_re.search(r"Warnings added:\t(\d+)", output)
    #         calls_replaced_num = int(calls_replaced.group(1)) if calls_replaced else None
    #         warnings_added_num = int(warnings_added.group(1)) if warnings_added else None

    #         efficiency = (
    #             round((calls_replaced_num * 100) / (calls_replaced_num + warnings_added_num), 2)
    #             if calls_replaced_num != warnings_added_num
    #             else 0
    #         )
    #         print(f"#{idx} {script}: {efficiency}")
    #         assert efficiency >= threshold

    ## NEW: Alternative pytest metrics to check conversion efficiency
    @pytest.mark.xfail
    @pytest.mark.skipif(OMIT_SLOW_TESTS, reason=OMIT_SLOW_REASON)
    def test_mez2std_conversion_efficiency(self, efficiency_threshold=0.7):
        """
        Evaluates conversion efficiency using a multi-factor scoring.
        
        Complexity Score Calculation:
        - Considers calls replaced vs warnings added
        - Penalizes scripts with high warning-to-replacement ratio
        - Provides overall conversion complexity assessment
        """
        print("\n=== Starting Mezcla Conversion Complexity Analysis ===\n")

        
        scripts = self.get_mezcla_scripts()
        if not scripts:
            print("[ERROR] No mezcla scripts found for analysis.")
            return
        
        m2s_path = self.get_mezcla_to_standard_script_path()
        if not m2s_path:
            print("[ERROR] Conversion script path is not set.")
            return

        total_scripts = len(scripts)
        complexity_scores = []

        for idx, script_path in enumerate(scripts, start=1):
            script_name = gh.basename(script_path)
            print(f"\n[ANALYSIS {idx}/{total_scripts}] Processing script: {script_name}")

            try:
                output, *_ = self.get_mezcla_command_output(
                    m2s_path=m2s_path, 
                    script_path=script_path, 
                    option="metrics", 
                    output_path="/dev/null"
                )

                # Extract metrics using regex
                calls_replaced = my_re.search(r"Calls replaced:\t(\d+)", output)
                warnings_added = my_re.search(r"Warnings added:\t(\d+)", output)
                
                calls_replaced_num = int(calls_replaced.group(1)) if calls_replaced else 0
                warnings_added_num = int(warnings_added.group(1)) if warnings_added else 0

                # Calculate complexity score
                total_modifications = calls_replaced_num + warnings_added_num
                if total_modifications > 0:
                    complexity_score = (
                        calls_replaced_num / total_modifications
                    )
                else:
                    complexity_score = 0

                complexity_scores.append(complexity_score)
                
                print(f"[DEBUG] {script_name}: Calls Replaced = {calls_replaced_num}, "
                      f"Warnings Added = {warnings_added_num}, "
                      f"Complexity Score = {complexity_score:.2f}")

            except Exception as e:
                print(f"[ERROR] Analysis failed for {script_name}: {e}")
                complexity_scores.append(0)

        # Calculate overall metrics
        avg_complexity = sum(complexity_scores) / total_scripts if complexity_scores else 0
        
        print("\n=== Conversion Complexity Analysis Summary ===")
        print(f"Total Scripts Analyzed: {total_scripts}")
        print(f"Average Complexity Score: {avg_complexity:.2f}")
        print(f"Complexity Threshold Score: {efficiency_threshold:.2f}")

        # Assert that the average complexity meets the threshold
        assert avg_complexity >= efficiency_threshold, (
            f"[ERROR] Average complexity score {avg_complexity:.2f} "
            f"is below the required threshold of {efficiency_threshold}"
        )

    # NEW: Test summary print handled by a different method
    def print_test_summary(self, metrics: dict):
        """Prints a detailed summary of test results based on the metrics."""
        print("\n=== Heuristic Test Summary ===")
        print(f"Total Scripts Processed: {metrics['processed']}")
        
        print("\nConversion Statistics:")
        print(f"- Successful Conversions: {metrics['successful']}")
        print(f"- Failed Conversions: {metrics['failed']}")
        success_rate = (metrics['successful'] / metrics['processed']) * 100 if metrics['processed'] > 0 else 0
        print(f"- Success Rate: {success_rate:.1f}%")
        
        print("\nQuality Metrics:")
        print(f"- Clean Conversions: {metrics['clean_conversions']}")
        print(f"- Conversions with Warnings: {metrics['warned_conversions']}")
        avg_efficiency = (sum(metrics['efficiency_scores']) / metrics["processed"]
                        if metrics['efficiency_scores'] else 0)
        print(f"- Average Efficiency Score: {avg_efficiency:.2f}")
        
        if metrics['failed_scripts']:
            print("\nFailed Scripts:")
            for script, error in metrics['failed_scripts']:
                print(f"- {script}: {error}")
        
        print()

if __name__ == "__main__":
    debug.trace_current_context()
    invoke_tests(__file__)
