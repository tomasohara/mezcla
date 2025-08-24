#! /usr/bin/env python3
#
# compute_tfidf.py: compute Term Frequency Inverse Document Frequency (TF-IDF)
# for a collection of documents. See https://en.wikipedia.org/wiki/Tf-idf.
#
# TODO3:
# - Add based trace level option (as with REGEX_TRACE_LEVEL in my_regex.py).
#
# TODO4:
# - Show examples.
# - Have option for producing document/term matrix.
# - Add option to omit TF, IDF and IDF fields (e.g., in case just interested in frequency counts).
# - Add option to put term at end, so numeric fields are aligned.
# - -and/or- Have ** max-output-term-length option and right pad w/ spaces.
# - See if IDF calculation should for 0 if just one document occurrence.
# - Reconcile with ngram_tfidf.py (e.g., overlap here with subsumption there).
# - Add simple example(s) to help.
#
# Note:
# - This script is just for running tfidf over text files.
# - See ngram_tfdif.py for a wrapper class around tfidf for use in applications
#   like Visual Diff Search that generate the text dynamically.
#


"""Compute Term Frequency/Inverse Document Frequency (TF-IDF) for a set of documents"""

# Standard packages
import csv
import os
import re
import sys

# Installed packages
# TODO: require version 1.1 with TPO hacks
from mezcla import tfidf
from mezcla.tfidf import MIN_NGRAM_SIZE, MAX_NGRAM_SIZE
from mezcla.tfidf.corpus import Corpus as tfidf_corpus
from mezcla.tfidf.preprocess import Preprocessor as tfidf_preprocessor

# Local packages
from mezcla import debug
from mezcla import system
from mezcla.system import PRECISION
from mezcla.text_utils import make_fixed_length

# Determine environment-based options
## TODO3: take before and after snapshots of environment options to support pruning
## in formatted_environment_option_descriptions.
DEFAULT_NUM_TOP_TERMS = system.getenv_int("NUM_TOP_TERMS", 10)
## OLD:
## MAX_NGRAM_SIZE = system.getenv_int("MAX_NGRAM_SIZE", 1)
## MIN_NGRAM_SIZE = system.getenv_int("MIN_NGRAM_SIZE", MAX_NGRAM_SIZE)
USE_NGRAM_SMOOTHING = system.getenv_boolean("USE_NGRAM_SMOOTHING", False)

## OLD: IDF_WEIGHTING = system.getenv_text("IDF_WEIGHTING", "basic")
DEFAULT_IDF_WEIGHTING = 'smooth' if USE_NGRAM_SMOOTHING else 'basic'
IDF_WEIGHTING = system.getenv_text("IDF_WEIGHTING", DEFAULT_IDF_WEIGHTING)
## OLD: TF_WEIGHTING = system.getenv_text("TF_WEIGHTING", "basic")
## TODO3: DEFAULT_IF_WEIGHTING = 'smooth' if USE_NGRAM_SMOOTHING else 'log'
DEFAULT_TF_WEIGHTING = 'basic'
TF_WEIGHTING = system.getenv_text("TF_WEIGHTING", DEFAULT_TF_WEIGHTING)
DELIMITER = system.getenv_text("DELIMITER", ",")
CORPUS_DUMP = system.getenv_value("CORPUS_DUMP", None,
                                  "Filename for corpus dump")
PRUNE_SUBSUMED_TERMS = system.getenv_bool("PRUNE_SUBSUMED_TERMS", False)
PRUNE_OVERLAPPING_TERMS = system.getenv_bool("PRUNE_OVERLAPPING_TERMS", False)
SKIP_STEMMING = system.getenv_bool("SKIP_STEMMING", False,
                                   "Skip word stemming (via Snowball)")
INCLUDE_STEMMING = not SKIP_STEMMING
STEMMER_LANGUAGE = system.getenv_value("STEMMER_LANGUAGE", None,
                                       "Language for stemming and stop words--not recommended")
