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
import atexit
import importlib
import os
import pathlib
import time
from collections.abc import Iterable

# Local modules
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import gpu_utils
from mezcla.main import Main, KEEP_TEMP_FILES
from mezcla import system
from mezcla import html_utils
from mezcla.my_regex import my_re
## NOTE: extract_document_text is now dynamic (in case textract not available)
## OLD: from mezcla import extract_document_text

# NOTE:
# - llm_desktop_search uses Hugging Face sentence-transformer embeddings backed by torch.
# - Prevent transformers from eagerly importing tensorflow unless the caller explicitly
#   opts in; newer protobuf releases can otherwise emit MessageFactory/GetPrototype warnings.
# - See https://leeroopedia.com/index.php/Heuristic:Huggingface_Datatrove_VLLM_Startup_Optimization.
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("TRANSFORMERS_NO_TF", "1")

# Installed modules
Document = importlib.import_module(
    "langchain_core.documents").Document
DirectoryLoader = importlib.import_module(
    "langchain_community.document_loaders").DirectoryLoader
TextLoader = importlib.import_module(
    "langchain_community.document_loaders").TextLoader
FAISS = importlib.import_module(
    "langchain_community.vectorstores").FAISS
CTransformers = importlib.import_module(
    "langchain_community.llms.ctransformers").CTransformers


def resolve_attr(module_names, attr_name):
    """Resolve ATTR_NAME from the first importable module in MODULE_NAMES."""
    debug.trace_expr(6, module_names, attr_name)
    for module_name in module_names:
        try:
            module = importlib.import_module(module_name)
            value = getattr(module, attr_name)
            debug.trace_expr(6, module_name, attr_name, value)
            return value
        except (ImportError, AttributeError):
            debug.trace_exception(7, f"resolve_attr({module_name}, {attr_name})")
    raise ImportError(f"Unable to resolve {attr_name} from {module_names}")


RecursiveCharacterTextSplitter = resolve_attr(
    ["langchain.text_splitter", "langchain_classic.text_splitter", "langchain_text_splitters"],
    "RecursiveCharacterTextSplitter")
PromptTemplate = resolve_attr(
    ["langchain.prompts", "langchain_classic.prompts", "langchain_core.prompts"],
    "PromptTemplate")
RetrievalQA = resolve_attr(
    ["langchain.chains", "langchain_classic.chains"],
    "RetrievalQA")
HuggingFaceEmbeddings = resolve_attr(
    ["langchain_huggingface", "langchain_community.embeddings"],
    "HuggingFaceEmbeddings")

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
## OLD: QA_LLM_DEFAULT = "llama-2-7b-chat.ggmlv3.q8_0.bin"
QA_LLM_DEFAULT = "mistral-7b-instruct-v0.3-q4_k_m.gguf"
QA_LLM_MODEL = system.getenv_text(
    "QA_LLM_MODEL", QA_LLM_DEFAULT,
    description="Path to LLM model file for Q&A, such as a llama-2-7b .bin file or mistral-7b-instruct .gguf file")
QA_LLM_TYPE = system.getenv_text(
    ## OLD: "QA_LLM_TYPE", "llama",
    "QA_LLM_TYPE", "mistral",
    description="Type of transformer model for Q&A, such as llama or mistral")
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
    "CONTEXT_LENGTH", 2048,
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


def get_file_mod_time(path: str) -> float:
    """Returns file modification time in fractional seconds
    Note: -1 is returned if the file doesn't exist
    """
    # EX: (get_file_mod_time("/etc/passwd") > get_file_mod_time("/boot/vmlinuz"))
    # EX: get_file_mod_time(" /etc /password") => -1
    result = (system.get_file_modification_time(path, as_float=True) or -1)
    debug.trace(7, f"get_file_mod_time({path}) => {result}")
    return result


def get_last_modified_date(iterable: Iterable) -> float:
    """return the newest modification date as a float, 
       or -1 if iterable is empty or files don't exist"""
    result = -1
    if iterable:
        result = max(map(get_file_mod_time, iterable))
    debug.trace(7, f"get_last_modified_date() => {result}")
    return result

