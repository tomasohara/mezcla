#! /usr/bin/env python3
#
# Support for performing Term Frequency (TF) Inverse Document Frequency (IDF)
# using ngrams. This is provides a wrapper class around the tfidf package
# by elzilrac (https://github.com/elzilrac/tf-idf).
#
# For details on computations, see following Wikipedia pages:
#    https://en.wikipedia.org/wiki/Tf-idf
#    https://en.wikipedia.org/wiki/N-gram.
#
# Note:
# - This provides the wrapper class ngram_tfidf_analysis around tfidf for use
#   in applications like Visual Diff Search (VDS) that use text from external sources
#   (e.g., http://www.scrappycito.com/init_search).
# - This incorporates a few optional heuristics, such as filtering overlapping ngrams
#   and boosting captialized ngrams.
# - See compute_tfidf.py for computing tfidf over files.
#
# TODO1: fix --regular over filename
#
# TODO3:
# - Add based trace level option (as with REGEX_TRACE_LEVEL in my_regex.py).
#
# TODO4:
# - Add more optional heuristics: part-of-speech boosting, adjoining ngram filtering,
#   noun-phrase boosting, etc.
# - Isolate ngram support into separate module.
# - Reconcile with compute_tfidf.py (e.g., subsumption here with overlap there).
#

"""TF-IDF using phrasal terms via ngram analysis

Examples:
  {script} -

  echo $'a b c\\nb c d\\nc d e' | MIN_NGRAM_SIZE=2 MAX_NGRAM_SIZE=2 SKIP_TFIDF_PREPROCESSOR=1 {script} {options} -
"""

# Standard packages
from collections import defaultdict
import re
import sys

# Installed packages
CountVectorizer = None

# Local packages
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main
from mezcla import system
from mezcla.system import round_num as rnd
## OLD: from mezcla import tpo_common as tpo
from mezcla import tfidf
from mezcla.compute_tfidf import terms_overlap, IDF_WEIGHTING, TF_WEIGHTING
from mezcla.text_utils import is_numeric
from mezcla.text_processing import stopwords as ENGLISH_STOPWORDS, create_text_proc, split_word_tokens
from mezcla.tfidf.corpus import Corpus as tfidf_corpus
from mezcla.tfidf.preprocess import Preprocessor as tfidf_preprocessor
from mezcla.tfidf import preprocess as tfidf_preprocess
from mezcla.tfidf import MIN_NGRAM_SIZE, MAX_NGRAM_SIZE


SKIP_TFIDF_PREPROCESSOR = system.getenv_bool(
    "SKIP_TFIDF_PREPROCESSOR", False,
    description="Skip tf/idf prepreprocessing",
    )
DEFAULT_PREPROCESSOR_LANG = "english" if (not SKIP_TFIDF_PREPROCESSOR) else None
PREPROCESSOR_LANG = system.getenv_value(
    ## TODO3: standardize wrt TFIDF_LANGUAGE and STEMMER_LANGUAGE
    "PREPROCESSOR_LANG", DEFAULT_PREPROCESSOR_LANG,
    description="Language for ngram preprocessor")
# NOTE: MIN_NGRAM_SIZE (e.g., 2) is alternative to deprecated ALL_NGRAMS (implies 1)
# TODO: add descriptions to all getenv options
ALL_NGRAMS = system.getenv_boolean("ALL_NGRAMS", False)
MAX_TERMS = system.getenv_int("MAX_TERMS", 100)
ALLOW_NGRAM_SUBSUMPTION = system.getenv_boolean(
    "ALLOW_NGRAM_SUBSUMPTION", False,
    description="Allow ngram subsumed by another--substring")
ALLOW_NGRAM_OVERLAP = system.getenv_boolean(
    "ALLOW_NGRAM_OVERLAP", False,
    description="Allows ngrams to overlap--token boundariese")
