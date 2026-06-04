"""Phase 3: RAG over architecture principles + a dataset of past critiques.

Public surface. Note these imports are intentionally light - the retriever's
heavy backends (Chroma, embeddings) load lazily only when retrieval runs, so
importing this package never forces the RAG dependencies on Phase 1/2.
"""

from archcritic.knowledge.retriever import (
    Passage,
    PrinciplesRetriever,
    Retriever,
)
from archcritic.knowledge.store import IndexReport, build_index

__all__ = [
    "Passage",
    "Retriever",
    "PrinciplesRetriever",
    "build_index",
    "IndexReport",
]
