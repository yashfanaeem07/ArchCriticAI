"""
archcritic
==========
The AI Studio Critic package.

Layout:
- core/        Shared building blocks (data models, image + LLM helpers).
- analysis/    Phase 1: analyse an image and critique it by category.
- generation/  Phase 2: generate improved concepts, presentations, jury points.
- knowledge/   Phase 3: RAG over architecture principles + a critique dataset.
- ui/          Reusable Streamlit rendering helpers.
"""

__version__ = "0.2.0"
