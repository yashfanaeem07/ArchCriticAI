"""
knowledge/chroma.py
-------------------
PHASE 3 - One place that knows how to open the ChromaDB collection.

Both the indexer (store.py, writes) and the retriever (retriever.py, reads) go
through here, so the persistence path, the collection name, and the similarity
metric are defined once and can't drift apart.

`chromadb` is imported lazily so importing this module (and therefore the
Phase 1 critic, which imports the retriever's types) never requires Chroma to be
installed unless RAG is actually used.
"""

from config import CHROMA_COLLECTION, CHROMA_DIR

# Cosine similarity matches our L2-normalised embeddings (see embeddings.py).
_COLLECTION_METADATA = {"hnsw:space": "cosine"}


def _client(persist_dir: str):
    """Create a persistent Chroma client rooted at `persist_dir`."""
    try:
        import chromadb
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ImportError(
            "The knowledge base needs 'chromadb'. Install it with: "
            "pip install chromadb"
        ) from exc
    return chromadb.PersistentClient(path=persist_dir)


def get_or_create_collection(
    persist_dir: str = CHROMA_DIR,
    collection_name: str = CHROMA_COLLECTION,
):
    """Open the collection for writing, creating it if it doesn't exist."""
    return _client(persist_dir).get_or_create_collection(
        name=collection_name,
        metadata=_COLLECTION_METADATA,
    )


def get_collection(
    persist_dir: str = CHROMA_DIR,
    collection_name: str = CHROMA_COLLECTION,
):
    """
    Open the collection for reading.

    Raises a clear, actionable error if the knowledge base hasn't been built yet,
    instead of Chroma's lower-level exception.
    """
    try:
        return _client(persist_dir).get_collection(name=collection_name)
    except Exception as exc:  # noqa: BLE001 - normalise to one helpful message
        raise RuntimeError(
            f"Knowledge base collection '{collection_name}' was not found in "
            f"'{persist_dir}'. Build it first by running:  python rag_embed.py"
        ) from exc
