#! /usr/bin/env python
#
# Customization of PyLucene SearchFiles.py for searching index of tabular file:
#    http://svn.apache.org/viewvc/lucene/pylucene/trunk/samples/SearchFiles.py
# This also includes an option to do similar searching via pysolr.
#
# Notes:
# - Searches the field 'contents' by default (as indexed by index_table_file.py).
# - The text returned by PyLucene routines can be in Unicode, so it should be converted
#   into UTF-8 under Python 2.x (see comments in show_unicode_info.py for details).
# - The Solr implementation is not as comprehensive as the Lucene support (e.g., term vectors not yet supported).
#
# Warning:
# - This is basically the same version from the misc-scripts repo,
#   so the style is archaic compared to other mezcla scripts.
# - This is mainly included for sake of completeness, because
#   analyze_tfidf.py got added to the repo inadvertantly.
# - It is also used in the test_format_profile.py as unlikely to change.
#
# TODO:
# - *** Add support for searching ngram tokens ***
# - Have option to use relative term frequency: tf(t, d) = f(t, d) / max(f(t', d) for t' in d).
# - Add TF/IDF support to interactive queries (e.g., via run()).
# - Track down discrepancy in document numbers in TF/IDF listing vs. query search.
# - Convert getenv-based arguments to argparse.
# - * Add sanity check for PyLucene 4.4 *
# - Add optional smoothing for TF/IDF.
# - Use remote_dispatching.py to encapsulate more of the remote processing support.
#

"""
Usage: {script} [index_dir [query_word1 ...]]

This script is loosely based on the Lucene demo sample SearchFiles.java
(i.e., org.apache.lucene.demo.SearchFiles).  It prompts for a search query, 
then it searches the Lucene index in the current directory called 'index' for the
search query entered against the 'contents' field.  It then displays the
'name' and 'contents' fields for each of the hits it finds in the index.  Note that
search.close() is currently commented out because it causes a stack overflow in
some cases.

Examples:

$ {script}  table-file-index  programmer  cashier

$ echo $'truck driver\\nsales associate\\n' | PHRASAL=1 INDEX_DIR=table-file-index {script} -

Notes:
- Can search against a Solr server, using 'id' and 'content' fields.
- The processing can be customized via the following environment variables:
	{descriptions}
- Use - for the query to search all documents (or all terms for DOC_FREQ).
"""

import logging
import math
import os
import re
import sys

from mezcla import glue_helpers as gh
from mezcla import tpo_common as tpo
from mezcla.tpo_common import getenv_text, getenv_boolean, getenv_integer, debug_print, print_stderr
from mezcla import system

USE_SOLR = getenv_boolean("USE_SOLR", False, "Query Solr server instead of Lucene")
USE_LUCENE = getenv_boolean("USE_LUCENE", not USE_SOLR, "Query Solr server instead of Lucene")
if USE_SOLR:
    import pysolr
elif USE_LUCENE:
    import lucene
    from java.io import File
    from org.apache.lucene.analysis.standard import StandardAnalyzer

    from org.apache.lucene.index import DirectoryReader, MultiFields, Term, TermsEnum
    from org.apache.lucene.queryparser.classic import QueryParser
    from org.apache.lucene.store import SimpleFSDirectory
    from org.apache.lucene.search import IndexSearcher, Query
    from org.apache.lucene.util import Version
    from org.apache.lucene.util import BytesRefIterator
else:
    debug_print("Warning: requires either USE_SOLR and USE_LUCENE", 4)
    pass

#------------------------------------------------------------------------
# Globals

INDEX_DIR = getenv_text("INDEX_DIR", "table-file-index", "Directory where Lucene index resides")
# Note: Solr by defaul uses id & content whereas PyLucene demo used name & contents for ID and data fields
FIELD = getenv_text("FIELD", ("content" if USE_SOLR else "contents"), "Field name for searching")
NAME = getenv_text("NAME", ("id" if USE_SOLR else "name"), "Name/ID field for results")
JUST_HITS = getenv_boolean("JUST_HITS", False, "Just show document hit count")
MAX_HITS = int(getenv_text("MAX_HITS", 50, "Maximum number of hits to return"))
SHOW_FREQ = getenv_boolean("SHOW_FREQ", False, "Show document frequency for terms")
PHRASAL = getenv_boolean("PHRASAL", False, "Use phrasal search")
TOKEN_REGEX = getenv_text("TOKEN_REGEX", ("\n" if PHRASAL else r"\W+"), "Regex for tokenizing input")
VERBOSE = getenv_boolean("VERBOSE", False, "Verbose output mode")
COUNT_TERMS = getenv_boolean("COUNT_TERMS", False, "Count number of terms in entire index")
SHOW_TFIDF = getenv_boolean("SHOW_TFIDF", False, "Show TF/IDF-based differntiating terms")
SKIP_UNIGRAMS = getenv_boolean("SKIP_UNIGRAMS", False,
                               "Don't include unigrams in TF/IDF listing")
