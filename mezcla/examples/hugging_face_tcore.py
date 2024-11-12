#! /usr/bin/env python

## TODO: Write description in detail
# Improved version of hugging_face_translation.py
# Uses class based approach

"""
Refined version of hugging_face_translation.py using OOP
"""

# Standard modules
## TODO: import json

# Installed modules

# Local modules
from mezcla import debug
from mezcla.main import Main, USE_PARAGRAPH_MODE
import mezcla.examples.hugging_face_speechrec as hf_speechrec
from mezcla import misc_utils
from mezcla.my_regex import my_re
from mezcla import system
from mezcla import glue_helpers as gh

# Environment Variables
## TODO: Add getenv like functions
FROM = system.getenv_text("FROM", "es")
TO = system.getenv_text("TO", "en")
SOURCE_LANG = system.getenv_text("SOURCE_LANG", FROM, "Source language")
TARGET_LANG = system.getenv_text("TARGET_LANG", TO, "Target language")
MT_TASK = system.getenv_text(
    "MT_TASK", f"translation_{FROM}_to_{TO}", "Machine Translation Task"
)
MT_MODEL = system.getenv_text(
    "MT_MODEL", f"Helsinki-NLP/opus-mt-{FROM}-{TO}", "Machine Translation Model"
)
MAX_LENGTH = system.getenv_int(
    "MAX_LENGTH", 512, description="Optional maximum length of tokens"
)
USE_GPU = system.getenv_bool("USE_GPU", True, "Uses Torch on GPU if True")
TEXT_FILE = system.getenv_text("TEXT_FILE", "-", "Text file to translate")
ROUND_TRIP = system.getenv_bool("ROUND_TRIP", False, "Perform round-trip translation")
SHOW_ELAPSED = system.getenv_bool("SHOW_ELAPSED", False, "Show elapsed time")
USE_INTERFACE = system.getenv_bool(
    "USE_INTERFACE", False, "Use web-based interface via gradio"
)
DYNAMIC_CHUNKING = system.getenv_bool(
    "DYNAMIC_WORD_CHUNKING",
    False,
    "(Default: Sentence Chunking) Splits longer text input to chunks based on word count",
)
PARALLEL_PROCESS = system.getenv_bool(
    "PARALLEL_PROCESS", False, "Perform translations using concurrent threads"
)

# Argument Constants
TEXT_ARG = "text"
FROM_ARG = "from"
TO_ARG = "to"
ELAPSED_ARG = "elapsed"
TASK_ARG = "task"
MODEL_ARG = "model"
UI_ARG = "ui"
ROUND_ARG = "round"
FILE_ARG = "file"
VERBOSE_ARG = "verbose"

# Misc Constants
TL = debug.TL
TRANSLATION_TEXT = "translation_text"
debug.assertion(SOURCE_LANG != TARGET_LANG)


