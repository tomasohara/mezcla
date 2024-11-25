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
# MT_TASK = system.getenv_text(
#     "MT_TASK", f"translation_{FROM}_to_{TO}", "Machine Translation Task"
# )
# MT_MODEL = system.getenv_text(
#     "MT_MODEL", f"Helsinki-NLP/opus-mt-{FROM}-{TO}", "Machine Translation Model"
# )
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
# Experimental
EXTENDED_UI = system.getenv_bool("EXTENDED_UI", False, "Generates extended UI options")
JSONIFY_OUTPUT = system.getenv_bool(
    "JSONIFY_OUTPUT", False, "Generates output in JSON format"
)
SHOW_GPU_USAGE = system.getenv_bool(
    "SHOW_GPU_USAGE", False, "Shows GPU usage if CUDA used"
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
DYNAMIC_ARG = "dynamic"
FILE_ARG = "file"
GPU_ARG = "gpu"
VERBOSE_ARG = "verbose"
PARALLEL_ARG = "parallel"

# Misc Constants
TL = debug.TL
TRANSLATION_TEXT = "translation_text"
debug.assertion(SOURCE_LANG != TARGET_LANG)


class TranslationArgsProcessing(Main):
    """
    TranslationArgsProcessing class is responsible for parsing and managing arguments for the translation process.
    It sets up configurations for translation based on command-line arguments, and it initiates translation by
    interfacing with the TranslationLogic class.

    Attributes:
    - result: Stores the output of the translation process for later retrieval.
    """

    def __init__(self, *args, **kwargs):
        """
        Initializes the TranslationArgsProcessing instance and sets up a `result` attribute to store translation output.

        Parameters:
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
        """
        super().__init__(*args, **kwargs)
        self.result = ""

    def setup(self):
        """
        Processes command-line arguments and reads the input file if specified. Sets up configurations such as
        source and target languages, model details, and processing options (e.g., round-trip, parallel processing).

        Parameters:
            - text: Direct text input for translation.
            - text_file: Path to an input text file for translation.
            - source_lang: Source language code.
            - target_lang: Target language code.
            - mt_task: Task for translation model (e.g., "translation_en_to_fr").
            - mt_model: Model name (e.g., "Helsinki-NLP/opus-mt-en-fr").
            - show_elapsed: Option to display elapsed time for translation.
            - round_trip: Boolean indicating if round-trip translation should be performed.
            - use_interface: Boolean indicating if the Gradio UI should be used.
            - parallel_process: Boolean for enabling parallel processing of text chunks.
            - verbose: Option for detailed logging.

        Raises:
            ValueError: If both `text` and `text_file` are empty or invalid.
        """
        debug.trace(7, f"\nTranslationArgsProcessing.setup({self})")

        self.text = self.get_parsed_option(TEXT_ARG)
        self.text_file = self.get_parsed_option(FILE_ARG)
        self.source_lang = self.get_parsed_option(FROM_ARG, SOURCE_LANG)
        self.target_lang = self.get_parsed_option(TO_ARG, TARGET_LANG)
        self.mt_task = (
            self.get_parsed_option(TASK_ARG)
            or f"translation_{self.source_lang}_to_{self.target_lang}"
        )
        self.mt_model = (
            self.get_parsed_option(MODEL_ARG)
            or f"Helsinki-NLP/opus-mt-{self.source_lang}-{self.target_lang}"
        )
        self.show_elapsed = self.get_parsed_option(ELAPSED_ARG)
        self.round_trip = self.get_parsed_option(ROUND_ARG, ROUND_TRIP)
        self.use_interface = self.get_parsed_option(UI_ARG, USE_INTERFACE)
        self.parallel_process = self.get_parsed_option(PARALLEL_ARG, PARALLEL_PROCESS)
        self.dynamic_chunking = self.get_parsed_option(DYNAMIC_ARG, DYNAMIC_CHUNKING)
        self.use_gpu = self.get_parsed_option(GPU_ARG, USE_GPU)
        self.verbose = self.get_parsed_option(VERBOSE_ARG)


        if self.text_file and self.text_file != "-":
            self.text = system.read_file(self.text_file)

    def run_main_step(self):
        """
        Executes the main translation step by creating an instance of TranslationLogic with the parsed arguments.
        It stores the translation result in the `result` attribute for later retrieval.

        Creates:
            - An instance of TranslationLogic to perform the translation.
            - Stores the output in `self.result` for easy access.

        Prints:
            The result if `use_interface` is set to False.
        """
        # debug.trace(7, f"TranslationArgsProcessing.run_main_setup({self})")
        debug.trace_object(
            5, self.run_main_step, label="TranslationArgsProcessing.run_main_setup"
        )

        translation_logic = TranslationLogic(
            text=self.text,
            source_lang=self.source_lang,
            target_lang=self.target_lang,
            round_trip=self.round_trip,
            text_file=self.text_file,
            mt_model=self.mt_model,
            mt_task=self.mt_task,
            use_gpu=self.use_gpu,
            show_elapsed=self.show_elapsed,
            parallel_process=self.parallel_process,
            use_interface=self.use_interface,
        )

        if self.use_interface:
            ui = TranslationUI(
                text=self.text,
                source_lang=self.source_lang,
                target_lang=self.target_lang,
                round_trip=self.round_trip,
                text_file=self.text_file,
                mt_model=self.mt_model,
                mt_task=self.mt_task,
                show_elapsed=self.show_elapsed,
                parallel_process=self.parallel_process,
                use_interface=self.use_interface,
            )
            ui.launch()

        self.result = translation_logic.return_results()

        if not self.use_interface:
            print(f"Machine Translation: {self.source_lang} TO {self.target_lang}")
            print(f"Original Text: {self.text}")
            
            if self.round_trip:
                rt_translated, rt_roundtrip, rt_score = self.result
                print(f"Translated Text: {rt_translated}")
                print(f"Round Trip Text: {rt_roundtrip}")
                print(f"Similarity Score: {rt_score}")
                print(f"\nDifferences in Original ({FROM}):")
                print(f"{misc_utils.string_diff(self.text, rt_roundtrip)}")
            print("Translated:", self.result)
            
            # if self.show_elapsed:
            #     print("Elapsed Time:", translation_logic._get_elapsed_time())
        
        if SHOW_GPU_USAGE:
            print(f"\nGPU Usage:\n{translation_logic.show_gpu_usage()}\n")


class TranslationLogic:
    """
    TranslationLogic class performs machine translation tasks, with support for forward and
    round-trip translation, text chunking, parallel processing, and similarity scoring. It can
    operate in both command-line mode and Gradio UI.

    Parameters:
    - text (str): The text to be translated.
    - source_lang (str): Source language code.
    - target_lang (str): Target language code.
    - round_trip (bool): Whether to perform round-trip translation.
    - text_file (str): Path to a text file containing input text.
    - mt_task (str): Task for the translation model (e.g., "translation_en_to_fr").
    - mt_model (str): Model name for translation (e.g., "Helsinki-NLP/opus-mt-en-fr").
    - use_gpu (bool): Whether to use GPU for translation.
    - use_interface (bool): If True, uses a Gradio-based UI for translation.
    - parallel_process (bool): If True, enables parallel translation of text chunks.
    - max_length (int): Maximum length of each text chunk.
    - show_elapsed (bool): If True, displays elapsed time for translation.
    - dynamic_chunking (bool): If True, enables dynamic chunking of text.
    """

    def __init__(
        self,
        text="",
        source_lang=SOURCE_LANG,
        target_lang=TARGET_LANG,
        round_trip=ROUND_TRIP,
        text_file=TEXT_FILE,
        mt_task="",
        mt_model="",
        use_gpu=USE_GPU,
        use_interface=USE_INTERFACE,
        parallel_process=PARALLEL_PROCESS,
        max_length=MAX_LENGTH,
        show_elapsed=SHOW_ELAPSED,
        dynamic_chunking=DYNAMIC_CHUNKING,
    ):
        """Class identifier"""
        debug.trace_object(5, self, label="\nTranslationLogic instance")

        self.text = text
        self.source_lang = source_lang
        self.target_lang = target_lang
        self.round_trip = round_trip
        self.text_file = text_file
        self.mt_task = mt_task
        self.mt_model = mt_model
        self.parallel_process = parallel_process
        self.max_length = max_length
        self.show_elapsed = show_elapsed
        self.use_interface = use_interface
        self.use_gpu = use_gpu
        self.device = self._get_device()
        self.dynamic_chunking = dynamic_chunking
        self.model, self.model_reverse = self._load_models()

    def _get_device(self):
        """
        Sets the device to CUDA if a GPU is available and `use_gpu` is True; otherwise, defaults to CPU.

        Returns:
            torch.device: The device object for either CUDA (GPU) or CPU.
        """
        import torch

        device = torch.device(
            "cuda" if (torch.cuda.is_available() and self.use_gpu) else "cpu"
        )

        debug.trace(5, f"\nTranslationLogic._get_device({self}) => {device}")
        return device

    def _load_models(self):
        """
        Loads translation models for both forward and reverse translation tasks,
        allowing for custom task and model overrides via parameters.

        Returns:
            tuple: Contains the forward translation model and the reverse translation model.
        """
        from transformers import pipeline

        # TODO: Add support for round trip translations for models imported from --model option
        # Swap source and target language substrings
        def swap_substrings(original_str, substring1, substring2):
            return (
                original_str.replace(substring1, "#TEMP#")
                .replace(substring2, substring1)
                .replace("#TEMP#", substring2)
            )

        forward_task = self.mt_task
        forward_model = self.mt_model

        # Reverse translation task and model
        reverse_task = swap_substrings(forward_task, self.source_lang, self.target_lang)
        reverse_model = swap_substrings(
            forward_model, self.source_lang, self.target_lang
        )

        # Load pipelines
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

        debug.trace(
            5,
            f"\nTranslationLogic._load_models({self}) => {model}: {forward_model}, {model_reverse}: {reverse_model}\n",
        )
        return model, model_reverse

    def _get_split_regex(self) -> str:
        """
        Returns a regex pattern for splitting text into paragraphs or sentences based on configuration.

        Returns:
            str: Regex pattern for splitting text based on the configured mode.
        """
        result = r"\n\s*\n" if USE_PARAGRAPH_MODE else r"(?<=[.!?]) +"
        debug.trace(5, f"\nTranslationLogic._get_split_regex({self}) => {result}")
        return result

    def _chunk_text(self, text) -> list:
        """
        Splits text into manageable chunks either by word count (dynamic chunking) or
        by splitting using a regex pattern (default).

        Parameters:
            text (str): The text to be chunked.
            dynamic_chunking (bool): If True, splits by word count; otherwise, by regex.

        Returns:
            list: List of text chunks based on the chosen splitting method.
        """
        if self.dynamic_chunking:
            words = text.split()
            result = [
                " ".join(words[i : i + self.max_length])
                for i in range(0, len(words), self.max_length)
            ]
            debug.trace(
                5,
                f"\nTranslationLogic._chunk_text({self}, text={text}, dynamic_chunking={self.dynamic_chunking}) => {result}",
            )
            return result

        split_regex = self._get_split_regex()
        segments = my_re.split(pattern=split_regex, string=text)
        chunks, current_chunk = [], []

        for segment in segments:
            if len(" ".join(current_chunk + [segment])) <= self.max_length:
                current_chunk.append(segment)
            else:
                chunks.append(" ".join(current_chunk))
                current_chunk = [segment]

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        debug.trace(
            5,
            f"\nTranslationLogic._chunk_text({self}, text={text}, dynamic_chunking={self.dynamic_chunking}) => {chunks}",
        )
        return chunks

    def _get_translated_text(self, model_obj: list) -> str:
        """
        Extracts the translated text from the model's output.

        Parameters:
            model_obj (list): The model's output containing translated text.

        Returns:
            str: The translated text string.
        """
        result = model_obj[0]["translation_text"] if model_obj else ""
        debug.trace(
            5,
            f"\nTranslationLogic._get_translated_text({self}, model_obj={model_obj}) => {result}",
        )
        return result

    def _get_similarity_score(
        self, text1: str, text2: str, floating_point: int = 4
    ) -> float:
        """
        Calculates the cosine similarity score between two text strings.

        Parameters:
            text1 (str): The first text for comparison.
            text2 (str): The second text for comparison.
            floating_point (int): Number of decimal places for rounding.

        Returns:
            float: Cosine similarity score between text1 and text2.
        """
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vectorizer = TfidfVectorizer().fit_transform([text1, text2])
        vectors = vectorizer.toarray()
        score = cosine_similarity(vectors)[0, 1]
        result = score if floating_point < 0 else round(score, floating_point)
        debug.trace(
            5,
            f"\nTranslationLogic._get_similarity_score({self}, text1={text1}, text2={text2}, floating_point={floating_point}) => {result}",
        )
        return result

    def _get_parallel_translation(self, texts: list[str]) -> list[str]:
        """
        Translates multiple chunks of text in parallel using a thread pool.

        Parameters:
            texts (list): List of text chunks to be translated.

        Returns:
            list: List of translated text chunks.
        """
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as executor:
            translated_texts = list(
                executor.map(
                    lambda chunk: self._get_translated_text(self.model(chunk)), texts
                )
            )
        debug.trace(
            5,
            f"\nTranslationLogic._get_parallel_translation({self}, texts={texts}) => {translated_texts}",
        )
        return translated_texts

    def _get_text_input(self):
        """
        Reads the input text either from the `text` attribute or from a specified text file.
        Throws an error if neither input is provided and the UI is not active.

        Raises:
            ValueError: If no valid input is provided when the UI is not in use.
        """
        # If UI mode is active, skip this function's checks
        debug.trace(
            5,
            f"TranslationLogc._get_text_input({self}): self.use_interface={self.use_interface}, self.text={self.text}, self.text_file={self.text_file}",
        )
        if self.use_interface:
            return

        if self.text:
            self.text = self.text
        elif self.text_file and self.text_file != "-":
            self.text = system.read_file(self.text_file)
        else:
            raise ValueError("No valid text input provided. Use --text or --file.")

    def _translate_text(self):
        """
        Translates the text by splitting it into chunks and translating each chunk.
        Enables parallel processing if configured.

        Returns:
            str: The full translated text as a single string.
        """
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

        result = " ".join(translated_chunks)
        debug.trace(5, f"\nTranslationLogic._translate_text({self}) => {result}")
        return result

    def _get_elapsed_time(self):
        """
        Measures and returns the time taken for the translation process.

        Returns:
            tuple: Contains the translated text and the elapsed time in seconds.
        """
        result = round(misc_utils.time_function(TranslationLogic) / 1000.0, 2)
        debug.trace(5, f"\nTranslationLogic._get_elapsed_time({self}) => {result}")
        return result

    def _round_trip_translation(self):
        """
        Performs round-trip translation, translating text from source to target language,
        then back to the source language, and calculates similarity.

        Returns:
            tuple: Contains the forward translation, reverse translation, and similarity score.
        """
        translated_text = self._translate_text()
        reverse_translations = self._get_translated_text(
            self.model_reverse(translated_text)
        )
        similarity_score = self._get_similarity_score(self.text, reverse_translations)
        result = (translated_text, reverse_translations, similarity_score)
        debug.trace(
            5, f"\nTranslationLogic._round_trip_translation({self}) => {result}"
        )
        return result

    def return_results(self, jsonify=JSONIFY_OUTPUT):
        """
        Returns translation results based on user-specified parameters.

        Parameters:
            jsonify (bool): If True, returns results as JSON format.

        Returns:
            str or dict: Translation results, optionally in JSON format.
        """
        if jsonify:
            result = {}
            result["text_file"] = self.text_file
            result["from"] = self.source_lang
            result["to"] = self.target_lang
            result["input_text"] = self.text
            result["translated_text"] = (
                self._translate_text()
                if not self.round_trip
                else self._round_trip_translation[0]
            )
            result["round_trip"] = self.round_trip
            result["round_trip_text"] = (
                None if not self.round_trip else self._round_trip_translation[1]
            )
            result["similarity_score"] = (
                None if not self.round_trip else self._round_trip_translation[2]
            )
            result["elapsed_time"] = None if not self.show_elapsed else self._get_elapsed_time()
            result["model"] = self.mt_model
            result["task"] = self.mt_task
        else:
            if self.round_trip:
                result = self._round_trip_translation()
            # elif self.show_elapsed:
            #     result = (self._translate_text(), self._get_elapsed_time())
            else:
                result = self._translate_text()

        debug.trace(5, f"\nTranslationLogic.return_results({self}) => {result}")
        return result

    def show_gpu_usage(self, trace_level = 5):
        """Displays GPU usage when USE_GPU is True"""
        device = self._get_device()
        if device.type == "cuda":
            try:
                result = gh.run("nvidia-smi")
                debug.code(trace_level, lambda: debug.trace(1, result))
                return result
            except Exception as e:
                debug.trace(1, f"Error fetching GPU usage: {str(e)}")
                return f"Error fetching GPU usage: {str(e)}"
        return "GPU not in usage"


## Add Translation UI class here
## TODO: Find a way to implement translation logic or create a logic within

class TranslationUI(TranslationLogic):
    def __init__(
        self,
        text="",
        source_lang=SOURCE_LANG,
        target_lang=TARGET_LANG,
        round_trip=ROUND_TRIP,
        text_file=TEXT_FILE,
        mt_task="",
        mt_model="",
        use_gpu=USE_GPU,
        use_interface=USE_INTERFACE,
        parallel_process=PARALLEL_PROCESS,
        max_length=MAX_LENGTH,
        show_elapsed=SHOW_ELAPSED,
        dynamic_chunking=DYNAMIC_CHUNKING,
    ):
        """Initialize the TranslationUI class by passing arguments to TranslationLogic"""
        super().__init__(
            text=text,
            source_lang=source_lang,
            target_lang=target_lang,
            round_trip=round_trip,
            text_file=text_file,
            mt_task=mt_task,
            mt_model=mt_model,
            use_gpu=use_gpu,
            use_interface=use_interface,
            parallel_process=parallel_process,
            max_length=max_length,
            show_elapsed=show_elapsed,
            dynamic_chunking=dynamic_chunking,
        )

        import gradio as gr

        self.app = gr.Blocks()
        self.create_ui()

    def create_ui(self):
        """Sets up the user interface"""
        with self.app:
            if EXTENDED_UI:
                self.round_trip_translation_ui()
                self.paragraph_mode_ui()
            else:
                self.machine_translation_ui()
                

    def _helper_machine_translation_ui(self, input_text):
        """Helper method for one-way MT user interface"""
        self.text = input_text
        result = self.return_results(jsonify=False)
        debug.trace(
            5,
            f"TranslationUI._helper_machine_translation_ui({self}, input_text={input_text}) => ({result})",
        )
        return result if isinstance(result, str) else result[0]

    def machine_translation_ui(self):
        """
        Creates a simple Gradio UI for machine translation, allowing users to input text
        and view translations interactively.
        """
        import gradio as gr

        debug.trace(5, f"\nTranslationUI.machine_translation_ui({self})")
        with gr.Tab("Machine Translation UI"):
            gr.Markdown(
                f"<h2>Machine Translation: {self.source_lang} TO {self.target_lang}</h2>"
            )
            gr.Markdown("This tool allows you to translate text interactively.")

            with gr.Row():
                input_box = gr.Textbox(
                    label=f"Input Text ({self.source_lang})",
                    placeholder="Enter text here...",
                )
                output_box = gr.Textbox(
                    label=f"Translated Output ({self.target_lang})",
                    interactive=False,
                )

            gr.Button("Submit").click(
                fn=self._helper_machine_translation_ui,
                inputs=input_box,
                outputs=output_box,
            )

    def _helper_round_trip_translation_ui(self, input_text):
        """Helper method for round robin MT user interface"""
        self.text = input_text
        self.round_trip = True
        result = self.return_results(jsonify=False)
        debug.trace(
            5,
            f"TranslationUI._helper_machine_translation_ui({self}, input_text={input_text}) => ({result})",
        )
        return result

    def round_trip_translation_ui(self):
        """UI for round trip translation (launched under alternative UIs)"""
        import gradio as gr

        with gr.Tab("Round Trip Translation"):
            gr.Markdown(
                f"<h2>Round Trip Translation: {self.source_lang} TO {self.target_lang}</h2>"
            )
            gr.Markdown(
                "This function takes a single input and provides multiple outputs."
            )

            with gr.Group():
                input_two = gr.Textbox(label="Input for Round Trip Translation")

            with gr.Group():
                gr.Markdown("### Output Section")
                output_1 = gr.Textbox(label="Output", interactive=False)
                output_2 = gr.Textbox(label="Round Trip Translation", interactive=False)
                output_3 = gr.Textbox(label="Similarity Score", interactive=False)

            gr.Button("Submit").click(
                fn=self._helper_round_trip_translation_ui,
                inputs=input_two,
                outputs=[output_1, output_2, output_3],
            )

    def _helper_paragraph_mode_ui(self, *segments):
        translated_segments = []
        for segment in segments:
            self.text = segment
            translated_segment = self.return_results()
            translated_segments.append(translated_segment) 
        return translated_segments

    @staticmethod
    def split_text(text, split_method, regex, num_paragraphs):
        if not text:
            return []

        if split_method == "Split by Regex":
            try:
                segments = my_re.split(regex, text)
            except my_re.error:
                return ["Invalid regex pattern"]
        else:
            sentences = my_re.split(r'(?<=[.!?]) +', text)  # Split by sentences
            total_sentences = len(sentences)

            # Ensure at least one sentence per paragraph
            segment_size = total_sentences // num_paragraphs
            remainder = total_sentences % num_paragraphs

            segments = []
            start = 0
            for i in range(num_paragraphs):
                end = start + segment_size + (1 if i < remainder else 0)
                segments.append(" ".join(sentences[start:end]))
                start = end

        return segments
    
    def paragraph_mode_ui(self):
        """Set up the Paragraph Mode UI within the app"""
        import gradio as gr
        with gr.Tab("Paragraph Mode UI"):
            gr.Markdown(f"<h2>Split Translation: {self.source_lang} TO {self.target_lang}</h2>")
            input_text = gr.Textbox(label="Input Text", placeholder="Enter text to split")
            split_method = gr.Radio(
                choices=["Split by Regex", "Specify Number of Paragraphs"],
                value="Split by Regex",
                label="Choose Splitting Method",
            )
            split_regex_input = gr.Textbox(
                label="Regex Pattern", value=r"\n", placeholder="Enter regex pattern"
            )
            num_paragraphs_input = gr.Number(
                value=2, label="Number of Paragraphs", visible=False
            )

            def update_input_visibility(method):
                return (
                    gr.update(visible=(method == "Split by Regex")),
                    gr.update(visible=(method == "Specify Number of Paragraphs")),
                )

            split_method.change(
                fn=update_input_visibility,
                inputs=split_method,
                outputs=[split_regex_input, num_paragraphs_input],
            )

            @gr.render(inputs=[input_text, split_method, split_regex_input, num_paragraphs_input])
            def process_and_display(text, method, regex, paragraphs):
                segments = self.split_text(text, method, regex, paragraphs)
                segment_textboxes = []
                translated_textboxes = []

                for seg in segments:
                    with gr.Row():
                        segment_textbox = gr.Textbox(value=seg, interactive=False)
                        translated_output = gr.Textbox(interactive=False)
                        segment_textboxes.append(segment_textbox)
                        translated_textboxes.append(translated_output)

                translate_button = gr.Button("Translate")
                translate_button.click(
                    fn=self._helper_paragraph_mode_ui,
                    inputs=segment_textboxes,
                    outputs=translated_textboxes,
                )

                return segment_textboxes + translated_textboxes

    def launch(self):
        """Launch the Gradio application"""
        self.app.launch()


if __name__ == "__main__":
    app = TranslationArgsProcessing(
        description="Translation tool with argument handling and optional UI.",
        text_options=[
            (FROM_ARG, "Source language code (default: es)"),
            (TO_ARG, "Target language code (default: en)"),
            (TASK_ARG, "Translation task"),
            (MODEL_ARG, "Translation model"),
            (TEXT_ARG, "Text to translate"),
            (FILE_ARG, "File with text to translate (override if --text specified)"),
        ],
        boolean_options=[
            (ELAPSED_ARG, "Show time taken"),
            (ROUND_ARG, "Use round-trip translation"),
            (UI_ARG, "Enable Gradio UI"),
            (GPU_ARG, "Use CUDA if installed"),
            (PARALLEL_ARG, "Use parallel processing"),
            (DYNAMIC_ARG, "Enable Dynamic Word Chunking"),
            (VERBOSE_ARG, "Enable detailed logging"),
        ],
        manual_input=True,
    )
    app.run()
