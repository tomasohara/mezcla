#! /usr/bin/env python3
#
# Test(s) for ../gpu_utils.py
#
# Notes:
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_gpu_utils.py
#
#-------
# Sample tested output
#
# Sat Mar  2 17:27:08 2024       
# +---------------------------------------------------------------------------------------+
# | NVIDIA-SMI 535.98                 Driver Version: 535.98       CUDA Version: 12.2     |
# |-----------------------------------------+----------------------+----------------------+
# | GPU  Name                 Persistence-M | Bus-Id        Disp.A | Volatile Uncorr. ECC |
# | Fan  Temp   Perf          Pwr:Usage/Cap |         Memory-Usage | GPU-Util  Compute M. |
# |                                         |                      |               MIG M. |
# |=========================================+======================+======================|
# |   0  NVIDIA GeForce RTX 3080        Off | 00000000:01:00.0  On |                  N/A |
# |  0%   50C    P8              33W / 320W |   4786MiB / 10240MiB |      0%      Default |
# |                                         |                      |                  N/A |
# +-----------------------------------------+----------------------+----------------------+
# |   1  Quadro P400                    Off | 00000000:05:00.0  On |                  N/A |
# | 34%   43C    P0              N/A /  N/A |    130MiB /  2048MiB |      0%      Default |
# |                                         |                      |                  N/A |
# +-----------------------------------------+----------------------+----------------------+

"""Tests for gpu_utils module"""

# Standard modules
## TODO: from collections import defaultdict

# Installed modules
import pytest

# Local modules
from mezcla.unittest_wrapper import TestWrapper, invoke_tests
## TODO: from mezcla.unittest_wrapper import trap_exception
from mezcla import debug
from mezcla.my_regex import my_re
from mezcla import system


# Note: Two references are used for the module to be tested:
#    THE_MODULE:                        global module object
#    TestIt.script_module:              path to file
import mezcla.gpu_utils as THE_MODULE

#------------------------------------------------------------------------

class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)

    @pytest.mark.xfail                   # TODO: remove xfail
    ## DEBUG: @trap_exception         ## TODO: from mezcla import glue_helpers as gh
    # TODO: remove when debugged
    def test_01_data_file(self):
        """Tests run_script w/ data file"""
        debug.trace(4, f"TestIt.test_01_data_file(); self={self}")
        output = self.run_script(options="", log_file=self.temp_file)
        log_contents = system.read_file(self.temp_file)
        self.do_assert(not output.strip())
        self.do_assert(my_re.search(r"not.*direct.*invocation", log_contents.strip().lower()))
        return

    @pytest.mark.skipif(not THE_MODULE.HAS_CUDA, reason="No CUDA support")
    @pytest.mark.xfail                   # TODO: remove xfail
    def test_02_gpu_usage(self):
        """TODO: flesh out test for whatever (capsys-like)"""
        debug.trace(4, f"TestIt2.test_02_whatever(); self={self}")
        THE_MODULE.trace_gpu_usage(level=1)
        captured = self.get_stderr()
        self.do_assert(my_re.search(r"NVIDIA-SMI\s+\S+\s+Driver Version:\s+\S+\s+CUDA.Version:\s+\S+",
                                    captured))
        return

    @pytest.mark.xfail                   # TODO: remove xfail
    def test_03_type_hints(self):
        """Test out validation via pydantic"""
        # NOTE: This will not work until there is automatic support for pydantic type checking,
        # TODO2: write gpu_utils.py with validation decorators to to temp mezcla repo and invoke pytest using that repo
        # TODO?: mod="gpu_utils.py"; tmp_dir="/tmp/mezcla"; mkdir -p $tmp_dir $tmp_dir/tests; perl -pe 's/^def /\@valdate_call\n$&/;' $mod | perl -0777 -pe 's/^import/from pydantic import validate_call\n$&/;' >| $tmp_dir/$mod; copy-force tests/test_$mod $tmp_dir/tests/test_$mod; PYTHONPATH="$tmp_dir" pytest --runxfail $tmp_dir/tests/test_$mod
        debug.trace(4, f"TestIt2.test_03_type_hints(); self={self}")
        captured = self.get_stderr()
        try:
            THE_MODULE.trace_gpu_usage(level="two")
        except:
            pass
        assert("ValidationError" in captured)
    
#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
