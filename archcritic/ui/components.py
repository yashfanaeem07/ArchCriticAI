"""
ui/components.py
----------------
Functions that draw parts of the page. app.py calls these so it stays short and
the look of the critique lives in one place.
"""

import pandas as pd
import streamlit as st

from archcritic.core.schemas import CategoryCritique, Critique
from archcritic.generation.keywords import ArchitecturalKeywords
from archcritic.generation.narrative import DesignNarrative
from archcritic.generation.presentation import Presentation
from archcritic.generation.jury import JuryPoint


def render_overview(critique: Critique) -> None:
    """Top section: overall score + a bar chart of category scores."""
    score = critique.overall_score

    col_metric, col_chart = st.columns([1, 2])
    with col_metric:
        st.metric("Overall score", f"{score} / 10")
        st.progress(min(max(score / 10, 0.0), 1.0))
    with col_chart:
        # A simple bar chart comparing every category at a glance.
        data = pd.DataFrame(
            {"score": [c.score for c in critique.categories]},
            index=[c.category for c in critique.categories],
        )
        st.bar_chart(data, height=220, color="#9c4221")

    st.markdown("### 💡 Concept interpretation")
    st.write(critique.concept_summary)


def render_category(cat: CategoryCritique) -> None:
    """One expandable card per architectural category."""
    with st.expander(f"**{cat.category}** — {cat.score} / 10", expanded=False):
        st.progress(min(max(cat.score / 10, 0.0), 1.0))

        st.caption("What the critic sees")
        st.write(cat.observation)

        st.markdown("**✅ Strengths**")
        for item in cat.strengths:
            st.markdown(f"- {item}")

        st.markdown("**⚠️ Weaknesses**")
        for item in cat.weaknesses:
            st.markdown(f"- {item}")

        st.markdown("**🔧 Suggestions**")
        for item in cat.suggestions:
            st.markdown(f"- {item}")


def render_critique(critique: Critique) -> None:
    """Draw the whole critique: overview, per-category cards, overall lists."""
    render_overview(critique)

    st.markdown("### 📐 Category breakdown")
    for cat in critique.categories:
        render_category(cat)

    st.markdown("### 🏆 Biggest strengths")
    for item in critique.overall_strengths:
        st.markdown(f"- {item}")

    st.markdown("### 🎯 Priorities to fix")
    for item in critique.overall_weaknesses:
        st.markdown(f"- {item}")


# ===========================================================================
# Phase 2 - Generate: presentation, jury defence, narrative, keywords
# ===========================================================================
def render_presentation(presentation: Presentation) -> None:
    """Draw the spoken jury presentation: thesis, length, then section-by-section."""
    st.markdown(f"> **Design thesis** — {presentation.thesis}")
    st.caption(f"🕐 ~{presentation.estimated_minutes} min spoken")

    for section in presentation.sections:
        st.markdown(f"#### {section.heading}")
        st.write(section.script)
        st.caption(f"🎙️ {section.delivery_note}")


def render_jury_defense(points: list[JuryPoint]) -> None:
    """Draw the anticipated jury questions as expandable Q&A cards."""
    for i, point in enumerate(points, start=1):
        with st.expander(f"**Q{i} · {point.topic}** — {point.question}", expanded=False):
            st.markdown("**🛡️ Your defence**")
            st.write(point.defense)
            st.caption(f"↪️ Likely follow-up: {point.follow_up}")


def render_design_narrative(narrative: DesignNarrative) -> None:
    """Draw the written design narrative: headline, concept, prose, key moves."""
    st.markdown(f"### {narrative.headline}")
    st.markdown(f"> *{narrative.concept_statement}*")
    st.write(narrative.narrative)

    st.markdown("**📐 Key design moves**")
    for move in narrative.design_moves:
        st.markdown(f"- {move}")


def render_keywords(keywords: ArchitecturalKeywords) -> None:
    """Draw the extracted architectural keywords, grouped by register."""
    st.markdown(f"**Parti** — {keywords.parti}")

    registers = [
        ("🧠 Conceptual", keywords.conceptual),
        ("🧭 Spatial", keywords.spatial),
        ("🧱 Tectonic", keywords.tectonic),
        ("✨ Experiential", keywords.experiential),
    ]
    for label, terms in registers:
        if terms:
            st.markdown(f"**{label}**")
            # Render each term as an inline "chip" for a panel-tag feel.
            st.markdown("  ".join(f"`{term}`" for term in terms))
