# 🏛️ AI Studio Critic

A portfolio-quality AI tool that gives architecture students an instant, detailed
"studio crit" of their design work. Upload a sketch, plan, model photo, or render,
and an AI vision model critiques it — scoring each architectural category
separately.

Built with **Python + Streamlit + Claude (vision)**, structured for growth.

---

## The plan (3 phases)

| Phase | What it does | Status |
|-------|--------------|--------|
| **1** | Analyse the image; critique **concept, spatial organization, hierarchy, circulation, transparency, massing**; give strengths, weaknesses & suggestions; score each category | ✅ Built |
| **2** | Generate a presentation script, jury defence points, a design narrative, and architectural keywords (concept images still scaffolded) | ✅ Text built |
| **3** | RAG knowledge base so feedback is grounded in real architecture theory, not generic LLM output | ✅ Built |

The code is structured so Phases 2 and 3 **plug into** Phase 1 rather than
requiring rewrites — see "Why it's scalable" below.

---

## Project structure

```
ArchCriticAI/
├── app.py                      # Thin Streamlit UI (tabs per phase)
├── run_archcritic_workflow.py  # Batch every image → features+scores+RAG+narrative
├── config.py                   # Model + settings in one place
├── requirements.txt
├── archcritic/                 # The package
│   ├── core/
│   │   ├── schemas.py          # Shared data models (Critique, CategoryCritique)
│   │   ├── images.py           # Image → API content block
│   │   ├── llm.py              # Anthropic client wrapper
│   │   └── rag_embed.py        # PHASE 3 CLI: build the knowledge base (main())
│   ├── analysis/               # ── PHASE 1 (built) ──
│   │   ├── categories.py       # The 6 categories, defined once
│   │   ├── prompts.py          # Critic instructions (+ RAG hook)
│   │   └── critic.py           # analyze_project(...) orchestrator
│   ├── generation/             # ── PHASE 2 (scaffolded) ──
│   │   ├── concept_images.py
│   │   ├── presentation.py
│   │   └── jury.py
│   ├── knowledge/              # ── PHASE 3 (RAG, built) ──
│   │   ├── loaders.py          # Read .pdf/.txt/.md principle docs
│   │   ├── chunking.py         # Split into ~500-word chunks
│   │   ├── embeddings.py       # Local Sentence-Transformers embedder
│   │   ├── chroma.py           # Shared ChromaDB collection access
│   │   ├── store.py            # build_index(): load→chunk→embed→store
│   │   └── retriever.py        # PrinciplesRetriever (critic accepts one)
│   └── ui/
│       └── components.py       # Reusable Streamlit render functions
├── rag_embed.py                # thin shim → archcritic/core/rag_embed.py
├── data/
│   ├── principles/             # Design-theory docs (Phase 3 RAG source)
│   ├── chroma/                 # Persisted vector index (built artifact)
│   └── critiques/              # Saved critiques dataset (Phase 3)
└── tests/
    ├── test_schemas.py
    ├── test_generation.py
    ├── test_app_smoke.py
    └── test_knowledge.py
```

---

## Why it's scalable

Three deliberate choices keep future phases cheap:

1. **One shared data model.** `core/schemas.py` defines what a critique *is*.
   The AI response, the UI, and any saved dataset all use it. The overall score
   is **computed from the category scores** in code, so it's always consistent.

2. **Dependency injection for RAG.** `analyze_project(...)` already takes an
   optional `retriever`. Today it's `None`. In Phase 3 you pass a real one and
   the critic grounds its feedback in retrieved theory — *the critic code barely
   changes*.

3. **Categories defined once.** Add or rename a category in
   `analysis/categories.py` and the prompt, the AI output, and the UI all follow.

---

## Setup

### 1. Install Python 3.10+ and (recommended) a virtual environment
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 2. Install packages
```powershell
pip install -r requirements.txt
```

### 3. Add your API key (optional)
The AI features need access to Claude **one of two ways** — you only need one:

