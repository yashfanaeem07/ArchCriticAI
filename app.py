"""
app.py
------
The AI Studio Critic UI.

Three phases, three tabs:
  * Phase 1 - Analyse:  upload a drawing/render and get a structured critique.
  * Phase 2 - Generate: turn the critique into a presentation, narrative,
                        keywords, and a jury defence.
  * Phase 3 - Knowledge: build the RAG knowledge base from principle documents
                        so the critique can be grounded in design theory.

Demo mode lets anyone explore the whole UI with no API key and no cost. Heavy
and real-mode imports are done lazily inside the button handlers, so a missing
dependency or model can never blank the whole page.
"""

import streamlit as st

from archcritic.core.images import SUPPORTED_IMAGE_TYPES
from archcritic.ui.components import (
    render_critique,
    render_design_narrative,
    render_jury_defense,
    render_keywords,
    render_presentation,
)
from config import get_api_key

st.set_page_config(page_title="AI Studio Critic", layout="wide", page_icon="◰")


def _inject_theme() -> None:
    """Editorial-paper look: warm paper, serif display headings, rust ink accent."""
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700&family=Inter:wght@400;500;600&display=swap');

        :root{
          --paper:#f4f1ea; --card:#fbf9f4; --ink:#2b2a27; --muted:#6f6a60;
          --rust:#9c4221; --rust-soft:#c2693f; --line:#ddd6c7;
        }

        /* Page + base type */
        .stApp{ background:var(--paper); }
        html, body, [class*="css"]{ font-family:'Inter',system-ui,sans-serif; color:var(--ink); }
        .block-container{ padding-top:4.5rem; max-width:1180px; }
        /* keep Streamlit's top toolbar from covering the masthead */
        [data-testid="stHeader"]{ background:transparent; }

        /* Display headings in a refined serif */
        h1,h2,h3,h4{ font-family:'Fraunces','Georgia',serif !important; color:var(--ink);
          letter-spacing:-.01em; }
        h2{ font-weight:600; margin-top:1.4rem; }
        h3{ font-weight:600; font-size:1.18rem; }

        /* Masthead */
        .masthead{ margin:.6rem 0 1.4rem; }
        .masthead .kicker{ font-family:'Inter',sans-serif; text-transform:uppercase;
          letter-spacing:.28em; font-size:.72rem; font-weight:600; color:var(--rust);
          line-height:1.6; display:block; white-space:nowrap; }
        .masthead h1{ font-size:2.9rem; font-weight:700; line-height:1.02; margin:.15rem 0 .35rem; }
        .masthead .dek{ font-family:'Fraunces',serif; font-style:italic; font-size:1.05rem;
          color:var(--muted); margin:0; }
        .rule{ height:2px; background:linear-gradient(90deg,var(--rust) 0 86px,var(--line) 86px);
          border:0; margin:.9rem 0 0; }

        /* Cards / expanders */
        [data-testid="stExpander"]{ background:var(--card); border:1px solid var(--line);
          border-radius:10px; box-shadow:0 1px 2px rgba(43,42,39,.04); overflow:hidden; }
        [data-testid="stExpander"] summary{ font-family:'Fraunces',serif; font-size:1rem; }
        [data-testid="stExpander"] summary:hover{ color:var(--rust); }

        /* Metric (overall score) as a framed card */
        [data-testid="stMetric"]{ background:var(--card); border:1px solid var(--line);
          border-left:4px solid var(--rust); border-radius:10px; padding:1rem 1.1rem; }
        [data-testid="stMetricValue"]{ font-family:'Fraunces',serif; font-weight:700; color:var(--rust); }

        /* Progress bars in rust */
        [data-testid="stProgress"] div[role="progressbar"]>div{ background:var(--rust) !important; }

        /* Buttons */
        .stButton>button, [data-testid="stBaseButton-primary"]{
          font-family:'Inter',sans-serif; font-weight:600; border-radius:8px;
          border:1px solid var(--rust); }
        .stButton>button[kind="primary"], [data-testid="stBaseButton-primary"]{
          background:var(--rust); color:#f8f5ee; }
        .stButton>button:hover{ border-color:var(--rust); color:var(--rust); }
        .stButton>button[kind="primary"]:hover{ background:var(--rust-soft); color:#fff; }

        /* Tabs */
        [data-baseweb="tab-list"]{ border-bottom:1px solid var(--line); gap:.4rem; }
        [data-baseweb="tab"]{ font-family:'Inter',sans-serif; font-weight:600; }
        [aria-selected="true"][data-baseweb="tab"]{ color:var(--rust); }
        [data-baseweb="tab-highlight"]{ background:var(--rust) !important; }

        /* Inline keyword chips (st.markdown `code`) */
        code{ background:#efe8d8; color:var(--rust); border:1px solid var(--line);
          border-radius:999px; padding:.12rem .6rem; font-family:'Inter',sans-serif;
          font-size:.8rem; font-weight:600; }

        /* Blockquotes (thesis / concept statements) */
        blockquote{ border-left:3px solid var(--rust); background:var(--card);
          border-radius:0 8px 8px 0; color:var(--ink); }

        /* Sidebar */
        [data-testid="stSidebar"]{ background:#efeadf; border-right:1px solid var(--line); }
        </style>
        """,
        unsafe_allow_html=True,
    )


_inject_theme()

st.markdown(
    """
    <div class="masthead">
      <div class="kicker">Architecture · Design Critique</div>
      <h1>AI Studio Critic</h1>
      <p class="dek">A studio-grade reading of your project — concept, space, light, and tectonics.</p>
      <hr class="rule"/>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar - global settings
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("⚙️ Settings")
    demo_mode = st.checkbox(
        "Demo mode (no API key needed)",
        value=False,
        key="demo_mode",
        help="Explore the full UI with a built-in sample project - no API calls.",
    )
    if demo_mode:
        st.warning(
            "Demo mode returns the **same fixed sample critique for every image** "
            "(it never looks at your upload). Turn it **off** for a real, "
            "per-image critique - the API key can stay blank (the `claude` CLI is "
            "used automatically)."
        )
    rag_mode = st.checkbox(
        "RAG mode (ground critique in principles)",
        value=False,
        key="rag_mode",
        help="Phase 3: retrieve relevant design principles and feed them to the critic.",
    )

    api_key = ""
    if not demo_mode:
        api_key = st.text_input(
            "Anthropic API key (optional)",
            type="password",
            value=get_api_key() or "",
            help="Optional. With a key, requests use the Anthropic SDK. Leave it "
                 "blank to run keyless via the authenticated `claude` CLI.",
        )

    st.caption(
        "Demo mode on → sample outputs. Demo mode off → live critique: with an "
        "API key via the SDK, or keyless via the `claude` CLI if the key is blank."
    )


def _build_retriever():
    """Phase 3 retriever, or None if RAG mode is off / unavailable."""
    if not rag_mode:
        return None
    try:
        from archcritic.knowledge.retriever import PrinciplesRetriever

        return PrinciplesRetriever()
    except Exception as exc:  # noqa: BLE001 - surface, don't crash the page
        st.warning(f"RAG mode unavailable, continuing without it: {exc}")
        return None


# ---------------------------------------------------------------------------
# Tabs - one per phase
# ---------------------------------------------------------------------------
tab_analyse, tab_generate, tab_knowledge = st.tabs(
    ["🔍 Analyse (Phase 1)", "✨ Generate (Phase 2)", "📚 Knowledge (Phase 3)"]
)

# ===========================================================================
# Phase 1 - Analyse
# ===========================================================================
with tab_analyse:
    st.subheader("Analyse a project")

    st.text_input("Project title", key="project_title", placeholder="e.g. Riverside Community Library")
    st.text_area(
        "Design intent / keywords",
        key="keywords",
        placeholder="e.g. permeable ground floor, timber structure, threshold to the river",
        help="A short note on the idea you are exploring - it focuses the critique.",
    )

    uploaded = st.file_uploader(
        "Upload a drawing, plan, or render",
        type=list(SUPPORTED_IMAGE_TYPES),
        help="PNG, JPG, WEBP, or GIF.",
    )
    if uploaded is not None:
        st.image(uploaded, caption=uploaded.name, use_container_width=True)

    if st.button("🔍 Critique", type="primary"):
        # Clear any previous result first so a stale critique can never linger on
        # screen (e.g. a demo sample left over after switching to live mode).
        st.session_state.pop("critique", None)
        st.session_state.pop("critique_source", None)

        if demo_mode:
            from archcritic.analysis.demo import sample_critique

            st.session_state["critique"] = sample_critique()
            st.session_state["critique_source"] = (
                "⚠️ DEMO sample — fixed, identical for every image (Demo mode is ON)"
            )
        elif uploaded is None:
            st.error("Upload an image to critique, or switch on Demo mode.")
        else:
            try:
                from archcritic.analysis.critic import analyze_project

                spin = "Analysing the project... (live `claude` CLI can take 15–60s)"
                with st.spinner(spin):
                    st.session_state["critique"] = analyze_project(
                        api_key=api_key,
                        image_bytes=uploaded.getvalue(),
                        media_type=uploaded.type,
                        project_title=st.session_state.get("project_title", ""),
                        keywords=st.session_state.get("keywords", ""),
                        retriever=_build_retriever(),
                    )
                st.session_state["critique_source"] = (
                    f"Live critique of **{uploaded.name}** via the Anthropic SDK"
                    if api_key else
                    f"Live critique of **{uploaded.name}** via the `claude` CLI (keyless)"
                )
            except Exception as exc:  # noqa: BLE001 - show the error, keep the page alive
                st.error(f"Critique failed: {exc}")
                st.exception(exc)

    critique = st.session_state.get("critique")
    if critique is not None:
        st.divider()
        source = st.session_state.get("critique_source")
        if source:
            (st.warning if source.startswith("⚠️") else st.caption)(source)
        render_critique(critique)
    else:
        st.info("Run a critique to see results here.")

# ===========================================================================
# Phase 2 - Generate
# ===========================================================================
with tab_generate:
    st.subheader("Generate from the critique")

    critique = st.session_state.get("critique")
    if critique is None:
        st.info("Run a critique in the **Analyse** tab first - the generators build on it.")
    else:
        title = st.session_state.get("project_title", "")
        kw = st.session_state.get("keywords", "")

        col1, col2 = st.columns(2)

        # --- Presentation --------------------------------------------------
        with col1:
            if st.button("🎤 Generate presentation"):
                if demo_mode:
                    from archcritic.generation.demo import sample_presentation

                    st.session_state["presentation"] = sample_presentation()
                else:
                    try:
                        from archcritic.generation import generate_presentation

                        with st.spinner("Writing the presentation..."):
                            st.session_state["presentation"] = generate_presentation(
                                api_key, critique, title, kw
                            )
                    except Exception as exc:  # noqa: BLE001
                        st.error(f"Could not generate presentation: {exc}")

        # --- Narrative -----------------------------------------------------
        with col2:
            if st.button("📝 Write design narrative"):
                if demo_mode:
                    from archcritic.generation.demo import sample_design_narrative

                    st.session_state["narrative"] = sample_design_narrative()
                else:
                    try:
                        from archcritic.generation import generate_design_narrative

                        with st.spinner("Writing the design narrative..."):
                            st.session_state["narrative"] = generate_design_narrative(
                                api_key, critique, title, kw
                            )
                    except Exception as exc:  # noqa: BLE001
                        st.error(f"Could not write narrative: {exc}")

        col3, col4 = st.columns(2)

        # --- Keywords ------------------------------------------------------
        with col3:
            if st.button("🏷️ Extract keywords"):
                if demo_mode:
                    from archcritic.generation.demo import sample_keywords

                    # Result lands in its own key so it never clobbers the
                    # user's design-intent text (stored under "keywords").
                    st.session_state["keywords_result"] = sample_keywords()
                else:
                    try:
                        from archcritic.generation import extract_architectural_keywords

                        with st.spinner("Extracting keywords..."):
                            st.session_state["keywords_result"] = (
                                extract_architectural_keywords(api_key, critique, title, kw)
                            )
                    except Exception as exc:  # noqa: BLE001
                        st.error(f"Could not extract keywords: {exc}")

        # --- Jury defence --------------------------------------------------
        with col4:
            if st.button("⚖️ Prepare jury defence"):
                if demo_mode:
                    from archcritic.generation.demo import sample_jury_defense

                    st.session_state["jury"] = sample_jury_defense()
                else:
                    try:
                        from archcritic.generation import generate_jury_defense

                        with st.spinner("Anticipating the jury..."):
                            st.session_state["jury"] = generate_jury_defense(
                                api_key, critique, title, kw
                            )
                    except Exception as exc:  # noqa: BLE001
                        st.error(f"Could not prepare jury defence: {exc}")

        # --- Render whatever has been generated ----------------------------
        if "presentation" in st.session_state:
            st.divider()
            st.markdown("## 🎤 Presentation script")
            render_presentation(st.session_state["presentation"])

        if "narrative" in st.session_state:
            st.divider()
            st.markdown("## 📝 Design narrative")
            render_design_narrative(st.session_state["narrative"])

        if "keywords_result" in st.session_state:
            st.divider()
            st.markdown("## 🏷️ Architectural keywords")
            render_keywords(st.session_state["keywords_result"])

        if "jury" in st.session_state:
            st.divider()
            st.markdown("## ⚖️ Jury defence")
            render_jury_defense(st.session_state["jury"])

# ===========================================================================
# Phase 3 - Knowledge (RAG)
# ===========================================================================
with tab_knowledge:
    st.subheader("Knowledge base (RAG)")
    st.write(
        "Phase 3 grounds the critique in design theory. Embed the principle "
        "documents below, then switch on **RAG mode** in the sidebar so the "
        "critic retrieves relevant passages while it analyses a project."
    )

    if st.button("📚 Build / refresh knowledge base"):
        # Imported lazily: rag_embed pulls in chromadb + a sentence-transformer
        # model at import time, which is heavy and only needed on demand.
        try:
            from rag_embed import embed_pdfs

            with st.spinner("Embedding principle PDFs into the knowledge base..."):
                embed_pdfs()
            st.success("Knowledge base updated.")
        except Exception as exc:  # noqa: BLE001 - surface, don't crash the page
            st.error(f"Could not build the knowledge base: {exc}")

    st.divider()

    # --- Placeholder: Phase 3 retrieval preview ----------------------------
    st.markdown("#### 🔎 Retrieval preview (Phase 3)")
    query = st.text_input(
        "Test a query against the knowledge base",
        placeholder="e.g. circulation and spatial order",
        key="rag_query",
    )
    if st.button("Search principles"):
        try:
            from archcritic.knowledge.retriever import PrinciplesRetriever

            with st.spinner("Searching the knowledge base..."):
                passages = PrinciplesRetriever().retrieve(query)
            if not passages:
                st.info("No passages found. Build the knowledge base first, then try again.")
            for p in passages:
                with st.expander(f"{p.source} — score {p.score}"):
                    st.write(p.text)
        except Exception as exc:  # noqa: BLE001
            st.error(f"Retrieval not available yet: {exc}")
