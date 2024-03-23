#! /usr/bin/env python
# 
# Desktop search support using large language models (LLMs).
#
# note:
# - Initially based on following sources:
#   https://swharden.com/blog/2023-07-29-ai-chat-locally-with-python
#   https://github.com/alejandro-ao/ask-multiple-pdfs
#

"""
Desktop search utility

Sample usage:
    {script} --index ..

    {script} --similar "license"
"""

# Standard modules
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
from mezcla import gpu_utils
from mezcla.main import Main
from mezcla import system
from mezcla import html_utils
from mezcla import extract_document_text
from mezcla.my_regex import my_re

# Constants
TL = debug.TL
INDEX_ARG = "index"
SEARCH_ARG = "search"
SIMILAR_ARG = "similar"
TORCH_DEVICE = gpu_utils.TORCH_DEVICE
#
QA_TEMPLATE = """Use the following pieces of information to answer the user's question.
If you don't know the answer, just say that you don't know, don't try to make up an answer.
Context: {context}
Question: {question}
Only return the helpful answer below and nothing else.
Helpful answer:
"""

# Environment options
NUM_SIMILAR = system.getenv_int(
    "NUM_SIMILAR", 10,
    description="Number of similar documents to show")
LLAMA_MODEL = system.getenv_text ("LLAMA_MODEL", '/home/tomohara/Downloads/llama-2-7b-chat.ggmlv3.q8_0.bin',
                                  description="path to llama model bin")

class DesktopSearch:
    """Class for searching local computer"""

    def __init__(self):
        """Initializer"""
        debug.trace_fmtd(TL.VERBOSE, "Helper.__init__(): self={s}", s=self)
        self.embeddings = None
        self.db = None
        self.llm = None
        self.qa_llm = None
        debug.trace_object(5, self, label=f"{self.__class__.__name__} instance")

    def index_dir(self, dir_path):
        """Index files at DIR_PATH"""
        debug.trace(4, f"DesktopSearch.index_dir({dir_path})")
        # define what documents to load
        
        def convert_to_txt(in_file: str) -> str:
            if file.endswith('.html'):
                text = html_utils.html_to_text(system.read_file(in_file))
            else:
                text = extract_document_text.document_to_text(in_file)
            return text
        
        #convert pdf, docs or html files into txt 
        old_files = system.read_directory(dir_path)
        non_txt_files = (found for found in old_files if my_re.match(r'.*\.(pdf|docx|html)', found) )
        for num,file in enumerate(non_txt_files):
            debug.trace_fmt(4,file)
            full_path = system.form_path(dir_path, file)
            system.write_file(f"{full_path}_temp_{num}.txt", convert_to_txt(full_path))
        
        loader = DirectoryLoader(dir_path, glob="*.txt", loader_cls=TextLoader)
        # interpret information in the documents
        documents = loader.load()
        splitter = RecursiveCharacterTextSplitter(chunk_size=500,
                                                  chunk_overlap=50)
        texts = splitter.split_documents(documents)
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': TORCH_DEVICE})

        # create and save the local database
        self.db = FAISS.from_documents(texts, self.embeddings)
        self.db.save_local("faiss")
        debug.trace_expr(4, self.db)
        gpu_utils.trace_gpu_usage()
        
        # delete converted files
        for new_file in (file for file in system.read_directory(dir_path) if file not in old_files):
            gh.delete_file(system.form_path(dir_path, new_file))

    def load_index(self, for_qa=False):
        """Load index of documents"""
        debug.trace(4, "DesktopSearch.load_index()")
        # load the language model
        ## OLD: config = {'max_new_tokens': 256, 'temperature': 0.01}
        config = {'max_new_tokens': 256, 'temperature': 0.01, 'context_length': 512}
        llm = CTransformers(model=LLAMA_MODEL,
                            model_type='llama', config=config)
        if for_qa:
            self.llm = llm

        # load the interpreted information from the local database
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': TORCH_DEVICE})
        self.db = FAISS.load_local("faiss", embeddings,
                                   # necessary to allow loading of possibly unsafe Pickle
                                   allow_dangerous_deserialization=True)
        gpu_utils.trace_gpu_usage()

    def prepare_qa_llm(self):
        """Prepare a version of the llm pre-loaded with the local content"""
        debug.trace(4, "prepare_qa_llm()")
        if not self.db:
            self.load_index(for_qa=True)        
        retriever = self.db.as_retriever(search_kwargs={'k': NUM_SIMILAR})
        prompt = PromptTemplate(
            template=QA_TEMPLATE,
            input_variables=['context', 'question'])

        self.qa_llm = RetrievalQA.from_chain_type(
            llm=self.llm, chain_type='stuff', retriever=retriever,
            return_source_documents=True, chain_type_kwargs={'prompt': prompt})
        gpu_utils.trace_gpu_usage()
        
    def search_to_answer(self, question):         # TODO2: rename like answer_question
        """Search documents to answer QUESTION"""
        debug.trace(4, f"DesktopSearch.search_to_answer({question})")
        if not self.qa_llm:
            self.prepare_qa_llm()
        model_path = self.qa_llm.combine_documents_chain.llm_chain.llm.model
        model_name = pathlib.Path(model_path).name
        time_start = time.time()
        output = self.qa_llm({'query': question})
        response = output["result"]
        time_elapsed = time.time() - time_start
        print(f'<code>{model_name} response time: {time_elapsed:.02f} sec</code>')
        print(f'<strong>Question:</strong> {question}')
        print(f'<strong>Answer:</strong> {response}')
        gpu_utils.trace_gpu_usage()

    def show_similar(self, query, num=None):
        """Show similar documents to QUERY in the vector store, up to NUM"""
        debug.trace(4, f"DesktopSearch.show_similar(query={query}, n={num})")
        if num is None:
            num = NUM_SIMILAR
        if not self.db:
            self.load_index()
        docs = self.db.similarity_search_with_score(query=query, k=num)
        print(docs)
        gpu_utils.trace_gpu_usage()