ALLOW_NUMERIC_NGRAMS = system.getenv_boolean(
    "ALLOW_NUMERIC_NGRAMS", False,
    description="Allow ngrams with numbers")
DEFAULT_USE_CORPUS_COUNTER = (not tfidf_preprocess.USE_SKLEARN_COUNTER)
USE_CORPUS_COUNTER = system.getenv_boolean(
    "USE_CORPUS_COUNTER", DEFAULT_USE_CORPUS_COUNTER,
    description="Use slow tfidf package ngram tabulation")
TFIDF_BOOST_CAPITALIZED = system.getenv_boolean(
    "TFIDF_BOOST_CAPITALIZED", False,
    description="Treat capitalized ngrams higher others of same weight; excludes inner function words")
TFIDF_NP_BOOST = system.getenv_float(
    "TFIDF_NP_BOOST", 0,
    description="Boost factor (e.g., 1.0+) for ngrams that are NP's")
TFIDF_VP_BOOST = system.getenv_float(
    "TFIDF_VP_BOOST", 0,
    description="Boost factor (e.g., 1.0+) for ngrams that are VP's")
TFIDF_NUMERIC_BOOST = system.getenv_float(
    "TFIDF_NUMERIC_BOOST", 0,
    description="Boost factor (e.g., <1.0) for ngrams that have numeric tokens")
TFIDF_TEXT_PROC = system.getenv_text(
    "TFIDF_TEXT_PROC", "spacy",
    description="name of text processor to use for chunking")
TFIDF_BAD_BOOST = system.getenv_float(
    "TFIDF_BAD_BOOST", 0,
    description="Boost factor (e.g., <1.0) for ngrams that have bad terms")
TFIDF_GOOD_BOOST = system.getenv_float(
    "TFIDF_GOOD_BOOST", 0,
    description="Boost factor (e.g., 1.0+) for ngrams that have good terms")
TFIDF_STOP_BOOST = system.getenv_float(
    "TFIDF_STOP_BOOST", 0,
    ## TODO3: reword to exclude inner stop words (once implemented)
    description="Boost factor (e.g., <1.0) for ngrams that have stop words")
ANY_TOKEN_BOOST = (TFIDF_NUMERIC_BOOST or TFIDF_BAD_BOOST or TFIDF_GOOD_BOOST or TFIDF_STOP_BOOST)
## TODO3: ANY_TOKEN_BOOST = ANY_TOKEN_BOOST or TFIDF_CAPITALIZED_BOOST)

# Do sanity check on TF/IDF package version
try:
    # Note major and minor revision values are assumed to be integral
    major_minor = re.sub(r"^(\d+\.\d+).*", r"\1", tfidf.__version__)
    TFIDF_VERSION = float(major_minor)
except:
    TFIDF_VERSION = 1.0
    system.print_stderr("Exception in main: " + str(sys.exc_info()))
assert(TFIDF_VERSION > 1.0)

# Do dynamic load(s)
if not USE_CORPUS_COUNTER:
    from sklearn.feature_extraction.text import CountVectorizer

def split_tokens(text, include_punct=None, include_stop=None):
    """Split TEXT into word tokens (via NLTK), optionally with INCLUDE_PUNCT and INCLUDE_STOP"""
    # EX: split_tokens("Jane's fast car") => ["Jane", "fast", "car"]
    # EX: split_tokens("the door") => ["door"]
    result = split_word_tokens(text, omit_punct=(not include_punct), omit_stop=(not include_stop))
    debug.trace(7, f"split_tokens({text!r}, punct={include_punct}, stop={include_stop}) => {result!r}")
    return result