LANGUAGE = (STEMMER_LANGUAGE or "")
TAB_FORMAT = system.getenv_bool("TAB_FORMAT", False,
                                 "Use tab-delimited format--facilitates spreadsheet import")
TERM_WIDTH = system.getenv_int("TERM_WIDTH", 32,
                               "Width of term column in output")
SCORE_WIDTH = system.getenv_int("SCORE_WIDTH", PRECISION + 6,
                                "Width of each score column in output (e.g., up to 12 for default precision of 6 as in 1.855712e-03)")
MAX_FIELD_SIZE = system.getenv_int(
    "MAX_FIELD_SIZE", -1,
    desc="Overide for default max field size (128k)")
SORT_FIELD = system.getenv_text(
    "SORT_FIELD", None,
    desc="Field name for override to default TF-IDF sorting")

# Option names and defaults
NGRAM_SIZE_OPT = "--ngram-size"
NUM_TOP_TERMS_OPT = "--num-top-terms"
SHOW_SUBSCORES = "--show-subscores"
SHOW_FREQUENCY = "--show-frequency"
SHOW_ALL = "--show-all"
CSV = "--csv"
TSV = "--tsv"
TEXT = "--text"
VERBOSE_OPT = "--verbose"
HEADER_OPT = "--header"
TEXT_DELIMITER = "\xFF"

#...............................................................................

def show_usage_and_quit(verbose=False):
    """Show command-line usage for script and then exit"""
    # TODO: make [???]
    usage = """
Usage: {prog} [options] file1 [... fileN]

Options: [--help] [{ngram_size_opt}=N] [{top_terms_opt}=N] [{subscores}] [{frequencies}]
         [{all}] [{csv} | {tsv} | {text}] [{header}]

Notes:
- Derives TF-IDF for set of documents, using single word tokens (unigrams), by default. 
- By default, the document ID is the position of the file on the command line (e.g., N for fileN above). The document text is the entire file.
- However, with {csv}, the document ID is taken from the first column, and the document text from the second columns (i.e., each row is a distinct document).
- With {text}, the document ID is taken from the line number.
- Use following environment options:
      DEFAULT_NUM_TOP_TERMS ({default_topn})
      MIN_NGRAM_SIZE ({min_ngram_size})
      MAX_NGRAM_SIZE ({max_ngram_size})
      TF_WEIGHTING ({tf_weighting}): {{log, norm_50, binary, basic, freq}}
      IDF_WEIGHTING ({idf_weighting}): {{smooth, max, prob, basic, freq}}
""".format(prog=sys.argv[0], ngram_size_opt=NGRAM_SIZE_OPT, top_terms_opt=NUM_TOP_TERMS_OPT, subscores=SHOW_SUBSCORES, frequencies=SHOW_FREQUENCY, all=SHOW_ALL, default_topn=DEFAULT_NUM_TOP_TERMS, min_ngram_size=MIN_NGRAM_SIZE, max_ngram_size=MAX_NGRAM_SIZE, tf_weighting=TF_WEIGHTING, idf_weighting=IDF_WEIGHTING, csv=CSV, tsv=TSV, text=TEXT, header=HEADER_OPT)
    print(usage)
    if verbose:
        print("- Full set of environment options")
        indent = "      "
        env_opts = system.formatted_environment_option_descriptions(sort=True, indent=indent)
        print(env_opts)
    else:
        print("- For others, use --verbose")

    sys.exit()


