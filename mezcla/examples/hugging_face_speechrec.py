#! /usr/bin/env python3
#
# Uses the Hugging Face API for automatic speech recognition (ASR).
#
# Based on following:
# https://stackoverflow.com/questions/71568142/how-can-i-extract-and-store-the-text-generated-from-an-automatic-speech-recognit # pylint: disable=line-too-long
#
# TODO:
# - Add chunking to handle large file:
#     https://huggingface.co/blog/asr-chunking
#

"""Speech recognition via Hugging Face

Example:

{dir}/{script} {dir}/fuzzy-testing-1-2-3.wav

USE_INTERFACE=1 {script} -
"""

# Standard modules
# TODO: import re

# Installed modules
# Note: done dynamically below

# Local modules
from mezcla import debug
from mezcla.main import Main
from mezcla.my_regex import my_re
from mezcla import system
from mezcla import glue_helpers as gh

# Constants
TL = debug.TL

# Constants and Environment options
ASR_TASK = "automatic-speech-recognition"
# TODO: WHISPER = getenv...("whisper-large"); DEFAULT_MODEL = ...
DEFAULT_MODEL = "facebook/s2t-medium-librispeech-asr"
ASR_MODEL = system.getenv_text(
    "ASR_MODEL", DEFAULT_MODEL,
    description="Hugging Face model for ASR")
## OLD:
## USE_GPU = system.getenv_bool("USE_GPU", False, description="Uses Torch on GPU if True")
## TORCH_DEVICE_DEFAULT = ("cuda" if USE_GPU else "cpu")
## TORCH_DEVICE = system.getenv_text(
##     "TORCH_DEVICE", TORCH_DEVICE_DEFAULT,
##     description="Torch device to use")

SOUND_FILE = system.getenv_text("SOUND_FILE", "fuzzy-testing-1-2-3.wav",
                                "Audio file with speech to recognize")
USE_INTERFACE = system.getenv_bool("USE_INTERFACE", False,
                                   "Use web-based interface via gradio")

# Globals
TORCH_DEVICE = None
torch = None

#-------------------------------------------------------------------------------

# Optionally load UI support
## TODO2: rework following hugging_face_translation.py
gr = None                               # pylint: disable=invalid-name
if USE_INTERFACE:
    import gradio as gr                 # pylint: disable=import-error

def init_torch_etc():
    """Load in supporting packages like torch
    note: returns torch module object for sake of clients
    """
    # pylint: disable=redefined-outer-name, import-outside-toplevel
    debug.trace(4, "init_torch_etc()")

    # Import torch
    global torch
    import torch                        # pylint: disable=import-outside-toplevel
    HAS_CUDA = torch.cuda.is_available()
    debug.trace_expr(5, torch.__version__, HAS_CUDA)

    # Determine device to use, with fallack to CPU if no cuda
    ## TODO2: rename TORCH_DEVICE as torch_device (because not a constant)
    global TORCH_DEVICE
    USE_CPU = system.getenv_bool(
        "USE_CPU", False,
        description="Uses Torch on CPU if True")
    TORCH_DEVICE_DEFAULT = ("cpu" if (USE_CPU or not HAS_CUDA) else "cuda")
    TORCH_DEVICE = system.getenv_text(
        "TORCH_DEVICE", TORCH_DEVICE_DEFAULT,
        description="Torch device to use")
    return torch

def main():
    """Entry point"""
    debug.trace(TL.USUAL, f"main(): script={system.real_path(__file__)}")

    # Show simple usage if --help given
    ## TODO2: rework script_dir fixup to os.path.delim or better yet split_path
    script_dir = gh.dirname(__file__)
    if script_dir.startswith(system.real_path(".")):
        script_dir = my_re.sub(fr"{system.real_path('.')}/?", "", script_dir)
    doc = __doc__.format(script=gh.basename(__file__),
                         dir=script_dir)
    dummy_app = Main(description=doc, skip_input=False, manual_input=False)

    # Resolve path for file
    sound_file = SOUND_FILE
    if not system.file_exists(sound_file):
        script_dir = gh.dirname(__file__)
        sound_file = gh.resolve_path(SOUND_FILE, base_dir=script_dir)
    if not system.file_exists(sound_file):
        system.exit(f"Error: unable to find SOUND_FILE '{sound_file}'")
    
    # Load "heavy" packages (delayed for sake of quicker usage)
    init_torch_etc()
    from transformers import pipeline   # pylint: disable=import-outside-toplevel

    # Load model
    device = torch.device(TORCH_DEVICE)
    model = pipeline(task=ASR_TASK, model=ASR_MODEL, device=device)

    # Show UI or transcribe input file
    if USE_INTERFACE:
        pipeline_if = gr.Interface.from_pipeline(
            model,
            title="Automatic Speech Recognition (ASR)",
            description="Using pipeline with default",
            examples=[sound_file])
        pipeline_if.launch()
    else:
        print((model(sound_file))["text"])
    return

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
