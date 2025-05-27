#! /usr/bin/env python3
#
# Utilities for working with GPU's such as via PyTorch or using NVIDIA commands.
#
#

"""GPU support"""

# Standard modules
from typing import Optional

# Installed modules
import torch

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import system

# Constants
TL = debug.TL
DEBUG_LEVEL = debug.get_level()
#
# Environment-based
HAS_CUDA = torch.cuda.is_available()
HAS_MPS = (hasattr(torch.backends, "mps") and torch.backends.mps.is_available())
USE_CPU = system.getenv_bool(
    "USE_CPU", False,
    description="Uses Torch on CPU if true")
## OLD: TORCH_DEVICE_DEFAULT = ("cpu" if (USE_CPU or not HAS_CUDA) else "cuda")
TORCH_DEVICE_DEFAULT = ("cuda" if HAS_CUDA else "mps" if HAS_MPS else "cpu")
TORCH_DEVICE = system.getenv_text(
    "TORCH_DEVICE", TORCH_DEVICE_DEFAULT,
    description="Device for running torch"
)
GPU_DEBUG_LEVEL = system.getenv_int(
    "GPU_DEBUG_LEVEL", TL.DETAILED,
    desc="Default trace level for trace_gpu_usage, etc.")

#-------------------------------------------------------------------------------

def trace_gpu_usage(level: Optional[int] = None, show_if_disabed: Optional[bool] = False):
    """Trace out usage for GPU memory, etc.
    Note: This used nvidia-smi and is omitted for non-CUDA unless SHOW_IF_DISABED.
    The optional level defaults to GPU_DEBUG_LEVEL.

    TODO: support other types besides NVidia"""
    if level is None:
        level = GPU_DEBUG_LEVEL
    if ((TORCH_DEVICE == "cuda") or show_if_disabed):
        debug.trace(level, "GPU usage")
        debug.trace(level, gh.run("nvidia-smi"))
    else:
        debug.trace(level, "No CUDA device enabled, so skipping nvidia-smi")
    ## DEBUG: debug.trace_expr(1, int(level), int(DEBUG_LEVEL), GPU_DEBUG_LEVEL)
    if level > DEBUG_LEVEL:
        debug.trace(TL.USUAL, "FYI: Use higher trace level with trace_gpu_usage (DEBUG_LEVEL >= $level)")
 

#-------------------------------------------------------------------------------
        
if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    system.print_error("Warning: Not intended for direct invocation.")
    debug.code(TL.USUAL, lambda: trace_gpu_usage())    # pylint: disable=unnecessary-lambda