SKIP_PLACEHOLDERS = getenv_boolean("SKIP_PLACEHOLDERS", False,
                                   "Skip phrasal terms with placeholders (e.g., '_ california')")
MAX_TERMS = getenv_integer("MAX_TERMS", 10, "Maximum number of terms for TF/IDF")
USE_NAME_FOR_ID = getenv_boolean("USE_NAME_FOR_ID", False, "Use the name field in place of Lucene docid")
REVERSE_ORDER = getenv_boolean("REVERSE_ORDER", False, "Produce document listing in reverse")
RETAIN_DOC_ID = getenv_boolean("RETAIN_DOC_ID", False, "Use Lucene docid in output")
SOLR_URL = getenv_text("SOLR_URL", "http://localhost:8983/solr", "URL for Solr server to query")
USE_DISMAX = getenv_boolean("USE_DISMAX", False, "Use DISMAX with Solr")
CONJUNCTIVE = getenv_boolean("CONJUNCTIVE", False, "Use conjunctive query with Solr")
#
DISTRIBUTED = getenv_boolean("DISTRIBUTED", False, "Run distributed with input partitioned and entire index copied")
## REMOTE_WORKERS = getenv_text("REMOTE_WORKERS", "", "String list of workers for remote distribution")
START_DOC = getenv_integer("START_DOC", 0)
SLEEP_SECONDS = getenv_integer("SLEEP_SECONDS", 60)
MAX_SLEEP = getenv_integer("MAX_SLEEP", 86400)
SKIP_INDEX = getenv_boolean("SKIP_INDEX", False)
## TODO: NUM_DOCS = getenv_integer("NUM_DOCS", system.MAX_INT)
## TODO: END_DOC = getenv_integer("END_DOC", START_DOC + NUM_DOCS)
START_DOC = getenv_integer("START_DOC", system.MAX_INT)
# Debugging options
MAX_EMPTY = getenv_integer("MAX_EMPTY", 1000)
IGNORE_EXCEPTIONS = getenv_boolean("IGNORE_EXCEPTIONS", (tpo.debugging_level() >= tpo.LEVEL4))


#------------------------------------------------------------------------

