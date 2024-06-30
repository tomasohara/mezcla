"""
Misc tests for mezcla_to_standard module
"""

# Standard packages
## NOTE: this is empty for now
import os

# Installed packages
import pytest

# Local packages
import mezcla.mezcla_to_standard as THE_MODULE
from mezcla import system, debug, glue_helpers as gh
from mezcla.my_regex import my_re
from mezcla.unittest_wrapper import TestWrapper

# Constants
MEZCLA_DIR = gh.form_path(gh.dir_path(__file__), "..")

class TestM2SBatchConversion(TestWrapper):
    """Class for batch conversion of test usage of equivalent calls for mezcla_to_standard"""

    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    
    # HELPER SCRIPT: COLLECT MEZCLA SCRIPTS
    def get_mezcla_scripts(self):
        """Returns an array of all Python3 scripts in MEZCLA_DIR"""
        return [x for x in os.listdir(MEZCLA_DIR) if x.endswith(".py")]
    
    def test_get_mezcla_scripts(self):
        """Returns an array of all Python3 scripts in MEZCLA_DIR"""
        assert len(self.get_mezcla_scripts()) == 58
    
    # HELPER SCRIPT: 
    def get_mezcla_command_output(self, m2s_path, script_path, option, output_path="/dev/null"):
        """Executes the mezcla script externally (option: to_standard, metrics)"""
        if output_path != "/dev/null":
            output_file = f"{output_path}/_mez2std_{gh.basename(script_path, '.py')}.py"
            command = f"python3 {m2s_path} --{option} {script_path} | tee {output_file}"
        else:
            output_file = ""
            command = f"python3 {m2s_path} --{option} {script_path} > {output_path}"
        output = gh.run(command)
        return output, output_file
    
    # HELPER SCRIPT: GET FULL PATH TO "mezcla_to_standard.py"
    def get_m2s_path(self):
        """Returns the path of mezcla_to_standard.py"""
        return gh.form_path(MEZCLA_DIR, "mezcla_to_standard.py")

    # TEST 1: Batch Conversion (from mezcla to standard)
    def test_mezcla_scripts_batch_conversion(self):
        """Test for batch conversion of mezcla scripts to standard script"""
        
        print("\nBatch Conversion (mez2std):\n")
        scripts = self.get_mezcla_scripts()
        m2s_path = self.get_m2s_path()
        option = "to_standard"
        output_path = gh.get_temp_dir()

        for idx, script in enumerate(scripts, start=1):
            script_path = gh.form_path(MEZCLA_DIR, script)
            output, output_file = self.get_mezcla_command_output(m2s_path, script_path, option, output_path)
            print(f"#{idx} {script} -> {output_file}")

            # Assertion: Check if for each script, there exists no empty file or error files
            assert len(output.split("\n")) > 5

            # Assertion: Check similarly between file content (file_size between +/- 20%)
            original_size = os.path.getsize(script_path)
            converted_size = os.path.getsize(output_file)
            assert 0.8 * original_size <= converted_size <= 1.2 * original_size


        # Assertion: Check if a converted output file exists for each script in mezcla
        assert len(os.listdir(output_path)) == len(scripts)

        
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