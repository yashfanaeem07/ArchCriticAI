"""
config.py
---------
Central place for settings. Change the model or limits here once, instead of
hunting through the code. Keeping config separate is what lets the project grow
without becoming messy.
"""

import os

from dotenv import load_dotenv

load_dotenv()  # Load .env if present so ANTHROPIC_API_KEY etc. are available.

# --- Models --------------------------------------------------------------
ANALYSIS_MODEL = "claude-opus-4-8"        # Phase 1 vision critique.
GENERATION_MODEL = "claude-opus-4-8"      # Phase 2 text generators.
CONCEPT_IMAGE_MODEL = "TBD-phase-2"       # Phase 2 image generation (scaffolded).
MAX_TOKENS = 4000

# --- Paths ---------------------------------------------------------------
PRINCIPLES_DIR = os.path.join(os.path.dirname(__file__), "data", "principles")
CRITIQUES_DIR = os.path.join(os.path.dirname(__file__), "data", "critiques")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "data", "chroma")
CHROMA_COLLECTION = "architecture_principles"

# --- RAG / embeddings ----------------------------------------------------
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHUNK_WORDS = 500
CHUNK_OVERLAP = 50
RETRIEVAL_TOP_K = 5


def get_api_key() -> str:
    """Return the Anthropic API key from the environment, or None if missing."""
    return os.getenv("ANTHROPIC_API_KEY")