class IndexLookup(object):
    """Class for performing queries against a Lucene index"""
    vm_obj = None

    def __init__(self, index_dir=INDEX_DIR, field=FIELD):
        debug_print("IndexLookup.__init__(%s, %s)" % (index_dir, field), 5)
        self.field = field
        self.frequencies = {}
        if USE_SOLR:
            self.init_solr()
        else:
            self.init_lucene(index_dir)
        return

    def init_solr(self):
        """Initialize Solr processing"""
        debug_print("IndexLookup.init_solr()", 5)
        #
        # Enable detailed Solr tracing if debugging
        if (tpo.verbose_debugging()):
            ## solr_logger = logging.getLogger('pysolr')
            ## solr_logger.setLevel(logging.DEBUG)
            # TODO: use mapping from symbolic LEVEL user option (e.g., via getenv)
            level = logging.INFO if (tpo.debug_level < 4) else logging.DEBUG
            logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=level)
        # format: Solr(url, [decoder=None], [timeout=60])
        # TODO: add option for timeout
        self.solr = pysolr.Solr(SOLR_URL)
        tpo.debug_print("solr=%s" % self.solr, 4)
        return

    def init_lucene(self, index_dir):
        """Initialize Lucene processing"""
        debug_print("IndexLookup.init_lucene(%s)" % index_dir, 5)
        if not IndexLookup.vm_obj:
            try:
                # Issue standard pylucene startup sequence
                # Note: headless is for vm's without graphical display
                IndexLookup.vm_obj = lucene.initVM(vmargs=['-Djava.awt.headless=true'])
                tpo.debug_format("vm_obj={vm}", 5, vm=IndexLookup.vm_obj)
            except:
                debug_print("Warning: Exception during IndexLookup __init__: %s" % str(sys.exc_info()), 4)
        debug_print('lucene version: %s' % lucene.VERSION, 3)
        directory = SimpleFSDirectory(File(index_dir))
        self.reader = DirectoryReader.open(directory)
        self.searcher = IndexSearcher(self.reader)
        self.analyzer = StandardAnalyzer(Version.LUCENE_CURRENT)
        return

    def run(self):
        """Interactive run queries specified on the console"""
        debug_print("IndexLookup.run()", 5)
        query_prompt = ("Query:" if VERBOSE else "")
        while True:
            if (VERBOSE):
                print("")
                print("Hit enter with no input to quit.")
            try:
                command = raw_input(query_prompt)
            except:
                break
            if command.strip() == '':
                break

            if SHOW_FREQ:
                gh.assertion(not USE_SOLR)
                tokens = [t for t in re.split(TOKEN_REGEX, command) if t]
                for term in tokens:
                    print("%s: %d" % (term, self.doc_freq(term)))
            elif JUST_HITS:
                print(self.get_hit_count(command))
            else:
                doc_names = self.issue_query(command)
                print("\n".join(doc_names))
        return

    def get_num_docs(self):
        """Returns number of documents in the Lucene index"""
        gh.assertion(not USE_SOLR)
        num_docs = 0
        try:
            num_docs = self.reader.numDocs()
        except:
            if (not IGNORE_EXCEPTIONS):
                tpo.debug_raise()
            debug_print("Warning: Exception during get_num_docs: %s" % str(sys.exc_info()), 4)
        debug_print("get_num_docs() => %d" % num_docs, 4)
        return (num_docs)

    def get_doc_terms_and_freqs(self, doc_id):
        """Return tuple with list of all indexed terms and list of their frequencies for DOC_ID"""
        gh.assertion(not USE_SOLR)
        if not isinstance(doc_id, int):
            doc_id = int(doc_id)
        terms = []
        tfs = []
        try:
            tv = self.reader.getTermVector(doc_id, self.field)
            if not tv:
                # Note: To distinguish between field with no entries and field w/o term vectors,
                # the document contents are retrieved. For this to work, the field must be stored
                # (e.g., via STORE_CONTENTS setting of index_table_file.py).
                # via http://lucene.apache.org/core/4_0_0/core/org/apache/lucene/document/Document.html
                #     Fields which are not stored are not available in documents retrieved from the index.
                # TODO: work out a way to detect this without storing the field
                doc = self.reader.document(doc_id)
                contents = doc.get(self.field) if doc else ""
                if contents:
                    print_stderr("Error: No term vectors for field %s (docid=%s)" % (self.field, doc_id))
                debug_print("doc=%s contents=%s" % (doc, contents), 8)
                debug_print("get_doc_terms_and_freqs(%s) => (%s, %s)" % (doc_id, terms, tfs), 7)
                return (terms, tfs)
            terms_enum = tv.iterator(None)
            terms = []
            tfs = []
            for utf8_term in BytesRefIterator.cast_(terms_enum):
                dp_enum = terms_enum.docsAndPositions(None, None)
                if not dp_enum:
                    debug_print("Warning: Problem enumerating document positions for term %s" % utf8_term, 3)
                    continue
                dp_enum.nextDoc()  # note: primes the enum which works only for the current doc
                freq = dp_enum.freq()
                debug_print("type(utf8_term)=%s" % type(utf8_term), 8)
                # note: term returned is Unicode, so codec.encode required before I/O [see print_stderr in tpo_common.py])
                term = utf8_term.utf8ToString()
                debug_print("type(term)=%s" % type(term), 8)
                debug_print("term: %s" % term, 8)
                if SKIP_PLACEHOLDERS and (term.startswith("_ ") or term.endswith(" _")):
                    debug_print("skipping term with placeholders: %s" % term, 7)
                    continue
                terms.append(term.encode('utf-8'))
                tfs.append(freq)
        except:
            if (not IGNORE_EXCEPTIONS):
                tpo.debug_raise()
            debug_print("Warning: Exception during get_doc_terms_and_freqs: %s" % str(sys.exc_info()), 4)
        debug_print("get_doc_terms_and_freqs(%s) => (%s, %s)" % (doc_id, terms, tfs), 7)
        return (terms, tfs)

    def get_all_terms(self):
        """A generator yielding of all terms in the index"""
        # via http://mail-archives.apache.org/mod_mbox/lucene-pylucene-dev/201402.mbox/%3CCAPJ5eE-WM78oZronESNAcurM3azp=ho2XHv-HS4aVr_S5V18Yg@mail.gmail.com%3E
        tpo.debug_format("in get_all_terms()", 6)
        fields = MultiFields.getFields(self.reader)
        terms = fields.terms(self.field)
        terms_enum = terms.iterator(None)
        terms_ref = BytesRefIterator.cast_(terms_enum)
        try:
            while (terms_ref.next()):
                term_value = TermsEnum.cast_(terms_ref)
                term_token = tpo.normalize_unicode(term_value.term().utf8ToString())
                tpo.debug_print("term: %s" % term_token, 7)
                yield term_token
        except StopIteration:
            pass
        except:
            print_stderr("Exception in get_all_terms: %s" % str(sys.exc_info()))
        tpo.debug_format("out get_all_terms()", 6)
        return

    def count_terms(self):
        """Returns total count of terms in index"""
        tpo.debug_format("count_terms()", 6)
        fields = MultiFields.getFields(self.reader)
        terms = fields.terms(self.field)
        terms_enum = terms.iterator(None)
        terms_ref = BytesRefIterator.cast_(terms_enum)
        num_terms = 1
        try:
            while (terms_ref.next()):
                num_terms += 1
        except StopIteration:
            pass
        except:
            print_stderr("Exception in count_terms: %s" % str(sys.exc_info()))
        tpo.debug_format("count_terms() => {num_terms}", 6)
        return (num_terms)

    def get_doc_terms(self, doc_id):
        """Return list of all indexed terms for DOC_ID"""
        # TODO: rework so that term vectors not required
        # TODO: customize for returning number of terms in the document
        gh.assertion(not USE_SOLR)
        (terms, _tfs) = self.get_doc_terms_and_freqs(doc_id)
        debug_print("get_doc_terms(%s) => %s" % (doc_id, terms), 6)
        return (terms)

    def get_docid(self, doc_id):
        """Get document label for DOC_ID to use for output listings (e.g., based on NAME field)"""
        # TODO: rename to get_doc_label once anlyze_tfidf.py updated
        gh.assertion(not USE_SOLR)
        doc_label = doc_id
        if USE_NAME_FOR_ID:
            if not isinstance(doc_id, int):
                doc_id = int(doc_id)
            doc_label = self.searcher.doc(doc_id).get(NAME)
        debug_print("get_docid(%s) => %s" % (doc_id, doc_label), 6)
        return (doc_label)

    def get_tfidf(self, doc_id):
        """Return list of top terms for DOC_ID ranked by TFIDF"""
        # Get list of terms and corresponding frequency for current document
        # note: term vector access based on ./samples/TermPositionVector.py in PyLucene source
        gh.assertion(not USE_SOLR)
        tfidf_info = []
        num_docs = self.get_num_docs()
        try:
            (terms, tfs) = self.get_doc_terms_and_freqs(doc_id)
            if SKIP_UNIGRAMS:
                ## TODO: (terms, tfs) = unzip([(t, f) for (t, f) in zip(terms, tfs) if not " " in t])
                terms_tfs = [(t, f) for (t, f) in zip(terms, tfs) if " " in t]
                terms = [t for (t, _f) in terms_tfs]
                tfs = [f for (_t, f) in terms_tfs]
            num_terms = len(terms)

            # Get (global) document frequency for term and compute TF/IDF
            # TODO: -log(1/dfs[i]) => log(N/dfs[i])
            indices = [i for i in range(len(terms))]
            dfs = [self.doc_freq(terms[i]) for i in indices]
            tfidfs = [tfs[i] * (math.log(num_docs / float(dfs[i])) if (dfs[i] > 0) else 0.0) for i in indices]
            tpo.trace_array(sorted(zip(terms, tfs, dfs, tfidfs), reverse=True, key=lambda t: t[-1]),
                            6, "term info")
            tpo.debug_format("#terms={num_terms}", 4)

            # Sort and get top-N items
            # TODO: filter phrasals subsumed by larger phrases
            sorted_indices = sorted(indices, reverse=True, key=lambda i: tfidfs[i])
            tfidf_info = ["%s:%s" % (terms[i], tpo.round_num(tfidfs[i])) for i in sorted_indices[:MAX_TERMS]]
        except Exception:
            if (not IGNORE_EXCEPTIONS):
                tpo.debug_raise()
            tpo.print_stderr("Warning: Exception during get_tfidf for doc %s: %s" % (doc_id, str(sys.exc_info())))
        if (len(tfidf_info) == 0):
            debug_print("Warning: No terms extracted for document %s" % doc_id)
        return (tfidf_info)

    def perform_query(self, query_text, field=None):
        """Helper function to performs all-words query using specified QUERY_TEXT (in FIELD), returing tuples with (estimated) number of hits and top documents"""
        # TODO: exclude or escape words that are lucene keywords (e.g., "NOT")
        # TODO: escape special characters: \ + - ! ( ) : ^ ] { } ~ * ?
        debug_print("perform_query(%s, [field=%s])" % (query_text, field), 6)
        query_field = field if field else self.field
        num_hits = 0
        try:
            query_text = query_text.strip()
            if PHRASAL and (" " in query_text) and (query_text[0] != '"'):
                query_text = '"' + query_text + '"'
            if USE_SOLR:
                # format: search(q, [kwargs=None])
                ## TODO: scoreDocs = self.solr.search(query_text, **{'df': query_field})
                ## BAD: solr_results = self.solr.search(query_text, **{'df': query_field, 'fl': 'id'})
                params = {
                    # note: df is for default fault, and fl is for (display) field list (thanks, SolR!)
                    ## TODO: specify query override
                    # 'df': query_field, 
                    ## OLD: 'fl': 'id,score',
                    'fl': NAME + ',score',
                    }
                if USE_DISMAX:
                    params['defType'] = "edismax"
                if CONJUNCTIVE:
                    # Use conjuntive query (disjunction is default)
                    params['q.op'] = 'AND'
                tpo.debug_format("params={p}", 5, p=params)
                solr_results = self.solr.search(query_text, **params)
                
                tpo.trace_object(solr_results, 5, "solr_results")
                # note: Solr only returns first 10 hits by default
                scoreDocs = [result['id'] for result in solr_results]
                # TODO: see if way to get total Solr hits
                num_hits = len(scoreDocs)
            else:
                # Treat query as conjunction unless phrasal
                if CONJUNCTIVE and not PHRASAL:
                    query_tokens = re.split(r"\W+", query_text)
                    query_text = " ".join([("+" + t) for t in query_tokens])
                query = QueryParser(Version.LUCENE_CURRENT, query_field,
                                    self.analyzer).parse(query_text)
                tpo.debug_format("Lucene query={query}; query_text='{query_text}'; field={query_field}", 6)
                top_docs = self.searcher.search(query, MAX_HITS)
                num_hits = top_docs.totalHits
                scoreDocs = top_docs.scoreDocs
                
            debug_print("%s returned documents for query '%s'" % (len(scoreDocs), query_text), 5)
            debug_print("%s total matching documents (estimated)" % (num_hits), 5)
            debug_print("scoreDocs=%s" % scoreDocs, 7)
            if RETAIN_DOC_ID:
                doc_names = [str(doc.doc) for doc in scoreDocs]
            else:
                if USE_SOLR:
                    doc_names = scoreDocs
                else:
                    # TODO: convert documents names to UTF-8 (e.g., to get rid of u'...' in output)
                    doc_names = [self.searcher.doc(doc.doc).get(NAME) or "" for doc in scoreDocs]
            if SHOW_TFIDF:
                gh.assertion(not USE_SOLR)
                for doc in scoreDocs:
                    # Display top cases
                    # TODO: use JSON-style format (to facilitate extraction); likewise below
                    debug_print("docid=%s tfidf=%s" % (self.get_docid(doc.doc), self.get_tfidf(doc.doc)), 6)
        except Exception:
            if (not IGNORE_EXCEPTIONS):
                tpo.debug_raise()
            tpo.print_stderr("Warning: Exception during perform_query of %s: %s" % (query_text, str(sys.exc_info())))
            doc_names = []
        result = (num_hits, doc_names)
        debug_print("perform_query(%s) => %s" % (query_text, result), 6)
        return result

    def issue_query(self, query_text, field=None):
        """Performs all-words query using specified TEXT (in FIELD)"""
        (_num_hits, docs) = self.perform_query(query_text, field)
        debug_print("issue_query(%s) => %s" % (query_text, docs), 5)
        return docs

    def get_hit_count(self, query_text, field=None):
        """Returns (estimated) number of documents matching QUERY_TEXT"""
        (num_hits, _docs) = self.perform_query(query_text, field)
        debug_print("get_hit_count(%s) => %s" % (query_text, num_hits), 5)
        return num_hits

    def doc_freq(self, term, cache=True):
        """Returns number of documents that TERM occurs in"""
        # TODO: rename as term_doc_freq???
        debug_print("doc_freq(%s)" % term, 8)
        gh.assertion(not USE_SOLR)
        if cache and term in self.frequencies:
            return (self.frequencies[term])
        try:
            term_object = Term(FIELD, term.strip())
            ## BAD (misleading documentation at http://lucene.apache.org/core/4_0_0/core/org/apache/lucene/index/IndexReader.html)
            ##    num_docs = self.reader.totalTermFreq(term_object)
            num_docs = self.reader.docFreq(term_object)
        except Exception:
            if (not IGNORE_EXCEPTIONS):
                tpo.debug_raise()
            tpo.print_stderr("Warning: Exception during doc_freq of %s: %s" % (term, str(sys.exc_info())))
            num_docs = 0
        if cache:
            self.frequencies[term] = num_docs
        debug_print("doc_freq(%s) => %d" % (term, num_docs), 7)
        return num_docs