class ngram_tfidf_analysis(object):
    """Class for performing TF-IDF over ngrams and returning sorted list"""

    def __init__(self, pp_lang=PREPROCESSOR_LANG, min_ngram_size=MIN_NGRAM_SIZE, max_ngram_size=MAX_NGRAM_SIZE,
                 good_terms=None, bad_terms=None, *args, **kwargs):
        """Class constructor: initialize corpus object (with PP_LANG, MIN_NGRAM_SIZE, and MAX_NGRAM_SIZE)
        Note: Optional BAD_TERMS used to boost or penalize certain ngrams (e.g., based on title)
        """
        # EX: ((self := ngram_tfidf_analysis(pp_lang="")) and (not self.pp.stopwords))
        # TODO: add option for stemmer; add all_ngrams and min_ngram_size to constructor
        debug.trace_fmtd(4, "ngram_tfidf_analysis.__init__(lang={pl}, min={minsz}, max={maxsz})",
                         pl=pp_lang, minsz=min_ngram_size, maxsz=max_ngram_size)
        debug.trace_fmtd(5, "\targs={a} kwargs={k}", a=args, k=kwargs)
        if pp_lang is None:
            pp_lang = PREPROCESSOR_LANG
        self.pp_lang = pp_lang
        self.min_ngram_size = min_ngram_size
        self.max_ngram_size = max_ngram_size
        self.pp = None
        self.corpus = None
        self.text_proc = None
        if TFIDF_NP_BOOST or TFIDF_VP_BOOST:
            self.text_proc = create_text_proc(TFIDF_TEXT_PROC)
        ## TODO2: add international stopwords (e.g., English plus frequent ones from common languages)
        self.stopwords = []
        self.good_terms = (good_terms or [])
        self.bad_terms = (bad_terms or [])
        self.noun_phrases = []
        self.verb_phrases = []
        self.reset()
        super().__init__(*args, **kwargs)

    def reset(self):
        """Re-initialize the instance"""
        debug.trace(5, f"reset({self=})")
        self.pp = tfidf_preprocessor(language=self.pp_lang,
                                     gramsize=self.max_ngram_size,
                                     min_ngram_size=self.min_ngram_size,
                                     all_ngrams=ALL_NGRAMS,
                                     stemmer=lambda x: x)
        self.corpus = tfidf_corpus(gramsize=self.max_ngram_size,
                                   min_ngram_size=self.min_ngram_size,
                                   all_ngrams=ALL_NGRAMS,
                                   language=self.pp_lang,
                                   preprocessor=self.pp)
        self.stopwords = (self.pp.stopwords or ENGLISH_STOPWORDS or [])
        self.noun_phrases = []
        self.verb_phrases = []
        debug.trace_object(5, self, label=f"{self.__class__.__name__} instance")

    def set_good_terms(self, text):
        """Sets good terms to TEXT split into word tokens"""
        self.good_terms = split_tokens(text)
        
    def set_bad_terms(self, text):
        """Sets bad terms to TEXT split into word tokens"""
        self.bad_terms = split_tokens(text)
        
    def add_doc(self, text, doc_id=None):
        """Add document TEXT to collection with key DOC_ID, which defaults to order processed (1-based)"""
        if doc_id is None:
            doc_id = str(len(self.corpus) + 1)
        self.corpus[doc_id] = text
        self.noun_phrases = defaultdict(list)
        self.verb_phrases = defaultdict(list)
        if TFIDF_NP_BOOST:
            self.noun_phrases[doc_id] = self.text_proc.noun_phrases(text) 
        if TFIDF_VP_BOOST:
            self.verb_phrases[doc_id] = self.text_proc.verb_phrases(text) 

    def get_doc(self, doc_id):
        """Return document data for DOC_ID"""
        return self.corpus[doc_id]

    def is_stopword(self, word):
        """Whether WORD is a stop word for preprocessing language or English if none"""
        # EX: self.is_stopword("of")
        # EX: ngram_tfidf_analysis(pp_lang="spanish").is_stopword("de")
        result = word.lower() in self.stopwords
        debug.trace(8, f"is_stopword({word!r}) => {result}")
        return result

    def capitalized_ngram(self, ngram):
        """Whethere NGRAM is capitalized, excepting internal stopwords"""
        ## EX: self.capitalized_ngram("House of Cards")
        ## EX: not self.capitalized_ngram("in New York")
        tokens = split_tokens(ngram, include_stop=True)
        result = (tokens and tokens[0].istitle()
                  and ((len(tokens) == 1) or tokens[-1].istitle()))
        if (result and (len(tokens) > 2)):
            for w in tokens[1: -1]:
                if not (w.istitle() or self.is_stopword(w)):
                    debug.trace(5, f"ngram with lower inner non-stop word {w!r}: {tokens!r}")
                    result = False
                    break
        debug.trace(7, f"capitalized_ngram({ngram!r}) => {result}")
        return result
    
    def get_top_terms(self, doc_id, tf_weight=TF_WEIGHTING, idf_weight=IDF_WEIGHTING, limit=MAX_TERMS,
                      allow_ngram_subsumption=ALLOW_NGRAM_SUBSUMPTION,
                      allow_ngram_overlap=ALLOW_NGRAM_OVERLAP, allow_numeric_ngrams=ALLOW_NUMERIC_NGRAMS):
        """Return list of (term, weight) tuples for DOC_ID up to LIMIT count, using TF_WEIGHT and IDF_WEIGHT schemes
        Notes:
        - TF_WEIGHT in {basic, binary, freq, log, norm_50}
        - IDF_WEIGHT in {basic freq, max, prob, smooth}
        - The top ngrams omit blanks and other relics of tokenization
        - Lower weighted ngrams are omitted if subsumed by higher (or vice versa) unless ALLOW_NGRAM_SUBSUMPTION;
          likewise, in the case of ngram overlap unless ALLOW_NGRAM_OVERLAP
        """
        # Get objects for top terms
        # ex: top_terms=[CorpusKeyword(term=<tfidf.dockeyword.DocKeyword object at 0x7f08b43bf550>, ngram=u'patuxent river', score=0.0015548719642054984), ... CorpusKeyword(term=<tfidf.dockeyword.DocKeyword object at 0x7f08b43cf110>, ngram=u'afognak native corporation', score=0.0009894639772216809)]
        ## TODO3: decompose using helper methods
        
        # Get twice as many top terms to display to account for filtering
        # TODO: keep track of how often too few terms shown
        debug.trace(6, (f"get_top_terms({doc_id}, tfw:{tf_weight}, idfw:{idf_weight}, lim={limit},"
                        f"allow_sub={allow_ngram_subsumption}, allow_over={allow_ngram_overlap},"
                        f"allow_num={allow_numeric_ngrams})"))
        top_terms = self.corpus.get_keywords(document_id=doc_id,
                                             tf_weight=tf_weight,
                                             idf_weight=idf_weight,
                                             )
        debug.trace_fmtd(7, "top_terms={tt}", tt=top_terms)

        # Skip empty tokens due to spacing and to punctuation removal (e.g, " ").
        # Also skip stop words (e.g., unigram).
        top_term_info = [(k.ngram, k.score) for k in top_terms
                         if k.ngram.strip() and not self.is_stopword(k.ngram)]
        #
        def round_terms(term_info):
            """Round scores for terms in TERM_INFO"""
            return [(t, system.round_num(s)) for (t, s) in term_info]
        #
        debug.trace_values(6, round_terms(top_term_info), "init top terms")

        # Apply various boosting heuristics that affect the ranking
        apply_reranking = (TFIDF_NP_BOOST or TFIDF_VP_BOOST or TFIDF_NUMERIC_BOOST)
        if apply_reranking:
            boosted = False
            for (i, (ngram, score)) in enumerate(top_term_info):
                ## TODO4: simplify old-score maintenance (e.g., via helper functions)
                init_score = score
                tokens = (split_tokens(ngram, include_stop=True) if ANY_TOKEN_BOOST else [])

                # Apply boost if entire ngram is a noun phrase and likewise for verb phrase
                old_score = init_score
                if (TFIDF_NP_BOOST and (ngram in self.noun_phrases[doc_id])):
                    score = old_score * TFIDF_NP_BOOST
                    debug.trace(5, f"boosted NP {ngram!r} from {rnd(old_score)} to {rnd(score)}")
                    old_score = score
                if (TFIDF_VP_BOOST and (ngram in self.verb_phrases[doc_id])):
                    score = old_score * TFIDF_VP_BOOST
                    debug.trace(5, f"boosted VP {ngram!r} from {rnd(old_score)} to {rnd(score)}")
                    old_score = score
                if (TFIDF_NUMERIC_BOOST and any(is_numeric(token) for token in tokens)):
                    score = old_score * TFIDF_NUMERIC_BOOST
                    debug.trace(5, f"boosted numeric {ngram!r} from {rnd(old_score)} to {rnd(score)}")
                    old_score = score
                if (TFIDF_GOOD_BOOST and system.intersection(tokens, self.good_terms)):
                    score = old_score * TFIDF_GOOD_BOOST
                    debug.trace(5, f"boosted good-term {ngram!r} from {rnd(old_score)} to {rnd(score)}")
                    old_score = score
                if (TFIDF_BAD_BOOST and system.intersection(tokens, self.bad_terms)):
                    score = old_score * TFIDF_BAD_BOOST
                    debug.trace(5, f"boosted bad-term {ngram!r} from {rnd(old_score)} to {rnd(score)}")
                    old_score = score
                if (TFIDF_STOP_BOOST and any(self.is_stopword(token) for token in tokens)):
                    ## TODO3: exclude stopwords in the middle of the ngram
                    score = old_score * TFIDF_STOP_BOOST
                    debug.trace(5, f"boosted with-stop-word {ngram!r} from {rnd(old_score)} to {rnd(score)}")
                    old_score = score
                # Update changed score
                if init_score != score:
                    top_term_info[i] = (ngram, score)
                    boosted = True
            # Re-rank if scores changed
            if boosted:
                top_term_info = sorted(top_term_info, key=lambda ng_sc: ng_sc[1], reverse=True)
        debug.trace_values(6, round_terms(top_term_info), "boosted top terms")
        
        # Move capitalized terms ahead of others with same weight
        # Note: allows for inner non-capitalized only if functions words
        ## TODO3: rework TFIDF_BOOST_CAPITALIZED as score applied above
        for (j, (ngram, score)) in enumerate(reversed(top_term_info)):
            if (TFIDF_BOOST_CAPITALIZED and (j > 0) and self.capitalized_ngram(top_term_info[j][0])
                and (top_term_info[j][1] == top_term_info[j - 1][1])):
                top_term_info[j - 1], top_term_info[j] = top_term_info[j], top_term_info[j - 1]
                debug.trace(5, f"moved capitalized ngram '{top_term_info[j - 1]}' up in list from {j} to {j - 1}")
        debug.trace_values(6, round_terms(top_term_info), "interim top terms")
        
        # Put spaces around ngrams to aid in subsumption tests
        check_ngram_overlap = (not (allow_ngram_subsumption and allow_ngram_overlap))
        if check_ngram_overlap:
            spaced_ngrams = [(" " + ngram + " ") for (ngram, _score) in top_term_info]
            debug.trace_fmtd(7, "spaced_ngrams={sn}", sn=spaced_ngrams)
        final_top_term_info = []
        for (i, (ngram, score)) in enumerate(top_term_info):
            
            if (not ngram.strip()):
                debug.trace_fmt(6, "Omitting invalid ngram '{ng}'", ng=ngram)
                continue
            if ((not allow_numeric_ngrams) and any(is_numeric(token) for token in split_tokens(ngram))):
                debug.trace_fmt(6, "Omitting ngram with numerics '{ng}'", ng=ngram)
                continue
            
            # Check for subsumption (e.g., "new york" in "new york city") and overlap (e.g. "new york" and "york city")
            ## TODO: record ngram offsets to facilitate contiguity tests
            include = True
            if check_ngram_overlap:
                for (j, other_spaced_ngram) in enumerate(spaced_ngrams):
                    is_subsumed = ((not allow_ngram_subsumption) and
                                   ((spaced_ngrams[i] in other_spaced_ngram)
                                     or (other_spaced_ngram in spaced_ngrams[i])))
                    has_overlap = ((not allow_ngram_overlap) and
                                   terms_overlap(spaced_ngrams[i], other_spaced_ngram))
                    if ((i > j) and (is_subsumed or has_overlap)):
                        include = False
                        label = ("in subsumption" if is_subsumed else "overlapping")
                        debug.trace_fmt(6, "Omitting lower-weighted ngram '{ng2}' {lbl} with '{ng1}': {s1} <= {s2}",
                                        ng1=other_spaced_ngram.strip(), ng2=spaced_ngrams[i].strip(), lbl=label,
                                        s1=rnd(top_term_info[i][1]), s2=rnd(top_term_info[j][1]))
                        break
            if not include:
                continue

            # OK
            final_top_term_info.append((ngram, score))
        debug.trace_values(6, round_terms(final_top_term_info), "final top terms")

        # Sanity check on number of terms displayed
        num_terms = len(final_top_term_info)
        if (num_terms < limit):
            debug.trace_fmt(4, "Warning: only {n} terms shown (of {m} max)",
                            n=num_terms, m=limit)
        debug.trace_fmtd(6, "final_top_term_info={tti}", tti=final_top_term_info)
        result = final_top_term_info[:limit]
        return result

    def old_get_ngrams(self, text):
        """Returns generator with ngrams in TEXT"""
        ## NOTE: Now returns the ngrams
        ngrams = []
        gen = self.pp.yield_keywords(text)
        more = True
        while (more):
            ## DEBUG: debug.trace(6, ".")
            try:
                ngrams.append(next(gen).text)
            except StopIteration:
                more = False
        debug.trace_fmt(6, "ngram_tfidf_analysis.old_get_ngrams({t}) [self={s}] => {nl}", 
                        t=text, s=self, nl=ngrams)
        return ngrams

    def get_ngrams(self, text):
        """Returns ngrams in TEXT (from size MIN_NGRAM_SIZE to MAX_NGRAM_SIZE)"""
        # Based on https://stackoverflow.com/questions/13423919/computing-n-grams-using-python.
        if USE_CORPUS_COUNTER:
            return self.old_get_ngrams(text)
        if self.corpus:
            debug.trace(6, "Note: not using tfidf corpus object")
        vectorizer = CountVectorizer(ngram_range=(self.min_ngram_size, self.max_ngram_size))
        analyzer = vectorizer.build_analyzer()
        ngram_list = analyzer(text)
        debug.trace_fmt(6, "ngram_tfidf_analysis.get_ngrams({t}) [self={s}] => {nl}", 
                        t=text, s=self, nl=ngram_list)
        return ngram_list

