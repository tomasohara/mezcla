#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Test(s) for ../llm_desktop_search.py
#
# Notes:
# - This can be run as follows:
#   $ PYTHONPATH=".:$PYTHONPATH" python ./mezcla/tests/test_llm_desktop_search.py
#
# TODO3:
# - Try to minize usage of run_script to just one or two tests:
#   it is an older style of testing. It is better to use DesktopSearch
#   class directly. More details follow in the warning.
#
# Warning:
# - The use of run_script as in test_01_data_file is an older style of testing.
#   It is better to directly invoke a helper class in the script that is independent
#   of the Script class based on Main, which is mainly for argument parsing.
#   (For an example of this, see python_ast.py and tests/tests_python_ast.py.)
# - Moreover, debugging tests with run_script is complicated because a separate
#   process is involved (e.g., with separate environment variables).
# - See discussion of SUB_DEBUG_LEVEL in unittest_wrapper.py for more info.
#

"""Tests for llm_desktop_search module"""

# Standard modules
import atexit
import json
import os
import re
import subprocess
from pathlib import Path
import sys
from types import SimpleNamespace

# Installed modules
import pytest

# Local modules
from mezcla.unittest_wrapper import TestWrapper, RUN_SLOW_TESTS, invoke_tests
from mezcla import debug
from mezcla import glue_helpers as gh
from mezcla import gpu_utils
from mezcla.main import KEEP_TEMP_FILES
from mezcla.my_regex import my_re
from mezcla import system

# Note: Two references are used for the module to be tested:
#    THE_MODULE:                        module instance (e.g,, <module 'mezcla.main' from '/home/testuser/Mezcla/mezcla/main.py'>
#    TestIt.script_module:              dotted module path (e.g., "mezcla.main")
try:
    import mezcla.llm_desktop_search as THE_MODULE
    get_last_modified_date = THE_MODULE.get_last_modified_date
except:
    THE_MODULE = None
    get_last_modified_date = None
    debug.trace_exception(3, "llm_desktop_search import")

#------------------------------------------------------------------------

