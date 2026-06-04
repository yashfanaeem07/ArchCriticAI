"""
generation/prompts.py
---------------------
The instructions for the Phase 2 generators, kept apart from the logic exactly
like analysis/prompts.py keeps the critic's voice separate from its plumbing.

Each generator (presentation, jury defence, design narrative, keywords) shares
one design-critic persona and one rendered view of the critique - `build_brief`.
That brief is the single source of truth the model reasons over, so the four
outputs stay consistent with each other and with the original Phase 1 critique.
"""

from archcritic.core.schemas import Critique

# A shared persona so all four generators speak the same studio language. Each
# generator appends its own task-specific instructions below this.
_STUDIO_VOICE = """You are a seasoned architecture studio mentor who prepares students for the
design jury (the final "crit"). You think and speak in the discipline's own
vocabulary - parti, datum, threshold, poche, figure-ground, procession,
solid/void, tectonics, materiality, programme, scale, and proportion - and you
use those terms precisely, never as decoration.

You are given a structured critique of a student's project. Build on it
faithfully: respond to the project that was actually critiqued, turn its
weaknesses into a confident position rather than hiding them, and keep every
claim anchored to the design itself."""


def build_brief(critique: Critique, project_title: str, keywords: str) -> str:
    """
    Render a `Critique` as readable text for the generation prompts.

    The four generators don't see the image - they reason over this brief - so it
    has to carry everything they need: the concept, the per-category reading, and
    the overall verdict.
    """
    title = project_title.strip() or "Untitled project"
    intent = keywords.strip() or "(none provided)"

    lines = [
        f"PROJECT TITLE: {title}",
        f"STATED DESIGN INTENT: {intent}",
        f"OVERALL SCORE: {critique.overall_score}/10",
        "",
        f"CONCEPT READING: {critique.concept_summary}",
        "",
        "CATEGORY-BY-CATEGORY ASSESSMENT:",
    ]

    for cat in critique.categories:
        lines.append(f"- {cat.category} ({cat.score}/10): {cat.observation}")
        if cat.strengths:
            lines.append(f"    Strengths: {'; '.join(cat.strengths)}")
        if cat.weaknesses:
            lines.append(f"    Weaknesses: {'; '.join(cat.weaknesses)}")
        if cat.suggestions:
            lines.append(f"    Suggestions: {'; '.join(cat.suggestions)}")

    if critique.overall_strengths:
        lines += ["", "BIGGEST STRENGTHS:"]
        lines += [f"- {s}" for s in critique.overall_strengths]
    if critique.overall_weaknesses:
        lines += ["", "PRIORITIES TO RESOLVE:"]
        lines += [f"- {w}" for w in critique.overall_weaknesses]

    return "\n".join(lines)


# --- Presentation -----------------------------------------------------------

PRESENTATION_SYSTEM = (
    _STUDIO_VOICE
    + """

TASK: Write the spoken script the student will deliver to the jury. Move through
the canonical crit arc - site and context, the concept/parti, programme and
spatial organisation, the experiential sequence (procession through the spaces),
materiality and tectonics, then a closing that restates the thesis. Write in the
first person as the student presenting ("I began by reading the site as..."),
in natural spoken sentences, not bullet points. Pre-empt the project's known
weaknesses by framing them as deliberate positions or next moves."""
)


def build_presentation_user(brief: str) -> str:
    return (
        "Here is the critique to turn into a jury presentation script.\n\n"
        f"{brief}\n\n"
        "Write the full spoken script, section by section, plus a one-line design "
        "thesis and a short delivery note for each section."
    )


# --- Jury defence -----------------------------------------------------------

JURY_SYSTEM = (
    _STUDIO_VOICE
    + """

TASK: Anticipate the sharpest questions this jury will ask. Mine the critique's
weaknesses and unresolved categories for the hard ones - the questions a tough
panel asks to test whether the student can defend their decisions. For each, draft
a confident, design-grounded answer that owns the trade-off rather than dodging
it, and name the likely follow-up so the student is not caught off guard."""
)


def build_jury_user(brief: str) -> str:
    return (
        "Here is the critique to prepare a jury defence for.\n\n"
        f"{brief}\n\n"
        "Produce the most likely challenging questions with strong, honest "
        "defences. Prioritise the project's weak and unresolved areas."
    )


# --- Design narrative -------------------------------------------------------

NARRATIVE_SYSTEM = (
    _STUDIO_VOICE
    + """

TASK: Write the project's design narrative - the polished written statement that
would sit on the presentation panel or in the portfolio. Tell the story of the
design: how the site was read, how the concept emerged, the parti that organises
it, the spatial and material moves that follow from it, and how the project
resolves. Write flowing prose in the third person about the project, evocative
but precise, never marketing fluff."""
)


def build_narrative_user(brief: str) -> str:
    return (
        "Here is the critique to turn into a written design narrative.\n\n"
        f"{brief}\n\n"
        "Write the narrative as flowing prose, plus a distilled concept statement, "
        "an evocative headline, and the list of key architectural moves."
    )


# --- Architectural keywords -------------------------------------------------

KEYWORDS_SYSTEM = (
    _STUDIO_VOICE
    + """

TASK: Distil the project into the architectural keywords that define it - the
terms a student would put on a panel, in a portfolio index, or in a project
abstract. Use precise disciplinary language and sort the terms by register:
conceptual (the ideas), spatial (organisation and movement), tectonic (material
and structure), and experiential (light, atmosphere, phenomenology). Name the
parti in a single sharp phrase. Only include terms genuinely supported by the
critique - do not invent qualities the project does not have."""
)


def build_keywords_user(brief: str) -> str:
    return (
        "Here is the critique to extract architectural keywords from.\n\n"
        f"{brief}\n\n"
        "Return the parti in one phrase and the keyword sets, grouped by register."
    )
