"""
knowledge/chunking.py
---------------------
PHASE 3 - Split a document into ~500-word chunks for embedding.

Retrieval works on chunks, not whole files: a chunk should be small enough to be
about one idea, but large enough to carry context. We split on words (not
characters) so the size maps to "roughly N words", and we overlap consecutive
chunks slightly so an idea straddling a boundary still lands whole in at least
one chunk.

Pure Python, no heavy dependencies - so it is trivially unit-testable.
"""

from config import CHUNK_OVERLAP, CHUNK_WORDS


def chunk_text(
    text: str,
    words_per_chunk: int = CHUNK_WORDS,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """
    Split `text` into chunks of about `words_per_chunk` words.

    Consecutive chunks share `overlap` words so context isn't lost at the seams.
    Returns an empty list for blank input. Raises ValueError on nonsensical
    parameters (overlap must be smaller than the chunk size, both non-negative).
    """
    if words_per_chunk <= 0:
        raise ValueError("words_per_chunk must be positive")
    if overlap < 0 or overlap >= words_per_chunk:
        raise ValueError("overlap must be >= 0 and < words_per_chunk")

    words = text.split()
    if not words:
        return []

    # Each step advances by (chunk - overlap) words, so chunks overlap by `overlap`.
    stride = words_per_chunk - overlap
    chunks: list[str] = []
    for start in range(0, len(words), stride):
        chunk_words = words[start : start + words_per_chunk]
        chunks.append(" ".join(chunk_words))
        # Stop once this chunk reached the end, so we don't emit a tiny tail that
        # is fully contained in the overlap of the previous chunk.
        if start + words_per_chunk >= len(words):
            break
    return chunks
