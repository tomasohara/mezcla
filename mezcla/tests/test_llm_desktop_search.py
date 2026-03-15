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
import re
from pathlib import Path
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
    INDEX_STORE_DIR = (THE_MODULE.INDEX_STORE_DIR.lstrip().lstrip(system.path_separator())
                       if THE_MODULE else None)
    use_temp_base_dir = True            # needed for self.temp_base to be a dir
    
    # set a temp dir to test index indexing setUpClass
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

    @pytest.mark.xfail                   # TODO: remove xfail
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
        prev_date = get_last_modified_date(system.get_directory_filenames(self.index_temp_dir, just_regular_files=True))
        
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
        

    @pytest.mark.xfail                   # TODO: remove xfail
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
    

    @pytest.mark.xfail                   # TODO: remove xfail
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
        

    @pytest.mark.xfail                   # TODO: remove xfail
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
        def __init__(self, chunk_size=None, chunk_overlap=None):
            """Capture the requested chunk configuration for sanity checking."""
            self.chunk_size = chunk_size
            self.chunk_overlap = chunk_overlap

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

#------------------------------------------------------------------------

if __name__ == '__main__':
    debug.trace_current_context()
    invoke_tests(__file__)