#------------------------------------------------------------------------
# Support for distributed processing
# note: this has now been been moostly integrated into remote_dispatching.py

def invoke_distributed(command_line, index_dir, total_num_docs):
    """Divide the task among client workers and then gather results"""
    # TODO: put generic processing in remote_dispatching.py
    # Note: To avoid having to parse the command line, all arguments are given via environment
    # and passed along.
    # TODO: import remote_dispatching above so that environment options made available for --help option
    import remote_dispatching as rd
    import time
    remote_workers = rd.REMOTE_WORKERS.split()
    num_workers = len(remote_workers)
    assert(num_workers > 0)
    dispatcher = rd.RemoteDispatcher()
    # Send index to clients and extract under /tmp
    if not SKIP_INDEX:
        dispatcher.copy_dir_to_workers(index_dir)
    # Reconstruct command line, including environment options with index directory override,
    # and send to clients.
    # TODO: start=i*INCR num=INCR
    environment_spec = dispatcher.get_bash_environment_options(ignore="DISTRIBUTED")
    index_basename = gh.basename(index_dir)
    num_docs = total_num_docs / len(remote_workers)
    command_base = "run_search_table_file_index"
    command_script = tpo.format("/tmp/{command_base}.sh")

    # Invoke commands
    # TODO: use run-specific filenames (e.g., /tmp/remote_search_table_file_index-<PID>.sh)
    this_module = gh.basename(__file__, ".py")

    remote_flag_file = tpo.format("/tmp/{command_base}.done")
    invocation_base = "invoke_remote_search_table_file_index"
    invocation_output_template = "/tmp/{invocation_base}.h{i}.output"
    for i in range(num_workers):
        invocation_script = tpo.format("/tmp/{invocation_base}.sh")
        invocation_output_file = tpo.format(invocation_output_template)
        start_doc = i * num_docs
        end_doc = start_doc + num_docs - 1
        gh.write_lines(command_script, [
            tpo.format("rm -f {remote_flag_file}"),
            # note: /tmp/tohara-1.1 created as part of setup
            tpo.format("{environment_spec} DEBUG_LEVEL=4 PYTHONPATH=/tmp/tohara-1.1 INDEX_DIR=/tmp/{index_basename} START_DOC={start_doc} END_DOC={end_doc} python -m {this_module} - >| {invocation_output_file}  2> {invocation_output_file}.log"),
            tpo.format("touch {remote_flag_file}"),
            ])
        gh.write_lines(invocation_script, [
            tpo.format("source {command_script} &")
            ])
        dispatcher.copy_file_to_worker(i, command_script)
        dispatcher.copy_file_to_worker(i, invocation_script)
        dispatcher.run_command_on_worker(i, tpo.format("source {invocation_script}"))

    # Wait for each host to finish, and then output corresponding result file
    # TODO: record process ID and make sure still running remotely
    num_left = num_workers
    still_running = [True] * num_workers
    time_slept = 0
    while (num_left > 0):
        if (time_slept >= MAX_SLEEP):
            tpo.print_stderr(tpo.format("Error: time out reached ({MAX_SLEEP} seconds) in invoke_distributed"))
            break
        time.sleep(SLEEP_SECONDS)
        time_slept += SLEEP_SECONDS

        # Check each active host for completion, downloading results when reached.
        for i in range(num_workers):
            if still_running[i]:
                flag_found = dispatcher.run_command_on_worker(i, tpo.format("ls {remote_flag_file} 2> /dev/null"))
                if flag_found:
                    still_running[i] = False
                    num_left -= 1
                    remote_output_file = tpo.format(invocation_output_template)
                    dispatcher.copy_file_from_worker(i, remote_output_file)
                    local_output_file = gh.basename(remote_output_file)
                    tpo.debug_format("Output from host {i}: {local_output_file}", 4)
                    print(gh.read_file(local_output_file))
    return