def get_suffix1_prefix2(subterms1, subterms2):
    """returns any suffix of SUBTERMS1 list that is a prefix of SUBTERMS2 list"""
    # EX: get_suffix1_prefix2(["my", "dog"], ["dog", "has"]) => ["dog"]
    # EX: get_suffix1_prefix2(["a", "b", "c"], ["b", "d"]) => []
    # TODO: support string arguments (e.g., by splitting on whitespace)
    prefix_len = 0
    for subterm1 in subterms1:
        if ((subterm1 in subterms2) and (subterms2.index(subterm1) == prefix_len)):
            prefix_len += 1
        else:
            prefix_len = 0
    prefix = (subterms1[-prefix_len:] if prefix_len else[])
    debug.trace_fmt(7, "get_suffix1_prefix2({st1}, {st2}) => {p}", st1=subterms1, st2=subterms2, p=prefix)
    return prefix
    

def terms_overlap(term1, term2):
    """Whether TERM1 and TERM1 overlap (and the overlapping text if so)
    Note: The overlap must occur at word boundaries
    """
    # EX: terms_overlap("ACME Rocket Research", "Rocket Research Labs") => "Rocket Research"
    # EX: not terms_overlap("Rocket Res", "Rocket Research")
    # TODO: put in text_utils
    subterms1 = term1.strip().split()
    subterms2 = term2.strip().split()
    overlap = ""
    if system.intersection(subterms1, subterms2):
        # pylint: disable=arguments-out-of-order
        overlap = " ".join((get_suffix1_prefix2(subterms1, subterms2) or get_suffix1_prefix2(subterms2, subterms1)))
    debug.trace_fmt(7, "terms_overlap({t1}, {t2}) => {o}", t1=term1.strip(), t2=term2.strip(), o=overlap)
    return overlap


def is_subsumed(term, terms, include_overlap=PRUNE_OVERLAPPING_TERMS):
    """Whether TERM is subsumed by another term in TERMS, accounting for overlapping terms if INCLUDE_OVERLAP
    Note: subsumption is based on string matching not token matching unlike the overlap check.
    """
    # EX: is_subsumed("White House", ["The White House", "Congress", "Supreme Court"])
    # EX: is_subsumed("White House", ["White Houses"])
    # TODO: Enforce word boundaries as with terms_overlap
    subsumed_by = [subsuming_term for subsuming_term in terms
                   if (((term in subsuming_term) 
                        or (include_overlap and terms_overlap(term, subsuming_term)))
                       and (term != subsuming_term))]
    subsumed = any(subsumed_by)
    debug.trace_fmt(6, "is_subsumed({t}) => {r}; subsumed by: {sb}",
                    t=term, r=subsumed, sb=subsumed_by)
    return subsumed

#...............................................................................

