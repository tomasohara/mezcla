"""
Misc tests for mezcla_to_standard module
"""

# Standard packages
## NOTE: this is empty for now
import os
import difflib
from typing import List

# Installed packages
import pytest
from pydantic import BaseModel

# Local packages
import mezcla.mezcla_to_standard as THE_MODULE
from mezcla import system, debug, glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla.unittest_wrapper import TestWrapper

# Constants
MEZCLA_DIR = gh.form_path(gh.dir_path(__file__), "..")
MEZCLA_SCRIPTS_COUNT = 58

# Environment Variables
RUN_SLOW_TESTS = system.getenv_bool(
    "RUN_SLOW_TESTS", 
    False,
    description="Run tests that can a while to run"
)

# Pydantic Class with Base Model
class ScriptComparison(BaseModel):
    original_script: str
    converted_script: str
    differences: List[str]
    total_original_lines: int
    total_converted_lines: int
    lines_added: int
    lines_removed: int
    lines_warned: int


class TestM2SBatchConversion(TestWrapper):
    """Class for batch conversion of test usage of equivalent calls for mezcla_to_standard"""

    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    
    def get_mezcla_scripts(self):
        # Helper Script 1: Collect all mezcla scripts from MEZCLA_DIR (i.e. .py files)
        """Returns an array of all Python3 scripts in MEZCLA_DIR"""
        return [x for x in os.listdir(MEZCLA_DIR) if x.endswith(".py")]
    
    def get_mezcla_command_output(self, m2s_path, script_path, option, output_path="/dev/null"):
        # Helper Script 2: Get the output of the execution of mezcla_to_standard.py (w/ options)        
        """Executes the mezcla script externally (option: to_standard, metrics)"""
        if output_path != "/dev/null":
            output_file = f"{output_path}/_mez2std_{gh.basename(script_path, '.py')}.py"
            command = f"python3 {m2s_path} --{option} {script_path} | tee {output_file}"
        else:
            output_file = ""
            command = f"python3 {m2s_path} --{option} {script_path} > {output_path}"
        output = gh.run(command)
        return output, output_file
    
    def get_m2s_path(self):
        # Helper Script 3: Get absolute path of "mezcla_to_standard.py"
        """Returns the path of mezcla_to_standard.py"""        
        return gh.form_path(MEZCLA_DIR, "mezcla_to_standard.py")

    def compare_scripts(self, original_script_path: str, converted_script_path: str) -> ScriptComparison:
        # Helper Script 4: Use Pydantic class to find comparision in the script
        """Uses Pydantic to compare the contents between the original & converted scripts"""
        original_code = system.read_file(original_script_path)
        converted_code = system.read_file(converted_script_path)
        
        original_lines = original_code.splitlines()
        converted_lines = converted_code.splitlines()

        diff = difflib.unified_diff(original_code.splitlines(), converted_code.splitlines())
        differences = [line for line in diff if line.strip()]
        
        lines_added = sum(1 for line in differences if line.startswith("+") and not line.startswith("+++"))
        lines_removed = sum(1 for line in differences if line.startswith("-") and not line.startswith("---"))
        lines_warned = sum(1 for line in converted_lines if 'WARNING not supported' in line)

        return ScriptComparison(
            original_script=original_script_path,
            converted_script=converted_script_path,
            differences=differences,
            total_original_lines=len(original_lines),
            total_converted_lines=len(converted_lines),
            lines_added=lines_added,
            lines_removed=lines_removed,
            lines_warned=lines_warned
        )
    
    def calculate_score(
            self, 
            lines_original:int, 
            lines_converted:int,
            lines_added:int,
            lines_removed:int, 
            lines_warned:int,
            epsilon:float = 0.001,
            wt_difference:float = 0.25,
            wt_added:float = 0.25,
            wt_removed:float = 0.25,
            wt_warning:float = 0.25
        ):
        """Calculates difference score using the above arguments and returns an efficiency score"""
        # Distribute the weights (maximum 1 when combined) if necessary
        line_diff_ratio = abs(lines_converted - lines_original)/(lines_original + epsilon)
        line_add_ratio = abs(lines_added)/(lines_original + epsilon)
        line_removed_ratio = abs(lines_removed)/(lines_original + epsilon)
        line_warning_ratio = abs(lines_warned)/(lines_original + epsilon)
        return 1 - (
            line_diff_ratio*wt_difference + 
            line_add_ratio*wt_added + 
            line_removed_ratio*wt_removed +
            line_warning_ratio*wt_warning 
        )
    
    
    def test_get_mezcla_scripts(self):
        # Test 1: Check all 58 scripts are collected 
        """Returns an array of all Python3 scripts in MEZCLA_DIR"""
        assert len(self.get_mezcla_scripts()) == MEZCLA_SCRIPTS_COUNT

    def test_mezcla_scripts_compare(self, threshold=0.75):
        # Test 2: Find the differences between the tests and optionally set a threshold for differences
        """Tests for comparing mezcla scripts with the original scripts"""
        scripts = self.get_mezcla_scripts()
        m2s_path = self.get_m2s_path()
        option = "to_standard"
        output_path = gh.get_temp_dir()

        for idx, script in enumerate(scripts, start=1):
            script_path = gh.form_path(MEZCLA_DIR, script)
            output, output_file = self.get_mezcla_command_output(m2s_path, script_path, option, output_path)
            comparison = self.compare_scripts(script_path, output_file)
            print(f"\n#{idx} Differences between {script_path} and {output_file}:")
            print("Lines Original:", comparison.total_original_lines)
            print("Lines Converted:", comparison.total_converted_lines)
            print("Lines Added:", comparison.lines_added)
            print("Lines Removed:", comparison.lines_removed)
            print("Warning Lines:", comparison.lines_warned)
            
            score = self.calculate_score(
                lines_original = comparison.total_original_lines,
                lines_converted = comparison.total_converted_lines,
                lines_added = comparison.lines_added,
                lines_removed = comparison.lines_removed,
                lines_warned = comparison.lines_warned
            )
            print("Score =", score)
            assert (score >= threshold)

    
    @pytest.mark.skip
    def test_mezcla_scripts_batch_conversion(self):
        """Test for batch conversion of mezcla scripts to standard script"""
        # Test 3: Batch Conversion (from mezcla to standard)

        print("\nBatch Conversion (mez2std):\n")
        scripts = self.get_mezcla_scripts()
        m2s_path = self.get_m2s_path()
        option = "to_standard"
        output_path = gh.get_temp_dir()

        for idx, script in enumerate(scripts, start=1):
            script_path = gh.form_path(MEZCLA_DIR, script)
            output, output_file = self.get_mezcla_command_output(m2s_path, script_path, option, output_path)
            
            # # Assertion A: Check file integrity (syntax errors)
            # try:
            #     converted_integrity_1 = ast.parse(source=output)
            #     converted_integrity_2 = ast.parse(source=system.read_file(output_file))
            # except SyntaxError:
            #     converted_integrity_1, converted_integrity_2 = None, None
            # # assert converted_integrity is not None
            # print(f"#{idx} {script} -> {output_file}\n\t{converted_integrity_1} \\ {converted_integrity_2}")

            print(f"#{idx} {script} -> {output_file}")

            # Assertion B: Check if for each script, there exists no empty file or error files
            assert len(output.split("\n")) > 5

            # Assertion C: Check similarly between file content (file_size between +/- 20%)
            original_size = os.path.getsize(script_path)
            converted_size = os.path.getsize(output_file)
            assert 0.8 * original_size <= converted_size <= 1.2 * original_size

        # Assertion: Check if a converted output file exists for each script in mezcla
        assert len(os.listdir(output_path)) == len(scripts)

    @pytest.mark.skip    
    def test_mezcla_scripts_metrics(self, threshold=0):
        """Tests external scripts through mezcla using metrics option (TODO: Write better description)"""
        debug.trace(6, f"test_exteral_scripts({self})")
        
        print(f"\nEfficiency Scores (out of 100 / threshold={threshold}):\n")
        # Run conversion
        scripts = self.get_mezcla_scripts()
        m2s_path = self.get_m2s_path()
        option = "metrics"
        output_path = "/dev/null"

        for idx, script in enumerate(scripts, start=1):
            script_path = gh.form_path(MEZCLA_DIR, script)
            output, output_file = self.get_mezcla_command_output(m2s_path, script_path, option, output_path)

            # Use regex to search calls replaced and warnings added
            calls_replaced = my_re.search(r"Calls replaced:\t(\d+)", output)
            warnings_added = my_re.search(r"Warnings added:\t(\d+)", output)
            calls_replaced_num = int(calls_replaced.group(1)) if calls_replaced else None
            warnings_added_num = int(warnings_added.group(1)) if warnings_added else None

            efficiency = (
                round((calls_replaced_num * 100) / (calls_replaced_num + warnings_added_num), 2)
                if calls_replaced_num != warnings_added_num
                else 0
            )
            print(f"#{idx} {script}: {efficiency}")
            assert efficiency >= threshold

if __name__ == "__main__":
    debug.trace_current_context()
    pytest.main([__file__])
