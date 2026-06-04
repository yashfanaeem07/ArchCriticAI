"""
pipeline.py
-----------
End-to-end ArchCriticAI automation. Runs all five phases in order and writes a
final JSON + Markdown report. Fully automatic: it uses the live Anthropic model
when an API key AND an image are available, and otherwise falls back to the
built-in sample so the whole pipeline still completes with zero manual input.

    python pipeline.py
    python pipeline.py --image path/to/render.png --keywords "timber, river view" --title my-project

Inputs may also come from the environment: ARCHCRITIC_IMAGE, ARCHCRITIC_KEYWORDS.
"""

import argparse
import json
import mimetypes
import os

from config import CRITIQUES_DIR, RETRIEVAL_TOP_K, get_api_key
from archcritic.core.schemas import Critique
from archcritic.knowledge.store import build_index, save_critique
from archcritic.knowledge.retriever import PrinciplesRetriever


def _log(step: str, msg: str) -> None:
    print(f"[{step}] {msg}")


# ---------------------------------------------------------------------------
# Phase 3a - Embed principle documents into the Chroma collection
# ---------------------------------------------------------------------------
def embed_principles() -> dict:
    report = build_index()  # loads data/principles, chunks, embeds, upserts
    _log("Phase 3", f"Indexed {report.chunks} chunk(s) from {report.documents} "
                    f"document(s) into '{report.collection}'.")
    return {
        "documents": report.documents,
        "chunks": report.chunks,
        "collection": report.collection,
        "persist_dir": report.persist_dir,
    }


# ---------------------------------------------------------------------------
# Phase 1 - Analyse the image + keywords -> Critique
# ---------------------------------------------------------------------------
def analyse(image, keywords, title, api_key, retriever):
    """Live critique when image+key exist; otherwise the built-in sample."""
    if image and os.path.isfile(image) and api_key:
        from archcritic.analysis.critic import analyze_project

        media_type = mimetypes.guess_type(image)[0] or "image/png"
        with open(image, "rb") as fh:
            critique = analyze_project(
                api_key=api_key,
                image_bytes=fh.read(),
                media_type=media_type,
                project_title=title,
                keywords=keywords,
                retriever=retriever,
            )
        _log("Phase 1", f"LIVE critique of '{os.path.basename(image)}'.")
        return critique, "live"

    from archcritic.analysis.demo import sample_critique

    reason = "no API key" if not api_key else "no readable image"
    _log("Phase 1", f"SAMPLE critique ({reason}).")
    return sample_critique(), "demo"


# ---------------------------------------------------------------------------
# Phase 3b - Retrieve the most relevant principles for the project
# ---------------------------------------------------------------------------
def retrieve(retriever, keywords, title, top_k):
    import re

    query = f"{title} {keywords}".strip()
    terms = [t.strip() for t in re.split(r"[,\n]", keywords) if t.strip()]
    passages = retriever.retrieve(query, k=top_k)
    out = []
    for rank, p in enumerate(passages, start=1):
        low = p.text.lower()
        out.append({
            "rank": rank,
            "source": p.source,
            "score": p.score,
            "matched_terms": [t for t in terms if t.lower() in low],
            "excerpt": " ".join(p.text.split())[:240],
        })
    _log("Phase 3", f"Retrieved {len(out)} principle(s) for query {query!r} "
                    f"(requested top {top_k}).")
    return query, out


# ---------------------------------------------------------------------------
# Phase 2 - Presentation (4 fixed slides) + design narrative
# ---------------------------------------------------------------------------
def generate(critique, keywords, title, api_key, principles):
    """Live generators when a key exists; otherwise the matching demo content."""
    if api_key:
        from archcritic.generation import (
            generate_design_narrative,
            generate_jury_defense,
        )
        narrative = generate_design_narrative(api_key, critique, title, keywords)
        jury = generate_jury_defense(api_key, critique, title, keywords)
        mode = "live"
    else:
        from archcritic.generation.demo import (
            sample_design_narrative,
            sample_jury_defense,
        )
        narrative = sample_design_narrative()
        jury = sample_jury_defense()
        mode = "demo"
    _log("Phase 2", f"{mode.upper()} narrative + jury defence generated.")

    concept_line = critique.concept_summary.split(" - ")[0].split(".")[0] + "."
    slides = [
        {
            "heading": "Overview",
            "bullets": [
                f"Overall score: {critique.overall_score} / 10",
                "Category scores: " + ", ".join(
                    f"{c.category} {c.score}" for c in critique.categories
                ),
                concept_line,
            ],
        },
        {
            "heading": "Design Intent",
            "concept_statement": narrative.concept_statement,
            "body": critique.concept_summary,
            "design_moves": narrative.design_moves,
        },
        {
            "heading": "Strengths & Weaknesses",
            "strengths": critique.overall_strengths,
            "weaknesses": critique.overall_weaknesses,
        },
        {
            "heading": "Jury Defense",
            "points": [
                {"topic": j.topic, "question": j.question,
                 "defense": j.defense, "follow_up": j.follow_up}
                for j in jury
            ],
        },
    ]
    narrative_dict = {
        "headline": narrative.headline,
        "concept_statement": narrative.concept_statement,
        "narrative": narrative.narrative,
        "design_moves": narrative.design_moves,
    }
    return slides, narrative_dict, mode


