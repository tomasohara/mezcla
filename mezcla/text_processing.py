#! /usr/bin/env python3
#
# text_processing.py: performs text processing (e.g., via NLTK), mainly for
# word tokenization and part-of-speech tagging. To make the part-of-speech
# output easier to digrest, there is an envionment option USE_CLASS_TAGS
# to enable use of class-based tags, such as those used in traditional 
# grammar (e.g., noun for NNS).
# 
#
# Notes:
# - function resulting caching ("memoization") is used via memodict decoration
# - environment variables (env-var) are used for some adhoc options
# - to bypass NLTK (e.g., for quick debugging), set SKIP_NLTK env-var to 0
#
#------------------------------------------------------------------------
# Miscelleneous notes
#
# Penn Tags (used by NLTK part-of-speech tagger)
# 
# CC    Coordinating conjunction
# CD    Cardinal number
# DT    Determiner
# EX    Existential there
# FW    Foreign word
# IN    Preposition or subordinating conjunction
# JJ    Adjective
# JJR   Adjective, comparative
# JJS   Adjective, superlative
# LS    List item marker
# MD    Modal
# NN    Noun, singular or mass
# NNS   Noun, plural
# NNP   Proper noun, singular
# NNPS  Proper noun, plural
# PDT   Predeterminer
# POS   Possessive ending
# PP    Personal pronoun
# PP$   Possessive pronoun ???
# PRP$  Possessive pronoun
# PRP   Personal pronoun
# RB    Adverb
# RBR   Adverb, comparative
# RBS   Adverb, superlative
# RP    Particle
# SYM   Symbol
# TO    to
# UH    Interjection
# VB    Verb, base form
# VBD   Verb, past tense
# VBG   Verb, gerund or present participle
# VBN   Verb, past participle
# VBP   Verb, non-3rd person singular present
# VBZ   Verb, 3rd person singular present
# WDT   Wh-determiner
# WP    Wh-pronoun
# WP$   Possessive wh-pronoun
# WRB   Wh-adverb
#
# See ftp://ftp.cis.upenn.edu/pub/treebank/doc/tagguide.ps.gz for more details.
#------------------------------------------------------------------------
# TODO:
# - Integrate punctuation isolation (see prep_brill.perl).
# - Add usage examples (e.g., part-of-speech tagging).
# - Warn that without NLTK or Enchant, the text processing just checks common cases.
#

"""Performs text processing (e.g., tokenization via NLTK)"""

# Standard packages
from abc import ABCMeta, abstractmethod
import sys                              # system interface (e.g., command line)
import re                               # regular expressions

# Installed packages
## TODO: import flair
## OLD:
## from flair.data import Sentence
## from flair.models import SequenceTagger
flair = None

# Local packages
from mezcla import debug
## OLD: from mezcla import misc_utils
## OLD: from mezcla import spacy_nlp
spacy_nlp = None
from mezcla import system
from mezcla import glue_helpers as gh
## OLD: from mezcla import tpo_common as tpo

# Constants
TL = debug.TL

#------------------------------------------------------------------------
# Globals

# Object for spell checking via enchant
speller = None
word_freq_hash = None
WORD_FREQ_FILE = system.getenv_text("WORD_FREQ_FILE", "word.freq")
nltk = None
enchant = None

# Hash for returning most common part of speech for a word (or token)
word_POS_hash = None
WORD_POS_FREQ_FILE = system.getenv_text("WORD_POS_FREQ_FILE", "word-POS.freq")

# Misc. options
LINE_MODE = system.getenv_boolean("LINE_MODE", False, "Process text line by line (not all all once)")
JUST_TAGS = system.getenv_boolean("JUST_TAGS", False, "Just show part of speech tags (not word/POS pair)")
OUTPUT_DELIM = system.getenv_text("OUTPUT_DELIM", " ", "Delimiter (separator) for output lists")
INCLUDE_MISSPELLINGS = system.getenv_boolean("INCLUDE_MISSPELLINGS", False, "Include spell checking")
SKIP_MISSPELLINGS = system.getenv_boolean("SKIP_MISSPELLINGS", not INCLUDE_MISSPELLINGS, "Skip spell checking")
SHOW_MISSPELLINGS = not SKIP_MISSPELLINGS
USE_CLASS_TAGS = system.getenv_boolean("USE_CLASS_TAGS", False, "Use class-based tags (e.g., Noun for NNP)")
SKIP_CLASS_TAGS = not USE_CLASS_TAGS
KEEP_PUNCT = system.getenv_boolean("KEEP_PUNCT", False, "Use punctuation symbol as part-of-speech label")
TERSE_OUTPUT = system.getenv_boolean("TERSE_OUTPUT", JUST_TAGS, "Terse output mode")
## OLD: VERBOSE = not TERSE_OUTPUT
VERBOSE_DEFAULT = not TERSE_OUTPUT
VERBOSE = system.getenv_boolean(         ## TODO3?: reconcile with main.py
    "VERBOSE", VERBOSE_DEFAULT,
    desc="Verbose output mode")
