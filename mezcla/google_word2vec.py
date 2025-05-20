#! /usr/bin/env python3
#
# google_word2vec.py: Create "deep learning" model for word vector representation
# using Google's word2vec algorithm (Mikolov et al. 2013) as implemented in Gensim.
# This can be used to support term similarity calculations.
#
# This also includes support for displaying term similarity based on the word2vec
# model for a list of phrases in the input. The similarity will be derived using
# all the terms together as positive cases as well as on just using each term
# individually.
#
# Notes:
# - (Mikolov et al. 2013): Mikolov, T., K. Chen, G. Corrado, and J. Dean (2013), 
#   "Efficient Estimation of Word Representations in Vector Space", ICLR workshop.
# - Based on http://radimrehurek.com/2014/02/word2vec-tutorial.
# - See gensim_test.py for script that supports document similarity instead of term similarity.
# - For reproducibility of results, the number of workers should be set to 1. Setting,
#   the random seed doesn't have any effect because gensim uses 1 by default.
#
# TODO:
# - *** Finalize the model to reduce memory footprint:
#   ex: model.init_sims(replace=True)
# - Have option to precompute top-n similarities for common words and save as shelve-like data file (e.g., to cut down on memory usage).
#
# TODO2:
# - Check gensim 4.0 API usage: https://github.com/piskvorky/gensim/wiki/Migrating-from-Gensim-3.x-to-4.
#
#------------------------------------------------------------------------
# Copyright (C) 2012-2018 Thomas P. O'Hara
#

"""Simple interface into Gensim's Word2vec algorithm"""

import argparse
import numpy
import os
import re
import sys
import logging
import multiprocessing

from gensim.models import Word2Vec
from mezcla import file_utils
from mezcla import glue_helpers as gh
from mezcla import system
from mezcla import tpo_common as tpo
## OLD:
## import tpo_common as tpo
## import glue_helpers as gh

WORD2VEC_MODEL_EXT = ".word2vec"
NUM_TOP = tpo.getenv_integer("NUM_TOP", 5, "Maximum number of related terms to display")
SKIP_TERMS_WITH_PUNCTUATION = tpo.getenv_boolean("SKIP_TERMS_WITH_PUNCTUATION", False, "Omit related terms with punctuation characters")
# TODO: rework so that SKIP_LOW_FREQUENCY_TERMS conditional upon TERM_FREQ_FILE
SKIP_LOW_FREQUENCY_TERMS = tpo.getenv_boolean("SKIP_LOW_FREQUENCY_TERMS", False, "Omit related terms that have low frequency")
DEFAULT_TERM_FREQ_FILE = "term.freq" if SKIP_LOW_FREQUENCY_TERMS else ""
TERM_FREQ_FILE = tpo.getenv_text("TERM_FREQ_FILE", DEFAULT_TERM_FREQ_FILE, "Frequency for term occurrences")
TERM_FREQ_HASH = tpo.create_lookup_table(TERM_FREQ_FILE) if gh.non_empty_file(TERM_FREQ_FILE) else {}
NUM_WORKERS = tpo.getenv_integer("NUM_WORKERS", multiprocessing.cpu_count(), "Number of worker threads; use 1 to reproduce results")
RANDOM_SEED = tpo.getenv_integer("RANDOM_SEED", -1, 
                                 "Integral seed for random number generation")
PRESERVE = tpo.getenv_boolean("PRESERVE", False,
                              "Preserve format of text")
DOWNCASE = tpo.getenv_boolean("DOWNCASE", not PRESERVE,
                              "Convert text to lowercase")
SKIP_INDIVIDUAL = tpo.getenv_boolean("SKIP_INDIVIDUAL", False,
                                     "Omit similarity for individual tokens in input sentences")
## TODO:
## JSON_FORMAT = system.getenv_bool(
##     "JSON_FORMAT", False,
##     desc="USe JSON format for output such as similarity")
SIM_OUTPUT_FILE = system.getenv_value(
    "SIM_OUTPUT_FILE", None,
    desc="Output file for similarity info for all terms")

