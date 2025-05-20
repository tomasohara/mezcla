#!/usr/bin/env python3

"""A Corpus is a collection of Documents. Calculates IDF and full TF-IDF.

Vocabulary:
    stem - to stem (or "stemming") is to convert to a word from the original
        conjugated, plural, etc. to a simpler form.
            Examples:
                cats -> cats
                winningly -> win
    term - a one or multi word string, no stemming
    ngram - a one or multi word string that has been pre-processed and stemmed.
        Stemming may not be idempotent, so it's important to not re-process the
        ngram.
        bi-gram = two-word ngram
        tri-gram = three-word ngram
        n-gram = "n" word ngram
    keyword - contains the ngram, references to all the document(s) it is located
        in, and the locations within the document so that the original term can
        also be re-calculated.
    document - a body of text
    corpus - a collection of documents that are at least somewhat comparible.
        it is recommended to NOT have multiple languages within a single corpus.
    TF - Term Frequency within a document
    IDF - Inverse Document Frequency, the inverse frequency of the term across
        all documents in a corpus
    TF-IDF - a combination of the TF and IDF scores reflecting the "importance"
        of a term within a particular document
"""

## NOTE: See TPO for Thomas P. O'Hara's hacks
## TODO:
## - add missing docstrings for a few of the methods below
## - turn string keyword arguments from kw=default to
##     kw=None ... if kw is None: kw = default
## - Add debug.trace_fmt(level, ...) in place of unconditional sys.stderr.write's.
##

from __future__ import absolute_import, division

# Standard modules
import math
from collections import namedtuple
## TODO
## import os
import sys

# Installed modules
## TEST: from cachetools import LRUCache, cached
from functools import lru_cache
from mezcla import debug
from mezcla import system
from mezcla import misc_utils

## TODO
## # HACK: For relative imports to work in Python 3.6
## # See https://stackoverflow.com/questions/16981921/relative-imports-in-python-3.
## sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Local modules
from mezcla.tfidf.config import BASE_DEBUG_LEVEL as BDL
from mezcla.tfidf.document import Document, PENALIZE_SINGLETONS
from mezcla.tfidf.preprocess import Preprocessor, clean_text

CorpusKeyword = namedtuple('CorpusKeyword', ['term', 'ngram', 'score'])

SKIP_NORMALIZATION = system.getenv_bool("SKIP_NORMALIZATION", False,
                                        "Skip term/ngram normalization")
NGRAM_EPSILON = system.getenv_float(
    "NGRAM_EPSILON", 0.000001,
    description="Occurrence count for unknown ngrams")
MISC_EPSILON = system.getenv_float(
    "MISC_EPSILON", 0.000001,
    description="Epsilon for misc. TF/IDF calculations")
TFIDF_NGRAM_LEN_WEIGHT = system.getenv_float(
    "TFIDF_NGRAM_LEN_WEIGHT", 0,
    description="Length factor for ngram token length")
MIN_NGRAM_SIZE = system.getenv_int(
    "MIN_NGRAM_SIZE", 2,
    description="Minimum size of grams")
MAX_NGRAM_SIZE = system.getenv_int(
    "MAX_NGRAM_SIZE", 4,
    description="Maxium size of grams")