def simple_main_test():
    """Run test extracting ngrams from this source file"""
    debug.trace(4, "simple_main_test()")
    # Tabulate ngram occurrences
    ngram_analyzer = ngram_tfidf_analysis(min_ngram_size=MIN_NGRAM_SIZE, max_ngram_size=MAX_NGRAM_SIZE)
    all_text = system.read_entire_file(__file__)
    all_ngrams = ngram_analyzer.get_ngrams(all_text)
    reversed_all_text = " ".join(list(reversed(split_tokens(all_text, include_punct=True, include_stop=True))))
    ngram_analyzer.add_doc(all_text, doc_id="doc1")
    ngram_analyzer.add_doc(reversed_all_text, doc_id="rev-doc1")
    top_ngrams = ngram_analyzer.get_top_terms("rev-doc1", allow_ngram_subsumption=False, allow_ngram_overlap=False)

    # Check for common ngrams
    debug.assertion("simple test follows" in all_ngrams)
    debug.assertion("system getenv_boolean" in top_ngrams)
    debug.assertion("system" not in all_ngrams)
    debug.assertion("getenv_boolean" not in all_ngrams)
    
    # Check for filtering based on subsumption and overlap
    debug.assertion("warning not" in top_ngrams)
    debug.assertion("warning not intended" not in top_ngrams)

    # Check for tf/idf values
    # TODO: add assertion for specific tfidf values
    try:
        debug.assertion(ngram_analyzer.corpus.tf_idf("system getenv_boolean", document_id="doc1")
                        == ngram_analyzer.corpus.tf_idf("getenv_boolean system", document_id="rev-doc1"))
    except:
        system.print_exception_info("corpus.tf_idf")

    # Output ngram sample
    SAMPLE_SIZE = 10
    init_ngram_spec = "\n\t".join(all_ngrams[:SAMPLE_SIZE])
    print(f"first 10 ngrams in {__file__}:\n\t{init_ngram_spec}")
    init_top_ngram_spec = "\n\t".join([f"{t}: {system.round_num(s, 3)}"
                                       for (t, s) in top_ngrams[:SAMPLE_SIZE]])
    print(f"top ngrams in {__file__}:\n\t{init_top_ngram_spec}")


