"""
tests/test_schemas.py
---------------------
Tiny tests for the shared data model. Run with:

    pytest

These don't call the AI - they just confirm the Critique model behaves (e.g. the
overall score is the average of the category scores).
"""

from archcritic.core.schemas import CategoryCritique, Critique


def _make_category(name: str, score: int) -> CategoryCritique:
    return CategoryCritique(
        category=name,
        observation="x",
        strengths=["s"],
        weaknesses=["w"],
        suggestions=["g"],
        score=score,
    )


def test_overall_score_is_average_of_categories():
    critique = Critique(
        concept_summary="A test project.",
        categories=[_make_category("Concept", 8), _make_category("Massing", 6)],
        overall_strengths=["strong concept"],
        overall_weaknesses=["weak massing"],
    )
    assert critique.overall_score == 7.0


def test_overall_score_handles_no_categories():
    critique = Critique(
        concept_summary="Empty.",
        categories=[],
        overall_strengths=[],
        overall_weaknesses=[],
    )
    assert critique.overall_score == 0.0
