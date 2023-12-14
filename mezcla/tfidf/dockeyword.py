#!/usr/bin/env python3

"""The basic unit of TF-IDF, the keyword.

This class allows you to have stemmed keywords, but still see the original text.

Warning: Note that this is low-level bookkeeping code, which is reflected in
the following example, which incorporates hard-coded stemming. See preprocess.py 
for usage with an actual stemmer.

Example:
    >>> import mezcla.tfidf.dockeyword as mtk
    >>> import mezcla.tfidf.document as mtd
    >>> text = 'dog dogs'
    >>> dog = mtk.DocKeyword('dog', mtd.Document(text), start=0, end=3)
    >>> dogs = mtk.DocKeyword('dog', mtd.Document(text), start=4, end=8)
    >>> dog.text == dogs.text
    True
    >>> dog.original_texts == dogs.original_texts
    False
    >>> str(dog)
    "Stem:dog, Instances:['dog'], Count:1"
    >>> str(dogs)
    "Stem:dog, Instances:['dogs'], Count:1"
"""

# Standard modules
from __future__ import absolute_import
from collections import namedtuple

# Local modules
from mezcla.tfidf.config import BASE_DEBUG_LEVEL as BDL
from mezcla import debug
from mezcla import system

# Constants
Location = namedtuple('Location', ['document', 'start', 'end'])


class DocKeyword(object):
    """Class for maintaining stemmed term and original"""
    # Note: debug tracing commented out to cut down on overhead
    
    def __init__(self, text, document=None, start=None, end=None):
        self.locations = set()
        self.text = text
        if (start is not None) and (end is not None):
            self.locations.add(Location(document, start, end))
        ## DEBUG: debug.trace_object(BDL + 4, self, "DocKeyword instance", show_all=False)

    def update_locations(self, locations):
        """Add LOCATIONS to other locations"""
        self.locations = self.locations.union(locations)

    def __add__(self, other):
        assert self.text == other.text
        out = DocKeyword(self.text)
        out.locations = self.locations
        out.update_locations(other.locations)
        return out

    def __ladd__(self, other):
        if other == 0:
            return self
        return self.__add__(other)

    def __len__(self):
        return len(self.locations)

    @property
    def original_texts(self):
        """Return list of original texts"""
        out = []
        for loc in self.locations:
            if loc.document:
                text = loc.document.text[loc.start: loc.end]
            else:
                text = ''
            out.append(text)
        ## DEBUG: debug.trace_expr(BDL + 3, out)
        return list(set(out))

    def get_first_text(self):
        """Return the first original text."""
        loc = next(iter(self.locations))
        ## DEBUG: debug.trace_expr(BDL + 3, loc.document.text)
        return loc.document.text[loc.start: loc.end]

    def __str__(self):
        return 'Stem:%s, Instances:%s, Count:%d' % (self.text, str(self.original_texts), len(self))

#-------------------------------------------------------------------------------
    
if __name__ == '__main__':
    system.print_stderr(f"Warning: {__file__} is not intended to be run standalone")
    debug.trace_object(BDL + -2, DocKeyword("monkeys"))
