#! /usr/bin/env python3
# 
# Desktop search support using large language models (LLMs).
#
# note:
# - Initially based on following sources:
#   https://swharden.com/blog/2023-07-29-ai-chat-locally-with-python
#   https://github.com/alejandro-ao/ask-multiple-pdfs
#
# TODO2:
# - Make sure the tests are more reliabile (e.g., perhaps issue due to caching).
# - Clarify the specific Python requirements (language and modules)
#
# TODO3:
# - Document the workflow better.
# - Note that --index arg changed from binary to text with index dir.
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
import atexit
from collections.abc import Iterable

# Installed modules
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
from langchain_core.documents import Document
from langchain_community.document_loaders import DirectoryLoader, TextLoader
## OLD: from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.llms import CTransformers
from langchain_community.vectorstores import FAISS

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import gpu_utils
from mezcla.main import Main, KEEP_TEMP_FILES
from mezcla import system
from mezcla import html_utils
from mezcla import extract_document_text
from mezcla.my_regex import my_re

# Constants
TL = debug.TL
INDEX_ARG = "index"
SEARCH_ARG = "search"
SIMILAR_ARG = "similar"
TORCH_DEVICE = system.getenv_text(
    "TORCH_DEVICE", gpu_utils.TORCH_DEVICE,
    desc="Torch devcice to use--cuda or mps if available else cpu")
debug.trace_expr(5, TORCH_DEVICE)
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
HOME_DIR = gh.HOME_DIR
EMBEDDING_MODEL = system.getenv_text(
    "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2",
    description="Model for sentence transformer embeddings")
# note: changed default to currrent dir rather than home
QA_LLM_DEFAULT = "llama-2-7b-chat.ggmlv3.q8_0.bin"
QA_LLM_MODEL = system.getenv_text(
    "QA_LLM_MODEL", QA_LLM_DEFAULT,
    description="Path to LLM model file for Q&A, such as a llama-2-7b .bin file")
QA_LLM_TYPE = system.getenv_text(
    "QA_LLM_TYPE", "llama",
    description="Type of transformer model for Q&A, such as llama or gpt2")
ALLOW_UNSAFE_MODELS_DEFAULT = True
ALLOW_UNSAFE_MODELS = system.getenv_value(
    "ALLOW_UNSAFE_MODELS", ALLOW_UNSAFE_MODELS_DEFAULT,
    description="Whether to allow loading of possibly unsafe Pickle models")
CHUNK_SIZE = system.getenv_int(
    "CHUNK_SIZE", 500,
    description="Number of characters for text splitter chunking")
CHUNK_OVERLAP = system.getenv_int(
    "CHUNK_OVERLAP", 50,
    description="Size of overlap in characters for text splitter chunking")
MAX_NEW_TOKENS = system.getenv_int(
    "MAX_NEW_TOKENS", 256,
    description="Max number of generated tokens for Q&A LLM")
TEMPERATURE = system.getenv_int(
    "TEMPERATURE", 0.01,
    description="Degree of randomness or creativity of generated text")
CONTEXT_LENGTH = system.getenv_int(
    "CONTEXT_LENGTH", 512,
    description="Context window size in tokens")
GPU_LAYERS = system.getenv_int(
    "GPU_LAYERS", (0 if (TORCH_DEVICE == "cpu") else -1),
    description="Number of layers to use for CTransfomers model")
INDEX_STORE_DIR = system.getenv_text(
    # note: changed default to current directory to avoid script dir being reused
    "INDEX_STORE_DIR", "faiss",
    description="path to store index data base")
INDEX_ONLY_RECENT = system.getenv_bool(
    "INDEX_ONLY_RECENT", True,
    description="whether or not to filter files by modification time newer than index")


def get_file_mod_fime(path: str) -> float:
    """Returns file modification time in fractional seconds
    Note: -1 is returned if the file doesn't exist
    """
    # EX: (get_file_mod_fime("/etc/passwd") > get_file_mod_fime("/boot/vmlinuz"))
    # EX: get_file_mod_fime(" /etc /password") => -1
    result = (system.get_file_modification_time(path, as_float=True) or -1)
    debug.trace(7, f"get_file_mod_fime({path}) => {result}")
    return result


