"""
generation/demo.py
------------------
Hand-written sample Phase 2 outputs for "Demo mode".

Like analysis/demo.py, these let anyone explore the full Generate tab - script,
defence, narrative, keywords - with no API key and no cost. They describe the
same fictional "Riverside Community Library" so the whole app reads as one piece,
and they return the exact same types the real generators produce.
"""

from archcritic.generation.jury import JuryPoint
from archcritic.generation.keywords import ArchitecturalKeywords
from archcritic.generation.narrative import DesignNarrative
from archcritic.generation.presentation import Presentation, PresentationSection


def sample_presentation() -> Presentation:
    """A realistic jury presentation script for the demo project."""
    return Presentation(
        thesis=(
            "A library conceived as a permeable threshold that pulls the public "
            "from the street through to the river."
        ),
        sections=[
            PresentationSection(
                heading="Site and context",
                script=(
                    "I began by reading the site as a seam between two publics - "
                    "the busy street edge and the quiet riverfront. Rather than "
                    "treating the building as an object dropped onto the plot, I "
                    "wanted it to behave like a piece of the public realm, a route "
                    "as much as a building."
                ),
                delivery_note="Point to the site plan; trace the street-to-river line.",
            ),
            PresentationSection(
                heading="The parti",
                script=(
                    "That reading gives the parti: a continuous public ground floor "
                    "that slips beneath two stacked timber reading volumes. The "
                    "threshold is the whole idea - the building dissolves its own "
                    "edge so the city flows through it toward the water."
                ),
                delivery_note="Hold on the section; let the 'floating' volumes register.",
            ),
            PresentationSection(
                heading="Programme and organisation",
                script=(
                    "Programme follows the noise gradient. The loudest, most public "
                    "uses sit at grade on the route; study and quiet reading climb "
                    "away from it. The service cores are consolidated to one side, "
                    "which keeps the reading floors open and column-light."
                ),
                delivery_note="Use the stacked-floor diagram to show the gradient.",
            ),
            PresentationSection(
                heading="Spatial sequence",
                script=(
                    "Moving through, you enter under the volumes into a double-height "
                    "space that frames the river, then rise into progressively "
                    "calmer rooms. I'll be honest that the vertical procession needs "
                    "work - right now the main stair is tucked away. My next move is "
                    "to expose it at the entry so the climb reads as part of the "
                    "public route, not a back-of-house afterthought."
                ),
                delivery_note="Acknowledge the weakness openly; show the proposed stair move.",
            ),
            PresentationSection(
                heading="Materiality and tectonics",
                script=(
                    "The tectonic strategy reinforces the concept: a recessed glazed "
                    "base reads as void so the timber volumes appear to float, and "
                    "the solid-to-void contrast expresses public versus quiet. Timber "
                    "carries warmth into the reading rooms where people linger."
                ),
                delivery_note="Gesture from the glazed base up to the timber mass.",
            ),
            PresentationSection(
                heading="Closing",
                script=(
                    "So the project is one clear idea carried from plan to section to "
                    "material - a library that earns its place by giving the city a "
                    "new way to reach the river. The work ahead is to let the "
                    "vertical experience live up to that ground-floor ambition."
                ),
                delivery_note="Return to the thesis line; end on the river view.",
            ),
        ],
    )