UNDO_NLTK_QUOTING = system.getenv_boolean(
    "UNDO_NLTK_QUOTING", False,
    desc="Undo NLTK's unintuitive ``...'' handling of double quotes")
SKIP_TOKENIZATION = system.getenv_boolean(
    "SKIP_TOKENIZATION", False,
    desc="Omit sentence and word tokenization, such as for LINE_MODE")

# Skip use of NLTK and/or ENCHANT packages (using simple versions of functions)
# TODO: make misspellings optional (add --classic mode???)
SKIP_NLTK = system.getenv_boolean("SKIP_NLTK", False, "Omit usage of Natural Language Toolkit (NLTK)")
SKIP_ENCHANT = system.getenv_boolean("SKIP_ENCHANT", SKIP_MISSPELLINGS, "Omit usage of Enchant package for spell checking")
DOWNLOAD_DATA = system.getenv_bool("DOWNLOAD_DATA", False,
                                   "Download data from NLTK")
FLAIR_MODEL = system.getenv_text(
    "FLAIR_MODEL", "flair/chunk-english-fast",
    description="Model for Flair: see https://huggingface.co/flair"
)
TEXT_PROC = system.getenv_text(
    "TEXT_PROC", "spacy",
    description="name of text processor to use for chunking")

# List of stopwords (e.g., high-freqency function words)
stopwords = None

#------------------------------------------------------------------------
# Optional libraries
## TODO4: add init function for dynamic loading (e.g., for testing purposes)

# NLP toolkit
if not SKIP_NLTK:
    import nltk            # pylint: disable=ungrouped-imports
# spell checking
if not SKIP_ENCHANT:
    import enchant         # pylint: disable=ungrouped-imports

#------------------------------------------------------------------------
# Functions

def split_sentences(text):
    """Splits TEXT into sentences"""
    # EX: split_sentences("I came. I saw. I conquered!") => ["I came.", "I saw.", "I conquered!"]
    # EX: split_sentences("Dr. Watson, it's elementary. But why?") => ["Dr. Watson, it's elementary.", "But why?"]
    if SKIP_NLTK:
        # Split around sentence-ending punctuation followed by space,
        # but excluding initials (TODO handle abbreviations (e.g., "mo.")
        #
        # TEST: Replace tabs with space and newlines with two spaces
        ## text = re.sub(r"\t", " ", text)
        ## text = re.sub(r"\n", "  ", text)
        # 
        # Make sure ending punctuaion followed by two spaces and preceded by one
        text = re.sub(r"([\.\!\?])\s", r" \1  ", text)
        #
        # Remove spacing added above after likely abbreviations
        text = re.sub(r"\b([A-Z][a-z]*)\s\.\s\s", r"\1. ", text)
        #
        # Split sentences by ending punctuation followed by two spaces
        # Note: uses a "positive lookbehind assertion" (i.e., (?<=...) to retain punctuation 
        sentences = re.split(r"(?<=[\.\!\?])\s\s+", text.strip())
    else:
        sentences = nltk.tokenize.sent_tokenize(text)
    return sentences


