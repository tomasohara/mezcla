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
import gradio as gr

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
MAX_LENGTH = 512
PARALLEL_PROCESS = False
FROM = "es"
SOURCE_LANG = FROM
TO = "en"
DEST_LANG = TO
TEXT_FILE = "-"
ROUND_TRIP = False
ELAPSED_TIME = False

# Args constant
TEXT_ARG = "text"
FROM_ARG = "from"
TO_ARG = "to"
ELAPSED_ARG = "elapsed-time"
TASK_ARG = "task"
MODEL_ARG = "model"
UI_ARG = "ui"
ROUND_ARG = "round"
FILE_ARG = "file"

class TranslationLogic:
    """Translated a"""

    def __init__(
        self,
        text=None,
        source_lang=SOURCE_LANG,
        dest_lang=DEST_LANG,
        round_trip=ROUND_TRIP,
        text_file=TEXT_FILE,
        parallel_process=PARALLEL_PROCESS,
        max_length=MAX_LENGTH,
        elapsed_time=ELAPSED_TIME
    ):
        self.text = text
        self.source_lang = source_lang
        self.dest_lang = dest_lang
        self.round_trip = round_trip
        self.text_file = text_file
        self.parallel_process = parallel_process
        self.max_length = max_length
        self.elapsed_time = elapsed_time
        self.device = self._get_device()
        self.model, self.model_reverse = self._load_models()

    def _get_device(self):
        """Sets device to CUDA if available, otherwise CPU."""
        import torch

        return torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def _load_models(self):
        """Loads translation models for forward and reverse translation."""
        from transformers import pipeline

        mt_model = f"Helsinki-NLP/opus-mt-{self.source_lang}-{self.dest_lang}"
        mt_model_reverse = f"Helsinki-NLP/opus-mt-{self.dest_lang}-{self.source_lang}"

        model = pipeline(
            task=f"translation_{self.source_lang}_to_{self.dest_lang}",
            model=mt_model,
            device=self.device,
        )
        model_reverse = pipeline(
            task=f"translation_{self.dest_lang}_to_{self.source_lang}",
            model=mt_model_reverse,
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

    # TODO: Implement it outside class
    def _get_text_input(self):
        """Read input from a text file"""
        if self.text_file != "-":
            self.text = system.read_file(self.text_file)

    def _translate_text(self):
        """Translates text by chunk (one-way translation only)."""
        self._get_text_input()
        chunks = self._chunk_text(self.text)

        # Use parallel processing if specified
        if self.parallel_process:
            translated_chunks = self._get_parallel_translation(chunks)
        else:
            translated_chunks = [self._get_translated_text(self.model(chunk)) for chunk in chunks]

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
        reverse_translations = self._get_translated_text(self.model_reverse(translated_text))
        similarity_score = self._get_similarity_score(self.text, reverse_translations)
        return translated_text, reverse_translations, similarity_score

    def return_results(self, jsonify=False):
        """Public class to return results based on parameters passed"""
        ## TODO: Add extended JSON result when jsonify = True
        if self.elapsed_time:
            return self._get_elapsed_time()
        elif self.round_trip:
            return self._round_trip_translation()            
        else:
            return self._translate_text()

class TranslationUI:
    def __init__(self):
        pass


# class TranslationArgsProcessing(Main):
#     """Arguments processing class"""
#     def __init__(self, description="Translation Script Argument Processor"):
        
#         super().__init__(
#             description=description,
#             skip_input=False,
#             manual_input=True,
#             boolean_options=[
#                 # Define any boolean options, such as round-trip translation
#                 (UI_ARG, "Invoke user interface"),
#                 (ROUND_ARG, "Enable round-trip translation"),
#             ],
#             text_options=[
#                 # Define text options like language codes and translation task
#                 (FROM_ARG, "Source language code"),
#                 (TO_ARG, "Target language code"),
#                 (TASK_ARG, "Translation task"),
#                 (MODEL_ARG, "Model for translation"),
#                 (TEXT_ARG, "Text to translate"),
#             ],
#         )
#         self.processed_args = self.parse_arguments()



if __name__ == "__main__":
    # text = "To refactor this code and improve abstraction, let's separate the logic into smaller, reusable classes and methods, ensuring that each class has a single responsibility. This restructuring will also make it easier to test and maintain each component individually."
    # text = "USE is designed for general-purpose sentence similarity and often captures grammar and syntax nuances. It’s well-suited for evaluating semantic similarity between sentences in a lightweight way."
    ## NOTE: If text_file is specified, it is given priority
    source_lang = "en"
    dest_lang = "fr"

    x = TranslationLogic(
        text = "Fellas in Paris",
        source_lang=source_lang,
        dest_lang=dest_lang,
        round_trip=0,
        elapsed_time=0,
        text_file="paul.txt",
    )

    print(x.return_results(jsonify=1))
