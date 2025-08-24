#! /usr/bin/env python3
#
# Example for using the KenLM language modeling utility (based on sample):
#     http://kheafield.com/code/kenlm [./python/example.py]
# This assumes the language model has already been created via lmplz
#
#--------------------------------------------------------------------------------
# Note: Build steps for C-based utility (based on https://github.com/kpu/kenlm)
# - Requirements:
#   sudo apt install build-essential cmake libboost-system-dev libboost-thread-dev libboost-program-options-dev libboost-test-dev libeigen3-dev zlib1g-dev libbz2-dev liblzma-dev
# - Main code:
#   mkdir -p build
#   cd build
#   cmake ..
#   make -j 4
#   sudo make install
# - Python code:
#   pip install https://github.com/kpu/kenlm/archive/master.zip
# - For more info, see following:
#   https://github.com/kpu/kenlm
#   https://github.com/kpu/kenlm/blob/master/BUILDING
#--------------------------------------------------------------------------------
#
# TODO:
# - Add lint comment disabling extraneous lint warning (or modify python
#   interface to initialize it):
#     Module 'kenlm' has no 'LanguageModel' member (no-member)
#
# TODO2: show sample output
#
# TODO3: Integrate train_language_model.py.
#

"""Example for using the KenLM language modeling utility"""

# Standard modules
import os
import sys

# Installed modules
import kenlm

# Local modules
from mezcla import debug
from mezcla.system import getenv_boolean, getenv_text
from mezcla import glue_helpers as gh
from mezcla import tpo_common as tpo
from mezcla import system

# Constants
TL = debug.TL

# Environment options
# OLD: Initialize globals, including adhoc options via environment variables
# Note: test.arpa is from kenlm repo (https://github.com/kpu/kenlm),
DEFAULT_LM_FILE = os.path.join(os.path.dirname(__file__), '..', 'lm', 'test.arpa')
LM = getenv_text("LM", DEFAULT_LM_FILE)
SENT_DELIM = getenv_text("SENT_DELIM", "\n", "Delimiter for sentence splitting")
VERBOSE = getenv_boolean("VERBOSE", False, "Verbose output")

# Globals
## TEMP: Need to rework tests/test_kenkm_example.py
model = None
normalized_score = None

#-------------------------------------------------------------------------------

def summed_constituent_score(s):
    """Return sum of scores for ngrams for sentence S
    note: helper function used when checking that total full score equals direct score
    """
    global model
    return sum(prob for (prob, _len, _oov) in model.full_scores(s))
    

def main():
    """Entry point"""

    # Sanity check
    show_usage = (len(sys.argv) > 1) and ("--help" in sys.argv[1])
    if (not show_usage) and (not gh.non_empty_file(LM)):
        print("Warning: Unable to find usable language model file '%s'" % LM)
        show_usage = True
    if show_usage:
        print("Usage: %s [--help] [sentence | -]" % sys.argv[0])
        print("")
        print("Example:")
        print("  kenlm=~/programs/kenlm")
        print("  export PATH=$kenlm/bin:$PATH")
        print("  export LM=$kenlm/test.arpa")
        print("  %s" % __file__)
        print("")
        print("Notes:")
        print("- Assumes lmplz already run: see train_language_model.py.")
        print("- Use LM environment variable to specify alternative language model (see lmplz)")
        print("- Use SENT_DELIM to specify sentence delimiter (default is newline)")
        print("- To use standard input, specify - for sentence above.")
        print("- Use the following environment options to customize processing")
        print("\t" + tpo.formatted_environment_option_descriptions())
        ## OLD: sys.exit()
        ## TODO?: system.exit(status_code=0)
        system.exit()
    
    # Load model from ARPA-format file
    global model
    model = kenlm.LanguageModel(LM)
    print('{0}-gram model'.format(model.order))
    
    # Read input
    sentences = 'language modeling is fun .'
    if (len(sys.argv) > 1):
        sentences = " ".join(sys.argv[1:])
    if (sentences == "-"):
        sentences = sys.stdin.read()
    
    # Check each sentence (or phrase)
    # TODO: rework sto avoid reading sentences entirely into memory (e.g., via generic iterator)
    for sentence in sentences.split(SENT_DELIM):
        if not sentence.strip():
            continue
        print("sentence: %s" % sentence)
        print("model score: %s" % tpo.round_num(model.score(sentence)))
        global normalized_score
        normalized_score = (model.score(sentence) / len(sentence.split()))
        print("normalized score: %s" % tpo.round_num(normalized_score))
        gh.assertion(abs(summed_constituent_score(sentence) - model.score(sentence)) < 1e-3)
    
        # Print diagnostics in verbose mode
        if VERBOSE:
            words = ['<s>'] + sentence.split() + ['</s>']
    
            # Show scores and n-gram matches
            print("Constituent ngrams")
            ## OLD: print("Offset\tProb\tLength\tWords")
            ## OLD: for i, (prob, length) in enumerate(model.full_scores(sentence)):
            print("Offset\tProb\tLength\tUnseen\tWords")
            for i, (prob, length, unseen) in enumerate(model.full_scores(sentence)):
                start = i + 2 - length
                end = start + length
                ## OLD: print('{0}\t{1}\t{2}\t{3}'.format(i, tpo.round_num(prob), length, ' '.join(words[start : end])))
                unseen_spec = "*" if unseen else ""
                print('{0}\t{1}\t{2}\t{3}\t{4}'.format(i, tpo.round_num(prob), length, unseen_spec, ' '.join(words[start : end])))
    
            # Find out-of-vocabulary words
            print("out-of-vocabulary words: %s" % [w for w in words if (not w in model)])

#-------------------------------------------------------------------------------
            
if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    debug.trace(5, f"module __doc__: {__doc__}")
    debug.assertion("TODO:" not in __doc__)
    main()
