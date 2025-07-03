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
ADD_DUMMY_LOCATION = system.getenv_boolean(
    ## TODO2: drop and just use SKIP_LOCATION
    "ADD_DUMMY_LOCATION", False,
    desc="Add dummy DocKeyword location for debugging purposes")
SKIP_DOC_LOCATION = system.getenv_boolean(
    "SKIP_DOC_LOCATION", False,
    desc="Skip location tracking")


class DocKeyword(object):
    """Class for maintaining stemmed term and original"""
    # Note: debug tracing commented out to cut down on overhead
    
    def __init__(self, text, document=None, start=None, end=None,
                 skip_location=None, add_dummy_location=None):
        self.locations = set()
        self.text = text
        self.count = 1
        if skip_location is None:
            skip_location = SKIP_DOC_LOCATION
        self.skip_location = skip_location
        if add_dummy_location is None:
            add_dummy_location = ADD_DUMMY_LOCATION
        self.add_dummy_location = add_dummy_location
        debug.assertion(not (self.skip_location and add_dummy_location))
        if self.add_dummy_location:
            if (start is None):
                start = -1
            if (end is None):
                end = -1
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
        length = len(self.locations) if not self.skip_location else self.count
        return length

    @property
    def original_texts(self):
        """Return list of original texts"""
        out = []
        if self.skip_location:
            ## TODO3: just show warning once
            debug.trace(BDL - 1, "FYI: original_texts disabled with skip_location")
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
        if self.skip_location:
            ## TODO3: just show warning once
            debug.trace(BDL - 1, "FYI: get_first_text disabled with skip_location")
        loc = next(iter(self.locations))
        ## DEBUG: debug.trace_expr(BDL + 3, loc.document.text)
        return loc.document.text[loc.start: loc.end]

    def __str__(self):
        return ('Stem:%s, Instances:%s, Count:%d, Len:%d, #Locs:%d'
                % (self.text, str(self.original_texts), self.count, len(self.locations), len(self)))

#-------------------------------------------------------------------------------
    
if __name__ == '__main__':
    system.print_stderr(f"Warning: {__file__} is not intended to be run standalone")
    monkey_keyword = DocKeyword("monkeys")
    print(f"{monkey_keyword=}")
    print(f"{str(monkey_keyword)=}")
    debug.trace_object(BDL - 2, monkey_keyword, "monkey_keyword")
