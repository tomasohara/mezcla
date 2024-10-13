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
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Constants and Environment options
TL = debug.TL
TRANSLATION_TEXT = "translation_text"

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
ROUND_ARG = "round"

USE_GPU = system.getenv_bool("USE_GPU", True, "Uses Torch on GPU if True")
MAX_LENGTH = system.getenv_int("MAX_LENGTH", 512, "Maximum Length of Tokens")
TEXT_FILE = system.getenv_text("TEXT_FILE", "-",
                               "Text file to translate")
USE_INTERFACE = system.getenv_bool("USE_INTERFACE", False,
                                   "Use web-based interface via gradio")

## NOTE: Round-trip translation: Translating text from one language to another and back to its original form
ROUND_TRIP = system.getenv_bool("ROUND_TRIP", False, 
                                "Perform round-trip translation")
## EXPERIMENT: Dynamic Chunking (disabled by default)
DYNAMIC_WORD_CHUNKING = system.getenv_bool("DYNAMIC_WORD_CHUNKING", False, 
                                "(Default: Sentence Chunking) Splits longer text input to chunks based on word count")

#-------------------------------------------------------------------------------

def show_gpu_usage(trace_level=None):
    """Show nvidia usage if under GPU"""
    if trace_level is None:
        trace_level = 5
    if (hf_speechrec.TORCH_DEVICE == "GPU"):
        debug.code(trace_level, lambda: debug.trace(1, gh.run("nvidia-smi")))
    return

def get_split_regex():
    if USE_PARAGRAPH_MODE:
        return r"\n\s*\n"
    elif not DYNAMIC_WORD_CHUNKING:
        return r'(?<=[.!?]) +'
    else:
        return None

def dynamic_chunking(text, max_len=MAX_LENGTH):
    if DYNAMIC_WORD_CHUNKING:
        words = text.split()
        chunks = [" ".join(words[i:i + max_len]) for i in range(0, len(words), max_len)]
    else:
        split_regex = get_split_regex()
        segments = my_re.split(split_regex, text)
        chunks = []
        current_chunk = []

        for segment in segments:
            if len(" ".join(current_chunk + [segment])) <= max_len:
                current_chunk.append(segment)
            else:
                chunks.append(" ".join(current_chunk))
                current_chunk = [segment]

        if current_chunk:
            chunks.append(" ".join(current_chunk))

    return chunks

# OLD: Translated Text
def translated_text(model_obj):
    TRANSLATION_TEXT = "translation_text"
    return model_obj[0][TRANSLATION_TEXT] or ""

def calculate_similarity(text1, text2):
    """Calculate the cosine similarity between the two strings"""
    vectorizer = TfidfVectorizer().fit_transform([text1, text2])
    vectors = vectorizer.toarray()
    return cosine_similarity(vectors)[0, 1]