def main():
    """Entry point for script"""
    args = sys.argv[1:]
    ## NOTE: debug now shows args
    debug.trace_fmtd(4, "main()")
    debug.trace_fmtd(4, "os.environ={env}", env=os.environ)

    # Parse command-line arguments
    # TODO2: rework via Main (see examples/template.py)
    i = 0
    max_ngram_size = MAX_NGRAM_SIZE
    num_top_terms = DEFAULT_NUM_TOP_TERMS
    show_subscores = False
    show_frequency = False
    csv_file = False
    is_text = False
    verbose = False
    include_text_header = False
    global DELIMITER
    ## TODO2: use main.Script for argument parsing
    while ((i < len(args)) and args[i].startswith("-")):
        option = args[i]
        debug.trace_fmtd(5, "arg[{i}]: {opt}", i=i, opt=option)
        if (option == VERBOSE_OPT):
            verbose = True
        elif (option == "--help"):
            ## TODO2: put after option parsing (so --help --verbose works)
            show_usage_and_quit(verbose=verbose)
        elif (option == NGRAM_SIZE_OPT):
            i += 1
            max_ngram_size = int(args[i])
        elif (option == NUM_TOP_TERMS_OPT):
            i += 1
            num_top_terms = int(args[i])
        elif (option == SHOW_SUBSCORES):
            show_subscores = True
        elif (option == SHOW_FREQUENCY):
            show_frequency = True
        elif (option == SHOW_ALL):
            show_subscores = True
            show_frequency = True
        elif (option == CSV):
            csv_file = True 
        elif (option == TSV):
            csv_file = True
            DELIMITER = "\t"
        elif (option == TEXT):
            csv_file = True
            is_text = True
            DELIMITER = TEXT_DELIMITER
        elif (option == HEADER_OPT):
            include_text_header = True
        else:
            sys.stderr.write("Error: unknown option '{o}'\n".format(o=option))
            show_usage_and_quit()
        i += 1
    debug.assertion((not (csv_file and is_text) or (DELIMITER == TEXT_DELIMITER)))
    args = args[i:]
    if (len(args) < 1):
        system.print_stderr("Error: missing filename(s)\n")
        show_usage_and_quit()
    if ((len(args) < 2) and (not csv_file) and (not show_frequency)):
        ## TODO: only issue warning if include-frequencies not specified
        system.print_stderr("Warning: TF-IDF not relevant with only one document")

    # Make sure TF-IDF package supports occurrence counts for TF
    ## TODO4: drop since now five versions ago
    tfidf_version = 1.0
    try:
        # Note major and minor revision values assumed to be integral
        major_minor = re.sub(r"^(\d+\.\d+).*", r"\1", tfidf.__version__)
        tfidf_version = float(major_minor)
    except:
        system.print_stderr("Exception in main: " + str(sys.exc_info()))
        assert(tfidf_version >= 1.2)
        
    # Initialize Tf-IDF module
    debug.assertion(not re.search(r"^en(_\w+)?$", LANGUAGE, re.IGNORECASE))
    # Note: disables stemming via no-op lambda by default
    stemmer_fn = None if INCLUDE_STEMMING else (lambda x: x)
    my_pp = tfidf_preprocessor(language=LANGUAGE, gramsize=max_ngram_size, min_ngram_size=MIN_NGRAM_SIZE, all_ngrams=False, stemmer=stemmer_fn)
    corpus = tfidf_corpus(gramsize=max_ngram_size, min_ngram_size=MIN_NGRAM_SIZE, all_ngrams=False, preprocessor=my_pp)

    # Overide the maxium field size if specified
    if MAX_FIELD_SIZE > -1:
        old_limit = csv.field_size_limit()
        debug.assertion(MAX_FIELD_SIZE > old_limit)
        csv.field_size_limit(MAX_FIELD_SIZE)
        debug.trace(4, f"Set max field size to {MAX_FIELD_SIZE}; was {old_limit}")

    # Process each of the filename arguments
    doc_filenames = {}
    for i, filename in enumerate(args):
        # If CSV file, treat each row as separate document, using ID from first column and data from second
        # Note: Special case with one-line per document using delimited 0xFF.
        if csv_file:
            text_col = 0 if is_text else 1
            with system.open_file(filename) as fh:
                csv_reader = csv.reader(iter(fh.readlines()), delimiter=DELIMITER, quotechar='"')
                line = 0
                for r, row in enumerate(csv_reader):
                    debug.trace(6, f"{line}: {r=} {row}")
                    if (not r) and (DELIMITER != TEXT_DELIMITER) and (not include_text_header):
                        debug.assertion((len(row) > 1) or (DELIMITER not in row[0]))
                        debug.trace(5, f"Ignoring header: {line=} {row=}")
                        continue
                    doc_id = str(r + 1) if is_text else row[0]
                    try:
                        doc_text = system.from_utf8(row[text_col])
                    except:
                        debug.trace_fmt(5, "Exception processing line {l}", l=line)
                        doc_text = ""
                    ## TODO: use defaultdict-type hash
                    if doc_id not in corpus:
                        corpus[doc_id] = ""
                    else:
                        ## TODO: corpus[doc_id] += " "
                        corpus[doc_id] = (corpus[doc_id].text + " ")
                    # Appends text to corpus document
                    ## TODO: corpus[doc_id] += doc_text
                    corpus[doc_id] = (corpus[doc_id].text + doc_text)
                    ## OLD: doc_filenames[doc_id] = filename + ":" + str(i + 1)
                    doc_filenames[doc_id] = f"{filename}:{r + 1}"
                    line += 1
        # Otherwise, treat entire file as document and use command-line position as the document ID
        else:
            doc_id = str(i + 1)
            doc_text = system.read_entire_file(filename)
            corpus[doc_id] = doc_text
            doc_filenames[doc_id] = filename
    debug.trace_object(7, corpus, "corpus")
    if CORPUS_DUMP:
        system.save_object(CORPUS_DUMP, corpus)

    # Derive headers
    headers = ["term"]
    if show_frequency:
        headers += ["TFreq", "DFreq"]
    if show_subscores:
        headers += ["TF", "IDF"]
    headers += ["TF-IDF"]
    debug.assertion(headers[0] == "term")
    sort_field_offset = (headers.index(SORT_FIELD) if SORT_FIELD in headers else 0)

    # Output the top terms per document with scores
    # TODO: change the IDF weighting
    for doc_id in corpus.keys():        # pylint: disable=consider-using-dict-items
        print("{id} [{filename}]".format(id=doc_id, filename=doc_filenames[doc_id]))
        if TAB_FORMAT:
            print("\t".join(headers))
        else:
            term_header_spec = make_fixed_length(headers[0], TERM_WIDTH)
            other_header_spec = " ".join([make_fixed_length(h, SCORE_WIDTH) for h in headers[1:]])
            print(term_header_spec + " " + other_header_spec)

        # Get ngrams for document and calculate overall score (TF-IDF).
        # Then print each in tabular format (e.g., "et al   0.000249")
        top_term_info = corpus.get_keywords(document_id=doc_id,
                                            idf_weight=IDF_WEIGHTING,
                                            limit=num_top_terms)
        # Optionally limit the result to terms that don't overlap with higher weighted ones.
        # TODO: Allow overlap if the terms occur in different parts of the document.
        if PRUNE_SUBSUMED_TERMS:
            top_terms = [term_info.ngram.strip() for term_info in top_term_info]
            top_term_info = [ti for (i, ti) in enumerate(top_term_info) 
                             if (not is_subsumed(ti.ngram, top_terms[0: i]))]
        all_scores = []
        for (term, score) in [(ti.ngram, ti.score)
                              for ti in top_term_info if ti.ngram.strip()]:
            # Get scores including component values (e.g., IDF)
            # TODO: don't round the frequency counts (e.g., 10.000 => 10)
            scores = [term]
            if show_frequency:
                scores.append(corpus[doc_id].tf_freq(term))
                scores.append(corpus.df_freq(term))
            if show_subscores:
                scores.append(corpus[doc_id].tf(term, tf_weight=TF_WEIGHTING))
                # TODO; idf_weight=TDF_WEIGHTING
                scores.append(corpus.idf(term))
            scores.append(score)
            all_scores.append(scores)

        if SORT_FIELD:
            all_scores = sorted(all_scores, reverse=True,
                                key=lambda scores: scores[sort_field_offset])
        for scores in all_scores:
             # Print term and rounded scores
            if TAB_FORMAT:
                print(scores[0] + "\t" + "\t".join(map(system.round_as_str, scores[1:])))
            else:
                rounded_scores = [make_fixed_length(system.round_as_str(s), SCORE_WIDTH) for s in scores[1:]]
                term_spec = make_fixed_length(system.to_utf8(scores[0]), TERM_WIDTH)
                score_spec = " ".join(rounded_scores)
                print(term_spec + " " + score_spec)
                ## TODO: debug.assertion((len(rounded_scores) * PRECISION) < len(score_spec) < (len(rounded_scores) * (1 + SCORE_WIDTH)))
        print("")

    return

#------------------------------------------------------------------------

if __name__ == '__main__':
    main()