def split_word_tokens(text, omit_punct=False, omit_stop=None,
                      skip_nltk=SKIP_NLTK, undo_nltk_quoting=UNDO_NLTK_QUOTING):
    """Splits TEXT into word tokens (i.e., words, punctuation, etc.), optionally with OMIT_PUNCT and OMIT_STOP.
    Note: run split_sentences first (e.g., to allow for proper handling of periods).
    By default, this uses NLTK's PunktSentenceTokenizer."""
    # EX: split_word_tokens("How now, brown cow?") => ['How', 'now', ',', 'brown', 'cow', '?']
    debug.trace(7, "split_word_tokens(%s); type=%s" % (text, type(text)))
    if skip_nltk:
        tokens = [t.strip() for t in re.split(r"(\W+)", text) if (len(t.strip()) > 0)]
    else:
        tokens = nltk.word_tokenize(text)

        # Restore awkward double quote tokenization
        # ex: ['``', 'Bond', ',', 'James', 'Bond', "''"] => ['""', 'Bond', ',', 'James', 'Bond', '""']
        if undo_nltk_quoting:
            is_nltk_quote = {"``": True, "''": True}
            ## TEST:
            ## new_text = my_re.sub("``(.*)''", r'"\1"', " ".join(tokens))
            ## debug.assertion(text.count('"') ==  new_text.count('"')
            tokens = [t if not is_nltk_quote.get(t) else '"' for t in tokens]
            debug.assertion(text.count('"') == " ".join(tokens).count('"'),
                            f"Problem restoring double quotes in {text!r}: {tokens=}")
    if omit_punct:
        tokens = [t for t in tokens if not is_punct(t)]
    if omit_stop:
        tokens = [t for t in tokens if not is_stopword(t)]
    debug.trace(7, "tokens: %s" % [(t, type(t)) for t in tokens])
    return tokens
#
# split_word_tokens("How now, brown cow?", omit_punct=True, omit_stop=True) => ['now', 'brown', 'cow']


def label_for_tag(POS, word=None):
    """Returns part-of-speech label for POS, optionally overriden based on WORD (e.g., original token if punctuation)"""
    label = POS
    if KEEP_PUNCT and word and re.match(r"\W", word[0]):
        label = word
        debug.trace_fmtd(5, "label_for_tag({t}, {w}) => {l}", t=POS, w=word, l=label)
    return label


fallback_POS_class = {  # classes for parts-of-speech not covered by rules (see class_for_tag)
    "CC": "conjunction",        # Coordinating conjunction
    "CD": "number",             # Cardinal number
    "DT": "determiner",         # Determiner
    "EX": "pronoun",            # Existential there
    "FW": "noun",               # Foreign word
    "IN": "preposition",        # Preposition or subordinating conjunction
    "JJ": "adjective",          # Adjective
    "JJR": "adjective",         # Adjective, comparative
    "JJS": "adjective",         # Adjective, superlative
    "LS": "punctuation",        # List item marker
    "MD": "auxiliary",          # Modal
    "PDT": "determiner",        # Predeterminer
    "POS": "punctuation",       # Possessive ending
    "SYM": "punctuation",       # Symbol
    "TO": "preposition",        # to
    "UH": "punctuation",        # Interjection
    "WDT": "determiner",        # Wh-determiner
    "WP": "pronoun",            # Wh-pronoun
    "WP$": "pronoun",           # Possessive wh-pronoun
    "WRB": "adverb",            # Wh-adverb
}


def class_for_tag(POS, word=None, previous=None):
    """Returns class label for POS tag, optionally over WORD and for PREVIOUS tag. Note: most cases are resolved without previous tag for context, except for gerunds and past participles which are considered nouns unless previous is auxiliary. Similarly, the word is only considered for special cases like punctuation."""
    # EX: class_for_tag("NNS") => "noun"
    # EX: class_for_tag("VBG") => "verb"
    # EX: class_for_tag("VBG", previous="MD") => "verb"
    # EX: class_for_tag("NNP", word="(") => "punctuation"
    tag_class = "unknown"
    if (POS == "VBG") and previous and ((previous[:2] == "VB") or (previous == "MD")):
        tag_class = "verb"
    elif (POS == "VBP") and previous and ((previous[:2] == "VB") or (previous == "MD")):
        tag_class = "verb"
    elif word and re.match(r"\W", word[0]):
        tag_class = "punctuation"
    # TODO: use prefix-based lookup table for rest (e.g., {"NN": "noun", ...})?
    elif POS[:2] == "NN":
        tag_class = "noun"
    elif POS[:2] == "JJ":
        tag_class = "adjective"
    elif POS[:2] == "VB":
        tag_class = "verb"
    elif POS[:2] == "RB":
        tag_class = "adverb"
    elif (POS[:2] == "PR") or (POS[:2] == "PP"):
        tag_class = "pronoun"
    else:
        tag_class = fallback_POS_class.get(POS, tag_class)
    debug.trace_fmtd(5, "class_for_tag({t}, {p}) => {c}", t=POS, p=previous, c=tag_class)
    return tag_class


