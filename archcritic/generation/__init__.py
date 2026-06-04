"""Phase 2: generate improved concepts, presentations, and jury defence points.

Public surface for the four generators so callers can import from one place:

    from archcritic.generation import generate_presentation, ArchitecturalKeywords
"""

from archcritic.generation.jury import (
    JuryDefense,
    JuryPoint,
    generate_jury_defense,
)
from archcritic.generation.keywords import (
    ArchitecturalKeywords,
    extract_architectural_keywords,
)
from archcritic.generation.narrative import (
    DesignNarrative,
    generate_design_narrative,
)
from archcritic.generation.presentation import (
    Presentation,
    PresentationSection,
    generate_presentation,
)

__all__ = [
    # Presentation explanation
    "Presentation",
    "PresentationSection",
    "generate_presentation",
    # Jury defence
    "JuryPoint",
    "JuryDefense",
    "generate_jury_defense",
    # Design narrative
    "DesignNarrative",
    "generate_design_narrative",
    # Architectural keywords
    "ArchitecturalKeywords",
    "extract_architectural_keywords",
]