class Script(Main):
    """Adhoc script class (e.g., no I/O loop, just run calls)"""
    ## TODO: class-level member variables for arguments (avoids need for class constructor)
    index_arg = False
    search_arg = False
    similar_arg = False
    text = None

    def setup(self):
        """Check results of command line processing"""
        debug.trace_fmtd(TL.VERBOSE, "Script.setup(): self={s}", s=self)
        self.index_arg = self.get_parsed_option(INDEX_ARG, self.index_arg)
        self.search_arg = self.get_parsed_option(SEARCH_ARG, self.search_arg)
        self.similar_arg = self.get_parsed_option(SIMILAR_ARG, self.similar_arg)
        self.text = self.filename
        debug.trace_object(5, self, label=f"{self.__class__.__name__} instance")

    def run_main_step(self):
        """Main processing step (n.b., assumes self.manual_input)"""
        debug.trace_fmtd(5, "Script.run_main_step(): self={s}", s=self)
        ds = DesktopSearch()
        if self.index_arg:
            ds.index_dir(self.filename)
        elif self.search_arg:
            ds.search_to_answer(self.search_arg)
        elif self.similar_arg:
            ds.show_similar(self.similar_arg)
        else:
            system.print_error("Error: Unexpected condition")


def main():
    """Entry point"""
    app = Script(
        description=__doc__.format(script=gh.basename(__file__)),
        skip_input=False, manual_input=True,
        boolean_options=[(INDEX_ARG, "Index directory")],
        text_options=[(SEARCH_ARG, "Search documents to answer question"),
                      (SIMILAR_ARG, "Show similar documents")],
        float_options=None)
    app.run()

#-------------------------------------------------------------------------------
    
if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    debug.trace(5, f"module __doc__: {__doc__}")
    debug.assertion("TODO:" not in __doc__)
    main()
