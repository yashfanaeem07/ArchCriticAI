"""
tests/test_knowledge.py
-----------------------
Phase 3 (RAG) tests.

The chunking, loader, and interface tests are pure Python and always run. The
end-to-end build+retrieve test needs chromadb + sentence-transformers, so it is
skipped automatically (importorskip) when those aren't installed.
"""

import pytest

from archcritic.knowledge.chunking import chunk_text
from archcritic.knowledge.loaders import Document, load_documents
from archcritic.knowledge.retriever import Passage, PrinciplesRetriever, Retriever


# --- Chunking ----------------------------------------------------------------
def test_chunk_sizes_and_overlap():
    words = " ".join(f"w{i}" for i in range(1200))
    chunks = chunk_text(words, words_per_chunk=500, overlap=50)
    # stride = 450 -> starts at 0, 450, 900; last chunk is the 300-word tail.
    assert len(chunks) == 3
    assert len(chunks[0].split()) == 500
    assert len(chunks[-1].split()) == 300
    # Consecutive chunks share `overlap` words at the seam.
    assert chunks[0].split()[-50:] == chunks[1].split()[:50]


def test_chunk_short_text_is_one_chunk():
    assert chunk_text("just a few words here") == ["just a few words here"]


def test_chunk_empty_text_returns_no_chunks():
    assert chunk_text("   ") == []


def test_chunk_rejects_bad_params():
    with pytest.raises(ValueError):
        chunk_text("a b c", words_per_chunk=10, overlap=10)  # overlap >= size
    with pytest.raises(ValueError):
        chunk_text("a b c", words_per_chunk=0)


# --- Loaders -----------------------------------------------------------------
def test_load_documents_reads_text_and_markdown(tmp_path):
    (tmp_path / "a.txt").write_text("alpha principle", encoding="utf-8")
    (tmp_path / "b.md").write_text("# Beta\nbeta principle", encoding="utf-8")
    (tmp_path / "ignore.png").write_bytes(b"\x89PNG")  # unsupported -> skipped
    (tmp_path / "empty.txt").write_text("   ", encoding="utf-8")  # blank -> skipped

    docs = load_documents(str(tmp_path))
    assert all(isinstance(d, Document) for d in docs)
    sources = {d.source for d in docs}
    assert sources == {"a.txt", "b.md"}


def test_load_documents_missing_dir_is_empty():
    assert load_documents("does/not/exist") == []


# --- Interface conformance (the critic depends only on this) -----------------
def test_principles_retriever_satisfies_protocol():
    # runtime_checkable Protocol: structural check, no heavy deps loaded.
    assert isinstance(PrinciplesRetriever(), Retriever)


def test_retriever_default_k_is_five():
    # The critique pipeline relies on the retriever returning 5 by default.
    import inspect

    assert inspect.signature(PrinciplesRetriever.retrieve).parameters["k"].default == 5


def test_empty_query_returns_no_passages():
    # No backend touched for a blank query, so this is safe without an index.
    assert PrinciplesRetriever().retrieve("   ") == []


# --- End-to-end: build index then retrieve (needs RAG deps) ------------------
def test_build_and_retrieve_roundtrip(tmp_path):
    pytest.importorskip("chromadb")
    pytest.importorskip("sentence_transformers")

    from archcritic.knowledge.store import build_index

    principles = tmp_path / "principles"
    principles.mkdir()
    (principles / "circulation.md").write_text(
        "Circulation is the armature of the plan. Expose the main stair near the "
        "entry so vertical movement is legible and becomes part of the public "
        "experience rather than back-of-house plumbing.",
        encoding="utf-8",
    )
    (principles / "massing.md").write_text(
        "Massing concerns proportion and how volumes meet. Vary a repeated volume "
        "to give the composition a clear figure and a dynamic silhouette.",
        encoding="utf-8",
    )

    persist = str(tmp_path / "chroma")
    report = build_index(str(principles), persist, "test_collection")
    assert report.documents == 2
    assert report.chunks >= 2

    retriever = PrinciplesRetriever(
        persist_dir=persist, collection_name="test_collection"
    )
    passages = retriever.retrieve("how should vertical circulation and stairs work?", k=2)
    assert passages and all(isinstance(p, Passage) for p in passages)
    # The circulation doc should win on a circulation query.
    assert passages[0].source == "circulation.md"
    assert 0.0 <= passages[0].score <= 1.0