def get_last_modified_date(iterable: Iterable) -> float:
    """return the newest modification date as a float, 
       or -1 if iterable is empty or files don't exist"""
    result = -1
    if iterable:
        result = max(map(get_file_mod_fime, iterable))
    return result

def correct_metadata(doc: Document, base_dir: str) -> Document:
    """removes BASE_DIR from the source metadata path
       so it represents the actual source of the file"""
    # TODO3: fix docstrings with respect to hardcoded assumptions
    debug.trace_expr(4, base_dir)
    doc_metadata = doc.metadata
    old_source = doc_metadata['source']
    debug.trace_expr(4, old_source)
    new_source = old_source.replace(base_dir, "")
    debug.assertion(new_source != old_source)
    debug.trace_expr(4, new_source)
    doc_metadata['source'] = new_source
    doc.metadata = doc_metadata
    debug.trace(5, f"correct_metadata({doc!r}, {base_dir!r}) => {doc!r}")
    return doc

def convert_to_txt(in_file: str) -> str:
    """reads non-txt files and returns the text inside them"""
    text = ""
    try:
        if in_file.endswith('.html'):
            text = html_utils.html_to_text(system.read_file(in_file))
        else:
            text = extract_document_text.document_to_text(in_file)
    except:
        debug.trace_exception(6, "convert_to_txt")
    debug.trace(7, f"convert_to_txt({in_file}) => {text!r}")
    return text


