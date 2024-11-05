import gradio as gr
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from transformers import pipeline
from mezcla import my_re


def gradio_translation_input(
    *words_src: str, is_round_trip: bool = False, model=None, model_reverse=None
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
        sentence_round_trip = model_reverse(sentence_dst)[0]["translation_text"].split(
            "."
        )[0]
        similarity_score = round(
            calculate_similarity(sentence_src, sentence_round_trip), 4
        )
    else:
        sentence_round_trip = ""
        similarity_score = 0.0

    return sentence_dst, sentence_round_trip, similarity_score


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


FROM = "es"
TO = "en"


class TranslationUI:
    def __init__(self, model=None, model_rev=None, alternative_ui_count=3):
        self.app = gr.Blocks()
        self.model = model
        self.model_rev = model_rev
        self.ui_count = alternative_ui_count
        self.create_ui()

    def create_ui(self):
        with self.app:
            self.machine_translation_ui()
            self.round_trip_translation_ui()
            self.alternative_ui()
            self.paragraph_mode_ui()

    def fn_machine_translation(self, input, include_period=True):
        result = gradio_translation_input(input, model=self.model)
        return result[0] + "." if include_period else result[0]

    def fn_round_trip_translation(self, input):
        result = gradio_translation_input(
            input, model=self.model, model_reverse=self.model_rev, is_round_trip=True
        )
        return result

    def fn_alternative_ui(self, *input_args) -> tuple:
        is_round_trip = input_args[-1]  # Last argument is the round-trip flag
        text_inputs = input_args[:-1]  # All other arguments are text inputs
        result = gradio_translation_input(
            *text_inputs,
            is_round_trip=is_round_trip,
            model=self.model,
            model_reverse=self.model_rev,
        )
        return result
    
    def fn_paragraph_mode(self, input_text, split_regex=None, num_paragraphs=2):
        output_original = []  # To store original text segments
        output_translated = []  # To store translated text segments
        
        # Determine paragraphs based on provided split method
        if split_regex:
            paragraphs = my_re.split(split_regex, input_text)
        elif num_paragraphs:
            sentences = my_re.split(r"(?<=[.!?])\s+", input_text)
            sentences_per_paragraph = max(1, len(sentences) // num_paragraphs)
            
            # Group sentences into paragraphs based on calculated number
            paragraphs = [
                " ".join(sentences[i:i + sentences_per_paragraph])
                for i in range(0, len(sentences), sentences_per_paragraph)
            ]
            
            # Merge excess segments if there are more than the desired number of paragraphs
            if len(paragraphs) > num_paragraphs:
                merged_paragraphs = (
                    paragraphs[:num_paragraphs - 1]
                    + [" ".join(paragraphs[num_paragraphs - 1:])]
                )
                paragraphs = merged_paragraphs
        else:
            return ["Error: No splitting method provided."]
        
        # Translate each paragraph and store separately
        for paragraph in paragraphs:
            if paragraph.strip():
                sentence_segments = my_re.split(r"(?<=[.!?])\s+", paragraph)
                original_translated_pair = []
                
                # Translate each sentence in the paragraph
                for sentence in sentence_segments:
                    if sentence.strip():
                        translated_sentence = self.fn_machine_translation(sentence)
                        original_translated_pair.append((sentence, translated_sentence))
                        
                # Separate the original and translated texts into lists
                output_original.append(" ".join([pair[0] for pair in original_translated_pair]))
                output_translated.append(" ".join([pair[1] for pair in original_translated_pair]))

        return output_original, output_translated  # Return both lists


    def machine_translation_ui(self):
        with gr.Tab("Machine Translation"):
            gr.Markdown("<h3>Machine Translation</h3>")
            gr.Markdown("This function takes an input and returns a formatted string.")

            with gr.Row():
                input_one = gr.Textbox(label="Input for Machine Translation")
                output_one = gr.Textbox(label="Output", interactive=False)

            gr.Button("Submit", elem_id="button_1").click(
                fn=self.fn_machine_translation, inputs=input_one, outputs=output_one
            )

    def round_trip_translation_ui(self):
        with gr.Tab("Round Trip Translation"):
            gr.Markdown("<h3>Round Trip Translation</h3>")
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

            def process_input(input_text):
                output_values = self.fn_round_trip_translation(input_text)
                return output_values

            gr.Button("Submit").click(
                process_input, inputs=input_two, outputs=[output_1, output_2, output_3]
            )

    def alternative_ui(self):
        with gr.Tab("Alternative UI"):
            gr.Markdown("<h3>Alternative UI</h3>")
            gr.Markdown("This function allows dynamically adding input fields.")

            # State to hold the count of input boxes
            text_count = gr.State(1)
            add_btn = gr.Button("Add Input Field")

            # Checkbox to enable round trip
            enable_round_trip = gr.Checkbox(
                label="Enable Round Trip and Similarity Score", value=False
            )

            # Function to dynamically render input boxes based on the current count
            def render_input_boxes(count):
                return [
                    gr.Textbox(label=f"Input #{i + 1}", key=f"input_{i}")
                    for i in range(count)
                ]

            # Initial rendering of input boxes based on text_count
            input_boxes = render_input_boxes(1)

            # Update the text_count and re-render input boxes when "Add Input Field" is clicked
            def update_input_boxes(count):
                return render_input_boxes(count)

            add_btn.click(lambda x: x + 1, inputs=text_count, outputs=text_count)
            add_btn.click(update_input_boxes, inputs=text_count, outputs=input_boxes)

            # Output section
            with gr.Group():
                gr.Markdown("### Output Section")
                output_1 = gr.Textbox(label="Output 1: Translated", interactive=False)
                output_2 = gr.Textbox(label="Output 2: Round Trip", interactive=False)
                output_3 = gr.Textbox(label="Output 3: Similarity Score", interactive=False)

            def process_all_inputs(*inputs):
                # Separate the text inputs and checkbox value
                is_round_trip = inputs[-1]
                text_inputs = inputs[:-1]
                output_values = self.fn_alternative_ui(*text_inputs, is_round_trip)
                return output_values

            # Button to process inputs and connect outputs
            gr.Button("Process All Inputs").click(
                process_all_inputs,
                inputs=input_boxes + [enable_round_trip],
                outputs=[output_1, output_2, output_3],
            )



    def paragraph_mode_ui(self):
        """Splits the texts into multiple paragraphs and performs output accordingly"""
        with gr.Tab("Paragraph Mode UI"):
            gr.Markdown("<h3>Paragraph Mode UI</h3>")
            gr.Markdown(
                "This function splits the input text based on the provided regex pattern or specified paragraph count and returns multiple outputs."
            )

            with gr.Group():
                gr.Markdown("### Input Section")
                input_text = gr.Textbox(label="Input Text")

                # Radio button selection for split method
                split_method = gr.Radio(
                    choices=["Split by Regex", "Specify Number of Paragraphs"],
                    label="Choose Splitting Method",
                    value="Split by Regex",
                )

                # Text input for each splitting method, initially only regex is visible
                split_regex_input = gr.Textbox(
                    label="Split Regex",
                    value=r"\n",  # Default regex pattern
                    visible=True,
                    placeholder="Enter regex pattern for splitting",
                )
                num_paragraphs_input = gr.Number(
                    label="Number of Paragraphs",
                    value=2,
                    visible=False,
                    # placeholder="Enter number of paragraphs",
                )

                # Toggle visibility of input boxes based on selection
                def update_split_method(method):
                    return gr.update(visible=(method == "Split by Regex")), gr.update(
                        visible=(method == "Specify Number of Paragraphs")
                    )

                split_method.change(
                    fn=update_split_method,
                    inputs=split_method,
                    outputs=[split_regex_input, num_paragraphs_input],
                )

            with gr.Group():
                gr.Markdown("### Output Section")
                with gr.Row():
                    split_text_box = gr.Textbox(label="Segmented Text", interactive=False)
                    output_box = gr.Textbox(label="Segmented Outputs", interactive=False)

        # Updated format_outputs function to work with Gradio outputs
        def format_outputs(input_text, split_method, split_regex_input, num_paragraphs_input):
            if split_method == "Split by Regex":
                output_segments = self.fn_paragraph_mode(input_text, split_regex_input)
            else:
                output_segments = self.fn_paragraph_mode(input_text, num_paragraphs=num_paragraphs_input)

            # Creating tuples for original and translated segments
            formatted_output = list(zip(output_segments[0], output_segments[1]))

            # Prepare output for Gradio display
            original_texts = "\n".join([segment[0] for segment in formatted_output])
            translated_texts = "\n".join([segment[1] for segment in formatted_output])

            return original_texts, translated_texts

        # Set up the button click event
        gr.Button("Process Text").click(
            format_outputs,
            inputs=[
                input_text,
                split_method,
                split_regex_input,
                num_paragraphs_input,
            ],
            outputs=[split_text_box, output_box]
        )

    def launch(self):
        self.app.launch()


# Create an instance of the TranslationApp class and launch the UI
FROM = "en"
TO = "es"
MT_MODEL = f"Helsinki-NLP/opus-mt-{FROM}-{TO}"
MT_MODEL_REVERSE = f"Helsinki-NLP/opus-mt-{TO}-{FROM}"
MT_TASK = "translation_{FROM}_to_{TO}"
MT_TASK_REVERSE = "translation_{TO}_to_{FROM}"
model = pipeline(task=MT_TASK, model=MT_MODEL)
model_rev = pipeline(task=MT_TASK_REVERSE, model=MT_MODEL_REVERSE)
ui = TranslationUI(model=model, model_rev=model_rev, alternative_ui_count=4)
ui.launch()