class TranslationArgsProcessing(Main):
    """Arguments processing class"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.result = None  # Initialize result attribute to store output

    def setup(self):
        """Process arguments and pre-read the input file if specified"""
        # Process standard arguments
        self.text = self.get_parsed_option(TEXT_ARG)
        self.text_file = self.get_parsed_option(FILE_ARG)
        self.source_lang = self.get_parsed_option(FROM_ARG, SOURCE_LANG)
        self.target_lang = self.get_parsed_option(TO_ARG, TARGET_LANG)
        self.mt_task = self.get_parsed_option(TASK_ARG, MT_TASK)
        self.mt_model = self.get_parsed_option(MODEL_ARG, MT_MODEL)
        self.show_elapsed = self.get_parsed_option(ELAPSED_ARG)
        self.round_trip = self.get_parsed_option(ROUND_ARG, ROUND_TRIP)
        self.use_interface = self.get_parsed_option(UI_ARG, USE_INTERFACE)
        self.verbose = self.get_parsed_option(VERBOSE_ARG)

        # Pre-read the text file if provided
        if self.text_file and self.text_file != "-":
            self.text = system.read_file(
                self.text_file
            )  # Assume `system.read_file` correctly reads file content

    def run_main_step(self):
        """Process the main step to obtain translation output"""
        translation_logic = TranslationLogic(
            text=self.text,
            source_lang=self.source_lang,
            dest_lang=self.target_lang,
            round_trip=self.round_trip,
            text_file=self.text_file,
            mt_model=self.mt_model,
            mt_task=self.mt_task,
            use_interface=self.use_interface
        )

        # Store the results in self.result for later access
        self.result = translation_logic.return_results()
        if not self.use_interface:
            print(self.result)


class TranslationLogic:
    """Translated a"""

    def __init__(
        self,
        text="",
        source_lang=SOURCE_LANG,
        dest_lang=TARGET_LANG,
        round_trip=ROUND_TRIP,
        text_file=TEXT_FILE,
        mt_task=MT_TASK,
        mt_model=MT_MODEL,
        use_gpu=USE_GPU,
        use_interface=USE_INTERFACE,
        parallel_process=PARALLEL_PROCESS,
        max_length=MAX_LENGTH,
        show_elapsed=SHOW_ELAPSED,
        dynamic_chunking=DYNAMIC_CHUNKING,
    ):
        self.text = text
        self.source_lang = source_lang
        self.dest_lang = dest_lang
        self.round_trip = round_trip
        self.text_file = text_file
        self.mt_task = mt_task
        self.mt_model = mt_model
        self.parallel_process = parallel_process
        self.max_length = max_length
        self.show_elapsed = show_elapsed
        self.use_interface = use_interface
        self.dynamic_chunking = dynamic_chunking
        self.use_gpu = use_gpu
        self.device = self._get_device()
        self.model, self.model_reverse = self._load_models()

    def _get_device(self):
        """Sets device to CUDA if available or USE_GPU is True, otherwise CPU."""
        import torch

        return torch.device(
            "cuda" if (torch.cuda.is_available() and self.use_gpu) else "cpu"
        )

    def _load_models(self):
        """Loads translation models for forward and reverse translation, allowing overrides via arguments."""
        from transformers import pipeline

        ## TODO: Fix support for --model and --task argument
        forward_task = f"translation_{self.source_lang}_to_{self.dest_lang}"
        forward_model = f"Helsinki-NLP/opus-mt-{self.source_lang}-{self.dest_lang}"

        reverse_task = f"translation_{self.dest_lang}_to_{self.source_lang}"
        reverse_model =  f"Helsinki-NLP/opus-mt-{self.dest_lang}-{self.source_lang}"
        
        model = pipeline(
            task=forward_task,
            model=forward_model,
            device=self.device,
        )
        model_reverse = pipeline(
            task=reverse_task,
            model=reverse_model,
            device=self.device,
        )

        return model, model_reverse

    def _get_split_regex(self) -> str:
        """Returns a regex pattern for splitting text based on environment settings."""
        return r"\n\s*\n" if USE_PARAGRAPH_MODE else r"(?<=[.!?]) +"

    def _chunk_text(self, text, dynamic_chunking=False) -> list:
        """Splits text into chunks based on regex or word count."""
        if dynamic_chunking:
            words = text.split()
            return [
                " ".join(words[i : i + self.max_length])
                for i in range(0, len(words), self.max_length)
            ]

        split_regex = self._get_split_regex()
        segments = my_re.split(split_regex, text)
        chunks, current_chunk = [], []

        for segment in segments:
            if len(" ".join(current_chunk + [segment])) <= self.max_length:
                current_chunk.append(segment)
            else:
                chunks.append(" ".join(current_chunk))
                current_chunk = [segment]

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks

    def _get_translated_text(self, model_obj: list) -> str:
        """Extracts translated text from model output."""
        return model_obj[0]["translation_text"] if model_obj else ""

    def _get_similarity_score(
        self, text1: str, text2: str, floating_point: int = 4
    ) -> float:
        """Calculates cosine similarity between two strings."""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vectorizer = TfidfVectorizer().fit_transform([text1, text2])
        vectors = vectorizer.toarray()
        score = cosine_similarity(vectors)[0, 1]
        return score if floating_point < 0 else round(score, floating_point)

    def _get_parallel_translation(self, texts: list[str]) -> list[str]:
        """Translates a list of texts in parallel."""
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as executor:
            translated_texts = list(
                executor.map(
                    lambda chunk: self._get_translated_text(self.model(chunk)), texts
                )
            )
        return translated_texts

    def _get_text_input(self):
        """Read input from a text file or text argument, if not using the UI."""
        # If UI mode is active, skip this function's checks
        if self.use_interface:
            return
        
        if self.text:
            self.text = self.text
        elif self.text_file and self.text_file != "-":
            self.text = system.read_file(self.text_file)
        else:
            raise ValueError("No valid text input provided. Use --text or --file.")

    def _translate_text(self):
        """Translates text by chunk (one-way translation only)."""
        if not self.use_interface:
            self._get_text_input()
        chunks = self._chunk_text(self.text)

        # Use parallel processing if specified
        if self.parallel_process:
            translated_chunks = self._get_parallel_translation(chunks)
        else:
            translated_chunks = [
                self._get_translated_text(self.model(chunk)) for chunk in chunks
            ]

        return " ".join(translated_chunks)

    def _get_elapsed_time(self):
        """Calculates and returns the elapsed time for translation."""
        import time

        start_time = time.time()
        translated_text = self._translate_text()
        end_time = time.time()
        elapsed_time = end_time - start_time

        return translated_text, elapsed_time

    def _round_trip_translation(self):
        """Performs round-trip translation and returns the translated text and similarity score."""
        translated_text = self._translate_text()
        reverse_translations = self._get_translated_text(
            self.model_reverse(translated_text)
        )
        similarity_score = self._get_similarity_score(self.text, reverse_translations)
        return translated_text, reverse_translations, similarity_score
    
    def _helper_translation_ui(self, text):
        """Helper function to perform translation on input from the Gradio UI."""
        self.text = text
        return self._translate_text()
    
    def _translation_ui(self):
        """Translation UI (Simple)""" 
        
        import gradio as gr

        with gr.Blocks() as ui:
            with gr.Tab("Machine Translation UI"):
                gr.Markdown("<h2>Machine Translation</h2>")
                gr.Markdown(f"<h3>FROM: {FROM}") 
                gr.Markdown(f"<h3>TO: {TO}")
                gr.Markdown(
                    "This function takes an input and returns a formatted string."
                )

                with gr.Row():
                    input_box = gr.Textbox(label="Input for Machine Translation")
                    output_box = gr.Textbox(label="Output", interactive=False)

                gr.Button("Submit", elem_id="button_1").click(
                    fn=self._helper_translation_ui, inputs=input_box, outputs=output_box
                )

        ui.launch()

    def return_results(self, jsonify=False):
        """Public method to return results based on parameters passed"""
        if self.use_interface:
            # Launch UI if specified by the user without needing --text or --file
            return self._translation_ui()

        if self.show_elapsed:
            return self._get_elapsed_time()
        
        if self.round_trip:
            return self._round_trip_translation()
        
        return self._translate_text()


class TranslationUI:
    def __init__(
        self,
        model=None,
        model_rev=None,
    ):
        pass


if __name__ == "__main__":
    app = TranslationArgsProcessing(
        description="Improved translation script with argument processing.",
        text_options=[
            (FROM_ARG, "source language"),
            (TO_ARG, "target language"),
            (TASK_ARG, "task"),
            (MODEL_ARG, "model"),
            (TEXT_ARG, "Input text for translation"),
            (FILE_ARG, "Input text file for translation"),
        ],
        boolean_options=[
            (ELAPSED_ARG, "Show elapsed time"),
            (ROUND_ARG, "Perform round-trip translation"),
            (UI_ARG, "Enable Gradio Interface"),
            (VERBOSE_ARG, "Verbose Mode"),
        ],
        manual_input=True,
    )
    app.run()
