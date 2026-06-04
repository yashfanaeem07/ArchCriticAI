"""
core/rag_embed.py
-----------------
PHASE 3 - Build the RAG knowledge base from the principle documents.

Run it directly whenever you add, edit, or remove files in data/principles/:

    python -m archcritic.core.rag_embed
"""

import argparse

from config import CHROMA_COLLECTION, CHROMA_DIR, PRINCIPLES_DIR
from archcritic.knowledge.store import build_index


def _show_status(persist_dir: str, collection_name: str) -> None:
    """Print how many chunks the collection currently holds, if it exists."""
    from archcritic.knowledge.chroma import get_collection

    try:
        collection = get_collection(persist_dir, collection_name)
    except RuntimeError as error:
        print(error)
        return
    print(f"Collection '{collection_name}' holds {collection.count()} chunks.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the architecture RAG index.")
    parser.add_argument(
        "--dir",
        default=PRINCIPLES_DIR,
        help="Folder of principle documents (.pdf/.txt/.md). Default: data/principles.",
    )
    parser.add_argument(
        "--persist",
        default=CHROMA_DIR,
        help="Where to persist the Chroma index. Default: data/chroma.",
    )
    parser.add_argument(
        "--collection",
        default=CHROMA_COLLECTION,
        help=f"Chroma collection name. Default: {CHROMA_COLLECTION}.",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Only report the current index status; don't rebuild.",
    )
    args = parser.parse_args()

    if args.show:
        _show_status(args.persist, args.collection)
        return

    print(f"Indexing documents in: {args.dir}")
    try:
        report = build_index(args.dir, args.persist, args.collection)
    except FileNotFoundError as error:
        raise SystemExit(str(error))

    print(
        f"Done. Indexed {report.chunks} chunks from {report.documents} "
        f"document(s) into collection '{report.collection}' at {report.persist_dir}."
    )


if __name__ == "__main__":
    main()