def main():
    """Entry point"""
    debug.trace(TL.USUAL, f"main(): script={system.real_path(__file__)}")

    
    # Show simple usage if --help given
    dummy_app = Main(description=__doc__.format(script=gh.basename(__file__)),
                     skip_input=False, manual_input=True,
                     boolean_options=[
                         ## TODO3: (ELAPSED_ARG, "Show elapsed time")],
                         (UI_ARG, "Invoke user interface"),
                         (ROUND_ARG, "Enable round-trip translation")
                         ],
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
    # Round-trip from argument
    round_trip = dummy_app.get_parsed_option(ROUND_ARG, ROUND_TRIP)
    use_interface = dummy_app.get_parsed_option(UI_ARG, USE_INTERFACE)
    
    MT_TASK = f"translation_{source_lang}_to_{target_lang}"                 # pylint: disable=invalid-name
    MT_MODEL = f"Helsinki-NLP/opus-mt-{source_lang}-{target_lang}"          # pylint: disable=invalid-name
    mt_task = dummy_app.get_parsed_option(TASK_ARG, MT_TASK)
    mt_model = dummy_app.get_parsed_option(MODEL_ARG, MT_MODEL)


    ## OLD
    # ## Creating language models and tasks in reverse for round-trip translation
    # if round_trip:
    #     MT_TASK_REVERSE = f"translation_{target_lang}_to_{source_lang}"                 # pylint: disable=invalid-name
    #     MT_MODEL_REVERSE = f"Helsinki-NLP/opus-mt-{target_lang}-{source_lang}"          # pylint: disable=invalid-name  
    #     mt_task_reverse = dummy_app.get_parsed_option(TASK_ARG, MT_TASK_REVERSE)
    #     mt_model_reverse = dummy_app.get_parsed_option(MODEL_ARG, MT_MODEL_REVERSE)
    
    MT_TASK_REVERSE = f"translation_{target_lang}_to_{source_lang}"                 # pylint: disable=invalid-name
    MT_MODEL_REVERSE = f"Helsinki-NLP/opus-mt-{target_lang}-{source_lang}"          # pylint: disable=invalid-name  
    mt_task_reverse = dummy_app.get_parsed_option(TASK_ARG, MT_TASK_REVERSE)
    mt_model_reverse = dummy_app.get_parsed_option(MODEL_ARG, MT_MODEL_REVERSE)

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

    ## Create a model for reverse translation when ROUND_TRIP is true
    model_reverse = pipeline(task=mt_task_reverse, model=mt_model_reverse)

    # Pull up web interface if requested
    ## TODO: Advised by Tom (2024-08-25): Add side by side translation 
    ## CONTINUE: Keep the input box as it is, show translation in the bottom side-by-side (split sentences)
    ## CONTINUE: Add option (checkbox) to split words [maybe]
    ## CONTINUE: Show the translation in the tabular format (keep the original & translated box as usual)
    ## TODO: Add column for for round trip translation as well, also with round-trip score
    ## Example (for round-trip enabled)

    # | **Original**               | **Translated**               | **Round-Trip**                 | **Comparison Score** |
    # |----------------------------|------------------------------|--------------------------------|----------------------|
    # | Hello, how are you?        | Hola, ¿cómo estás?           | Hello, how are you?            | 1.0                  |
    # | I hope you are doing well. | Espero que estés bien.       | I hope you are doing well.     | 1.0                  |
    # | Let's meet tomorrow.       | Vamos a vernos mañana.       | Let's meet tomorrow.           | 1.0                  |


    ## COMPLETED: Checkbox for round trip translation and comparison score added 

    if use_interface:
        import gradio as gr
        from transformers import pipeline
        model_reverse = pipeline(task=mt_task_reverse, model=mt_model_reverse)

        def gradio_translation_input(word_src, is_round_trip):
            word_dst = model(word_src)[0]["translation_text"].split(".")[0]
            word_round_trip = model_reverse(word_dst)[0]["translation_text"].split(".")[0] if is_round_trip else ''
            similarity_score = calculate_similarity(word_src, word_round_trip) if is_round_trip else ""
            return word_dst, word_round_trip, similarity_score
        
        ui = gr.Interface(
            title="Hugging Face Language Translation (with round-trip similarity score)",
            description=f"From: {FROM} | To: {TO}",
            fn=gradio_translation_input,
            inputs=[
                gr.Textbox(lines=2, placeholder="Enter text to translate", label="Input Text"),
                gr.Checkbox(label="Enable Round-trip Translation"),
                # gr.Checkbox(label="Split Sentences"),
                # gr.Checkbox(label="Dynamic Chunking"),
            ],
            outputs=[
                gr.Textbox(label="Translated Text"),
                gr.Textbox(label="Round-trip Translation"),
                gr.Number(label="Similarity Score (0 to 1)")
            ],
        )
        ui.launch(share=False)


    ## Original Code (uncomment if too much f up)
    # if use_interface:
    #     # TODO2: add language controls
    #     ## TODO: Add option for round trip translation
    #     import gradio as gr             # pylint: disable=import-outside-toplevel
    #     pipeline_if = gr.Interface.from_pipeline(
    #         model,
    #         title="Machine translation (MT)",
    #         ## TODO2: subtitle=f"From: {FROM}; To: {TO}",
    #         description=f"From: {FROM}; To: {TO}",
    #         ## TODO3: examples=[...]); See example in hf_stable_diffusion.py.
    #         )
    #     pipeline_if.launch()

    # Otherwise, do translation and output
    else:
        TRANSLATION_TEXT = "translation_text"
        
        ## OLD: Before dynamic chunking (and get_split_regex function)
        # split_regex = r"\n\s*\n" if USE_PARAGRAPH_MODE else "\n"
        ## Avoid "I'm sorry" bug when reading from stdin
        # segments = my_re.split(split_regex, text)

        segments = dynamic_chunking(text)
        # print(segments)

        if segments[-1] == "":
            segments = segments[:-1]
        ## OLD:
        # for segment in my_re.split(split_regex, text)
        
        for segment in segments:
            try:
                # Translation Level I (FROM -> TO)
                translation = model(segment, max_length=MAX_LENGTH)
                ##### ERROR: CURRENT METHOD NOT APPLIED; WORKS WELL WITH 
                translation_text = translated_text(translation)
                
                ## Round-Trip translation uses the reverse model to re-translate back to original form
                if round_trip:
                    # Translation Level II (TO -> FROM_AUX)
                    translation_reverse = model_reverse(translation_text, max_length=MAX_LENGTH)
                    translation_reverse_text = translated_text(translation_reverse)
                    
                    # Translation Level III (FROM_AUX -> TO)
                    translation_round = model(translation_reverse_text, max_length=MAX_LENGTH)
                    translation_round_text = translated_text(translation_round)

                debug.assertion(isinstance(translation, list)
                                and (TRANSLATION_TEXT in translation[0]))
                translation_reverse_text = translation_reverse_text if round_trip else ''
                translation_round_text = translation_round_text if round_trip else ''

                ## OLD: Before round-trip translation
                # print(translation[0].get(TRANSLATION_TEXT) or "")
                
                ## For round trip translation, print all possible translations along with their language code
                if round_trip:
                    print(f"\nOriginal      ({FROM}):\n{segment}")
                    print(f"\nTranslate     ({TO}):\n{translation_text}")
                    print(f"\nOriginal  [R]   ({FROM}):\n{translation_reverse_text}")
                    print(f"\nTranslate [R]  ({TO}):\n{translation_round_text}")
                    round_trip_diff_original =  (segment != translation_reverse_text)
                    round_trip_diff_translate = (translation_round_text != translation_text)
                    round_trip_difference = round_trip_diff_original or round_trip_diff_translate
                    print(f"\nDifference in Translation: {round_trip_difference}\n")
                    
                    ## If there is any difference during round-trip translation, print the difference
                    if round_trip_difference:
                        print("="*40)
                        print(f"\nDifferences in Original ({FROM}):")
                        print(f"{misc_utils.string_diff(segment, translation_reverse_text) if round_trip_diff_original else None}")
                        print(f"Differences in Translated ({TO}):")
                        print(f"{misc_utils.string_diff(translation_text, translation_round_text) if round_trip_diff_translate else None}")
                else:
                    print(translation_text)
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
