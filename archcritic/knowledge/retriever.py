"""
knowledge/retriever.py
----------------------
PHASE 3 (scaffolded).

This defines the *interface* for retrieval-augmented generation (RAG). The
Phase 1 critic already accepts any object that matches the `Retriever` protocol,
so when we implement real retrieval here, the critic uses it with no changes.

Planned implementation:
  1. Load architecture design-theory documents from data/principles/.
  2. Split them into passages and embed them (e.g. with an embedding model).
  3. Store the vectors (e.g. Chroma / FAISS / a simple in-memory index).
  4. `retrieve()` embeds the query and returns the closest passages.
"""

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class Passage:
    """A chunk of retrieved design theory, with where it came from."""

    text: str
    source: str  # filename or citation
    score: float = 0.0  # similarity score (higher = more relevant)


@runtime_checkable
class Retriever(Protocol):
    """
    Anything that can fetch relevant principles for a query.

    Implement this in Phase 3. The critic depends only on this interface, so any
    backend (Chroma, FAISS, keyword search...) will work as long as it has a
    `retrieve` method with this signature.
    """

    def retrieve(self, query: str, k: int = 4) -> list[Passage]:
        ...


class PrinciplesRetriever:
    """
    RAG retriever backed by the ChromaDB principle index.

    It satisfies the `Retriever` protocol, so the Phase 1 critic can use it with
    no changes: the critic calls `retrieve(query)` and feeds the returned
    passages into its prompt.

    Heavy dependencies (Chroma, the embedding model) are imported lazily inside
    `retrieve`, so importing this module - which the critic does for the
    `Retriever`/`Passage` types - stays cheap and dependency-free.
    """

    def __init__(
        self,
        principles_dir: str | None = None,
        persist_dir: str | None = None,
        collection_name: str | None = None,
    ):
        # Defaults come from config; args stay optional for tests / custom setups.
        from config import CHROMA_COLLECTION, CHROMA_DIR, PRINCIPLES_DIR

        self.principles_dir = principles_dir or PRINCIPLES_DIR
        self.persist_dir = persist_dir or CHROMA_DIR
        self.collection_name = collection_name or CHROMA_COLLECTION

    def retrieve(self, query: str, k: int = 5) -> list[Passage]:
        """
        Return the `k` most relevant principle chunks for `query`.

        `k` defaults to 5 - the number the critique pipeline feeds into the
        prompt. Raises RuntimeError (with how to fix it) if the index hasn't been
        built yet.
        """
        from archcritic.knowledge.chroma import get_collection
        from archcritic.knowledge.embeddings import embed_query

        query = query.strip()
        if not query:
            return []

        collection = get_collection(self.persist_dir, self.collection_name)
        result = collection.query(
            query_embeddings=[embed_query(query)],
            n_results=k,
        )

        # Chroma returns parallel lists wrapped one level deep (one per query).
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0] or [{}] * len(documents)
        distances = result.get("distances", [[]])[0] or [0.0] * len(documents)

        passages: list[Passage] = []
        for text, meta, distance in zip(documents, metadatas, distances):
            passages.append(
                Passage(
                    text=text,
                    source=(meta or {}).get("source", "unknown"),
                    # Cosine distance -> similarity in [0, 1] (higher = closer).
                    score=round(1.0 - float(distance), 4),
                )
            )
        return passages