def sample_jury_defense() -> list[JuryPoint]:
    """A realistic set of anticipated jury questions and defences for the demo."""
    return [
        JuryPoint(
            topic="Circulation",
            question=(
                "You rely on a single vertical core - what happens at peak use, and "
                "is that not a fire-egress problem?"
            ),
            defense=(
                "It is the project's weakest point and I own that. The single core "
                "kept the reading floors open, but it under-serves the building. My "
                "resolution is a second stair on the river side that doubles as "
                "egress and shortens travel distances, while exposing the primary "
                "stair at the entry so vertical movement becomes part of the public "
                "route rather than a bottleneck."
            ),
            follow_up="Where exactly does the second core land in plan, and what does it cost you?",
        ),
        JuryPoint(
            topic="Massing",
            question=(
                "The two upper volumes read as nearly identical - isn't the massing "
                "just repetitive rather than composed?"
            ),
            defense=(
                "The calm, matched proportions were deliberate, to keep the timber "
                "mass quiet against the active base. But the panel is right that it "
                "flattens the silhouette. Shifting and slightly rotating the upper "
                "volume to align with the river view would give the composition a "
                "figure without losing the floating reading."
            ),
            follow_up="If you rotate it, how do you keep the floor plates working inside?",
        ),
        JuryPoint(
            topic="Transparency",
            question=(
                "The street elevation looks closed - does the library turn its back "
                "on the city it claims to serve?"
            ),
            defense=(
                "The solid street face protects quiet reading and drives people "
                "toward the river, which is the concept. That said, a fully opaque "
                "edge undercuts the 'permeable' claim, so I would introduce measured "
                "openings at eye level - enough to keep the library legible and "
                "active from the approach without diluting the solid/void strategy."
            ),
            follow_up="What ground-floor programme animates that street edge?",
        ),
        JuryPoint(
            topic="Hierarchy",
            question=(
                "Beyond the entry, your spaces read at a similar weight - where is "
                "the spatial hierarchy?"
            ),
            defense=(
                "The double-height entry establishes the primary space, but I agree "
                "the secondary rooms compete with it. I would differentiate them "
                "through ceiling height, top-light, and a material shift so the main "
                "reading room is unmistakably the heart, with a vertical void as a "
                "datum to orient visitors."
            ),
            follow_up="Which space, specifically, becomes the project's landmark?",
        ),
    ]


def sample_design_narrative() -> DesignNarrative:
    """A realistic written design narrative for the demo project."""
    return DesignNarrative(
        headline="Crossing to the Water: A Library as Public Threshold",
        concept_statement=(
            "A continuous public ground floor slips beneath two stacked timber "
            "reading volumes, turning the library into a permeable threshold that "
            "draws the city through to the river."
        ),
        narrative=(
            "The Riverside Community Library begins not with a building but with a "
            "route. Reading the site as a seam between the animated street and the "
            "quiet riverfront, the project refuses to sit as an object on its plot "
            "and instead behaves as a piece of the public realm - a passage the city "
            "can move through on its way to the water.\n\n"
            "From that reading comes the parti. A generous, glazed ground floor "
            "dissolves the building's edge and carries pedestrians beneath two "
            "stacked timber volumes that hold the reading rooms. The recessed base "
            "reads as void, so the timber mass appears to float, and the resulting "
            "solid-to-void contrast becomes the project's argument made physical: "
            "the public and porous below, the quiet and contemplative above.\n\n"
            "Programme follows a noise gradient. The most public uses anchor the "
            "route at grade, while study spaces climb away from the activity into "
            "progressively calmer rooms. Consolidated service cores free the upper "
            "floors to remain open and light, and a double-height entry frames the "
            "river as both arrival and destination.\n\n"
            "The project's next chapter is vertical. Today the procession upward is "
            "understated; the resolution is to expose the primary stair at the entry "
            "and let a stepped void carry the threshold idea through the section, so "
            "the climb to the reading rooms becomes part of the same public crossing "
            "that defines the ground - and the building keeps its single, clear idea "
            "from plan to section to material."
        ),
        design_moves=[
            "Lift the reading volumes onto a recessed glazed base so the mass floats.",
            "Thread a continuous public route from street to river beneath the building.",
            "Stack programme along a noise gradient, quietest at the top.",
            "Express the concept through a deliberate solid/void, timber-on-glass contrast.",
            "Carry the threshold vertically with a stepped void linking route to reading rooms.",
        ],
    )


def sample_keywords() -> ArchitecturalKeywords:
    """A realistic architectural keyword set for the demo project."""
    return ArchitecturalKeywords(
        parti="A permeable public threshold from street to river",
        conceptual=["threshold", "permeability", "public route", "figure-ground"],
        spatial=[
            "procession",
            "noise gradient",
            "stacked volumes",
            "double-height entry",
        ],
        tectonic=["timber reading volumes", "recessed glazed base", "consolidated cores"],
        experiential=["floating mass", "framed river view", "solid/void contrast"],
    )
