"""
generation/concept_images.py
----------------------------
PHASE 2 (scaffolded).

Goal: from the original image + the critique, generate improved architectural
concept images that visualise the suggestions.

Note: the Claude vision model *reads* images but does not *create* them, so this
phase will call a dedicated image-generation model/service. This stub fixes the
interface (inputs/outputs) so the UI can be built against it now.
"""

from archcritic.core.schemas import Critique


def generate_concept_images(
    api_key: str,
    image_bytes: bytes,
    media_type: str,
    critique: Critique,
    n_images: int = 2,
) -> list[bytes]:
    """Return a list of generated image byte-strings. Implemented in Phase 2."""
    raise NotImplementedError(
        "Phase 2: connect an image-generation model and return improved concepts."
    )