class DesktopSearch:
    """Class for searching local computer"""

    def __init__(self, index_store_dir=None):
        """Initializer; index placed in INDEX_STORE_DIR"""
        debug.trace_fmtd(TL.VERBOSE, "Helper.__init__(): self={s}", s=self)
        if index_store_dir is None:
            index_store_dir = INDEX_STORE_DIR
        self.index_store_dir = index_store_dir
        self.embeddings = None
        self.db = None
        self.llm = None
        self.qa_llm = None
        debug.trace_object(5, self, label=f"{self.__class__.__name__} instance")

    def index_dir(self, dir_path):
        """Index files at DIR_PATH"""
        ## TODO4: look into indexing files from buffers rather than external files
        debug.trace(4, f"DesktopSearch.index_dir({dir_path})")

        # Make sure target index directory exists
        if not system.is_directory(self.index_store_dir):
            gh.full_mkdir(self.index_store_dir)
        
        # define what documents to load
        text_loader_kwargs={'autodetect_encoding': True}
        loader = DirectoryLoader(dir_path, glob="./*.txt", loader_cls=TextLoader, loader_kwargs=text_loader_kwargs)
        debug.trace_expr(5, loader)
        
        # copy files over to temp dir
        # note: timestamp strips the time of day (e.g., 2024-05-11)
        timestamp = debug.timestamp().split(' ', maxsplit=1)[0]
        real_path = system.real_path(dir_path)
        # note: using [1:] to remove the initial path separator 
        temp_base = system.form_path(system.TEMP_DIR, f"llm_desktop_search.{timestamp}")
        temp_path = system.form_path(temp_base,real_path[1:])
        gh.full_mkdir(temp_path)
        
        list_files = system.get_directory_filenames(real_path)
        filtered_files = list_files
        # filter files by modification time if needed
        # note: The modification time is -1 
        modif_time = get_last_modified_date(system.get_directory_filenames(self.index_store_dir))
        if INDEX_ONLY_RECENT:
            filtered_files = [f for f in list_files if (get_file_mod_fime(f) > modif_time)]
        
        files_to_convert = [found for found in filtered_files if my_re.match(r'.*\.(pdf|docx|html|txt)', found)]
        # register cleanup function before creating temp files
        if not KEEP_TEMP_FILES:
            atexit.register(gh.delete_directory, temp_path)
        for num, file in enumerate(files_to_convert):
            filename = system.filename_proper(file)
            file_tmp_path = system.form_path(temp_path, filename) 
            if file.endswith('.txt'):
                system.write_file(file_tmp_path, system.read_entire_file(file, encoding="unicode_escape"))
            else:
                system.write_file(f"{file_tmp_path}_temp_{num}.txt", convert_to_txt(file))
        
        # interpret information in the documents
        loader = DirectoryLoader(temp_path, glob="*.txt", loader_cls=TextLoader)
        documents = loader.load()
        debug.trace_expr(5, len(documents), documents, max_len=1024)
        splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE,
                                                  chunk_overlap=CHUNK_OVERLAP)
        # documents are splitted to a maximum of 500 characters per chunk (by default)
        texts = splitter.split_documents(documents)
        corrected_texts = [correct_metadata(text, temp_base) for text in texts]
        if not self.embeddings:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL,
                model_kwargs={'device': TORCH_DEVICE})

        # add (or create from docs) to the db and save it
        try:
            self.load_index()
        except RuntimeError:
            debug.trace_exception(6, "load_index")
        if self.db is not None:
            self.db.add_documents(corrected_texts)
        else:
            self.db = FAISS.from_documents(corrected_texts, self.embeddings)
        self.db.save_local(self.index_store_dir)

        debug.trace_expr(4, self.db)
        gpu_utils.trace_gpu_usage()

        # show index info
        num_chunks = len(self.db.index_to_docstore_id)
        print(f"{num_chunks} chunks indexed")

    def load_index(self, for_qa=False):
        """Load index of documents"""
        debug.trace(4, "DesktopSearch.load_index()")
        # load the language model
        config = {'max_new_tokens': MAX_NEW_TOKENS, 'temperature': TEMPERATURE,
                  'context_length': CONTEXT_LENGTH}
        if for_qa:
            llm = CTransformers(model=QA_LLM_MODEL, model_type=QA_LLM_TYPE,
                                config=config, gpu_layers=GPU_LAYERS)
            debug.trace_expr(4, llm)
            debug.trace_object(5, llm)
            self.llm = llm

        # load the interpreted information from the local database
        if not self.embeddings:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL,
                model_kwargs={'device': TORCH_DEVICE})
        options = {}
        if ALLOW_UNSAFE_MODELS:
            options["allow_dangerous_deserialization"] = ALLOW_UNSAFE_MODELS
        self.db = FAISS.load_local(self.index_store_dir, self.embeddings, **options)
        debug.trace_expr(5, self.llm, self.embeddings, self.db)
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
        print("Similar documents:")
        for doc in docs:
            print(doc)
        gpu_utils.trace_gpu_usage()

class Script(Main):
    """Adhoc script class (e.g., no I/O loop, just run calls)"""
    # note: class-level variables for arguments avoids need for class constructor
    index_arg = None
    search_arg = False
    similar_arg = False

    def setup(self):
        """Check results of command line processing"""
        debug.trace_fmtd(TL.VERBOSE, "Script.setup(): self={s}", s=self)
        self.index_arg = self.get_parsed_option(INDEX_ARG, self.index_arg)
        self.search_arg = self.get_parsed_option(SEARCH_ARG, self.search_arg)
        self.similar_arg = self.get_parsed_option(SIMILAR_ARG, self.similar_arg)
        debug.trace_object(5, self, label=f"{self.__class__.__name__} instance")

    def run_main_step(self):
        """Main processing step (n.b., assumes self.manual_input)"""
        debug.trace_fmtd(5, "Script.run_main_step(): self={s}", s=self)
        ds = DesktopSearch()
        if self.index_arg:
            ds.index_dir(self.index_arg)
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
        skip_input=True, manual_input=True,
        boolean_options=[],
        text_options=[(INDEX_ARG, "Index directory"),
                      (SEARCH_ARG, "Search documents to answer question"),
                      (SIMILAR_ARG, "Show similar documents")],
        float_options=None)
    app.run()

#-------------------------------------------------------------------------------
    
if __name__ == '__main__':
    debug.trace_current_context(level=TL.QUITE_VERBOSE)
    debug.trace(5, f"module __doc__: {__doc__}")
    main()
