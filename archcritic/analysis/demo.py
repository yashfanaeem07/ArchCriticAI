"""
analysis/demo.py
----------------
A hand-written sample critique used by "Demo mode".

This lets anyone explore the full UI - scores, charts, category cards - without
an API key, without spending money, and without needing model access. It returns
the exact same `Critique` type the real AI produces, so the rest of the app can't
tell the difference.

The sample describes a fictional "Riverside Community Library" so the output reads
like a real studio crit.
"""

from archcritic.core.schemas import CategoryCritique, Critique


def sample_critique() -> Critique:
    """Return a realistic, fixed critique for demo/testing (no API call)."""
    return Critique(
        concept_summary=(
            "The project reads as a 'permeable threshold' - a library that "
            "dissolves the edge between street and river. A continuous public "
            "ground floor slips beneath two stacked timber reading volumes, "
            "pulling pedestrians through the site toward the water. The parti is "
            "legible and ambitious, though the upper massing competes with the "
            "clarity of that ground-level idea."
        ),
        categories=[
            CategoryCritique(
                category="Concept",
                observation=(
                    "A single strong idea - a public route threading the building "
                    "to the river - drives the plan and section."
                ),
                strengths=[
                    "The 'threshold' concept is clear and repeated at multiple scales.",
                    "Program supports the idea: public functions sit on the route.",
                ],
                weaknesses=[
                    "The concept weakens at the upper floors, which feel additive.",
                ],
                suggestions=[
                    "Carry the threshold idea vertically - e.g. a stepped void that "
                    "links the route to the upper reading rooms.",
                ],
                score=8,
            ),
            CategoryCritique(
                category="Spatial Organization",
                observation=(
                    "Public, semi-public, and quiet zones are stacked vertically, "
                    "with the noisiest uses at grade."
                ),
                strengths=[
                    "Logical noise gradient from active ground floor to quiet top.",
                    "Service cores are consolidated, freeing open reading floors.",
                ],
                weaknesses=[
                    "The transition between public and study zones is abrupt.",
                    "No clear in-between 'lounge' space to mediate the two.",
                ],
                suggestions=[
                    "Insert a buffer level (cafe, exhibition) between street and study.",
                ],
                score=7,
            ),
            CategoryCritique(
                category="Hierarchy",
                observation=(
                    "The entry and main reading room are emphasised, but secondary "
                    "spaces read at a similar weight."
                ),
                strengths=[
                    "The double-height entry clearly signals the main public space.",
                ],
                weaknesses=[
                    "Secondary rooms compete visually with primary ones.",
                    "No strong vertical landmark to orient visitors.",
                ],
                suggestions=[
                    "Differentiate primary vs. secondary spaces through ceiling "
                    "height, light, or material change.",
                ],
                score=6,
            ),
            CategoryCritique(
                category="Circulation",
                observation=(
                    "A single primary stair anchors movement; the public route is "
                    "generous but the vertical circulation is tight."
                ),
                strengths=[
                    "The ground-level route is intuitive and well-lit.",
                ],
                weaknesses=[
                    "One vertical core may bottleneck at peak use.",
                    "The path to upper floors is hidden from the entry.",
                ],
                suggestions=[
                    "Expose the main stair near the entry so vertical movement is "
                    "immediately legible.",
                    "Add a secondary stair for resilience and shorter travel distances.",
                ],
                score=5,
            ),
            CategoryCritique(
                category="Transparency",
                observation=(
                    "The ground floor is highly glazed toward the river; upper "
                    "volumes are more solid timber."
                ),
                strengths=[
                    "Strong solid/void contrast expresses the public vs. quiet idea.",
                    "River-facing glazing frames the key view convincingly.",
                ],
                weaknesses=[
                    "Street-facing elevation risks feeling closed and opaque.",
                ],
                suggestions=[
                    "Introduce measured openings on the street side to keep the "
                    "library visually active from the approach.",
                ],
                score=8,
            ),
            CategoryCritique(
                category="Massing",
                observation=(
                    "Two stacked rectangular volumes sit on a recessed glazed base, "
                    "giving a 'floating' reading."
                ),
                strengths=[
                    "The floating massing reinforces the permeable ground floor.",
                    "Proportions of the upper volumes are calm and considered.",
                ],
                weaknesses=[
                    "The two upper volumes read as nearly identical, flattening the "
                    "composition.",
                ],
                suggestions=[
                    "Shift, rotate, or vary one volume to respond to the river and "
                    "create a more dynamic silhouette.",
                ],
                score=7,
            ),
        ],
        overall_strengths=[
            "A clear, repeatable concept that ties plan, section, and program together.",
            "Confident solid/void strategy that expresses the public idea.",
        ],
        overall_weaknesses=[
            "Vertical circulation and hierarchy need development to match the "
            "strength of the ground-floor concept.",
            "Upper massing is too repetitive and slightly undercuts the parti.",
        ],
    )