def format_related_terms(model, positive_terms, max_num=NUM_TOP):
    """Determine related terms from MODEL for POSITIVE_TERMS, returning at most MAX_NUM entries each."""
    # Try to get most similar terms. If words are not in the vocabulary
    # try with the remainder if any.
    all_related_info = []
    try:
        ## OLD: all_related_info = model.most_similar(positive=positive_terms)
        all_related_info = model.wv.most_similar(positive=positive_terms)
    except KeyError:
        missing = [w for w in positive_terms if w not in model]
        tpo.print_stderr("Warning: omitting words not in model: %s" % missing)
        ok_words = tpo.difference(positive_terms, missing)
        if ok_words:
            try:
                all_related_info = model.wv.most_similar(positive=ok_words)
            except:
                tpo.print_stderr("Unexpected error in format_related_terms: " + str(sys.exc_info()))

    # Add related terms unless filtered due to low frequency or embedded punctuation
    related_specs = []
    for (term, score) in all_related_info:
        if SKIP_LOW_FREQUENCY_TERMS and term.lower() not in TERM_FREQ_HASH:
            tpo.debug_print("Skipping low frequency related term '%s'" % term, 6)
            continue
        if SKIP_TERMS_WITH_PUNCTUATION and re.search(r"\W", term):
            tpo.debug_print("Skipping related term '%s' due to punctuation" % term, 6)
            continue
        related_specs.append(term + ": " + tpo.round_num(score))
        if len(related_specs) == max_num:
            break
    return ", ".join(related_specs)

def tokenize(text):
    r"""Tokenize TEXT according to regex word tokens (i.e., \W+), which defaults to [A-Za-z0-9_]+"""
    # TODO: Allow for tokenization regex to be overwritten
    token_regex = r"(\W+)" if not PRESERVE else r"(\S+)"
    tokens = [t.strip() for t in re.split(token_regex, text) if t.strip()]
    if DOWNCASE:
        tokens = [t.lower() for t in tokens]
        
    tpo.debug_format("tokenize({txt!r}) => {t!r}", 7, txt=text, t=tokens)
    return tokens


class MySentences(object):
    """Class for processing files line by line. Note: the input file should have one document per line, and the text will remain case sensitive in word2vec."""
    # Note: based on Sentences class from gensim sample.
    # TODO: Rename to Documents for clarity; make downcase an option of the class

    def __init__(self, file_name):
        """Class constructor: FILE_NAME is text file or directory"""
        tpo.debug_format("MySentences.__init__({f})", 6, f=file_name)
        self.file_name = file_name
        return

    def __iter__(self):
        """Returns iterator producing one line at a time"""
        # Derive the list of filenames to process
        # TODO: support recursive directory descent
        tpo.debug_print("in MySentences.__iter__()", 6)
        file_names = None
        if os.path.isdir(self.file_name):
            dir_name = self.file_name
            file_names = [os.path.join(dir_name, f) for f in os.listdir(dir_name)]
        else:
            file_names = [self.file_name]

        # Feed each sentence individually from each file
        # TODO: add preprocessing (e.g., tokenize, make lowercase, etc.)
        for file_name in file_names:
            if os.path.isdir(file_name):
                tpo.debug_format("Warning: skipping subdirectory {f}", tpo.WARNING, f=file_name)
                continue
            tpo.debug_format("Processing file {f}", tpo.DETAILED, f=file_name)
            for line in system.open_file(file_name):
                ## OLD: tokens = line.split()
                tokens = tokenize(line)
                tpo.debug_format("MySentences.__iter__: yielding {t}", 6, t=tokens)
                yield tokens
        tpo.debug_print("out MySentences.__iter__()", 6)
        return


