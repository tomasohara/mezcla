#! /usr/bin/env python
#
# Uses the Hugging Face API for machine translation (MT)
#
# Based on:
# - https://stackoverflow.com/questions/71568142/how-can-i-extract-and-store-the-text-generated-from-an-automatic-speech-recognit
# - Hugging Face's NLP with Transformers text
#

"""Machine translation via Hugging Face

Example:

echo "How now Bourne cow?" | FROM=en TO=es {script} -

USE_INTERFACE=1 {script} -
"""

# Standard modules
# TODO: import re

# Intalled module
## OLD: import gradio as gr
## TODO: import transformers
## OLD: from transformers import pipeline

# Local modules
from mezcla import debug
from mezcla.main import Main
# TODO2: add new mezcla.hugging_face module for common stuff
from mezcla.examples.hugging_face_speechrec import TORCH_DEVICE
from mezcla import misc_utils
from mezcla import system
from mezcla import glue_helpers as gh

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

FROM = system.getenv_text("FROM", "es")
TO = system.getenv_text("TO", "en")
SOURCE_LANG = system.getenv_text("SOURCE_LANG", FROM,
                                 "Source language")
TARGET_LANG = system.getenv_text("TARGET_LANG", TO,
                                 "Target language")
debug.assertion(SOURCE_LANG != TARGET_LANG)
## OLD:
## MT_TASK = f"translation_{SOURCE_LANG}_to_{TARGET_LANG}"
## DEFAULT_MODEL = f"Helsinki-NLP/opus-mt-{SOURCE_LANG}-{TARGET_LANG}"
## OLD:
## MT_MODEL = system.getenv_value("MT_MODEL", None,
##                                "Hugging Face model for MT")
SHOW_ELAPSED = system.getenv_bool("SHOW_ELAPSED", False,
                                  "Show elapsed time")
MAX_LENGTH = system.getenv_value(
    "MAX_LENGTH", None,
    description="Optional maximum length of tokens")

TEXT_ARG = "text"
FROM_ARG = "from"
TO_ARG = "to"
## TODO: ELAPSED_ARG = "elapsed-time"
TASK_ARG = "task"
MODEL_ARG = "model"

#-------------------------------------------------------------------------------

TEXT_FILE = system.getenv_text("TEXT_FILE", "-",
                               "Text file to translate")
USE_INTERFACE = system.getenv_bool("USE_INTERFACE", False,
                                   "Use web-based interface via gradio")

# Optionally load UI support
gr = None
if USE_INTERFACE:
    import gradio as gr                 # pylint: disable=import-error


def main():
    """Entry point"""
    debug.trace(TL.USUAL, f"main(): script={system.real_path(__file__)}")

    # Show simple usage if --help given
    ## OLD: dummy_app = Main(description=__doc__, skip_input=False, manual_input=False)
    dummy_app = Main(description=__doc__.format(script=gh.basename(__file__)),
                     skip_input=False, manual_input=True,
                     ## TODO: bool_options=[(ELAPSED_ARG, "Show elapsed time")],
                     text_options=[
                         (FROM_ARG, "Source language code"),
                         (TO_ARG, "Target language code"),
                         (TASK_ARG, "Translation task"),
                         (MODEL_ARG, "Model for translation"),
                         (TEXT_ARG, "Text to translate")])
    debug.trace_object(5, dummy_app)
    debug.assertion(dummy_app.parsed_args)
    text = dummy_app.get_parsed_option(TEXT_ARG)
    source_lang = dummy_app.get_parsed_option(FROM_ARG, SOURCE_LANG)
    target_lang = dummy_app.get_parsed_option(FROM_ARG, TARGET_LANG)
    #
    MT_TASK = f"translation_{source_lang}_to_{target_lang}"
    MT_MODEL = f"Helsinki-NLP/opus-mt-{source_lang}-{target_lang}"
    mt_task = dummy_app.get_parsed_option(TASK_ARG, MT_TASK)
    mt_model = dummy_app.get_parsed_option(MODEL_ARG, MT_MODEL)

    # Get input file
    text_file = TEXT_FILE
    if ((text is not None) or USE_INTERFACE):
        pass
    elif (text_file == "-"):
        text_file = dummy_app.temp_file
        text = dummy_app.read_entire_input()
    else:
        text = system.read_file(text_file)

    ## TEMP:
    ## pylint: disable=import-outside-toplevel
    import torch
    from transformers import pipeline
    ## OLD: model = pipeline(task=mt_task, model=mt_model)
    device = torch.device(TORCH_DEVICE)
    debug.trace_expr(5, device)
    model = pipeline(task=mt_task, model=mt_model, device=device)

    if USE_INTERFACE:
        # TODO2: add language controls
        pipeline_if = gr.Interface.from_pipeline(
            model,
            title="Machine translation (MT)",
            ## TODO2: subtitle=f"From: {FROM}; To: {TO}",
            ## OLD:
            ## description="Using pipeline with default",
            description=f"From: {FROM}; To: {TO}",
            ## examples=[text_file])
            )
        pipeline_if.launch()
    else:
        TRANSLATION_TEXT = "translation_text"
        try:
            translation = model(text)
            ## TODO3: max_length = (system.to_int(MAX_LENGTH) if MAX_LENGTH else min(len(text.split()) * 0.75, MODEL_MAX_LENGTH))
            ## BAD: translation = model(text, max_length=MAX_LENGTH)
            debug.assertion(isinstance(translation, list)
                            and (TRANSLATION_TEXT in translation[0]))
            print(translation[0].get(TRANSLATION_TEXT) or "")
        except:
            system.print_exception_info("translation")
    debug.code(5, lambda: debug.trace(1, gh.run("nvidia-smi")))

    return

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    ## OLD: main()
    elapsed = misc_utils.time_function(main)
    if SHOW_ELAPSED:
       print(f"Elapsed time: {system.round_as_str(elapsed)}ms")