- **Keyless via the `claude` CLI** *(default, no key)* — if [Claude Code](https://claude.com/claude-code)
  is installed and logged in (`claude` on your PATH), the app and batch use it
  automatically. Nothing to configure.
- **Anthropic SDK via an API key** — copy `.env.example` to `.env` and paste your
  key (console.anthropic.com → API Keys), or paste it into the app's sidebar at
  runtime. When a key is present it's used instead of the CLI (and is faster).

---

## Run

### The web app
```powershell
streamlit run app.py
```
Opens at **http://localhost:8501**. In the **Analyse** tab: enter a title, add
design keywords, upload an image, and click **Critique**. A badge above each result
shows its source — `claude CLI (keyless)`, `Anthropic SDK`, or `DEMO sample`.

> Run it from **your own terminal** so it keeps serving independently of any editor
> or Claude Code chat session. Stop it with `Ctrl+C`. **Demo mode** (sidebar) needs
> no key/CLI but returns the *same fixed sample for every image* — turn it **off**
> for a real, per-image critique.

### Batch the whole folder (CLI-driven, keyless)
Process every image in `data/images/` automatically — extract numeric features,
score 5 categories, retrieve RAG principles, and write a Claude narrative critique:
```powershell
python run_archcritic_workflow.py
```
Per image it writes to `data/critiques/`:
`<image>.json` (numeric features + scores) and `<image>.narrative.json` (critique).

### What needs Claude, what doesn't

| Feature | Needs `claude` CLI **or** API key? |
|---|---|
| Batch numeric scores (`<image>.json`), Demo mode, RAG/Knowledge tab | ❌ No — pure Python + local ChromaDB |
| Live critique (app Phase 1 & 2), batch narratives (`<image>.narrative.json`) | ✅ Yes — CLI (keyless) **or** `ANTHROPIC_API_KEY` |

Each AI call spawns its own `claude -p` process, so the live features keep working
as long as the CLI stays installed and logged in — no chat session required. Remove
the CLI? Set `ANTHROPIC_API_KEY` and it falls back to the SDK automatically.

## Test

```powershell
pytest
```

---

## Phase 3 — Knowledge base (RAG)

Ground the critique in real architecture theory instead of generic LLM output.

**1. Add principle documents.** Drop `.pdf`, `.txt`, or `.md` files into
`data/principles/` (two starter docs on parti and circulation ship with the repo).

**2. Build the index** (run again whenever you add or edit documents):
```powershell
python rag_embed.py            # load → chunk (~500 words) → embed → store in ChromaDB
python rag_embed.py --show     # report how many chunks are indexed
```
This embeds every chunk with a local **Sentence-Transformers** model
(`all-MiniLM-L6-v2`, no API key, no cost) and stores the vectors in a persistent
**ChromaDB** collection named `architecture_principles` under `data/chroma/`.

**3. Use it.** In the **Analyse** tab, tick **📚 Ground critique in the knowledge
base (RAG)** before clicking *Critique my project*. The pipeline retrieves the
**top 5** principle chunks most relevant to your title + keywords and feeds them
into the critique prompt. The **Knowledge** tab shows the index status.

How it plugs in: the retriever satisfies the `Retriever` protocol the Phase 1
critic already accepts, so the critic and prompts are **unchanged** — `app.py`
simply passes a `PrinciplesRetriever()` when the toggle is on.

---

## Extending each phase (quick map for contributors)

- **Phase 2 — Presentation / Jury** (text tasks, easy): fill in
  `generation/presentation.py` and `generation/jury.py` using `core/llm.py`,
  then add a button in the *Generate* tab of `app.py`.
- **Phase 2 — Concept images**: Claude reads images but doesn't generate them, so
  `generation/concept_images.py` will call a dedicated image-generation model.
- **Phase 3 — RAG**: implement `knowledge/store.py` (build the index) and
  `knowledge/retriever.py` (`PrinciplesRetriever`), then pass it into
  `analyze_project(retriever=...)` from `app.py`. Nothing else changes.
