"""
core/schemas.py
---------------
The data shapes used across the whole app.

Defining these once (instead of passing loose dictionaries around) means every
phase - analysis, generation, RAG - agrees on what a critique looks like. The
UI, the AI response, and the tests all share these types.
"""

from pydantic import BaseModel, Field


class CategoryCritique(BaseModel):
    """The AI's assessment of a single architectural category (e.g. Circulation)."""

    category: str = Field(
        description="Name of the architectural category being assessed."
    )
    observation: str = Field(
        description="Objective description of what is visible for this category."
    )
    strengths: list[str] = Field(
        description="Specific strengths for this category."
    )
    weaknesses: list[str] = Field(
        description="Specific weaknesses or risks for this category."
    )
    suggestions: list[str] = Field(
        description="Concrete, actionable suggestions to improve this category."
    )
    score: int = Field(
        description="Quality score from 0 (poor) to 10 (excellent) for this category."
    )


class Critique(BaseModel):
    """The full critique of one project: a summary plus a per-category breakdown."""

    concept_summary: str = Field(
        description="One-paragraph reading of the overall design concept."
    )
    categories: list[CategoryCritique] = Field(
        description="One entry per requested architectural category."
    )
    overall_strengths: list[str] = Field(
        description="The 2-3 biggest strengths across the whole project."
    )
    overall_weaknesses: list[str] = Field(
        description="The 2-3 most important things to fix across the whole project."
    )

    @property
    def overall_score(self) -> float:
        """
        Average of the category scores, on a 0-10 scale.

        We compute this ourselves rather than asking the model for it, so the
        overall number is always consistent with the per-category scores shown.
        """
        if not self.categories:
            return 0.0
        return round(sum(c.score for c in self.categories) / len(self.categories), 1)
