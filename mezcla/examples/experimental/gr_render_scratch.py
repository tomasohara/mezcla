import gradio as gr
import re
def split_text(text, split_method, regex, num_paragraphs):
    if not text:
        return []

    if split_method == "Split by Regex":
        try:
            segments = re.split(regex, text)
        except re.error:
            return ["Invalid regex pattern"]
    else:
        sentences = re.split(r'(?<=[.!?]) +', text)  # Split by sentences
        total_sentences = len(sentences)

        # If num_paragraphs is greater than sentences, split into at least one sentence per paragraph
        segment_size = total_sentences // num_paragraphs
        remainder = total_sentences % num_paragraphs
        
        segments = []
        start = 0
        
        for i in range(num_paragraphs):
            # If there are remaining sentences, add one to this segment
            end = start + segment_size + (1 if i < remainder else 0)
            segments.append(" ".join(sentences[start:end]))
            start = end

    return segments

def translate_text(*segments):
    translated_segments = [f"Hello {segment}" for segment in segments]
    return translated_segments

with gr.Blocks() as demo:
    gr.Markdown("<h3>Paragraph Mode UI</h3>")
    input_text = gr.Textbox(label="Input Text", placeholder="Enter text to split")
    split_method = gr.Radio(choices=["Split by Regex", "Specify Number of Paragraphs"], value="Split by Regex", label="Choose Splitting Method")
    split_regex_input = gr.Textbox(label="Regex Pattern", value=r"\n", placeholder="Enter regex pattern")
    num_paragraphs_input = gr.Number(value=2, label="Number of Paragraphs", visible=False)
    if num_paragraphs_input is None:
        num_paragraphs_input = 1

    def update_input_visibility(method):
        return gr.update(visible=(method == "Split by Regex")), gr.update(visible=(method == "Specify Number of Paragraphs"))

    split_method.change(fn=update_input_visibility, inputs=split_method, outputs=[split_regex_input, num_paragraphs_input])

    output_boxes = gr.Column()

    @gr.render(inputs=[input_text, split_method, split_regex_input, num_paragraphs_input])
    def process_and_display(text, method, regex, paragraphs):
        segments = split_text(text, method, regex, paragraphs)
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
            fn=translate_text, 
            inputs=segment_textboxes,
            outputs=translated_textboxes
        )

        return segment_textboxes + translated_textboxes

demo.launch()
