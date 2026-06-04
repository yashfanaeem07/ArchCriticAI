"""
generation/narrative.py
-----------------------
PHASE 2 - Design narrative generator.

Turns a critique into the project's written design narrative: the polished
statement that sits on the presentation panel or in the portfolio. It tells the
story of the design - site reading, concept genesis, the parti, the spatial and
material moves that follow, and how the project resolves.

Text task; routes through the shared generation engine in core/llm.py.
"""

from pydantic import BaseModel, Field

from archcritic.core.llm import generate_structured
from archcritic.core.schemas import Critique
from archcritic.generation.prompts import (
    NARRATIVE_SYSTEM,
    build_brief,
    build_narrative_user,
)


class DesignNarrative(BaseModel):
    """A written design narrative / project statement built from a critique."""

    headline: str = Field(
        description="An evocative title or tagline that captures the project."
    )
    concept_statement: str = Field(
        description="The distilled parti in one or two sentences."
    )
    narrative: str = Field(
        description="The flowing multi-paragraph design narrative in third person."
    )
    design_moves: list[str] = Field(
        description="The key architectural moves that carry the concept."
    )


def generate_design_narrative(
    api_key: str,
    critique: Critique,
    project_title: str,
    keywords: str,
) -> DesignNarrative:
    """Write the project's design narrative from a critique."""
    brief = build_brief(critique, project_title, keywords)
    return generate_structured(
        api_key,
        NARRATIVE_SYSTEM,
        build_narrative_user(brief),
        DesignNarrative,
    )
