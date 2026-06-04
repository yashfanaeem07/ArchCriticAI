"""
analysis/prompts.py
-------------------
The instructions we send to the AI. Kept separate from the logic so the
"personality" of the critic is easy to read and refine.

Note the `principles` argument in build_system_prompt: this is the hook for
Phase 3 (RAG). When we later retrieve relevant architecture theory, we pass it
in here and it becomes part of the critic's knowledge - no other code changes.
"""

from archcritic.analysis.categories import categories_as_prompt_text

_BASE_SYSTEM_PROMPT = """You are an experienced architecture studio critic (a "design crit" reviewer)
with a strong grounding in architectural theory, spatial design, and visual
communication.

You review student and early-career architectural sketches, plans, model photos,
and renders. Be honest, specific, and constructive - like a supportive studio
tutor at a design jury:
- Tie every observation to something you can actually see in the image.
- Avoid vague praise. Each strength, weakness, and suggestion must be concrete.
- Frame weaknesses as opportunities to develop the project.

You assess the project across these categories:
{categories}

For EACH category, give an observation, strengths, weaknesses, suggestions, and a
score from 0 to 10. Then give an overall concept summary and the project's biggest
strengths and weaknesses. Always reply in the exact structured format requested."""

_PRINCIPLES_SECTION = """

Use the following established architecture principles and design theory to ground
your critique in real architectural thinking rather than generic feedback. Refer
to these ideas where relevant:
---
{principles}
---"""


def build_system_prompt(principles: str | None = None) -> str:
    """
    Build the critic's system prompt.

    If `principles` is provided (Phase 3 RAG), it is appended so the critique is
    grounded in real design theory. If None, the base critic prompt is used.
    """
    prompt = _BASE_SYSTEM_PROMPT.format(categories=categories_as_prompt_text())
    if principles:
        prompt += _PRINCIPLES_SECTION.format(principles=principles.strip())
    return prompt


def build_user_prompt(project_title: str, keywords: str) -> str:
    """The text part of the user's message (the image is attached separately)."""
    title = project_title.strip() or "Untitled project"
    intent = keywords.strip() or "(none provided)"
    return f"""Please critique this architecture project.

Project title: {title}
Design keywords / intent: {intent}

Analyse the attached image and give your full studio critique, scoring each
category separately."""
