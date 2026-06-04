"""
generation/presentation.py
--------------------------
PHASE 2 - Presentation explanation generator.

Turns a critique into the spoken script a student delivers at the jury: a clear
design thesis followed by the canonical crit arc (site -> parti -> programme ->
spatial sequence -> materiality -> closing), with a delivery note per section.

It is a text task, so it reuses the shared generation engine in core/llm.py.
"""

from pydantic import BaseModel, Field

from archcritic.core.llm import generate_structured
from archcritic.core.schemas import Critique
from archcritic.generation.prompts import (
    PRESENTATION_SYSTEM,
    build_brief,
    build_presentation_user,
)

# A speaker covers roughly this many words per minute at an unhurried jury pace.
_WORDS_PER_MINUTE = 130


class PresentationSection(BaseModel):
    """One beat of the spoken presentation (e.g. the parti, the spatial sequence)."""

    heading: str = Field(
        description="Short label for this beat of the talk, e.g. 'The parti'."
    )
    script: str = Field(
        description="What the student says out loud, first person, spoken prose."
    )
    delivery_note: str = Field(
        description="A short staging cue: what to point to, emphasise, or pause on."
    )


class Presentation(BaseModel):
    """A complete jury presentation script built from a critique."""

    thesis: str = Field(
        description="The one-line design thesis (parti) the talk argues for."
    )
    sections: list[PresentationSection] = Field(
        description="The ordered beats of the spoken presentation."
    )

    @property
    def estimated_minutes(self) -> float:
        """Rough spoken length, so the student can pace the talk to the time slot."""
        words = sum(len(s.script.split()) for s in self.sections)
        return round(words / _WORDS_PER_MINUTE, 1)


def generate_presentation(
    api_key: str,
    critique: Critique,
    project_title: str,
    keywords: str,
) -> Presentation:
    """Build a spoken jury presentation script from a critique."""
    brief = build_brief(critique, project_title, keywords)
    return generate_structured(
        api_key,
        PRESENTATION_SYSTEM,
        build_presentation_user(brief),
        Presentation,
    )