class Corpus(object):
    """A corpus is made up of Documents, and performs TF-IDF calculations on them.

    After initialization, add "documents" to the Corpus by adding text
    strings with a document "key". These will generate Document objects.

    Example:
        >>> import mezcla.tfidf.corpus as mtc
        >>> c = mtc.Corpus(gramsize=2)
        >>> c['doc1'] = 'Mary had a little lamb.'
        >>> c['doc2'] = 'Hannible is not a lamb.'
        >>> c['doc3'] = 'The shark sleeps a little.'
        >>> round(c.df_freq('lamb'))
        0
        >>> round(c.df_freq('little lamb'))
        1
        >>> round(c.df_freq('a little'))
        2
        >>> round(c.idf('a little'), 3)
        0.405
        >>> round(c.tf_idf('a little', document_id='doc1').score, 3)
        0.013
        >>> round(c.tf_idf('a little', document_id='doc2').score, 3)
        0.0
        >>> round(c.tf_idf('little lamb', document_id='doc1').score, 3)
        0.034
    """

    def __init__(self, min_ngram_size=None, max_ngram_size=None,
                 language=None, preprocessor=None,
                 gramsize=None, all_ngrams=None):
        """Initalize.

        Parameters:
            min_ngram_size (int-or-None):
                if integral, gives the lower bound for ngram sie
            max_ngram_size (int-or-None):
                if integral, gives the upper bound for ngram size
            language (str):
                Uses NLTK's stemmer and local stopwords files appropriately for the
                language.
                Check available languages with Preprocessor.supported_languages
            preprocessor (object):
                pass in a preprocessor object if you want to manually configure stemmer
                and stopwords
            all_ngrams (bool):
                if True, return all possible ngrams of size "gramsize" and smaller.
                else, only return keywords of exactly length "gramsize"
                Note: deprecated (use min_ngram_size instead).
            gramsize (int): number of words in a keyword
                deprecated: use max_ngram_size instead
        """
        debug.assertion(not (gramsize and max_ngram_size))
        debug.assertion(not (all_ngrams and min_ngram_size))
        self.__documents = {}
        self.__document_occurrences = {}
        self.__gramsize = (max_ngram_size or gramsize)
        self.__max_raw_frequency = None
        self.__max_rel_doc_frequency = None
        self.__max_doc_frequency = None
        if preprocessor:
            self.preprocessor = preprocessor
        else:
            self.preprocessor = Preprocessor(
                language=language, min_ngram_size=min_ngram_size, max_ngram_size=max_ngram_size,
                ## TODO: remove deprecated
                gramsize=gramsize, all_ngrams=all_ngrams)

    def __contains__(self, document_id):
        """A Corpus contains Document ids."""
        return document_id in self.__documents

    def __len__(self):
        """Length of a Corpus is the number of Documents it holds."""
        return len(self.__documents)

    def __getitem__(self, document_id):
        """Fetch a Document from the Corpus by its id."""
        return self.__documents[document_id]

    def __setitem__(self, document_id, text):
        """Add a Document to the Corpus using a unique id key."""
        text = clean_text(text)
        self.__documents[document_id] = Document(text, self.preprocessor)

    @property
    def gramsize(self):
        """Number of words in the ngram. Not editable post init."""
        return self.__gramsize

    def keys(self):
        """The document ids in the corpus."""
        return self.__documents.keys()

    @property
    def max_raw_frequency(self):
        """Highest frequency across all Documents in the Corpus."""
        ## TPO: caches value
        if self.__max_raw_frequency is None:
            self.__max_raw_frequency = max(_.max_raw_frequency for _ in self.__documents.values())
        return self.__max_raw_frequency

    @lru_cache()
    def count_doc_occurrences(self, ngram):
        """Count the number of documents the corpus has with the matching ngram."""
        # Note: caches the values as called multiple times for TFIDF calculation
        if ngram in self.__document_occurrences:
            count = self.__document_occurrences[ngram]
        else:
            count = sum((1 + NGRAM_EPSILON) if ngram in doc else 0 for doc in self.__documents.values())
        if ((count == 1) and PENALIZE_SINGLETONS):
            count = 0
        if (count == 0):
            count = NGRAM_EPSILON
        return count

    ## TPO
    @property
    def max_rel_doc_frequency(self):
        """"Highest relative document frequency for all ngrams in the corpus"""
        if self.__max_rel_doc_frequency is None:
            max_doc_frequency = max(self.count_doc_occurrences(ngram) for doc in self.__documents.values() for ngram in doc.keywordset)
            self.__max_rel_doc_frequency = max_doc_frequency / float(len(self))
        return self.__max_rel_doc_frequency
    
    ## TPO
    @property
    def max_doc_frequency(self):
        """"Highest relative document frequency for all ngrams in the corpus"""
        if self.__max_doc_frequency is None:
            max_doc_frequency = max(self.count_doc_occurrences(ngram) for doc in self.__documents.values() for ngram in doc.keywordset)
            self.__max_doc_frequency = max_doc_frequency
        return self.__max_doc_frequency
    
    def df_freq(self, ngram):
        """Return document frequency (DF) count for NGRAM"""
        return self.count_doc_occurrences(ngram)

    def df_norm(self, ngram, normalize_term=None):
        """Return DF in range [epsilon, 1] for NGRAM, with NORMALIZE_TERM by default.
        Note: The denominator is the max doc frequency rather than number of documents,
        so the values of df_norm are better comparable for different collections."""
        if normalize_term is None:
            normalize_term = not SKIP_NORMALIZATION
        if normalize_term:
            ngram = self.preprocessor.normalize_term(ngram)
        rel_doc_freq = 0
        if self.max_rel_doc_frequency > 0:
            rel_doc_freq = (self.df_freq(ngram) / self.max_doc_frequency)
        return rel_doc_freq

    def idf_basic(self, ngram):
        """Returns IDF based on log of relative document frequency"""
        debug.assertion(self.count_doc_occurrences(ngram) >= 1)
        if self.count_doc_occurrences(ngram) == 0:
            ## OLD: raise Exception(ngram)
            raise ValueError(f"count_doc_occurrences 0 for {ngram}")
        num_occurrences = self.count_doc_occurrences(ngram)
        ## TPO: TEST
        ## # HACK: give singletons a max DF to lower IDF score
        ## if (num_occurrences == 1) and PENALIZE_SINGLETONS:
        ##     num_occurrences = len(self.__documents)
        idf = math.log(float(len(self)) / num_occurrences)
        debug.trace_fmt(BDL + 2, "idf_basic({ng} len(self)={l} max_doc_occ={mdo} num_occ={no}) => {idf}",
                        ng=ngram, l=len(self), mdo=self.max_doc_frequency, no=num_occurrences, idf=idf)
        return idf

    def idf_freq(self, ngram):
        """Returns inverse proper of DF (not N/DF)"""
        debug.assertion(self.count_doc_occurrences(ngram) >= 1)
        if self.count_doc_occurrences(ngram) == 0:
            ## OLD: raise Exception(ngram)
            raise ValueError(f"count_doc_occurrences 0 for {ngram}")
        num_occurrences = self.count_doc_occurrences(ngram)
        idf = 1 / num_occurrences
        debug.trace_fmt(BDL + 2, "idf_freq({ng} len(self)={l} max_doc_occ={mdo} num_occ={no}) => {idf}",
                        ng=ngram, l=len(self), mdo=self.max_doc_frequency, no=num_occurrences, idf=idf)
        return idf

    def idf_smooth(self, ngram):
        """Returns IDF using simple smoothing with add-1 relative frequency (prior to log)"""
        debug.assertion(self.count_doc_occurrences(ngram) >= 1)
        idf = math.log(1 + (float(len(self)) / self.count_doc_occurrences(ngram)))
        debug.trace_fmt(BDL + 2, "idf_smooth({ng} len(self)={l} doc_occ={do}) => {idf}",
                        ng=ngram, l=len(self), do=self.count_doc_occurrences(ngram), idf=idf)
        return idf

    def idf_max(self, ngram):
        ## TODO: make sure this interpretation makes sense; also, make sure float conversion not required
        """Use maximum ngram TF in place of N and also perform add-1 smoothing"""
        debug.assertion(self.count_doc_occurrences(ngram) >= 1)
        idf = math.log(1 + self.max_raw_frequency / self.count_doc_occurrences(ngram))
        debug.trace_fmt(BDL + 2, "idf_smooth({ng} len(self)={l} doc_occ={do}) => {idf}",
                        ng=ngram, l=len(self), do=self.count_doc_occurrences(ngram), idf=idf)
        return idf

    def idf_probabilistic(self, ngram):
        """Returns IDF via probabilistic interpretation: log((N - d)/d), where d is the document occcurrence count for the NGRAM
        Note: Adds epsilon to avoid -inf when N equals d.
        """
        debug.assertion(self.count_doc_occurrences(ngram) >= 1)
        num_doc_occurrences = self.count_doc_occurrences(ngram)
        try:
            # See https://tmtoolkit.readthedocs.io/en/latest/api.html#tmtoolkit.bow.bow_stats.idf_probabilistic
            idf = math.log(float(len(self) - num_doc_occurrences) / num_doc_occurrences + MISC_EPSILON)
        except:
            idf = 0
            debug.trace_exception(BDL, "idf_probabilistic")
        debug.trace_fmt(BDL + 2, "idf_probabilistic({ng} len(self)={l} doc_occ={do}) => {idf}",
                        ng=ngram, l=len(self), do=num_doc_occurrences, idf=idf)
        return idf

    def idf(self, ngram, idf_weight='basic'):
        """Inverse document frequency (IDF) indicates ngram common-ness across the Corpus."""
        result = 0
        if idf_weight == 'freq':
            result = self.idf_freq(ngram)
        elif idf_weight == 'smooth':
            result = self.idf_smooth(ngram)
        elif idf_weight == 'basic':
            result = self.idf_basic(ngram)
        elif idf_weight == 'max':
            result = self.idf_max(ngram)
        elif idf_weight == 'prob':
            result = self.idf_probabilistic(ngram)
        ## TODO: allow for raw frequency
        elif idf_weight == 'freq':
            result = self.idf_freq(ngram)
        else:
            raise ValueError("Invalid idf_weight: " + idf_weight)
        debug.trace_fmt(BDL + 2, "idf({ng}, idfw={idfw}) => {r}",
                        ng=ngram, l=len(self), idfw=idf_weight, r=result)
        return result

    def tf_idf(self, ngram, document_id=None, text=None, idf_weight='basic', tf_weight='basic',
               normalize_term=None):
        """TF-IDF score. Must specify a document id (within corpus) or pass text body."""
        assert document_id or text
        if normalize_term is None:
            normalize_term = not SKIP_NORMALIZATION
        document = None
        if document_id:
            document = self[document_id]
        if text:
            text = clean_text(text)
            document = Document(text, self.preprocessor)
        norm_ngram = self.preprocessor.normalize_term(ngram) if normalize_term else ngram
        score = document.tf(ngram, tf_weight=tf_weight) * self.idf(norm_ngram, idf_weight=idf_weight)
        if TFIDF_NGRAM_LEN_WEIGHT:
            len_weight = TFIDF_NGRAM_LEN_WEIGHT ** len(ngram.split())
            debug.trace(BDL + 3, f"Factoring in ngram weight of {round(len_weight, 3)} into score {round(score, 3)} for {ngram!r}")
            score *= len_weight
        result = CorpusKeyword(document[ngram], ngram, score)
        debug.trace_fmt(BDL + 2, "tf_idf({ng}, id={id}, text={t} idfw={idfw}, tfw={tfw}, norm={n}) => {r}",
                        ng=ngram, id=document_id, t=text, idfw=idf_weight, tfw=tf_weight, n=normalize_term, r=result)
        return result

    @lru_cache()
    def get_keywords(self, document_id=None, text=None, idf_weight='basic',
                     tf_weight='basic', limit=100):
        """Return a list of keywords with TF-IDF scores. Defaults to the top 100."""
        debug.trace(BDL + 2, f"in get_keywords(); self={self}")
        debug.trace_expr(BDL + 2, document_id, text, idf_weight, tf_weight, limit)
        assert document_id or text
        document = None
        if document_id:
            document = self[document_id]
        if text:
            debug.assertion(document is None)
            text = clean_text(text)
            document = Document(text, self.preprocessor)
        out = []
        for ngram, kw in document.keywordset.items():
            ## TODO3: use tf_idf
            score = document.tf(ngram, tf_weight=tf_weight) * \
                self.idf(ngram, idf_weight=idf_weight)
            if TFIDF_NGRAM_LEN_WEIGHT:
                len_weight = TFIDF_NGRAM_LEN_WEIGHT ** len(ngram.split())
                debug.trace(BDL + 3, f"Factoring in ngram weight of {round(len_weight, 3)} into score {round(score, 3)} for {ngram!r}")
                score *= len_weight
            out.append(CorpusKeyword(kw, ngram, score))
        out.sort(key=lambda x: x.score, reverse=True)
        result = out[:limit]
        debug.trace(BDL + 3, f"get_keywords() => {result}")
        return result

