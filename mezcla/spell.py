#! /usr/bin/env python
#
# spell.py: simple spell checker (e.g., via Enchant module)
#
# TODO:
# - integrate code for suggestions based on spelling distance
#

"""Basic spell checking"""

# Standard modules
# TODO: sys => system
import sys
import fileinput

# Installed modules
import enchant			# spell checking

# Local modules
from mezcla import debug
## TODO: from mezcla.main import Main
## TODO: from mezcla import system
from mezcla.my_regex import my_re

# Process command line
# TODO: upgrade to using Main script (see template.py)
i = 1
show_usage = (i == len(sys.argv))
while (i < len(sys.argv)) and (sys.argv[i][0] == "-"):
    if (sys.argv[i] == "--help"):
        show_usage = True
    elif (sys.argv[i] == "-"):
        pass
    else:
        print("Error: unexpected argument '%s'" % sys.argv[i])
        show_usage = True
    i += 1
if (show_usage):
    print("Usage: %s [options] input-file" % sys.argv[0])
    print("")
    print("Options: [--help]")
    print("")
    print("Examples:")
    print("")
    print("  %s query-keywords.list" % sys.argv[0])
    print("")
    print("  echo 'how now browne cow?' | {prog} -".format(prog=sys.argv[0]))
    print("")
    sys.exit()
# Discard any used arguments (for sake of fileinput)
if (i > 1):
    debug.trace(5, f"discarding used args: {sys.argv[1: i]}")
    sys.argv = [sys.argv[0]] + sys.argv[i:]

# Initialize spell checking
speller = enchant.Dict("en_US")

# Check input
for line in fileinput.input():
    line = line.strip()
    debug.trace_fmt(5, "L{line_num}: {line_text}", line_num=fileinput.filelineno(), line_text=line)

    # Extract word tokens and print those not recognized 
    word_tokens = [t.strip() for t in my_re.split(r"\W+", line.lower(), my_re.LOCALE|my_re.UNICODE)
                   if (len(t.strip()) > 0)]
    debug.trace(4, f"tokens: {word_tokens}")
    for w in word_tokens:
        if not speller.check(w):
            print(w)
