#! /usr/bin/env python

from mezcla import glue_helpers as gh
from mezcla.main import Main
from mezcla import debug
from mezcla import system
from mezcla.unittest_wrapper import TestWrapper
from mezcla.examples import hugging_face_translation as THE_MODULE

# System modules
import time
# System Environment Variables

# FROM = system.getenv_text("FROM", "en")
# TO = system.getenv_text("TO", "es")
# SOURCE_LANG = system.getenv_text("SOURCE_LANG", FROM, "Source Language")
# TARGET_LANG = system.getenv_text("TARGET_LANG", TO, "Target Language")
# MT_TASK = f"translation_{SOURCE_LANG}-{TARGET_LANG}"
# DEFAULT_MODEL = f"helsinki-NLP/opus-mt-{SOURCE_LANG}-{TARGET_LANG}"
# MT_MODEL = system.getenv_text("MT_MODEL", DEFAULT_MODEL, "Huggingface Model for MT")
TEXT_FILE = system.getenv_text("TEXT_FILE", "-", "Text File to Translate")
OUTPUT_FILE = system.getenv_text("OUTPUT_FILE", "-", "Output File after Translation")
module_path = THE_MODULE.__file__

TL = debug.TL

t1_start = time.time()
def main():
    debug.trace(TL.USUAL, f"main(): script={system.real_path(__file__)}")

    # Show simple usage if --help given
    # dummy_main_app = Main(description=__doc__, skip_input=False, manual_input=False)
    # debug.assertion(dummy_main_app.parsed_args)

    text_file = "./translate1.txt"
    output_file = "./out3.txt"
    gh.run(f"{module_path} {text_file} > {output_file}")
    print(time.time())

t2_start = time.time()

print ("The difference in execution of time:", t1_start-t2_start)
if __name__ == '__main__':
    main() 