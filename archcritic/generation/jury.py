"""
generation/jury.py
------------------
PHASE 2 - Jury defence generator.

Anticipates the toughest questions a jury might ask - mined from the critique's
weak and unresolved areas - and prepares strong, honest, design-grounded answers
so the student walks in ready instead of cornered.

Text task; routes through the shared generation engine in core/llm.py.
"""

from pydantic import BaseModel, Field

from archcritic.core.llm import generate_structured
from archcritic.core.schemas import Critique
from archcritic.generation.prompts import JURY_SYSTEM, build_brief, build_jury_user


class JuryPoint(BaseModel):
    """One likely jury question with a strong suggested defence."""

    topic: str = Field(
        description="The design area the question targets, e.g. 'Circulation'."
    )
    question: str = Field(description="A challenging question the jury might ask.")
    defense: str = Field(
        description="A confident, design-grounded answer that owns the trade-off."
    )
    follow_up: str = Field(
        description="The likely follow-up question, so the student is not caught off guard."
    )


class JuryDefense(BaseModel):
    """The full set of anticipated jury questions and defences."""

    points: list[JuryPoint] = Field(
        description="Likely questions and defences, hardest first."
    )


def generate_jury_defense(
    api_key: str,
    critique: Critique,
    project_title: str,
    keywords: str,
) -> list[JuryPoint]:
    """Anticipate likely jury questions and return strong defences, hardest first."""
    brief = build_brief(critique, project_title, keywords)
    result = generate_structured(
        api_key,
        JURY_SYSTEM,
        build_jury_user(brief),
        JuryDefense,
    )
    return result.points
