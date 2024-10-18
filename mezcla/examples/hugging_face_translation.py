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
SOURCE_LANG = system.getenv_text("SOURCE_LANG", FROM, "Source language")
TARGET_LANG = system.getenv_text("TARGET_LANG", TO, "Target language")
debug.assertion(SOURCE_LANG != TARGET_LANG)
SHOW_ELAPSED = system.getenv_bool("SHOW_ELAPSED", False, "Show elapsed time")
MAX_LENGTH = system.getenv_value(
    "MAX_LENGTH", None, description="Optional maximum length of tokens"
)

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
TEXT_FILE = system.getenv_text("TEXT_FILE", "-", "Text file to translate")
USE_INTERFACE = system.getenv_bool(
    "USE_INTERFACE", False, "Use web-based interface via gradio"
)

## NOTE: Round-trip translation: Translating text from one language to another and back to its original form
ROUND_TRIP = system.getenv_bool("ROUND_TRIP", False, "Perform round-trip translation")
## EXPERIMENTAL: Dynamic Chunking (disabled by default)
DYNAMIC_WORD_CHUNKING = system.getenv_bool(
    "DYNAMIC_WORD_CHUNKING",
    False,
    "(Default: Sentence Chunking) Splits longer text input to chunks based on word count",
)
## EXPERIMENAL: Alternative Gradio Interface for multiple input fields
ALTERNATIVE_UI = system.getenv_int(
    "ALTERNATIVE_UI",
    2,
    "(Alternative to USE_INTERFACE) Use a gradio UI with multiple input sections",
)

# -------------------------------------------------------------------------------


def show_gpu_usage(trace_level: int = None) -> None:
    """
    Displays NVIDIA GPU usage information if the device is set to GPU.

    Parameters:
        trace_level (int, optional): The level of detail for tracing. Defaults to 5 if not provided.

    Returns:
        None: This function does not return a value, it only prints GPU usage information.

    Example:
        >>> show_gpu_usage()
        # Displays the GPU usage information with the default trace level.
    """
    if trace_level is None:
        trace_level = 5
    if hf_speechrec.TORCH_DEVICE == "GPU":
        debug.code(trace_level, lambda: debug.trace(1, gh.run("nvidia-smi")))
    return


def get_split_regex() -> str:
    """
    Get the regex to split the input words according to the environment variables or args

    Parameters:
        (none)
    Returns:
        str: A regex for spliting words
    """
    if USE_PARAGRAPH_MODE:
        return r"\n\s*\n"
    elif not DYNAMIC_WORD_CHUNKING:
        return r"(?<=[.!?]) +"
    else:
        return None


def dynamic_chunking(text: str, max_len: int = MAX_LENGTH) -> list:
    """
    Splits the input text into chunks based on word length or specified regex.

    Parameters:
        text (str): The input text to be chunked.
        max_len (int): The maximum number of words per chunk. Default is `MAX_LENGTH`.

    Returns:
        list: A list of text chunks, where each chunk contains words that do not exceed the specified length.

    Example:
        >>> dynamic_chunking("This is a simple test to demonstrate chunking.", max_len=5)
        ['This is a simple', 'test to demonstrate', 'chunking.']
    """

    if DYNAMIC_WORD_CHUNKING:
        words = text.split()
        chunks = [
            " ".join(words[i : i + max_len]) for i in range(0, len(words), max_len)
        ]
    else:
        # Get a suitable regex if DYNAMIC_WORD_CHUNKING is disabled
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