@pytest.mark.skipif(not THE_MODULE, reason="Unable to load module")
class TestIt(TestWrapper):
    """Class for command-line based testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__, THE_MODULE)
    ## TODO2: simplify logic (e.g. lstrip) and reduce redundancy
    INDEX_STORE_DIR = (THE_MODULE.INDEX_STORE_DIR.lstrip().lstrip(system.path_separator())
                       if THE_MODULE else None)
    use_temp_base_dir = True            # needed for self.temp_base to be a dir    
    # set a temp dir to test index indexingL setUpClass
    # Note: index_temp_dir needs to be unique
    index_temp_dir = None
    index_parent = None

    @classmethod
    def setUpClass(cls, filename=None, module=None):
        """One-time initialization (i.e., for entire class)"""
        # note: creates default FAISS index shared by tests (unless overriden)
        debug.trace(6, f"TestIt.setUpClass(); cls={cls}")
        # note: should do parent processing first
        super().setUpClass(filename, module)
        cls.index_parent = cls.temp_base
        cls.index_temp_dir = gh.form_path(cls.index_parent, cls.INDEX_STORE_DIR)
        if not system.is_directory(cls.index_temp_dir):
            gh.full_mkdir(cls.index_temp_dir)
        if THE_MODULE.INDEX_ONLY_RECENT:
            THE_MODULE.INDEX_ONLY_RECENT = False
        debug.trace_object(5, cls, label=f"{cls.__class__.__name__} instance")
        return

    @classmethod
    def ensure_shared_index(cls):
        """Build the shared FAISS index lazily so tests can run in isolation."""
        debug.assertion(cls.index_temp_dir)
        index_file = gh.form_path(cls.index_temp_dir, "index.faiss")
        if system.file_exists(index_file):
            return
        file_dir = gh.real_path(gh.dirname(__file__))
        repo_base_dir = gh.form_path(file_dir, "..", "..")
        debug.assertion(system.file_exists(gh.form_path(repo_base_dir, "LICENSE.txt")))
        desktop = THE_MODULE.DesktopSearch(index_store_dir=cls.index_temp_dir)
        desktop.index_dir(repo_base_dir)
        debug.assertion(system.file_exists(index_file))

    @pytest.mark.skipif(not RUN_SLOW_TESTS, reason="Ignoring slow test")
    def test_01_index_dir(self):
        """Tests run_script to index directory"""
        # Warning: see notes above about potential issues with run_script-based tests.
        debug.trace(4, f"TestIt.test_01_index_dir(); self={self}")
        if not KEEP_TEMP_FILES:
            atexit.register(gh.delete_directory, self.index_temp_dir)
            
        if not system.is_directory(self.index_parent):
            debug.assertion(False)
            gh.full_mkdir(self.index_parent)
        
        # test if indexing works with with no existing db
        file_dir = gh.real_path(gh.dirname(__file__))
        repo_base_dir = gh.form_path(file_dir, "..", "..")
        
        init_output = self.run_script(options=f"--index {repo_base_dir}",
                                      env_options=f"INDEX_STORE_DIR={self.index_temp_dir}")
        self.do_assert(my_re.search(r"(\d\d+) chunks indexed", init_output))
        num_initial_chunks = int(my_re.group(1))
        index_files = system.read_directory(self.index_temp_dir)
        
        # assert INDEX_STORE_DIR is not empty
        self.do_assert(index_files != [])
        
        # save modified date for comparing later 
        prev_date = get_last_modified_date(
            system.get_directory_filenames(self.index_temp_dir,
                                            just_regular_files=True))
        
        # test that indexing with an already existing DB works
        resource_dir = gh.form_path(file_dir, "resources")
        revised_output = self.run_script(options=f"--index {resource_dir}",
                                         env_options=f"INDEX_STORE_DIR={self.index_temp_dir}")
        self.do_assert(my_re.search(r"(\d\d+) chunks indexed", revised_output))
        num_final_chunks = int(my_re.group(1))
        self.do_assert(num_final_chunks > num_initial_chunks)
       
        # get modification time and check if it changed
        new_date = get_last_modified_date(system.get_directory_filenames(self.index_temp_dir, just_regular_files=True))
        self.do_assert(new_date > prev_date)
        

    @pytest.mark.skipif(not RUN_SLOW_TESTS, reason="Ignoring slow test")
    def test_02_search_docs(self):
        """Test for something_else: TODO..."""
        debug.trace(4, f"TestIt.test_02_search_docs(); self={self}")
        self.ensure_shared_index()
        desktop = THE_MODULE.DesktopSearch(self.index_temp_dir)
        desktop.search_to_answer('What license is used?')
        output = self.get_stdout()
        
        self.do_assert(my_re.search(r"GNU", output.strip()))
        

    @pytest.mark.skipif(gpu_utils.TORCH_DEVICE != "cuda", reason="Ignoring non-CUDA device")
    @pytest.mark.skipif(not RUN_SLOW_TESTS, reason="Ignoring slow test")
    def test_03_gpu_usage(self):
        """Test for GPU libs being used"""
        # Note: verifies [python] process using GPU via nvida-smi
        #  |  GPU   GI   CI        PID   Type   Process name            GPU Memory |
        #  ...
        #  |    0   N/A  N/A   1111609      C   python                      366MiB |
        debug.trace(4, f"TestIt.test_03_gpu_usage(); self={self}")
        self.ensure_shared_index()
        ds = THE_MODULE.DesktopSearch(self.index_temp_dir)
        ds.show_similar("license")
        trace_level = max(1, debug.get_level())
        gpu_utils.trace_gpu_usage(level=trace_level)
        stdout, stderr = self.get_stdout_stderr()
        self.do_assert("GNU" in stdout)           # license
        # Check that python process in nvida-smi listing.
        # Assumes that no other python processes using GPU active.
        pid = system.get_process_id()
        self.do_assert(my_re.search(fr"\b{pid}\b.*python", stderr))
        return
    
    @pytest.mark.skipif(not RUN_SLOW_TESTS, reason="Ignoring slow test")
    def test_04_show_similar(self):
        """Test run_script to show similar document to QUERY"""
        debug.trace(4, f"test_04_show_similar(): self={self}")
        self.ensure_shared_index()
        desktop = THE_MODULE.DesktopSearch(index_store_dir=self.index_temp_dir)
        
        desktop.show_similar(query="LICENSE", num=1)
        output = self.get_stdout()
        if not KEEP_TEMP_FILES:
            gh.delete_directory(self.index_temp_dir)
        self.do_assert("Lesser General Public License" in output)
        

    @pytest.mark.skipif(not RUN_SLOW_TESTS, reason="Ignoring slow test")
    def test_05_index_via_API(self):
        """Run indexing via class-based API"""
        debug.trace(4, f"test_05_index_via_API(): self={self}")
        
        # Index the files
        # note: index is specific to this test case
        temp_index_dir = gh.form_path(self.temp_base, "index")
        test_dir = gh.dirname(__file__)
        doc_dir = gh.resolve_path("resources", base_dir=test_dir)
        ds = THE_MODULE.DesktopSearch(index_store_dir=temp_index_dir)
        ds.index_dir(doc_dir)

        # Make sure most of expected content got indexed included (e.g., 75%)
        #
        # Note: document contents check as follows
        # In [67]: docid = db.index_to_docstore_id[0];  db.docstore.search(docid).page_content
        # Out[67]: 'Tío Tomás\t\t\t\tUncle Tom\n\n¡Buenos días!\t\t\t\tGood morning\n\nçãêâôöèäàÃëÇÂîòïÔìðÊÅåùÀŠý\t\tcaeaooeaaAeCAioiOioEAauASy'
        #
        expected_text = ["Tío Tomás", "Library", "validation", "Iris", "Argentina"]
        num_total = len(expected_text)
        num_found = 0
        for text in expected_text:
           for docid in ds.db.index_to_docstore_id.values():
              if text in ds.db.docstore.search(docid).page_content:
                 num_found += 1
                 break
        pct_75 = (3 * num_total // 4)
        debug.trace_expr(5, num_found, num_total, pct_75)
        assert(num_found >= pct_75)

#...............................................................................

if THE_MODULE:
    class _FakeLoader:
        """Simple text loader for deterministic llm_desktop_search tests"""
        def __init__(self, dir_path, glob=None, loader_cls=None, loader_kwargs=None):
            """Store the target directory and validate the fake loader contract."""
            self.dir_path = Path(dir_path)
            debug.assertion(self.dir_path)
            debug.assertion(glob in [None, "*.txt"])
            debug.assertion(loader_cls in [None, THE_MODULE.TextLoader])
            debug.assertion((loader_kwargs is None) or isinstance(loader_kwargs, dict))

        def load(self):
            """Return deterministic `Document` instances for all text files."""
            debug.assertion(self.dir_path.exists())
            debug.assertion(self.dir_path.is_dir())
            documents = []
            for path in sorted(self.dir_path.glob("*.txt")):
                debug.assertion(path.is_file())
                documents.append(THE_MODULE.Document(
                    page_content=path.read_text(encoding="utf-8"),
                    metadata={"source": str(path)}))
            debug.assertion(documents)
            return documents

    class _FakeSplitter:
        """Splitter stub that preserves document ordering"""
<<<<<<< development
        def __init__(self, chunk_size=None, chunk_overlap=None, add_start_index=None):
            """Capture the requested chunk configuration for sanity checking."""
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap
            self.add_start_index = add_start_index
=======
        def __init__(self, chunk_size=None, chunk_overlap=None):
            """Capture the requested chunk configuration for sanity checking."""
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap
>>>>>>> main

        def split_documents(self, documents):
            """Return the input documents unchanged for deterministic tests."""
            debug.assertion(isinstance(documents, list))
            return list(documents)

    class _FakeEmbeddings:
        """Embedding stub for DesktopSearch unit tests"""
        def __init__(self, model_name=None, model_kwargs=None):
            """Record embedding configuration without loading external models."""
            debug.assertion(model_name)
            debug.assertion(isinstance((model_kwargs or {}), dict))
            self.model_name = model_name
            self.model_kwargs = model_kwargs or {}

    class _FakeDocStore:
        """Docstore stub compatible with FAISS tests"""
        def __init__(self, mapping):
            """Keep a searchable mapping from fake FAISS doc ids to documents."""
            debug.assertion(isinstance(mapping, dict))
            self.mapping = mapping

        def search(self, key):
            """Return the document stored under KEY."""
            debug.assertion(key in self.mapping)
            return self.mapping[key]

    class _FakeRetriever:
        """Retriever stub backed by the fake FAISS implementation"""
        def __init__(self, db, limit):
            """Bind a fake FAISS store and retrieval limit."""
            debug.assertion(db is not None)
            debug.assertion(limit >= 1)
            self.db = db
            self.limit = limit

        def get_relevant_documents(self, query):
            """Return the ranked documents only, mirroring retriever behavior."""
            debug.assertion(isinstance(query, str))
            debug.assertion(query)
            return [doc for (doc, _score) in self.db.similarity_search_with_score(query, self.limit)]

    class _FakeFAISS:
        """Persisted vector store stub for deterministic tests"""
        STORE_FILE = "fake-faiss-store.json"

        def __init__(self, documents, embeddings):
            """Capture stored documents and rebuild docstore metadata."""
            debug.assertion(isinstance(documents, list))
            debug.assertion(embeddings is not None)
            self.documents = list(documents)
            self.embeddings = embeddings
            self._refresh()

        def _refresh(self):
            """Refresh fake FAISS ids and docstore after document mutations."""
            debug.assertion(isinstance(self.documents, list))
            self.index_to_docstore_id = {
                num: f"doc-{num}" for num in range(len(self.documents))
            }
            mapping = {
                doc_id: self.documents[num]
                for (num, doc_id) in self.index_to_docstore_id.items()
            }
            debug.assertion(len(mapping) == len(self.documents))
            self.docstore = _FakeDocStore(mapping)

        @classmethod
        def from_documents(cls, documents, embeddings):
            """Build a fake FAISS store from a document list."""
            debug.assertion(documents)
            return cls(documents, embeddings)

        def add_documents(self, documents):
            """Append documents and refresh fake FAISS bookkeeping."""
            debug.assertion(isinstance(documents, list))
            debug.assertion(documents != [])
            self.documents.extend(documents)
            self._refresh()

        def save_local(self, index_store_dir):
            """Persist the fake store as sorted JSON for reproducible tests."""
            store_path = Path(index_store_dir)
            debug.assertion(store_path)
            store_path.mkdir(parents=True, exist_ok=True)
            payload = [{
                "page_content": doc.page_content,
                "metadata": doc.metadata,
            } for doc in self.documents]
            store_file = store_path / self.STORE_FILE
            store_file.write_text(
                json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2),
                encoding="utf-8")
            debug.assertion(store_file.exists())

        @classmethod
        def load_local(cls, index_store_dir, embeddings, **_kwargs):
            """Load the persisted fake store from disk."""
            store_file = Path(index_store_dir) / cls.STORE_FILE
            if not store_file.exists():
                raise RuntimeError(f"missing fake store: {store_file}")
            payload = json.loads(store_file.read_text(encoding="utf-8"))
            debug.assertion(isinstance(payload, list))
            documents = [
                THE_MODULE.Document(
                    page_content=item["page_content"],
                    metadata=item["metadata"])
                for item in payload
            ]
            debug.assertion(documents != [])
            return cls(documents, embeddings)

        def similarity_search_with_score(self, query, k):
            """Return deterministically ranked documents and simple scores."""
            debug.assertion(isinstance(query, str))
            debug.assertion(k >= 1)
            query_tokens = set(re.findall(r"[A-Za-z]+", query.casefold()))
            matches = []
            for doc in self.documents:
                searchable_text = f"{doc.metadata.get('source', '')}\n{doc.page_content}".casefold()
                score = 0
                if query_tokens:
                    score = -sum(token in searchable_text for token in query_tokens)
                matches.append((doc, score))
            matches.sort(key=lambda item: (
                item[1],
                item[0].metadata.get("source", ""),
                item[0].page_content))
            debug.assertion(matches)
            return matches[:k]

        def as_retriever(self, search_kwargs=None):
            """Create a fake retriever using the requested top-k limit."""
            limit = (search_kwargs or {}).get("k", THE_MODULE.NUM_SIMILAR)
            debug.assertion(limit >= 1)
            return _FakeRetriever(self, limit)

    class _FakeCTransformers:
        """LLM stub exposing the model path expected by search_to_answer"""
        def __init__(self, model, model_type=None, config=None, gpu_layers=None):
            """Store constructor arguments without loading a real model."""
            debug.assertion(model)
            self.model = model
            self.model_type = model_type
            self.config = config or {}
            self.gpu_layers = gpu_layers

    class _FakeRetrievalQA:
        """RetrievalQA stub that requires an initialized llm"""
        def __init__(self, llm, retriever):
            """Wrap fake LLM metadata in the shape search_to_answer expects."""
            debug.assertion(llm is not None)
            debug.assertion(retriever is not None)
            self.retriever = retriever
            self.combine_documents_chain = SimpleNamespace(
                llm_chain=SimpleNamespace(llm=llm))

        @classmethod
        def from_chain_type(cls, llm, chain_type=None, retriever=None, **kwargs):
            """Build a fake RetrievalQA chain from the provided retriever."""
            debug.assertion(chain_type == 'stuff')
            debug.assertion(kwargs.get("return_source_documents") is True)
            debug.assertion(isinstance(kwargs.get("chain_type_kwargs"), dict))
            assert llm is not None
            return cls(llm, retriever)

        def __call__(self, payload):
            """Return a deterministic answer payload from retrieved documents."""
            debug.assertion(isinstance(payload, dict))
            debug.assertion("query" in payload)
            docs = self.retriever.get_relevant_documents(payload["query"])
            answer_doc = next(
                (doc for doc in docs if "gnu" in doc.page_content.casefold()),
                (docs[0] if docs else None))
            answer = (answer_doc.page_content if answer_doc else "I do not know")
            return {"result": answer, "source_documents": docs}

@pytest.fixture(name="fake_desktop_search_env")
def desktop_search_env_fixture(tmp_path, monkeypatch):
    """Prepare a deterministic DesktopSearch environment with fake FAISS persistence"""
    if not THE_MODULE:
        pytest.skip("Unable to load llm_desktop_search module")
    doc_dir = tmp_path / "docs"
    index_dir = tmp_path / "index"
    doc_dir.mkdir()
    (doc_dir / "z-license.txt").write_text(
        "GNU Lesser General Public License\n",
        encoding="utf-8")
    (doc_dir / "a-notes.txt").write_text(
        "Argentina library validation Iris\n",
        encoding="utf-8")
    debug.assertion((doc_dir / "z-license.txt").exists())
    debug.assertion((doc_dir / "a-notes.txt").exists())
    monkeypatch.setattr(THE_MODULE, "DirectoryLoader", _FakeLoader)
    monkeypatch.setattr(THE_MODULE, "RecursiveCharacterTextSplitter", _FakeSplitter)
    monkeypatch.setattr(THE_MODULE, "HuggingFaceEmbeddings", _FakeEmbeddings)
    monkeypatch.setattr(THE_MODULE, "FAISS", _FakeFAISS)
    monkeypatch.setattr(THE_MODULE, "CTransformers", _FakeCTransformers)
    monkeypatch.setattr(THE_MODULE, "RetrievalQA", _FakeRetrievalQA)
    monkeypatch.setattr(THE_MODULE, "INDEX_ONLY_RECENT", False)
    return (doc_dir, index_dir)

@pytest.mark.skipif(not THE_MODULE, reason="Unable to load module")
@pytest.mark.parametrize("query_order", [("similar", "search"), ("search", "similar")])
def test_query_order_reuses_same_persistent_index(fake_desktop_search_env, capsys, query_order):
    """DesktopSearch should support similar/search in either order on one persisted index"""
    doc_dir, index_dir = fake_desktop_search_env
    ds = THE_MODULE.DesktopSearch(index_store_dir=str(index_dir))
    ds.index_dir(str(doc_dir))
    capsys.readouterr()
    initial_store = (index_dir / _FakeFAISS.STORE_FILE).read_text(encoding="utf-8")
    debug.assertion(initial_store)
    reloaded = THE_MODULE.DesktopSearch(index_store_dir=str(index_dir))

    for operation in query_order:
        debug.assertion(operation in ["similar", "search"])
        if operation == "similar":
            reloaded.show_similar("license", num=1)
        else:
            reloaded.search_to_answer("What license is used?")
        output = capsys.readouterr().out
        assert "GNU Lesser General Public License" in output

    assert reloaded.llm is not None
    assert (index_dir / _FakeFAISS.STORE_FILE).read_text(encoding="utf-8") == initial_store

@pytest.mark.skipif(not THE_MODULE, reason="Unable to load module")
def test_index_dir_persists_documents_in_sorted_order(fake_desktop_search_env):
    """Index persistence should be deterministic for stable tests"""
    doc_dir, index_dir = fake_desktop_search_env
    ds = THE_MODULE.DesktopSearch(index_store_dir=str(index_dir))
    ds.index_dir(str(doc_dir))
    payload = json.loads((index_dir / _FakeFAISS.STORE_FILE).read_text(encoding="utf-8"))
    debug.assertion(isinstance(payload, list))
    debug.assertion(payload)
    persisted_sources = [item["metadata"]["source"] for item in payload]
    assert persisted_sources == sorted(persisted_sources)

@pytest.mark.skipif(not THE_MODULE, reason="Unable to load module")
def test_import_disables_tensorflow_backend_by_default():
    """Module import should avoid TensorFlow backend warnings unless requested."""
    repo_root = Path(__file__).resolve().parents[2]
    command = [
        sys.executable,
        "-c",
        (
            "import os; "
            "import mezcla.llm_desktop_search; "
            "print(os.getenv('USE_TF')); "
            "print(os.getenv('TRANSFORMERS_NO_TF'))"
        ),
    ]
    env = os.environ.copy()
    env.pop("USE_TF", None)
    env.pop("TRANSFORMERS_NO_TF", None)
    env["PYTHONPATH"] = str(repo_root)
    completed = subprocess.run(
        command,
        capture_output=True,
        check=False,
        cwd=repo_root,
        env=env,
        text=True)
    assert completed.returncode == 0, completed.stderr
    assert "MessageFactory" not in completed.stderr
    assert "GetPrototype" not in completed.stderr
    assert completed.stdout.splitlines()[-2:] == ["0", "1"]

<<<<<<< development
## TODO: Use self.script_output method if possible instead of gh.run()
# Environment Variables for newer tests
## TODO2: use getenv_value when default is empty: use DEBUG_LEVEL=4 to find out why!
LLM_PATH = system.getenv_text(
    ## TODO23: use default from tested script
    "LLM_PATH", "",
    description="Path for LLM model"
)

class TestLLMDesktopSearch(TestWrapper):
    """Class for command-line based testcase definition"""
    script_module = TestWrapper.get_testing_module_name(__file__)
    script_file = TestWrapper.get_module_file_path(__file__)
    INDEX_STORE_DIR = (THE_MODULE.INDEX_STORE_DIR.lstrip().lstrip(system.path_separator()) if THE_MODULE else None)
    use_temp_base_dir = True
    mezcla_base = gh.form_path(gh.dirname(__file__), "..", "..")   
    e2e_index_store = gh.get_temp_dir()

    def helper_run_script(self, allow_unsafe_models=True, qa_llm_model=LLM_PATH, index_store_dir=e2e_index_store, options="-h", env_variables=""):
        """Helper script for self.run_script()"""
        ## NOTE: In case of stderr, the function doesn't return anything. Use gh.run in such cases
        env_options= f"ALLOW_UNSAFE_MODELS={allow_unsafe_models} QA_LLM_MODEL={qa_llm_model} INDEX_STORE_DIR={index_store_dir} " + env_variables
        cmd_options = f'{options}'
        return self.run_script(options=cmd_options, env_options=env_options) 

    def helper_create_sample_files(self):
        """Create a temporary directory consisting of document type files"""
        temp_dir = gh.get_temp_dir()
        doc_content = "You can generate random words or sentences in Python without using any external libraries (like nltk or faker) by using built-in modules like random and defining your own word lists."
        file_extensions = ["txt", "doc", "pdf", "html"]
        for ext in file_extensions[0]:
            filename = "sample_file." + ext
            system.write_file(temp_dir + "/" + filename, doc_content)
        return temp_dir
    
    def helper_extract_compatible_documents(self, directory):
        """Extract documents supported by the script from a directory"""
        files = system.get_directory_filenames(directory)
        extensions = ["txt", "html", "doc", "md"]
        result = []
        for file in files:
            extension = file.split(".")[-1]
            if extension in extensions:
                result.append(gh.basename(file))
        return result

    def test_func_get_file_mod_time(self):
        """Ensures get_file_mod_time method works as expected"""
        existing_dir = "/etc/passwd"
        non_existing_dir = "/etc/password"
        
        self.assertNotEqual(
            THE_MODULE.get_file_mod_time(existing_dir), -1
        )
        self.assertEqual(
            THE_MODULE.get_file_mod_time(non_existing_dir), -1
        )

    def test_func_get_last_modified_date(self):
        """Ensures get_last_modified_date works as expected"""
        temp_dir = gh.get_temp_dir()
        last_modified_date = THE_MODULE.get_last_modified_date(temp_dir)
        self.assertIsInstance(last_modified_date, float)
    
    @pytest.mark.skipif(not system.file_exists(LLM_PATH), reason="LLM_PATH does not exist")
    @pytest.mark.skipif(not RUN_SLOW_TESTS, reason="--search option takes some time for operation")
    def test_preliminary_is_model_loaded(self):
        """Test if test based model is loaded"""

        # Check if QA_LLM_MODEL uses llama by default
        self.assertIn("llama-2-7b-chat", THE_MODULE.QA_LLM_MODEL)

        string_allow_unsafe_models = "ALLOW_UNSAFE_MODELS=True"
        string_qa_llm_model = f"QA_LLM_MODEL={LLM_PATH}" 
        command_base = f"python3 {self.mezcla_base}/mezcla/llm_desktop_search.py --index {self.mezcla_base}"
        
        ##1 Test for base command: should lead to ValueError as index files are not created
        base_output = gh.run(command_base)
        error_msgs = [
            "ValueError: The de-serialization relies loading a pickle file.", 
            "Traceback (most recent call last)",
            "mezcla/llm_desktop_search.py", 
            "self.load_index"
        ]
        for msg in error_msgs:
            self.assertIn(msg, base_output)

        ##2 Test for allow_unsafe_models: ALLOW_UNSAFE_MODEL
        command_with_allow_unsafe_models = " ".join([string_allow_unsafe_models, command_base])
        allow_unsafe_models_output = gh.run(command_with_allow_unsafe_models)
        self.assertIn("ValueError: not enough values to unpack (expected 2, got 1)", allow_unsafe_models_output)
        self.assertIn("Traceback (most recent call last)", allow_unsafe_models_output)
        self.assertIn("mezcla/llm_desktop_search.py", allow_unsafe_models_output)

        ##3 Test for qa_llm_model: QA_LLM_MODEL
        command_with_llm_loaded = " ".join([string_qa_llm_model, command_base])
        output_with_llm_loaded = gh.run(command_with_llm_loaded)
        error_msgs = [
            "ValueError: The de-serialization relies loading a pickle file.", 
            "Traceback (most recent call last)",
            "mezcla/llm_desktop_search.py", 
            "self.load_index"
        ]
        for msg in error_msgs:
            self.assertIn(msg, output_with_llm_loaded)

        ##4 Final test: Everything in place
        final_command = self.helper_run_script(options=f'--index "{self.mezcla_base}",')
        self.assertEqual(final_command, "")

    @pytest.mark.skipif(not system.file_exists(LLM_PATH), reason="LLM_PATH does not exist")
    @pytest.mark.skipif(not RUN_SLOW_TESTS, reason="--search option takes some time for operation")
    def test_generate_index_store(self):
        """Test to ensure index files (faiss, pkl) are generated"""
        index_store_temp = gh.get_temp_dir()
        self.run_script(options=f"--index {self.mezcla_base}",
                        env_options=f"ALLOW_UNSAFE_MODELS=1 QA_LLM_MODEL={LLM_PATH} INDEX_STORE_DIR={index_store_temp}")
        index_store_content = gh.run(f"ls {index_store_temp}")
        assert "index.faiss" in index_store_content
        assert "index.pkl" in index_store_content
    
    @pytest.mark.skipif(not system.file_exists(LLM_PATH), reason="LLM_PATH does not exist")
    @pytest.mark.skipif(not RUN_SLOW_TESTS, reason="--search option takes some time for operation")
    def test_scenario_detect_document_file(self):
        """Test to check if document files are detected by THE_MODULE"""
        # temp_file_store = self.helper_create_sample_files()
        valid_extensions = "pdf|docx|html|txt"
        doc_files_path = self.mezcla_base
        doc_files_count = gh.run(f"ls {doc_files_path} | grep -E '{valid_extensions}' | wc -l")
        
        # If the documents are accepted by script, index is created
        # The output is blank in case of success
        temp_index_store_dir = gh.get_temp_dir()
        llm_command_result = self.helper_run_script(index_store_dir=temp_index_store_dir, options=f'--index {doc_files_path}')
        self.assertGreaterEqual(int(doc_files_count), 0)
        self.assertEqual(llm_command_result, "")
        index_store_contents = gh.run(f"ls {temp_index_store_dir}")
        self.assertIn("pkl", index_store_contents)
        self.assertIn("faiss", index_store_contents)

    @pytest.mark.skipif(not system.file_exists(LLM_PATH), reason="LLM_PATH does not exist")
    def test_scenario_no_document_file(self):
        """Test to check if non document files are not detected by modules"""
        # NOTE: <MEZCLA_BASE>/mezcla is taken as the path as it consists of no documents
        no_docs_path = self.mezcla_base + "/mezcla"
        txt_count = gh.run(f"ls {no_docs_path} | grep 'txt' | wc -l")
        
        # If the documents are not accepted by script, no index is created
        # The output consists of Exception messages
        temp_index_store_dir = gh.get_temp_dir()
        llm_command_result = gh.run(
            f"ALLOW_UNSAFE_MODELS=1 QA_LLM_MODEL={LLM_PATH} INDEX_STORE_DIR={temp_index_store_dir} python3 {self.mezcla_base}/mezcla/llm_desktop_search.py --index {no_docs_path}"
        )
        self.assertEqual(int(txt_count), 0)
        self.assertNotEqual(llm_command_result, "")
        self.assertIn("IndexError: list index out of range", llm_command_result)
        index_store_contents = gh.run(f"ls {temp_index_store_dir}")
        self.assertEqual(index_store_contents, "")

    @pytest.mark.skipif(not system.file_exists(LLM_PATH), reason="LLM_PATH does not exist")
    @pytest.mark.skipif(not RUN_SLOW_TESTS, reason="--search option takes some time for operation")
    def test_e2e_index_option(self):
        """End-to-end tests to check if --index option work as expected"""
        command_output = self.run_script(options=f"--index {self.mezcla_base}",
                        env_options=f"ALLOW_UNSAFE_MODELS=1 QA_LLM_MODEL={LLM_PATH} INDEX_STORE_DIR={self.e2e_index_store}")
        self.assertEqual(command_output, "")
        index_dir_contents = gh.run(f"ls {self.e2e_index_store}")
        self.assertIn("index.faiss", index_dir_contents)
        self.assertIn("index.pkl", index_dir_contents)

    
    @pytest.mark.skipif(not system.file_exists(LLM_PATH), reason="LLM_PATH does not exist")
    @pytest.mark.skipif(not RUN_SLOW_TESTS, reason="--search option takes some time for operation")
    def test_e2e_search_option(self):
        """End-to-end tests to check if --search option works as expected"""
        ## Create an index at first, and proceed for the search
        temp_index_store = gh.get_temp_dir()
        CONTEXT_LENGTH = 1152
        self.helper_run_script(index_store_dir=temp_index_store, options=f"--index {self.mezcla_base}")
        search_term = "Explain me in a sentence about the licenses used in this project"
        command_output = self.helper_run_script(env_variables=f"CONTEXT_LENGTH={CONTEXT_LENGTH}", index_store_dir=temp_index_store, options=f'--search "{search_term}"')

        outputs = command_output.split("\n")
        self.assertIn("Question", command_output)
        self.assertIn("Answer", command_output)
        self.assertIn("response time", command_output)
        self.assertEqual(len(outputs), 3)
        result_question = outputs[1].split("</strong>")[-1].strip()
        result_answer = outputs[2].split("<strong>")[-1].strip()
        self.assertIn(gh.basename(LLM_PATH), outputs[0])
        self.assertEqual(result_question, search_term)
        ## The response must be in a single sentence as defined by the prompt
        self.assertTrue(result_answer.endswith(".") and result_answer.count(".") == 1)
        self.assertTrue(len(command_output) >= 50)

    @pytest.mark.skipif(not system.file_exists(LLM_PATH), reason="LLM_PATH does not exist")
    @pytest.mark.skipif(not RUN_SLOW_TESTS, reason="--search option takes some time for operation")
    def test_e2e_similar_option(self):
        """End-to-end tests to check if --similar option works as expected"""
        temp_index_store = gh.get_temp_dir()
        self.helper_run_script(index_store_dir=temp_index_store, options=f"--index {self.mezcla_base}")
        similar_term = "GNU"
        command_output = self.helper_run_script(index_store_dir=temp_index_store, options=f"--similar {similar_term}")

        self.assertNotEqual(command_output, "")
        self.assertIn(similar_term, command_output)
        result_pattern = r"\(Document\(id='([a-f0-9-]{36})',\s*metadata={'source':\s*'([^']+)'},\s*page_content='((?:[^']|\\')+)'\),\s*np\.float32\((\d+\.\d+)\)\)"
        self.assertRegex(command_output, result_pattern)
        compatible_docs = self.helper_extract_compatible_documents(directory=self.mezcla_base)
        self.assertEqual(len(compatible_docs), 6)
        docs_occurrences = sum(command_output.count(c) for c in compatible_docs)
        self.assertTrue(docs_occurrences >= 1)


    def test_e2e_help_option(self):
        """End-to-end tests to check if --help option works as expected"""
        terms = ["usage", "llm_desktop_search.py", "verbose", "help", "Desktop search utility", "options", THE_MODULE.INDEX_ARG, THE_MODULE.SEARCH_ARG, THE_MODULE.SIMILAR_ARG]
        ## OLD (Below command equivalent to self.run_script(options="h"))
        # command_output = self.run_script(options="-h")
        command_output = self.helper_run_script()
        self.assertNotEqual(command_output, "")
        for t in terms:
            self.assertIn(t, command_output)

=======
>>>>>>> main
#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
