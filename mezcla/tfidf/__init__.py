## TPO: new version and docstring
"""
Package for Term Frequency (TF) Inversion Document Frequency (IDF): TF-IDF
"""
__version__ = "1.6"

## TODO
## # HACK: For relative imports to work in Python 3.6
## # See https://stackoverflow.com/questions/16981921/relative-imports-in-python-3.
## import os
## import sys;
## sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mezcla.tfidf.corpus import MIN_NGRAM_SIZE, MAX_NGRAM_SIZE

__all__ = ["MIN_NGRAM_SIZE", "MAX_NGRAM_SIZE"]
