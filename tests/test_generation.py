"""
tests/test_generation.py
------------------------
Tests for the Phase 2 generators that need no API key: the demo samples, the
schemas/derived properties, and the prompt builders. These confirm the four
generators produce well-formed output and that the brief carries the critique
into every prompt.
"""

from archcritic.analysis.demo import sample_critique
from archcritic.generation.demo import (
    sample_design_narrative,
    sample_jury_defense,
    sample_keywords,
    sample_presentation,
)
from archcritic.generation.jury import JuryPoint
from archcritic.generation.keywords import ArchitecturalKeywords
from archcritic.generation.narrative import DesignNarrative
from archcritic.generation.presentation import Presentation
from archcritic.generation.prompts import (
    build_brief,
    build_jury_user,
    build_keywords_user,
    build_narrative_user,
    build_presentation_user,
)


# --- Demo samples are valid, well-formed objects -----------------------------
def test_sample_presentation_is_valid():
    pres = sample_presentation()
    assert isinstance(pres, Presentation)
    assert pres.thesis
    assert len(pres.sections) >= 3
    # estimated_minutes is derived from the script word count, so it must be > 0.
    assert pres.estimated_minutes > 0


def test_sample_jury_defense_is_valid():
    points = sample_jury_defense()
    assert points and all(isinstance(p, JuryPoint) for p in points)
    for p in points:
        assert p.topic and p.question and p.defense and p.follow_up


def test_sample_design_narrative_is_valid():
    narr = sample_design_narrative()
    assert isinstance(narr, DesignNarrative)
    assert narr.headline and narr.concept_statement and narr.narrative
    assert narr.design_moves


def test_sample_keywords_is_valid():
    kw = sample_keywords()
    assert isinstance(kw, ArchitecturalKeywords)
    assert kw.parti
    # Every register should contribute at least one term to the flattened list.
    assert kw.all_keywords()


def test_keywords_all_keywords_dedupes():
    kw = ArchitecturalKeywords(
        parti="test parti",
        conceptual=["threshold", "Threshold"],  # case-insensitive duplicate
        spatial=["procession"],
        tectonic=[],
        experiential=["procession"],  # duplicate across registers
    )
    assert kw.all_keywords() == ["threshold", "procession"]


# --- The brief carries the critique into the prompts -------------------------
def test_build_brief_includes_concept_and_categories():
    critique = sample_critique()
    brief = build_brief(critique, "Riverside Library", "permeable, timber")

    assert "Riverside Library" in brief
    assert "permeable, timber" in brief
    assert critique.concept_summary[:20] in brief
    # Every scored category should appear in the brief the model reasons over.
    for cat in critique.categories:
        assert cat.category in brief


def test_build_brief_handles_blank_inputs():
    critique = sample_critique()
    brief = build_brief(critique, "   ", "")
    assert "Untitled project" in brief
    assert "(none provided)" in brief


def test_user_prompt_builders_embed_the_brief():
    brief = "BRIEF-SENTINEL"
    for builder in (
        build_presentation_user,
        build_jury_user,
        build_narrative_user,
        build_keywords_user,
    ):
        assert brief in builder(brief)
