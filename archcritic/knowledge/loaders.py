"""
knowledge/loaders.py
--------------------
PHASE 3 - Read principle documents from data/principles/ into plain text.

Supports PDFs (architecture theory is often distributed as PDF) plus .txt and
.md. Each file becomes one `Document`; chunking happens later in chunking.py.

`pypdf` is imported lazily inside the PDF branch so plain-text knowledge bases
work even if pypdf isn't installed.
"""

import os
from dataclasses import dataclass

# File types we know how to read. Anything else in the folder is skipped.
SUPPORTED_EXTENSIONS = (".pdf", ".txt", ".md", ".markdown")


@dataclass
class Document:
    """One source document loaded from the principles folder."""

    source: str  # filename, used as the citation on retrieved passages
    text: str    # full extracted text


def _read_pdf(path: str) -> str:
    """Extract text from a PDF, page by page. Requires pypdf."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ImportError(
            "Reading PDFs needs 'pypdf'. Install it with: pip install pypdf"
        ) from exc

    reader = PdfReader(path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n".join(pages)


def _read_text(path: str) -> str:
    """Read a UTF-8 text/markdown file."""
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def load_document(path: str) -> Document:
    """Load a single file into a `Document` based on its extension."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        text = _read_pdf(path)
    else:
        text = _read_text(path)
    return Document(source=os.path.basename(path), text=text)


def load_documents(principles_dir: str) -> list[Document]:
    """
    Load every supported document in `principles_dir`.

    Files with no extractable text (e.g. a scanned, image-only PDF) are skipped
    with their source still reported by the caller, so the index never contains
    empty chunks. Returns an empty list if the folder is missing or empty.
    """
    if not os.path.isdir(principles_dir):
        return []

    documents: list[Document] = []
    for name in sorted(os.listdir(principles_dir)):
        path = os.path.join(principles_dir, name)
        if not os.path.isfile(path):
            continue
        if os.path.splitext(name)[1].lower() not in SUPPORTED_EXTENSIONS:
            continue
        doc = load_document(path)
        if doc.text.strip():
            documents.append(doc)
    return documents