#-------------------------------------------------------------------------------

def  main():
    """Entry point for script"""
    # Check command-line arguments
    # TODO: rework via argparse (e.g., removing nonstandard '-' for index-dir)
    debug_print("sys.argv: %s" % sys.argv, 5)
    if ((len(sys.argv) <= 1) or (sys.argv[1] == "--help")):
        print(__doc__.format(script=sys.argv[0], descriptions=tpo.formatted_environment_option_descriptions()))
        sys.exit()
    index_dir = INDEX_DIR
    if (sys.argv[1] != "-"):
        index_dir = sys.argv[1]

    # Initialize the index lookup
    il = IndexLookup(index_dir)
    tpo.trace_object(il, 7)
    
    # For distributed processing, act as dispatcher and then exit
    if DISTRIBUTED:
        invoke_distributed(sys.argv, index_dir, il.get_num_docs())
        sys.exit()

    # If additional arguments, issue query from remainder of command line
    # Note: if all numeric, treated as document ID's
    # TODO: unify the tfidf listing formatting
    if (len(sys.argv) > 2):
        remainder = sys.argv[2:]
        if SHOW_FREQ:
            gh.assertion(not USE_SOLR)
            if remainder == ["-"]:
                remainder = il.get_all_terms()
            print("term\tfreq")
            for term in remainder:
                print("%s\t%d" % (term, il.doc_freq(term, cache=False)))
        elif (SHOW_TFIDF and all(tpo.is_numeric(arg) for arg in remainder)):
            gh.assertion(not USE_SOLR)
            for doc_id in remainder:
                print("docid=%s tfidf=%s" % (il.get_docid(doc_id), il.get_tfidf(doc_id)))
        else:
            query_text = " ".join(remainder)
            if JUST_HITS:
                result = il.get_hit_count(query_text)
            else:
                doc_names = il.issue_query(query_text)
                result = "\n".join(doc_names)
            if SHOW_TFIDF:
                gh.assertion(not USE_SOLR)
                for doc_id in doc_names:
                    print("docid=%s tfidf=%s" % (il.get_docid(doc_id), il.get_tfidf(doc_id)))
            else:
                print(result)

    # Handle processing when no arguments given
    else:
        # Special case to produce TF/IDF listings for all documents
        if COUNT_TERMS:
            print("Number of terms: %s" % il.count_terms())
        elif SHOW_TFIDF:
            gh.assertion(not USE_SOLR)
            # TODO: rework via PyLucene enumerate-documents API
            num_missing = 0
            all_docs = range(0, il.get_num_docs())
            if REVERSE_ORDER:
                all_docs = sorted(all_docs, reverse=True)
            for doc in all_docs:
                # Get the next TF/IDF listing and do some sanity checks
                tfidfs = il.get_tfidf(doc)
                if tfidfs is None:
                    break
                if (len(tfidfs) == 0):
                    num_missing += 1
                    if (num_missing == MAX_EMPTY):
                        debug_print("Warning: stopping due to %d empty tf/idf listings" % MAX_EMPTY)
                        break

                # Print the info and advance document
                print("docid=%s tfidf=%s" % (il.get_docid(doc), tfidfs))
                doc += 1

        # Otherwise, run interactively
        else:
            il.run()
    return
            
#------------------------------------------------------------------------

if __name__ == '__main__':
    main()