def tag_part_of_speech(tokens):
    """Return list of part-of-speech taggings of form (token, tag) for list of TOKENS"""
    # EX: tag_part_of_speech(['How', 'now', ',', 'brown', 'cow', '?']) => [('How', 'WRB'), ('now', 'RB'), (',', ','), ('brown', 'JJ'), ('cow', 'NN'), ('?', '.')]
    if SKIP_NLTK:
        part_of_speech_taggings = [(word, get_most_common_POS(word)) for word in tokens]
    else:
        part_of_speech_taggings = []
        previous = None
        raw_part_of_speech_taggings = nltk.pos_tag(tokens)
        debug.trace(5, "raw tags: %s" % [t for (_w, t) in raw_part_of_speech_taggings])
        for (word, POS) in raw_part_of_speech_taggings:
            tag = label_for_tag(POS, word) if SKIP_CLASS_TAGS else class_for_tag(POS, word, previous)
            part_of_speech_taggings.append((word, tag))
            previous = POS
    debug.trace_fmt(6, "tag_part_of_speech({tokens}) => {tags}", 
                    tokens=tokens, tags=part_of_speech_taggings)
    return part_of_speech_taggings


def tokenize_and_tag(text):
    """Run sentence(s) and word tokenization over text and then part-of-speech tag it"""
    # TODO: return one list per sentence not just one combined list
    debug.trace(7, "tokenize_and_tag(%s)" % text)
    ## OLD: text = tpo.ensure_unicode(text)
    text_taggings = []
    sentences = split_sentences(text) if not SKIP_TOKENIZATION else [text]
    for sentence in sentences:
        if not SKIP_TOKENIZATION:
            debug.trace(5, "sentence: %s" % sentence.strip())
            tokens = split_word_tokens(sentence)
            debug.trace(5, "tokens: %s" % tokens)
        else:
            tokens = sentence.split()
        taggings = tag_part_of_speech(tokens)
        debug.trace(5, "taggings: %s" % taggings)
        text_taggings += taggings
    return text_taggings


def tokenize_text(text):
    """Run sentence and word tokenization over text returning a list of sentence word lists"""
    tokenized_lines = []
    for sentence in split_sentences(text):
        sent_tokens = split_word_tokens(sentence)
        debug.trace(5, "sent_tokens: %s" % sent_tokens)
        tokenized_lines.append(sent_tokens)
    return tokenized_lines


@system.memodict
def is_stopword(word):
    """Indicates whether WORD should generally be excluded from analysis (e.g., function word)"""
    # note: Intended as a quick filter for excluding non-content words.
    global stopwords
    if (stopwords is None):
        if SKIP_NLTK:
            stopwords = ['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers', 'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now']
        else:
            stopwords = nltk.corpus.stopwords.words('english')
        debug.trace(6, "stopwords: %s" % stopwords)
    return (word.lower() in stopwords)


@system.memodict
def has_spelling_mistake(term):
    """Indicates whether TERM represents a spelling mistake"""
    # TODO: rework in terms of a class-based interface
    has_mistake = False
    try:
        if SKIP_ENCHANT:
            global word_freq_hash
            if not word_freq_hash:
                word_freq_path = gh.resolve_path(WORD_FREQ_FILE)
                gh.assertion(gh.non_empty_file(word_freq_path))
                word_freq_hash = read_freq_data(word_freq_path)
            has_mistake = term.lower() not in word_freq_hash
        else:
            global speller
            if not speller:
                speller = enchant.Dict("en_US")
            has_mistake = not speller.check(term)
    except:
        system.print_exception_info(f"spell checking of {term}")
    debug.trace(6, f"has_spelling_mistake({term}) => {has_mistake}")
    return has_mistake


def read_freq_data(filename):
    """Reads frequency listing for words (or other keys). A hash table is returned from (lowercased) key to their frequency."""
    # Sample input:
    #   # Word      Freq
    #   the 179062
    #   to  123567
    #   is  99390
    #   and 95920
    #   a   76679
    debug.trace(4, "read_freq_data(%s)" % filename)
    freq_hash = {}

    # Process each line of the file
    input_handle = system.open_file(filename)
    line_num = 0
    for line in input_handle:
        line_num += 1
        # Ignore comments
        line = line.strip()
        if (len(line) > 0) and (line[0] == '#'):
            continue

        # Extract the four fields and warn if not defined
        fields = line.split("\t")
        if (len(fields) != 2):
            debug.trace(3, "Ignoring line %d of %s: %s" % (line_num, filename, line))
            continue
        (key, freq) = fields
        key = key.strip().lower()

        # Store in hash
        if key not in freq_hash:
            freq_hash[key] = freq
        else:
            debug.trace(6, "Ignoring alternative freq for key %s: %s (using %s)" 
                        % (key, freq, freq_hash[key]))
        
    return (freq_hash)