# ---------------------------------------------------------------------------
# Phase 5 - Render the final Markdown report
# ---------------------------------------------------------------------------
def render_markdown(report: dict) -> str:
    L = [f"# {report['project_title']} - ArchCriticAI Report\n"]
    L.append(f"*Mode: **{report['mode']}**  |  keywords: `{report['keywords']}`  |  "
             f"image: `{report['image'] or 'none'}`*\n")

    idx = report.get("phase3_index")
    if idx:
        L.append(f"> Knowledge base: {idx['chunks']} chunk(s) from {idx['documents']} "
                 f"document(s) in `{idx['collection']}`.\n")

    if report["phase3_retrieval"]["principles"]:
        cites = ", ".join(
            f"`{p['source']}` ({p['score']:.2f})"
            for p in report["phase3_retrieval"]["principles"]
        )
        L.append(f"> Grounded in: {cites}\n")

    for i, s in enumerate(report["phase2_presentation"]["slides"], 1):
        L.append(f"## Slide {i} - {s['heading']}\n")
        if s["heading"] == "Overview":
            L += [f"- {b}" for b in s["bullets"]]
            L.append("")
        elif s["heading"] == "Design Intent":
            L.append(f"> *{s['concept_statement']}*\n")
            L.append(s["body"] + "\n")
            L.append("**Key design moves**")
            L += [f"- {m}" for m in s["design_moves"]]
            L.append("")
        elif s["heading"] == "Strengths & Weaknesses":
            L.append("**Strengths**")
            L += [f"- {x}" for x in s["strengths"]]
            L.append("\n**Weaknesses / priorities to fix**")
            L += [f"- {x}" for x in s["weaknesses"]]
            L.append("")
        elif s["heading"] == "Jury Defense":
            for n, p in enumerate(s["points"], 1):
                L.append(f"### Q{n} - {p['topic']}: {p['question']}")
                L.append(f"**Defence:** {p['defense']}")
                L.append(f"*Likely follow-up: {p['follow_up']}*\n")

    nar = report["phase2_presentation"]["narrative"]
    L.append("---\n")
    L.append("## Design Narrative\n")
    L.append(f"### {nar['headline']}\n")
    L.append(f"> *{nar['concept_statement']}*\n")
    L.append(nar["narrative"] + "\n")
    return "\n".join(L)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the full ArchCriticAI pipeline.")
    parser.add_argument("--image", default=os.getenv("ARCHCRITIC_IMAGE", ""))
    parser.add_argument("--keywords",
                        default=os.getenv("ARCHCRITIC_KEYWORDS",
                                          "timber structure, open floor, river view"))
    parser.add_argument("--title", default="uploaded-project")
    parser.add_argument("--top-k", type=int, default=RETRIEVAL_TOP_K)
    args = parser.parse_args()

    api_key = get_api_key()
    os.makedirs(CRITIQUES_DIR, exist_ok=True)

    # Phase 3a - embed
    index_info = embed_principles()
    retriever = PrinciplesRetriever()

    # Phase 1 - analyse (grounded in retrieval when live)
    critique, p1_mode = analyse(args.image, args.keywords, args.title, api_key, retriever)
    critique_path = save_critique(critique, args.title, keywords=args.keywords)
    _log("Phase 1", f"Critique saved -> {os.path.basename(critique_path)}")

    # Phase 3b - retrieve
    query, principles = retrieve(retriever, args.keywords, args.title, args.top_k)

    # Phase 2 - presentation + narrative
    slides, narrative, p2_mode = generate(
        critique, args.keywords, args.title, api_key, principles
    )

    # Phase 5 - final report
    report = {
        "schema_version": 1,
        "project_title": args.title,
        "keywords": args.keywords,
        "image": args.image or None,
        "mode": "live" if (p1_mode == "live" and p2_mode == "live") else "demo",
        "phase1_mode": p1_mode,
        "phase2_mode": p2_mode,
        "phase3_index": index_info,
        "phase1_critique": {**critique.model_dump(),
                            "overall_score": critique.overall_score},
        "phase3_retrieval": {
            "query": query,
            "top_k_requested": args.top_k,
            "results_returned": len(principles),
            "principles": principles,
        },
        "phase2_presentation": {"slides": slides, "narrative": narrative},
    }

    json_out = os.path.join(CRITIQUES_DIR, f"{args.title}.report.json")
    md_out = os.path.join(CRITIQUES_DIR, f"{args.title}.report.md")
    with open(json_out, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)
    with open(md_out, "w", encoding="utf-8") as fh:
        fh.write(render_markdown(report))

    _log("Phase 5", f"Final report -> {os.path.basename(json_out)}, {os.path.basename(md_out)}")
    print(f"\nDONE (mode={report['mode']}). Outputs in {CRITIQUES_DIR}")


if __name__ == "__main__":
    main()