def output_tfidf_analysis(main_app, good_text=None, bad_text=None):
    """Output results for ngram TF/IDF analysis over input from MAIN_APP"""
    debug.trace(4, f"output_tfidf_analysis({main_app})")
    ## TODO3: let ngram_tfidf_analysis class do the splitting
    good_terms = ([] if not good_text else split_tokens(good_text))
    bad_terms = ([] if not bad_text else split_tokens(bad_text))
    ngram_analyzer = ngram_tfidf_analysis(min_ngram_size=MIN_NGRAM_SIZE, max_ngram_size=MAX_NGRAM_SIZE,
                                          good_terms=good_terms, bad_terms=bad_terms)
    all_text = main_app.read_entire_input()
    num_docs = 0
    for l, line in enumerate(all_text.splitlines()):
        ngram_analyzer.add_doc(line, doc_id=(l + 1))
        num_docs += 1

    # Output ngram sample
    SAMPLE_SIZE = 10
    for l in range(num_docs):
        top_ngrams = ngram_analyzer.get_top_terms(l + 1)
        top_ngram_spec = "; ".join([f"{t}: {system.round_num(s, 3)}"
                                    for (t, s) in top_ngrams[:SAMPLE_SIZE]])
        print(f"{l}\t{top_ngram_spec}")
    

