"""
knowledge/embeddings.py
-----------------------
PHASE 3 - Turn text into vectors with a local Sentence-Transformers model.

Both sides of RAG use this one embedder so chunks and queries land in the same
vector space: indexing (store.py) embeds the chunks, retrieval (retriever.py)
embeds the query. The model is loaded once and cached, because loading it is the
slow part - calling it is cheap.

Runs locally (no API key, no per-call cost). To switch models, change
EMBEDDING_MODEL in config.py.
"""

from functools import lru_cache

from config import EMBEDDING_MODEL


@lru_cache(maxsize=1)
def _get_model(model_name: str):
    """Load (once) and cache the Sentence-Transformers model."""
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise ImportError(
            "Embeddings need 'sentence-transformers'. Install it with: "
            "pip install sentence-transformers"
        ) from exc
    return SentenceTransformer(model_name)


def embed_texts(texts: list[str], model_name: str = EMBEDDING_MODEL) -> list[list[float]]:
    """
    Embed a batch of texts into a list of float vectors.

    Vectors are L2-normalised so cosine similarity reduces to a dot product,
    which is what the Chroma collection is configured for.
    """
    if not texts:
        return []
    model = _get_model(model_name)
    vectors = model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
    )
    return vectors.tolist()


def embed_query(query: str, model_name: str = EMBEDDING_MODEL) -> list[float]:
    """Embed a single query string into one vector."""
    return embed_texts([query], model_name)[0]