def main():
    """Entry point for script"""
    tpo.debug_print("main(): sys.argv=%s" % sys.argv, 4)

    # Parse command-line arguments
    env_options = tpo.formatted_environment_option_descriptions(indent="  ")
    usage_description = tpo.format("""
Creates Google word2vec model (via gensim) of word distributions inferrred from 
the occurrences in the input text file. Note: input should be a text file 
(or directory) when creating from scratch or the basename of model file 
if loading existing model.

Notes:
- The input file should have one document per line (multiple sentences allowed).
- The following environment options are available:
  {env}
    """, env=env_options)
    parser = argparse.ArgumentParser(description=usage_description,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--save", default=False, action='store_true', help="Save model to disk")
    parser.add_argument("--load", default=False, action='store_true', help="Load model from disk")
    parser.add_argument("--list-terms", default=False, action='store_true', help="Print vocabulary")
    parser.add_argument("--print", default=False, action='store_true', help="Print vectors on standard output")
    parser.add_argument("filename", default=None, help="Input data filename (or basename when loading previously saved model); if a directory all files within are processed")
    parser.add_argument("--output-basename", default=None, help="Basename to use for output (by default input file without .txt extension)")
    parser.add_argument("--show-similarity", default=False, action='store_true', help="Show similar terms for those from input (one per line)")
    # TODO: parser.add_argument("--language-model", default=None, help="Language model to use for rating similar terms")
    args = vars(parser.parse_args())
    tpo.debug_print("args = %s" % args, 5)
    filename = args['filename']
    save = args['save']
    load = args['load']
    list_terms = args['list_terms']
    print_vectors = args['print']
    show_similarity = args['show_similarity']
    output_basename = args['output_basename']
    # TODO: put version of glue_helper's assertion into tpo_common.py already!
    gh.assertion(filename)

    # Derive the basename if not given (checking one of .txt/.list/.prep extensions if training or .word2vec if loading)
    # TODO: rework in terms of stripping whatever file extension is used (e.g., "it.fubar" => "it")
    if not output_basename:
        input_extensions = [".txt", ".list", ".prep"] if (not load) else [WORD2VEC_MODEL_EXT]
        output_basename = filename
        for extension in input_extensions:
            output_basename = gh.remove_extension(filename, extension)
            if (output_basename != filename):
                break
    tpo.debug_print("output_basename=%s" % output_basename, 5)

    # Enable logging if debugging
    if (tpo.debugging_level()):
        # TODO: use mapping from symbolic LEVEL user option (e.g., via getenv)
        level = logging.INFO if (tpo.debug_level < 4) else logging.DEBUG
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=level)

    # Optionally set random seed
    if RANDOM_SEED != -1:
        tpo.debug_format("Setting random seed to {RANDOM_SEED}")
        numpy.random.seed(RANDOM_SEED)

    # Process the input file(s), either creating model from scratch or loading existing one
    if load:
        model = Word2Vec.load(filename)
    else:
        sentences = MySentences(filename)
        if tpo.verbose_debugging():
            # TODO: try to develop develop read-only function that makes copy of iterator
            sentences = list(sentences)
            gh.assertion(len(sentences) > 0)
            tpo.debug_format("sentences={s}", 6, s=sentences)
        # Notes: 1 is default for word2vec (todo, try None)
        seed = 1 if (RANDOM_SEED == -1) else RANDOM_SEED
        model = Word2Vec(sentences, workers=NUM_WORKERS, seed=seed)

        # Optionally save model to disk
        if (save):
            model.save(output_basename + WORD2VEC_MODEL_EXT)

    # Print the vocabulary
    if list_terms:
        all_words = sorted(model.wv.key_to_index.keys())
        print("\n".join(all_words))
            
    # Print the vector representations
    # TODO: add option to print word similarity matrix
    if print_vectors:
        ## OLD: all_words = sorted(model.vocab.keys())
        all_words = sorted(model.wv.key_to_index.keys())
        tpo.debug_format("model={m}", 6, m=model)
        print("Vocaulary terms: %s" % all_words)
        for word in all_words:
            ## OLD:
            ## tpo.debug_format("model[%s]=%s" % (word, model[word]), 5)
            ## print("%s\t%s" % (word, model[word]))
            tpo.debug_format("model[%s]=%s" % (word, model.wv[word]), 5)
            print("%s\t%s" % (word, model.wv[word]))

    # Show similarity info for terms from input
    # TODO: add better recovery for terms unknown
    if show_similarity:
        tpo.debug_print("Show similarity for terms from stdin", 4)
        print("term(s): similarity info")
        for line in sys.stdin:
            ## OLD: terms = [t.strip() for t in re.split(r"\W+", line.strip().lower())]
            terms = tokenize(line)
            try:
                # TODO: shows language model score for terms replaced by related terms
                if not terms:
                    pass
                elif len(terms) > 1 or SKIP_INDIVIDUAL:
                    print("[%s]: %s" % (", ".join(terms), format_related_terms(model, terms)))
                else:
                    if not SKIP_INDIVIDUAL:
                        for term in terms:
                            print("[%s]: %s" % (term, format_related_terms(model, [term])))
                print("")
            except KeyError:
                tpo.print_stderr("Error: %s" % str(sys.exc_info()))
    if SIM_OUTPUT_FILE:
        sim_info = {}
        for term in sorted(model.wv.key_to_index.keys()):
            sim_info[term] = model.wv.most_similar(positive=[term])
        file_utils.write_json(SIM_OUTPUT_FILE, sim_info, default=str)
    return

#------------------------------------------------------------------------

if __name__ == '__main__':
    main()
