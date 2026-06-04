"""
generation/keywords.py
----------------------
PHASE 2 - Architectural keywords extraction.

Distils a critique into the architectural terms that define the project - the
words a student puts on a panel, in a portfolio index, or in a project abstract.
Terms are sorted by register (conceptual, spatial, tectonic, experiential) and
the central organising idea is named as a single parti phrase.

Text task; routes through the shared generation engine in core/llm.py.
"""

from pydantic import BaseModel, Field

from archcritic.core.llm import generate_structured
from archcritic.core.schemas import Critique
from archcritic.generation.prompts import (
    KEYWORDS_SYSTEM,
    build_brief,
    build_keywords_user,
)


class ArchitecturalKeywords(BaseModel):
    """The architectural vocabulary that defines a project, grouped by register."""

    parti: str = Field(
        description="The central organising idea, named in a single sharp phrase."
    )
    conceptual: list[str] = Field(
        description="Conceptual terms - the ideas, e.g. 'threshold', 'permeability'."
    )
    spatial: list[str] = Field(
        description="Spatial terms - organisation and movement, e.g. 'procession'."
    )
    tectonic: list[str] = Field(
        description="Tectonic terms - material and structure, e.g. 'timber frame'."
    )
    experiential: list[str] = Field(
        description="Experiential terms - light, atmosphere, phenomenology."
    )

    def all_keywords(self) -> list[str]:
        """Every keyword across all registers, in reading order, de-duplicated."""
        seen: set[str] = set()
        ordered: list[str] = []
        for group in (self.conceptual, self.spatial, self.tectonic, self.experiential):
            for term in group:
                key = term.lower()
                if key not in seen:
                    seen.add(key)
                    ordered.append(term)
        return ordered


def extract_architectural_keywords(
    api_key: str,
    critique: Critique,
    project_title: str,
    keywords: str,
) -> ArchitecturalKeywords:
    """Extract the architectural keywords that define the critiqued project."""
    brief = build_brief(critique, project_title, keywords)
    return generate_structured(
        api_key,
        KEYWORDS_SYSTEM,
        build_keywords_user(brief),
        ArchitecturalKeywords,
    )