def read_word_POS_data(filename):
    """Reads frequency listing for words in particular parts of speech
    to derive dictionay of the most common part-of-speech for words (for quick-n-dirty part-of-speech
    tagging). A hash table is returned from (lowercased) words to their most common part-of-speech."""
    # Sample input:
    #   # Token     POS     Freq
    #   ,           ,       379752
    #   .           .       372550
    #   the         DT      158317
    #   to          TO      122189
    debug.trace(4, "read_word_POS_freq(%s)" % filename)
    global word_POS_hash
    word_POS_hash = {}

    # Process each line of the file
    input_handle = system.open_file(filename)
    line_num = 0
    for line in input_handle:
        line_num += 1
        # Ignore comments
        line = line.strip()
        if (len(line) > 0) and (line[0] == '#'):
            continue

        # Extract the four fields and warn if not defined
        fields = line.split("\t")
        if (len(fields) != 3):
            debug.trace(3, "Ignoring line %d of %s: %s" % (line_num, filename, line))
            continue
        (word, POS, _freq) = fields
        word = word.strip().lower()

        # Store in hash
        if word not in word_POS_hash:
            word_POS_hash[word] = POS
        else:
            debug.trace(6, "Ignoring alternative POS for word %s: %s (using %s)" 
                            % (word, POS, word_POS_hash[word]))
        
    return (word_POS_hash)


def get_most_common_POS(word):
    """Returns the most common part-of-speech label for WORD, defaulting to NN (noun)"""
    # EX: get_most_common_POS("can") => "MD"
    # EX: get_most_common_POS("notaword") => "NN"
    global word_POS_hash
    if not word_POS_hash:
        word_POS_freq_path = gh.resolve_path(WORD_POS_FREQ_FILE)
        gh.assertion(gh.non_empty_file(word_POS_freq_path))
        word_POS_hash = read_word_POS_data(word_POS_freq_path)
    label = "NN"
    word = word.lower()
    if (word in word_POS_hash):
        label = word_POS_hash[word]
    return label

#------------------------------------------------------------------------
# Utility functions
#
# TODO: make POS optional for is_POS-type functions (and use corpus frequencies to guess)
#

def is_noun(_token, POS):
    """Indicates if TOKEN is a noun, based on POS"""
    return (POS[0:2] == "NN")


def is_verb(_token, POS):
    """Indicates if TOKEN is a verb, based on POS"""
    # EX: is_verb('can', 'NN') => False
    return (POS[0:2] == "VB")


def is_adverb(_token, POS):
    """Indicates if TOKEN is an adverb, based on POS"""
    # EX: is_adverb('quickly', 'RB') => True
    return (POS[0:2] == "RB")


def is_adjective(_token, POS):
    """Indicates if TOKEN is an adjective, based on POS"""
    # EX: is_adverb('quick', 'JJ') => True
    return (POS[0:2] == "JJ")


def is_comma(token, POS):
    """Indicates if TOKEN is a comma"""
    return ((token == ",") or (POS[0:1] == ","))


def is_quote(token, _POS):
    """Indicates if TOKEN is a quotation mark"""
    # Note: this includes checks for MS Word smart quotes because in training data
    # TODO: make handled properly with respect to Unicode encoding (e.g., UTF-8)
    return token in "\'\"\x91\x92\x93\x94"

def is_punct(token, POS=None):
    """Indicates if TOKEN is a punctuation symbol"""
    # EX: is_punct('$', '$') => True
    return (re.search("[^A-Za-z0-9]", token[0:1]) or 
            (POS and re.search("[^A-Za-z]", POS[0:1])))

# TODO: alternative to is_punct
## def is_punctuation(token, POS):
##     """Indicates if TOKEN is a punctuation symbol"""
##     # EX: is_punct('$', '$') => True
##     # TODO: find definitive source (or use ispunct-type function)
##     punctuation_chars_regex = r"[\`\~\!\@\#\$\%\^\&\*\(\)\_\-\+\=\{\}\[\]\:\;\"\'\<\>\,\.]"
##     return (re.search(punctuation_chars_regex, token[0:1]) or (POS
## re.search("[^A-Za-z]", POS[0:1]))


