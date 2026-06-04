"""
knowledge/store.py
------------------
PHASE 3 - Build the knowledge base the AI critiques *with*.

Pipeline:
  1. Load design-theory docs from data/principles/      (loaders.py)
  2. Split each into ~500-word chunks                    (chunking.py)
  3. Embed every chunk                                   (embeddings.py)
  4. Upsert the vectors into the Chroma collection       (chroma.py)

`build_index` is what the `rag_embed.py` helper script calls. `save_critique`
remains a stub for the second Phase 3 job (growing a dataset of past critiques);
it is not part of the RAG pipeline.
"""

import json
import os
import re
from dataclasses import dataclass

from config import CHROMA_COLLECTION, CHROMA_DIR, CRITIQUES_DIR, PRINCIPLES_DIR
from archcritic.core.schemas import Critique
from archcritic.knowledge.chroma import get_or_create_collection
from archcritic.knowledge.chunking import chunk_text
from archcritic.knowledge.embeddings import embed_texts
from archcritic.knowledge.loaders import load_documents


@dataclass
class IndexReport:
    """A small summary of an indexing run, for the CLI and the UI to display."""

    documents: int
    chunks: int
    collection: str
    persist_dir: str


def build_index(
    principles_dir: str = PRINCIPLES_DIR,
    persist_dir: str = CHROMA_DIR,
    collection_name: str = CHROMA_COLLECTION,
) -> IndexReport:
    """
    (Re)build the principle index from scratch and return a summary.

    The collection is reset first so re-running after editing or removing a
    document never leaves stale chunks behind - the index always mirrors the
    current contents of `principles_dir`.

    Raises FileNotFoundError if the folder has no readable documents, so the
    caller can tell the user to add some.
    """
    documents = load_documents(principles_dir)
    if not documents:
        raise FileNotFoundError(
            f"No readable principle documents found in '{principles_dir}'. "
            "Add .pdf, .txt, or .md files and try again."
        )

    # Chunk every document, carrying its source through for citations.
    chunks: list[str] = []
    sources: list[str] = []
    for doc in documents:
        for chunk in chunk_text(doc.text):
            chunks.append(chunk)
            sources.append(doc.source)

    # Reset the collection so the index exactly mirrors the current folder.
    collection = get_or_create_collection(persist_dir, collection_name)
    existing = collection.get()["ids"]
    if existing:
        collection.delete(ids=existing)

    embeddings = embed_texts(chunks)
    collection.add(
        ids=[f"chunk-{i}" for i in range(len(chunks))],
        documents=chunks,
        embeddings=embeddings,
        metadatas=[{"source": s} for s in sources],
    )

    return IndexReport(
        documents=len(documents),
        chunks=len(chunks),
        collection=collection_name,
        persist_dir=persist_dir,
    )


def _slugify(text: str) -> str:
    """Turn a project title into a safe, lower-case filename stem."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "critique"


def save_critique(
    critique: Critique,
    project_title: str,
    critiques_dir: str = CRITIQUES_DIR,
    keywords: str = "",
) -> str:
    """
    Save one critique as JSON and return the saved file path.

    The file is the Phase 2 hand-off: it carries the validated Critique plus the
    project title and keywords the generators need, so Phase 2 can rebuild it with
    `Critique.model_validate(payload["critique"])`. Critique is a Pydantic model,
    so `model_dump()` already gives us clean, round-trippable JSON.
    """
    os.makedirs(critiques_dir, exist_ok=True)
    path = os.path.join(critiques_dir, f"{_slugify(project_title)}.json")
    payload = {
        "schema_version": 1,
        "project_title": project_title,
        "keywords": keywords,
        "overall_score": critique.overall_score,
        "critique": critique.model_dump(),
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
    return path