#--------------------------------------------------------------------------------

def new_main():
    """New entry point for script: counts ngrams in input file (one line per document)"""
    # TODO: reconcile with code in ../ngram_tfidf.py; parameterize (e.g., ngram size)
    if (sys.argv[1] == "--help"):
        system.print_error("Usage: {prog} [--help] corpus-file".format(prog=sys.argv[0]))
        return
    input_file = sys.argv[1]

    # Create corpus from line documents in file
    corp = Corpus(min_ngram_size=MIN_NGRAM_SIZE, max_ngram_size=MAX_NGRAM_SIZE)
    doc_IDs = []
    for i, doc_text in enumerate(system.read_lines(input_file)):
        doc_IDs.append(f"line-doc{i + 1}")
        corp[doc_IDs[i]] = doc_text
               
    # Output top ngrams for each document
    SAMPLE_SIZE = system.getenv_int("SAMPLE_SIZE", 10,
                                    "Number of ngram samples to show")
    print(f"top {SAMPLE_SIZE} ngrams in each document/line")
    for i in range(len(doc_IDs)):
        tuples = corp.get_keywords(document_id=doc_IDs[i], limit=SAMPLE_SIZE)
        # note: ignores empty tokens
        ngram_info = [(ng.ngram + ":" + system.round_as_str(ng.score, 3)) for ng in tuples if ng.ngram.strip()]
        ngram_spec = "{" + ",".join(ngram_info) + "}"
        print(f"{doc_IDs[i]}:\t{ngram_spec}")
    return