def translated_text(model_obj: list) -> str:
    """
    Retrieves the translated text from the model output.

    Parameters:
        model_obj (list): A list containing the model's output, where the first element
                          is expected to be a dictionary with a key 'translation_text'.

    Returns:
        str: The translated text if available; otherwise, an empty string.
    """

    TRANSLATION_TEXT = "translation_text"
    return model_obj[0][TRANSLATION_TEXT] or ""


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculates the cosine similarity between two strings.

    Parameters:
        text1 (str): The first string to compare.
        text2 (str): The second string to compare.

    Returns:
        float: A similarity score between 0 and 1, where 1 indicates identical strings
               and 0 indicates no similarity.
    """

    vectorizer = TfidfVectorizer().fit_transform([text1, text2])
    vectors = vectorizer.toarray()
    return cosine_similarity(vectors)[0, 1]


def main():
    """Entry point"""
    debug.trace(TL.USUAL, f"main(): script={system.real_path(__file__)}")

    # Show simple usage if --help given
    dummy_app = Main(
        description=__doc__.format(script=gh.basename(__file__)),
        skip_input=False,
        manual_input=True,
        boolean_options=[
            ## TODO3: (ELAPSED_ARG, "Show elapsed time")],
            (UI_ARG, "Invoke user interface"),
            (ROUND_ARG, "Enable round-trip translation"),
        ],
        text_options=[
            (FROM_ARG, "Source language code"),
            (TO_ARG, "Target language code"),
            (TASK_ARG, "Translation task"),
            (MODEL_ARG, "Model for translation"),
            (TEXT_ARG, "Text to translate"),
        ],
    )

    debug.trace_object(5, dummy_app)
    debug.assertion(dummy_app.parsed_args)
    text = dummy_app.get_parsed_option(TEXT_ARG)
    source_lang = dummy_app.get_parsed_option(FROM_ARG, SOURCE_LANG)
    target_lang = dummy_app.get_parsed_option(FROM_ARG, TARGET_LANG)
    # Round-trip from argument
    round_trip = dummy_app.get_parsed_option(ROUND_ARG, ROUND_TRIP)
    use_interface = dummy_app.get_parsed_option(UI_ARG, USE_INTERFACE)
    # alternative_ui = dummy_app.get_parsed_option(ALTERNATIVE_UI)


    MT_TASK = (
        f"translation_{source_lang}_to_{target_lang}"  # pylint: disable=invalid-name
    )
    MT_MODEL = f"Helsinki-NLP/opus-mt-{source_lang}-{target_lang}"  # pylint: disable=invalid-name
    mt_task = dummy_app.get_parsed_option(TASK_ARG, MT_TASK)
    mt_model = dummy_app.get_parsed_option(MODEL_ARG, MT_MODEL)

    MT_TASK_REVERSE = (
        f"translation_{target_lang}_to_{source_lang}"  # pylint: disable=invalid-name
    )
    MT_MODEL_REVERSE = f"Helsinki-NLP/opus-mt-{target_lang}-{source_lang}"  # pylint: disable=invalid-name
    mt_task_reverse = dummy_app.get_parsed_option(TASK_ARG, MT_TASK_REVERSE)
    mt_model_reverse = dummy_app.get_parsed_option(MODEL_ARG, MT_MODEL_REVERSE)

    # Get input file
    debug.trace_expr(5, dummy_app.input_stream, text, TEXT_FILE)
    text_file = TEXT_FILE
    if (text is not None) or use_interface:
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

    # Create a model for reverse translation when ROUND_TRIP is true
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

    if use_interface:

        import gradio as gr
        from transformers import pipeline

        def gradio_translation_input(
            *words_src: str, is_round_trip: bool = False
        ) -> tuple[str, str, float]:
            """
            Translates input words and optionally performs round-trip translation with overall similarity scoring.

            Parameters:
                words_src (str): Variable-length argument for input words to be translated.
                is_round_trip (bool): If True, performs round-trip translation and calculates a single similarity score for the entire sentence.

            Returns:
                tuple: A tuple containing:
                    - str: Translated words as a single string.
                    - str: Round-trip translated sentence as a single string (if `is_round_trip` is True).
                    - float: A similarity score between the original sentence and the round-trip translation,
                            where the score is between 0 and 1 (if `is_round_trip` is True); otherwise, returns 0.

            Example:
                >>> gradio_translation_input("Hello", "World", is_round_trip=True)
                ('Hola Mundo', 'Hello World', 0.98)
            """

            # Join all the input words into a single sentence
            sentence_src = " ".join(words_src)

            # Translate the sentence
            sentence_dst = model(sentence_src)[0]["translation_text"].split(".")[0]

            # Perform round-trip translation if requested
            if is_round_trip:
                sentence_round_trip = model_reverse(sentence_dst)[0][
                    "translation_text"
                ].split(".")[0]
                similarity_score = round(
                    calculate_similarity(sentence_src, sentence_round_trip), 4
                )
            else:
                sentence_round_trip = ""
                similarity_score = 0.0

            return sentence_dst, sentence_round_trip, similarity_score

        ## EXPERIMENTAL: Added supoort for alternative UI
        ## BUG: ValueError (empty vocabulary) occurs for single alphabets (e.g. 'I' as a word)
        # ValueError: empty vocabulary; perhaps the documents only contain stop words
        ## TODO: Include a checkbox to print the tuple in the output instead of a single sentence
        ## TODO: Include a checkbox to switch separators (either comma or spaces)

        if ALTERNATIVE_UI > 0:
            inputs = [
                gr.Textbox(label=f"Input {i+1}", lines=2) for i in range(ALTERNATIVE_UI)
            ]
            description = (
                f"From: {FROM} | To: {TO} | Alternative UI: {ALTERNATIVE_UI} inputs"
            )
        else:
            inputs = [
                gr.Textbox(
                    lines=2, placeholder="Enter text to translate", label="Input Text"
                ),
            ]
            description = f"From: {FROM} | To: {TO}"

        inputs.append(gr.Checkbox(label="Enable Round-trip Translation"))

        def interface_fn(*input_args: str) -> tuple:
            """
            Support function for gr.Interface() for ALTERNATIVE_UI
            """
            is_round_trip = input_args[-1]
            text_inputs = input_args[:-1]
            return gradio_translation_input(*text_inputs, is_round_trip=is_round_trip)

        # Create the Gradio interface for ALTERNATIVE_UI
        ui = gr.Interface(
            title="Hugging Face Language Translation",
            description=description,
            fn=interface_fn,
            inputs=inputs,
            outputs=[
                gr.Textbox(label="Translated Text"),
                gr.Textbox(label="Round-trip Translation"),
                gr.Number(label="Similarity Score (0 to 1)"),
            ],
        )
        ui.launch(share=False)

    else:
        TRANSLATION_TEXT = "translation_text"

        ## OLD: Before Dynamic Chunking support
        # split_regex = r"\n\s*\n" if USE_PARAGRAPH_MODE else "\n"
        # # Avoid "I'm sorry" bug when reading from stdin
        # segments = my_re.split(split_regex, text)
        segments = dynamic_chunking(text)
        if segments[-1] == "":
            segments = segments[:-1]

        for segment in segments:
            try:
                # Translation Level I (FROM -> TO)
                translation = model(segment, max_length=MAX_LENGTH)
                translation_text = translated_text(translation)

                ## Round-Trip translation uses the reverse model to re-translate back to original form
                if round_trip:
                    # Translation Level II (TO -> FROM_AUX)
                    translation_reverse = model_reverse(
                        translation_text, max_length=MAX_LENGTH
                    )
                    translation_reverse_text = translated_text(translation_reverse)

                    # Translation Level III (FROM_AUX -> TO)
                    translation_round = model(
                        translation_reverse_text, max_length=MAX_LENGTH
                    )
                    translation_round_text = translated_text(translation_round)

                debug.assertion(
                    isinstance(translation, list)
                    and (TRANSLATION_TEXT in translation[0])
                )
                translation_reverse_text = (
                    translation_reverse_text if round_trip else ""
                )
                translation_round_text = translation_round_text if round_trip else ""

                ## OLD: Before round-trip translation
                # print(translation[0].get(TRANSLATION_TEXT) or "")

                ## For round trip translation, print all possible translations along with their language code
                if round_trip:
                    print(f"\nOriginal      ({FROM}):\n{segment}")
                    print(f"\nTranslate     ({TO}):\n{translation_text}")
                    print(f"\nOriginal  [R]   ({FROM}):\n{translation_reverse_text}")
                    print(f"\nTranslate [R]  ({TO}):\n{translation_round_text}")
                    round_trip_diff_original = segment != translation_reverse_text
                    round_trip_diff_translate = (
                        translation_round_text != translation_text
                    )
                    round_trip_difference = (
                        round_trip_diff_original or round_trip_diff_translate
                    )
                    print(f"\nDifference in Translation: {round_trip_difference}\n")

                    ## If there is any difference during round-trip translation, print the difference
                    if round_trip_difference:
                        print("=" * 40)
                        print(f"\nDifferences in Original ({FROM}):")
                        print(
                            f"{misc_utils.string_diff(segment, translation_reverse_text) if round_trip_diff_original else None}"
                        )
                        print(f"Differences in Translated ({TO}):")
                        print(
                            f"{misc_utils.string_diff(translation_text, translation_round_text) if round_trip_diff_translate else None}"
                        )
                else:
                    print(translation_text)
            except Exception as e:
                system.print_exception_info("translation")

            show_gpu_usage()

    # Wrap up
    show_gpu_usage()
    return


# -------------------------------------------------------------------------------

if __name__ == "__main__":
    elapsed = misc_utils.time_function(main)
    if SHOW_ELAPSED:
        print(f"Elapsed time: {system.round_as_str(elapsed)}ms")
