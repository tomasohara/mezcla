#! /usr/bin/env python
#
# Utilities for working with GPU's such as via PyTorch or using NVIDIA commands.
#
#

"""GPU support"""

# Standard modules
## TODO: import numpy

# Installed modules
import torch

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import system

# Constants
TL = debug.TL
#
# Environment-based
HAS_CUDA = torch.cuda.is_available()
USE_CPU = system.getenv_bool(
    "USE_CPU", False,
    description="Uses Torch on CPU if True")
TORCH_DEVICE_DEFAULT = ("cpu" if (USE_CPU or not HAS_CUDA) else "cuda")
TORCH_DEVICE = system.getenv_text(
    "TORCH_DEVICE", TORCH_DEVICE_DEFAULT,
    description="Device for running torch"
)

#-------------------------------------------------------------------------------

def trace_gpu_usage(level=TL.DETAILED):
    """Trace out usage for GPU memory, etc.
    TODO: support other types besides NVidia"""
    if TORCH_DEVICE == "cuda":
        debug.trace(level, "GPU usage")
        debug.trace(level, gh.run("nvidia-smi"))


#-------------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    system.print_error("Warning: Not intended for direct invocation.")
