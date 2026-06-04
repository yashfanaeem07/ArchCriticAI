"""
rag_embed.py  (repo-root convenience entry point)
-------------------------------------------------
Build the Phase-3 RAG knowledge base from data/principles/.

This is a thin shim that delegates to the real implementation in
`archcritic.core.rag_embed` (backed by `archcritic.knowledge.store.build_index`),
which reads .md / .txt / .pdf files, chunks them, embeds them with the configured
Sentence-Transformers model, and PERSISTS them to the ChromaDB index at CHROMA_DIR.

It exists so the command documented in data/principles/README.md works as-is:

    python rag_embed.py            # rebuild the index
    python rag_embed.py --show     # report the current index status

These are equivalent to `python -m archcritic.core.rag_embed`.
"""

import os
import sys

# Make `config` and `archcritic` importable when run from the repo root.
_ROOT = os.path.abspath(os.path.dirname(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from config import CHROMA_COLLECTION, CHROMA_DIR, PRINCIPLES_DIR
from archcritic.core.rag_embed import main


def embed_pdfs(pdf_folder=PRINCIPLES_DIR, persist_dir=CHROMA_DIR,
               collection=CHROMA_COLLECTION):
    """
    Build/refresh the persistent RAG index from a folder of principle documents.

    Kept for backward compatibility with the Streamlit "Build / refresh knowledge
    base" button (app.py). Despite the legacy name it indexes .md / .txt / .pdf
    (not only PDFs) and PERSISTS to ChromaDB via the real builder.
    """
    from archcritic.knowledge.store import build_index

    return build_index(pdf_folder, persist_dir, collection)


if __name__ == "__main__":
    main()