def main():
    """Entry point for script: just runs a simple test"""
    # TODO: rename main as simple_test?
    if ((len(sys.argv) > 1) and (sys.argv[1] != "-")):
        new_main()
        return

    # Create simple corpus with two documents
    c = Corpus(min_ngram_size=2, max_ngram_size=4)
    doc_text = ["abc  def  ghi  jkl  mno         ",
                "abc  def       jkl  mno         ",
                "abc  def                pdq  rst"]
    ngrams = set()
    for i in range(len(doc_text)):
        doc_id = ("d" + str(i + 1))
        c[doc_id] = doc_text[i]
        print("{id}:\t{doc_text}".format(id=doc_id, doc_text=doc_text[i]))
        words = doc_text[i].split()
        debug.assertion(len(words) > 1)
        ngrams.update({(words[i] + " " + words[i + 1]) for i in range(len(words) - 1)})
    all_ngrams = sorted(ngrams)

    # Show combined set of ngrams
    print("ngrams:\t{spec}".format(spec="\t".join(ng.replace(" ", "_") for ng in sorted(all_ngrams))))

    # Show per-document TF for each ngram
    for docid in sorted(c.keys()):
        print("{id} TF:\t{spec}".
              format(id=docid, spec="\t".join([str(c[docid].tf_freq(ng)) for ng in all_ngrams])))

    # Show IDF, and TF-IDF for each ngram
    print("IDF:   \t{spec}".format(spec="\t".join([system.round_as_str(c.idf(ng), 3) for ng in all_ngrams])))
    debug.assertion(misc_utils.is_close(c.idf("abc def"), 0))
    debug.assertion(c.idf("jkl mno") < c.idf("pdq rst"))
    debug.assertion(c.idf("def ghi") == c.idf("ghi jkl") == c.idf("pdq rst"))
    for docid in sorted(c.keys()):
        print("{id} TF/IDF:   \t{spec}".          # TODO3: exclude CorpusKeyword info
              format(id=docid, spec="\t".join([str(c.tf_idf(ng, docid)) for ng in all_ngrams])))

#-------------------------------------------------------------------------------
    
if __name__ == '__main__':
    system.print_stderr(f"Warning: {__file__} is not intended to be run standalone. A simple test will be run.")
    main()
