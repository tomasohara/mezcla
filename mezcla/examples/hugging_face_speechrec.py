#! /usr/bin/env python
#
# Uses the Hugging Face API for automatic speech recognition (ASR).
#
# Based on following:
#   https://stackoverflow.com/questions/71568142/how-can-i-extract-and-store-the-text-generated-from-an-automatic-speech-recognit
#
# TODO:
# - Add chunking to handle large file:
#     https://huggingface.co/blog/asr-chunking
#

"""Speech recognition via Hugging Face"""

# Standard modules
# TODO: import re

# Intalled module
import gradio as gr
from transformers import pipeline

# Local modules
from mezcla import debug
## from mezcla.main import Main, dummy_app
from mezcla import system
## TODO:
## from mezcla import glue_helpers as gh

# Constants
TL = debug.TL

## TODO:
## # Environment options
## # Notes:
## # - These are just intended for internal options, not for end users.
## # - They also allow for enabling options in one place rather than four
## #   when using main.Main (e.g., [Main member] initialization, run-time
## #   value, and argument spec., along with string constant definition).
## #
## ENABLE_FUBAR = system.getenv_bool("ENABLE_FUBAR", False,
##                                   description="Enable fouled up beyond all recognition processing")

ASR_TASK = "automatic-speech-recognition"
# TODO: WHISPER = getenv...("whisper-large"); DEFAULT_MODEL = ...
DEFAULT_MODEL = "facebook/s2t-medium-librispeech-asr"
ASR_MODEL = system.getenv_text("ASR_MODEL", DEFAULT_MODEL,
                               "Hugging Face model for ASR")

#-------------------------------------------------------------------------------

SOUND_FILE = system.getenv_text("SOUND_FILE", "data/ljspeech.wav",
                                "Audio file with speech to recognize")
USE_INTERFACE = system.getenv_bool("USE_INTERFACE", False,
                                   "Use web-based interface via gradio")

def main():
    """Entry point"""
    debug.trace(TL.USUAL, f"main(): script={system.real_path(__file__)}")

    ## BAD:
    ## model = pipeline(task="automatic-speech-recognition",
    ##                  model="facebook/s2t-medium-librispeech-asr")
    model = pipeline(task=ASR_TASK, model=ASR_MODEL)

    if USE_INTERFACE:
        pipeline_if = gr.Interface.from_pipeline(
            model,
            title="Automatic Speech Recognition (ASR)",
            ## OLD: description="Using pipeline with Facebook S2T for ASR.",
            description="Using pipeline with default",
            examples=[SOUND_FILE])
        pipeline_if.launch()
    else:
        print(model(SOUND_FILE))

    return

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    main()