def main():
    """Entry point for script"""
    debug.trace(4, "main()")
    SIMPLE_TEST_OPT = "simple-test"
    REGULAR_OPT = "regular"
    GOOD_TERMS_OPT = "good-terms"
    BAD_TERMS_OPT = "bad-terms"
    main_app = Main(
        description=__doc__.format(script=gh.basename(__file__),
                                   options=f"--{REGULAR_OPT}"),
        boolean_options=[(SIMPLE_TEST_OPT, "Run simple canned test--default"),
                         (REGULAR_OPT, "Process regular input--not canned test")],
        text_options=[(GOOD_TERMS_OPT, "Overlap terms for boosting ngrams scores"),
                      (BAD_TERMS_OPT, "Overlap terms for de-boosting ngrams scores")],
        skip_input=False, manual_input=True)
    regular = main_app.get_parsed_option(REGULAR_OPT)
    simple_test = main_app.get_parsed_option(SIMPLE_TEST_OPT, not regular)
    good_terms_text = main_app.get_parsed_option(GOOD_TERMS_OPT)
    bad_terms_text = main_app.get_parsed_option(BAD_TERMS_OPT)
    if (simple_test):
        simple_main_test()
    else:
        output_tfidf_analysis(main_app, good_text=good_terms_text, bad_text=bad_terms_text)
   
#-------------------------------------------------------------------------------

if __name__ == '__main__':
    main()
