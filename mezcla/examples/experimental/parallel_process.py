from transformers import pipeline
import concurrent.futures
import time

# Step 1: Create a translation pipeline using Hugging Face (English to French translation)
translator = pipeline("translation_en_to_fr")

# Step 2: Define a list of texts to translate
texts = [
    "Hello, how are you?",
    "This is a test sentence.",
    "I am learning to translate in parallel.",
    "Python makes it easy to run tasks concurrently.",
    "This should speed up the translation process."
]

# Step 3: Define a function that performs translation on a single text
def translate_text(text):
    return translator(text)[0]['translation_text']

# Sequential (non-parallel) processing
def sequential_process(texts):
    translations = []
    for text in texts:
        translations.append(translate_text(text))
    return translations

# Parallel processing
def parallel_process(texts):
    """Parallel process using concurrent.futures.ThreadPoolExecutor"""
    with concurrent.futures.ThreadPoolExecutor() as executor:
        translations_parallel = list(executor.map(translate_text, texts))
    return translations_parallel

# Time comparison
if __name__ == "__main__":
    # Time sequential processing
    start_time = time.time()
    sequential_translations = sequential_process(texts)
    sequential_duration = time.time() - start_time
    print(f"Sequential processing time: {sequential_duration:.2f} seconds")
    print(f"Sequential translations: {sequential_translations}\n")

    # Time parallel processing
    start_time = time.time()
    parallel_translations = parallel_process(texts)
    parallel_duration = time.time() - start_time
    print(f"Parallel processing time: {parallel_duration:.2f} seconds")
    print(f"Parallel translations: {parallel_translations}\n")