def init():
    """Makes sure globals defined and optionally loads resources"""

    # Note: stop word check is done for side of effect of loading list
    unexpected_stopword = is_stopword("movement")
    debug.assertion(not unexpected_stopword)

    if DOWNLOAD_DATA:
        download_nltk_resources()
    
#-------------------------------------------------------------------------------

class TextProc(metaclass=ABCMeta):
    """Base class for text processing, such as via NLTK, Spacy or Flair"""

    def __init__(self, model=None):
        """Initializer: with provider-specific MODEL"""
        debug.trace(TL.VERBOSE, f"TextProc.__init__({model}): self={self}")
        debug.trace_object(5, self, label="TextProc instance")

    @abstractmethod
    def noun_phrases(self, text):
        """Return list of noun chunks in text"""
        raise NotImplementedError()
        
    @abstractmethod
    def verb_phrases(self, text):
        """Return list of verb chunks in text"""
        raise NotImplementedError()
        
class SpacyTextProc(TextProc):
    """TextProc via Spacy"""
    
    def __init__(self, model=None):
        super().__init__(model)
        global spacy_nlp
        if spacy_nlp is None:
            # pylint: disable=import-outside-toplevel, disable=redefined-outer-name
            from mezcla import spacy_nlp
        self.spacy = spacy_nlp.Chunker(model)
        debug.trace_object(5, self, label="SpacyTextProc instance")

    def noun_phrases(self, text):
        return self.spacy.noun_phrases(text)

    def verb_phrases(self, text):
        debug.trace(4, "FYI: Spacy doesn't support verb phrase chunking")
        result = []
        debug.trace(6, f"noun_phrases({text!r}) => {result!r}")
        return result

class FlairTextProc(TextProc):
    """TextProc via Flair"""

    def __init__(self, model=None):
        super().__init__(model)
        if model is None:
            model = FLAIR_MODEL
        global flair
        if flair is None:
            # pylint: disable=import-outside-toplevel, disable=redefined-outer-name
            import flair
        self.tagger = flair.models.SequenceTagger.load(model)
        debug.trace_object(5, self, label="FlairTextProc instance")
    
    def noun_phrases(self, text):
        # Based on https://huggingface.co/flair/chunk-english-fast
        sentence = flair.data.Sentence(text)
        self.tagger.predict(sentence)
        noun_phrases = [phr.text for phr in sentence.get_spans()  if (phr.tag == "NP")]
        debug.trace(6, f"noun_phrases({text!r}) => {noun_phrases!r}")
        return noun_phrases

    def verb_phrases(self, text):
        # Based on https://huggingface.co/flair/chunk-english-fast
        sentence = flair.Sentence(text)
        self.tagger.predict(sentence)
        verb_phrases = [phr.text for phr in sentence.get_spans()  if (phr.tag == "VP")]
        debug.trace(6, f"verb_phrases({text!r}) => {verb_phrases!r}")
        return verb_phrases


def create_text_proc(name, *args, **kwargs):
    """Return class to use for TextProc NAME
    Note: Passes along optional ARGS and KWARGS to constructor
    """
    # EX: (create_text_proc("flair").__class__ == FlairTextProc().__class__)
    # TODO2: see if standard way to do class displatching
    class_instance = None
    try:
        ## BAD: class_object = misc_utils.get_class_from_name(name.capitalize())
        ## TODO: class_object = misc_utils.get_class_from_name(name.capitalize(), module_name=__name__)
        ## OLD: class_object = (SpacyTextProc if (name == "spacy") else FlairTextProc if (name == "flair") else TextProc)
        class_object = (SpacyTextProc if (name == "spacy") else FlairTextProc if (name == "flair") else None)
        ## BAD:
        ## debug.assertion(class_object.__class__.__name__.endswith("TextProc"))
        ## class_instance = class_object.__new__(*args, **kwargs)
        class_instance = class_object(*args, **kwargs)
        debug.trace_expr(6, class_object, class_instance)
    except:
        system.print_exception_info("create_text_proc")
    return class_instance


def download_nltk_resources():
    """Download NLTK resources from their website"""
    nltk.download(['punkt', 'punkt_tab', 
                   'averaged_perceptron_tagger',
                   'averaged_perceptron_tagger_eng',
                   'stopwords'])

