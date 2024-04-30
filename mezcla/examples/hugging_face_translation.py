#! /usr/bin/env python
#
# Uses the Hugging Face API for machine translation (MT)
#
# Based on:
# - https://stackoverflow.com/questions/71568142/how-can-i-extract-and-store-the-text-generated-from-an-automatic-speech-recognit #pylint: disable=line-too-long
# - Hugging Face's NLP with Transformers text
#

"""Machine translation via Hugging Face

Example:

echo "How now Bourne cow?" | FROM=en TO=es {script} -

USE_INTERFACE=1 {script} -
"""

# Standard modules
## TODO: import json

# Intalled modules
# Note: done dynamically below

# Local modules
from mezcla import debug
from mezcla.main import Main, USE_PARAGRAPH_MODE
# TODO2: add new mezcla.hugging_face module for common stuff
import mezcla.examples.hugging_face_speechrec as hf_speechrec
from mezcla import misc_utils
from mezcla.my_regex import my_re
from mezcla import system
from mezcla import glue_helpers as gh

# Constants and Environment options
TL = debug.TL

FROM = system.getenv_text("FROM", "es")
TO = system.getenv_text("TO", "en")
SOURCE_LANG = system.getenv_text("SOURCE_LANG", FROM,
                                 "Source language")
TARGET_LANG = system.getenv_text("TARGET_LANG", TO,
                                 "Target language")
debug.assertion(SOURCE_LANG != TARGET_LANG)
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
UI_ARG = "ui"

USE_GPU = system.getenv_bool("USE_GPU", True, "Uses Torch on GPU if True")
MAX_LENGTH = system.getenv_int("MAX_LENGTH", 512, "Maximum Length of Tokens")
TEXT_FILE = system.getenv_text("TEXT_FILE", "-",
                               "Text file to translate")
USE_INTERFACE = system.getenv_bool("USE_INTERFACE", False,
                                   "Use web-based interface via gradio")

#-------------------------------------------------------------------------------

def show_gpu_usage(trace_level=None):
    """Show nvidia usage if under GPU"""
    if trace_level is None:
        trace_level = 5
    if (hf_speechrec.TORCH_DEVICE == "GPU"):
        debug.code(trace_level, lambda: debug.trace(1, gh.run("nvidia-smi")))
    return


def main():
    """Entry point"""
    debug.trace(TL.USUAL, f"main(): script={system.real_path(__file__)}")

    # Show simple usage if --help given
    dummy_app = Main(description=__doc__.format(script=gh.basename(__file__)),
                     skip_input=False, manual_input=True,
                     boolean_options=[
                         ## TODO3: (ELAPSED_ARG, "Show elapsed time")],
                         (UI_ARG, "Invoke user interface")],
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
    MT_TASK = f"translation_{source_lang}_to_{target_lang}"                 # pylint: disable=invalid-name
    MT_MODEL = f"Helsinki-NLP/opus-mt-{source_lang}-{target_lang}"          # pylint: disable=invalid-name
    mt_task = dummy_app.get_parsed_option(TASK_ARG, MT_TASK)
    mt_model = dummy_app.get_parsed_option(MODEL_ARG, MT_MODEL)
    use_interface = dummy_app.get_parsed_option(UI_ARG, USE_INTERFACE)

    # Get input file
    debug.trace_expr(5, dummy_app.input_stream, text, TEXT_FILE)
    text_file = TEXT_FILE
    if ((text is not None) or use_interface):
        pass
    elif text_file == "-":
        text_file = dummy_app.temp_file
        text = dummy_app.read_entire_input()
    else:
        text = system.read_file(text_file)

    # Load PyTorch and Hugging Face pipeline support
    # pylint: disable=import-outside-toplevel
    torch = hf_speechrec.init_torch_etc()
    debug.trace_expr(4, torch)
    if torch is None:
        import torch
        debug.trace_expr(4, torch)
    from transformers import pipeline   
    
    # Load Model
    device = torch.device(hf_speechrec.TORCH_DEVICE)
    debug.trace_expr(5, device)
    model = pipeline(task=mt_task, model=mt_model, device=device)

    # Pull up web interface if requested
    if use_interface:
        # TODO2: add language controls
        import gradio as gr             # pylint: disable=import-outside-toplevel
        pipeline_if = gr.Interface.from_pipeline(
            model,
            title="Machine translation (MT)",
            ## TODO2: subtitle=f"From: {FROM}; To: {TO}",
            description=f"From: {FROM}; To: {TO}",
            ## TODO3: examples=[...]); See example in hf_stable_diffusion.py.
            )
        pipeline_if.launch()

    # Otherwise, do translation and output
    else:
        TRANSLATION_TEXT = "translation_text"
        split_regex = r"\n\s*\n" if USE_PARAGRAPH_MODE else "\n"
        for segment in my_re.split(split_regex, text):
            try:
                translation = model(segment, max_length=MAX_LENGTH)
                debug.assertion(isinstance(translation, list)
                                and (TRANSLATION_TEXT in translation[0]))
                print(translation[0].get(TRANSLATION_TEXT) or "")
            except:
                system.print_exception_info("translation")
            show_gpu_usage()

    # Wrap up
    show_gpu_usage()
    return

#-------------------------------------------------------------------------------

if __name__ == '__main__':
    elapsed = misc_utils.time_function(main)
    if SHOW_ELAPSED:
        print(f"Elapsed time: {system.round_as_str(elapsed)}ms")