def correct_metadata(doc: Document, base_dir: str) -> Document:
    """removes BASE_DIR from the source metadata path
       so it represents the actual source of the file"""
    # TODO3: fix docstrings with respect to hardcoded assumptions
    debug.trace_expr(6, base_dir)
    doc_metadata = doc.metadata
    old_source = doc_metadata['source']
    new_source = old_source.replace(base_dir, "")
    debug.assertion(new_source != old_source)
    debug.trace_expr(6, old_source, new_source)
    doc_metadata['source'] = new_source
    doc.metadata = doc_metadata
    debug.trace(6, f"correct_metadata({doc!r}, {base_dir!r}) => {doc!r}")
    return doc

def convert_to_txt(in_file: str) -> str:
    """reads non-txt files and returns the text inside them"""
    debug.trace(5, f"convert_to_txt({in_file})")
    text = ""
    try:
        if in_file.endswith('.html'):
            text = html_utils.html_to_text(system.read_file(in_file))
        else:
            extract_document_text = importlib.import_module("mezcla.extract_document_text")
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

    def load_embeddings(self):
        """Load embeddings model if needed"""
        debug.trace(4, "load_embeddings()")
        if not self.embeddings:
            self.embeddings = HuggingFaceEmbeddings(
                model_name=EMBEDDING_MODEL,
                model_kwargs={'device': TORCH_DEVICE})
        debug.trace_expr(5, self.embeddings)
        return self.embeddings

    def load_llm(self):
        """Load Q&A model if needed"""
        debug.trace(4, "load_llm()")
        if not self.llm:
            model_path = pathlib.Path(QA_LLM_MODEL).expanduser()
            # note: with_name only accepts a bare filename, not a path with separators
            model_basename = pathlib.Path(QA_LLM_MODEL).name
            module_model_path = pathlib.Path(__file__).with_name(model_basename)
            if model_path.exists():
                model_name = str(model_path.resolve())
            elif module_model_path.exists():
                model_name = str(module_model_path.resolve())
            else:
                model_name = QA_LLM_MODEL
            config = {'max_new_tokens': MAX_NEW_TOKENS, 'temperature': TEMPERATURE,
                      'context_length': CONTEXT_LENGTH}
            self.llm = CTransformers(model=model_name, model_type=QA_LLM_TYPE,
                                     config=config, gpu_layers=GPU_LAYERS)
            debug.trace_expr(5, self.llm)
            debug.trace_object(5, self.llm)
        return self.llm

    def ensure_index_store_dir(self):
        """Ensure the persistent index directory exists."""
        debug.trace(5, f"ensure_index_store_dir(): dir={self.index_store_dir!r}")
        if not system.is_directory(self.index_store_dir):
            gh.full_mkdir(self.index_store_dir)

    def create_temp_index_dir(self, dir_path):
        """Create and return the temp directory used while indexing."""
        debug.trace(4, f"create_temp_index_dir({dir_path!r})")
        timestamp = debug.timestamp().split(' ', maxsplit=1)[0]
        real_path = system.real_path(dir_path)
        temp_base = system.form_path(system.TEMP_DIR, f"llm_desktop_search.{timestamp}")
        # note: using [1:] to remove the initial path separator
        temp_path = system.form_path(temp_base, real_path[1:])
        gh.full_mkdir(temp_path)
        debug.trace_expr(5, real_path, temp_base, temp_path)
        return (real_path, temp_base, temp_path)

    def get_files_to_convert(self, real_path):
        """Return eligible files, optionally filtered by modification time."""
        debug.trace(4, f"get_files_to_convert({real_path!r})")
        list_files = sorted(system.get_directory_filenames(real_path))
        filtered_files = list_files
        modif_time = get_last_modified_date(system.get_directory_filenames(self.index_store_dir))
        if INDEX_ONLY_RECENT:
            filtered_files = [f for f in list_files if (get_file_mod_time(f) > modif_time)]
        result = sorted(
            found for found in filtered_files
            if my_re.match(r'.*\.(pdf|docx|html|txt)', found))
        debug.trace(4, f"get_files_to_convert() => {len(result)} file(s): {result}")
        return result

    def populate_temp_index_dir(self, temp_path, files_to_convert):
        """Copy or convert source files into the temp indexing directory."""
        debug.trace(4, f"populate_temp_index_dir({temp_path!r}): {len(files_to_convert)} file(s)")
        if not KEEP_TEMP_FILES:
            atexit.register(gh.delete_directory, temp_path)
        for num, file in enumerate(files_to_convert):
            filename = system.filename_proper(file)
            file_tmp_path = system.form_path(temp_path, filename)
            if file.endswith('.txt'):
                debug.trace(5, f"  [{num}] copying txt: {file!r}")
                text = system.read_entire_file(file, encoding="unicode_escape")
                system.write_file(file_tmp_path, text)
            else:
                temp_file = f"{file_tmp_path}_temp.txt"
                debug.trace(5, f"  [{num}] converting to txt: {file!r} => {temp_file!r}")
                system.write_file(temp_file, convert_to_txt(file))

    def load_chunked_documents(self, temp_path, temp_base):
        """Load, normalize, and split temp documents into sorted chunks."""
        debug.trace(4, f"load_chunked_documents({temp_path!r})")
        loader = DirectoryLoader(temp_path, glob="*.txt", loader_cls=TextLoader)
        documents = sorted(
            loader.load(),
            key=lambda doc: (doc.metadata.get('source', ''), doc.page_content))
        debug.trace(4, f"  loaded {len(documents)} document(s)")
        debug.trace_expr(5, documents, max_len=1024)
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP, add_start_index=True)
        texts = splitter.split_documents(documents)
        debug.trace(4, f"  split into {len(texts)} chunk(s)")
        corrected_texts = [correct_metadata(text, temp_base) for text in texts]
        result = sorted(
            corrected_texts,
            key=lambda doc: (doc.metadata.get('source', ''), doc.page_content))
        debug.trace(5, f"load_chunked_documents() => {len(result)} chunk(s)")
        return result

    def save_index_documents(self, corrected_texts):
        """Merge chunked documents into the persistent vector store."""
        debug.trace(4, f"save_index_documents(): {len(corrected_texts)} chunk(s)")
        self.load_embeddings()
        try:
            self.load_index()
        except RuntimeError:
            debug.trace_exception(6, "load_index")
        if self.db is not None:
            self.db.add_documents(corrected_texts)
        else:
            self.db = FAISS.from_documents(corrected_texts, self.embeddings)
        self.db.save_local(self.index_store_dir)
        self.qa_llm = None

    def index_dir(self, dir_path):
        """Index files at DIR_PATH"""
        ## TODO4: look into indexing files from buffers rather than external files
        debug.trace(4, f"DesktopSearch.index_dir({dir_path})")
        self.ensure_index_store_dir()
        (_real_path, temp_base, temp_path) = self.create_temp_index_dir(dir_path)
        files_to_convert = self.get_files_to_convert(system.real_path(dir_path))
        self.populate_temp_index_dir(temp_path, files_to_convert)
        corrected_texts = self.load_chunked_documents(temp_path, temp_base)
        self.save_index_documents(corrected_texts)

        debug.trace_expr(5, self.db)
        gpu_utils.trace_gpu_usage()

        # show index info
        num_chunks = len(self.db.index_to_docstore_id)
        print(f"{num_chunks} chunks indexed")

    def load_index(self, for_qa=False):
        """Load index of documents"""
        debug.trace(4, "DesktopSearch.load_index()")
        if for_qa:
            self.load_llm()

        # load the interpreted information from the local database
        self.load_embeddings()
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
            self.load_index()
        self.load_llm()
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
        print(f"Similar documents ({len(docs)}):")
        for i, (doc, score) in enumerate(docs):
            meta = doc.metadata
            source = meta.get('source', '?')
            start_index = meta.get('start_index', '?')
            extra = {k: v for k, v in meta.items() if k not in ('source', 'start_index')}
            print(f"- result: {i + 1}")
            print(f"  score: {score:.4f}")
            print(f"  source: {source}")
            print(f"  start_index: {start_index}")
            for key, val in extra.items():
                print(f"  {key}: {val}")
            print("  content:")
            print(gh.indent(doc.page_content, indentation="    "))
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
