"""
analysis/categories.py
----------------------
The architectural categories the AI scores, defined in ONE place.

The prompt text, the AI's expected output, and the UI all read from this list.
To add or rename a category, edit it here - nothing else needs to change.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Category:
    """A single thing the critic evaluates."""

    name: str
    description: str  # what this category means - guides the AI's focus


# The categories from the project brief. Order = order shown to the AI and user.
ARCHITECTURAL_CATEGORIES: list[Category] = [
    Category(
        "Concept",
        "The core design idea (parti) and how clearly it reads in the drawing/model.",
    ),
    Category(
        "Spatial Organization",
        "How interior and exterior spaces are arranged and relate to one another.",
    ),
    Category(
        "Hierarchy",
        "Whether important spaces/elements are emphasised and the design has a clear order.",
    ),
    Category(
        "Circulation",
        "Movement through the project: entries, paths, flow, and connections between spaces.",
    ),
    Category(
        "Transparency",
        "Openness, light, and visual permeability - the balance of solid and void.",
    ),
    Category(
        "Massing",
        "The overall three-dimensional form: proportion, composition, and how volumes meet.",
    ),
]


def categories_as_prompt_text() -> str:
    """Format the categories as a bulleted list to drop into the prompt."""
    lines = [f"- {c.name}: {c.description}" for c in ARCHITECTURAL_CATEGORIES]
    return "\n".join(lines)


def category_names() -> list[str]:
    """Just the names, e.g. for validation or display."""
    return [c.name for c in ARCHITECTURAL_CATEGORIES]
