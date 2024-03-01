#! /usr/bin/env python
# 
# Desktop search support using large language models (LLMs).
#
# note:
# - Initially based on following articles:
#   https://swharden.com/blog/2023-07-29-ai-chat-locally-with-python
#   https://github.com/alejandro-ao/ask-multiple-pdfs
#

"""
Desktop search utility

Sample usage:
   echo $'TODO:task1\\nDONE:task2' | {script} --TODO-arg --
"""

# Standard modules
import json
import time
import pathlib

# Installed modules
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import CTransformers
from langchain_community.vectorstores import FAISS

# Local modules
# TODO: def mezcla_import(name): ... components = eval(name).split(); ... import nameN-1.nameN as nameN
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla.main import Main
from mezcla.my_regex import my_re
from mezcla import system
## TODO:
## from mezcla import data_utils as du
##
## Optional:
## # Increase trace level for regex searching, etc. (e.g., from 6 to 7)
## my_re.TRACE_LEVEL = debug.QUITE_VERBOSE
debug.trace(5, f"global __doc__: {__doc__}")
debug.assertion(__doc__)

## TODO: Constants for switches omitting leading dashes (e.g., DEBUG_MODE = "debug-mode")
## Note: Run following in Emacs to interactively replace TODO_ARG with option label
##    M-: (query-replace-regexp "todo\\([-_]\\)arg" "arg\\1name")
## where M-: is the emacs keystroke short-cut for eval-expression.
INDEX_ARG = "index"
SEARCH_ARG = "search"
## TEXT_ARG = "text-arg"
## ALT_FILENAME = "alt_filename"

# Constants
TL = debug.TL
QA_TEMPLATE = """Use the following pieces of information to answer the user's question.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
Context: {context}
Question: {question}
Only return the helpful answer below and nothing else.
Helpful answer:
"""

# Environment options
# Note: These are just intended for internal options, not for end users.
# It also allows for enabling options in one place rather than four
# (e.g., [Main member] initialization, run-time value, and argument spec., along
# with string constant definition).
# WARNING: To minimize environment comflicts with other programs make the names
# longer such as two or more tokens (e.g., "FUBAR" => "FUBAR_LEVEL").
#
TODO_FUBAR = system.getenv_bool("TODO_FUBAR", False,
                                description="TODO:Fouled Up Beyond All Recognition processing")
DEVICE = system.getenv_text(
    "TORCH_DEVICE", "cuda",
    description="Device for running torch"
)

class DesktopSearch:
    """Class for searching local computer"""

    def __init__(self):
        """Initializer"""
        debug.trace_fmtd(TL.VERBOSE, "Helper.__init__(): self={s}", s=self)
        self.embeddings = None
        self.db = None
        self.qa_llm = None
        debug.trace_object(5, self, label=f"{self.__class__.__name__} instance")

    def index_dir(self, dir_path):
        """Index files at DIR_PATH"""
        # define what documents to load
        loader = DirectoryLoader(dir_path, glob="*.txt", loader_cls=TextLoader)

        # interpret information in the documents
        documents = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=500,
                                                  chunk_overlap=50)
        texts = splitter.split_documents(documents)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': DEVICE})

        # create and save the local database
        self.db = FAISS.from_documents(texts, self.embeddings)
        self.db.save_local("faiss")
        debug.trace_expr(4, self.db)
    

    def load_index(self):
        """Load index of documents"""
        # load the language model
        ## OLD: config = {'max_new_tokens': 256, 'temperature': 0.01}
        config = {'max_new_tokens': 256, 'temperature': 0.01, 'context_length': 512}
        llm = CTransformers(model='/home/tomohara/Downloads/llama-2-7b-chat.ggmlv3.q8_0.bin',
                            model_type='llama', config=config)

        # load the interpreted information from the local database
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': DEVICE})
        db = FAISS.load_local("faiss", embeddings)

        # prepare a version of the llm pre-loaded with the local content
        retriever = db.as_retriever(search_kwargs={'k': 2})
        prompt = PromptTemplate(
            template=QA_TEMPLATE,
            input_variables=['context', 'question'])

        self.qa_llm = RetrievalQA.from_chain_type(
            llm=llm, chain_type='stuff', retriever=retriever,
            return_source_documents=True, chain_type_kwargs={'prompt': prompt})
        
    def search(self, question):
        """Search documents to answer QUESTION"""
        if not self.qa_llm:
            self.load_index()
        model_path = self.qa_llm.combine_documents_chain.llm_chain.llm.model
        model_name = pathlib.Path(model_path).name
        time_start = time.time()
        output = self.qa_llm({'query': question})
        response = output["result"]
        time_elapsed = time.time() - time_start
        print(f'<code>{model_name} response time: {time_elapsed:.02f} sec</code>')
        print(f'<strong>Question:</strong> {question}')
        print(f'<strong>Answer:</strong> {response}')


class Script(Main):
    """Adhoc script class (e.g., no I/O loop, just run calls)"""
    ## TODO: class-level member variables for arguments (avoids need for class constructor)
    index_arg = False
    search_arg = False

    def setup(self):
        """Check results of command line processing"""
        debug.trace_fmtd(TL.VERBOSE, "Script.setup(): self={s}", s=self)
        ## TODO: extract argument values
        self.index_arg = self.get_parsed_option(INDEX_ARG, self.index_arg)
        self.search_arg = self.get_parsed_option(SEARCH_ARG, self.search_arg)
        ## TODO:
        ## self.text_arg = self.get_parsed_option(TEXT_ARG, self.text_arg)
        ## self.alt_filename = self.get_parsed_argument(ALT_FILENAME)
        debug.trace_object(5, self, label=f"{self.__class__.__name__} instance")

    def run_main_step(self):
        """Main processing step (n.b., assumes self.manual_input)"""
        debug.trace_fmtd(5, "Script.run_main_step(): self={s}", s=self)
        ds = DesktopSearch()
        if self.index_arg:
            ds.index_dir(self.filename)
        else:
            ds.search(self.filename)


def main():
    """Entry point"""
    app = Script(
        description=__doc__.format(script=gh.basename(__file__)),
        # Note: skip_input controls the line-by-line processing, which is inefficient but simple to
        # understand; in contrast, manual_input controls iterator-based input (the opposite of both).
        skip_input=False,
        manual_input=True,
        ## TODO (specify auto_help such as when manual_input set):
        ## # Note: shows brief usage if no arguments given
        ## auto_help=True,
        ## -or-: # Disable inference of --help argument
        ## auto_help=False,
        ## TODO: specify options and (required) arguments
        boolean_options=[(INDEX_ARG, "Index directory"),
                         (SEARCH_ARG, "Search documents")],
        ## TODO
        ## Note: FILENAME is default argument unless skip_input
        ## positional_arguments=[ALT_FILENAME], 
        ## text_options=[(TEXT_ARG, "TODO-desc")],
        ## Note: Following added for indentation float options not common (TODO: remove?)
        float_options=None)
    app.run()
    # Make sure no TODO_vars above (i.e., in namespace)
    debug.assertion(not any(my_re.search(r"^TODO_", m, my_re.IGNORECASE)
                            for m in dir(app)))    
    
#-------------------------------------------------------------------------------
    
if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    debug.trace(5, f"module __doc__: {__doc__}")
    debug.assertion("TODO:" not in __doc__)
    main()