#-------------------------------------------------------------------------------

def usage():
    """Displays command-line usage"""
    usage_note = """
Usage: _SCRIPT_ [--help] [--just-tokenize] [--just-chunk] [--lowercase] file
Example:

echo "My dawg has fleas." | _SCRIPT_ -

Notes:
- Intended more as a library module
- In standalone mode it runs the text processing pipeline over the file:
     sentence splitting, word tokenization, and part-of-speech tagging
- Set SKIP_NLTK environment variable to 1 to disable NLTK usage.
"""
    # TODO: __file__ => sys.argv[1]???
    system.print_stderr(usage_note.replace("_SCRIPT_", __file__))
    return

def main():
    """
    Main routine: parse arguments and perform main processing
    TODO: revise comments
    Note: Used to avoid conflicts with globals (e.g., if this were done at end of script).
    """
    # Initialize
    debug.trace(5, "main(): sys.argv=%s" % sys.argv)

    # Show usage statement if no arguments or if --help specified
    just_tokenize = False
    make_lowercase = False
    just_chunk = False
    show_usage = ((len(sys.argv) == 1) or (sys.argv[1] == "--help"))
    arg_num = 1
    while ((not show_usage) and arg_num < len(sys.argv) and (sys.argv[arg_num][0] == "-")):
        if (sys.argv[arg_num] == "--just-tokenize"):
            just_tokenize = True
        elif (sys.argv[arg_num] == "--lowercase"):
            make_lowercase = True
        elif (sys.argv[arg_num] == "--just-chunk"):
            just_chunk = True
        elif sys.argv[arg_num] == "-":
            break
        else:
            system.print_stderr("Invalid argument: %s" % sys.argv[arg_num])
            show_usage = True
        arg_num += 1
    if (show_usage):
        usage()
        sys.exit()

    # Run the text from each file through the pipeline
    for i in range(arg_num, len(sys.argv)):
        # Input the entire text from the file (or stdin if - specified)
        filename = sys.argv[i]
        input_handle = system.open_file(filename) if (filename != "-") else sys.stdin
        debug.trace_expr(5, filename, input_handle)

        # Analyze the text
        while True:
            text = input_handle.readline() if LINE_MODE else input_handle.read()
            if text == "":
                break
            text = text.strip()
            if just_tokenize:
                # Just tokenize sentence and words
                # Note: text lowercased at end to allow for case clues (e.g., "Dr. Jones")
                for tokenized_line in tokenize_text(text):
                    tokenized_text = " ".join(tokenized_line)
                    if make_lowercase:
                        tokenized_text = tokenized_text.lower()
                    print(tokenized_text)
            elif just_chunk:
                ## OLD: text_proc = FlairTextProc()
                text_proc = create_text_proc(TEXT_PROC)
                if VERBOSE:
                    print(f"text: {text}")
                    print("NP chunks: ", end="")
                ## TODO: print(OUTPUT_DELIM.join(text_proc.noun_phrases(text)))
                print(text_proc.noun_phrases(text))
                if VERBOSE:
                    print("")
            else:
                # Show complete pipeline step-by-step
                taggings = tokenize_and_tag(text)
                
                # Show the results
                # TODO: show original tags if class-based; put JUST_TAGS support in tag_part_of_speech
                # TODO: flesh out support for verbose mode
                if VERBOSE:
                    print("text: %s" % text)
                if JUST_TAGS:
                    if VERBOSE:
                        print("tokens: %s" % OUTPUT_DELIM.join([w for (w, _POS) in taggings]))
                        print("tags: %s" % OUTPUT_DELIM.join([POS for (_w, POS) in taggings]))
                    else:
                        print(OUTPUT_DELIM.join([POS for (_w, POS) in taggings]))
                else:
                    gh.assertion(VERBOSE)
                    print("taggings: %s" % taggings)
                if SHOW_MISSPELLINGS:
                    misspellings = [w for (w, POS) in taggings if has_spelling_mistake(w)]
                    gh.assertion(VERBOSE)
                    print("misspellings: %s" % misspellings)
                if VERBOSE:
                    print("")

    # Cleanup
    debug.trace(5, "stop %s: %s" % (__file__, debug.timestamp()))
    return

#------------------------------------------------------------------------
# Initialization

init()

if __name__ == "__main__":
    main()
