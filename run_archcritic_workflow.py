"""
run_archcritic_workflow.py
--------------------------
End-to-end ArchCriticAI automation over a folder of images. For every image it:

  a) extracts numeric CV features          (archcritic/core/image_score_pipeline)
  b) maps them to five 0-10 category scores (same module)
  c) retrieves the top-K architectural principles from the Phase-3 RAG index
     (archcritic/core/rag_embed + ChromaDB)
  d) generates a concise, professional, architecture-specific NARRATIVE critique
     with Claude - grounded in the category scores, the overall score and the
     retrieved principles
  e) writes two JSON files per image into data/critiques/:
        <image>.json            -> numeric features + category scores (+ RAG)
        <image>.narrative.json  -> Claude's structured narrative critique

The numeric scores are derived from the actual pixels, so they vary dynamically
with the visual content of each image (brightness, edges, colour, symmetry...).

Claude is reached through the authenticated `claude` CLI (no ANTHROPIC_API_KEY
required). If a key IS present the same CLI is still used; set one only if you
later want to switch to the SDK path.

    python run_archcritic_workflow.py
    python run_archcritic_workflow.py --input data/images --top-k 5
    python run_archcritic_workflow.py --keywords "transparency, circulation"

Fully automatic and idempotent-friendly: re-running simply regenerates outputs.
No manual file editing required.
"""

import argparse
import json
import os
import re
import shutil
import subprocess
import sys

# Make `config` and `archcritic` importable when run as a bare script.
_ROOT = os.path.abspath(os.path.dirname(__file__))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from config import CRITIQUES_DIR, RETRIEVAL_TOP_K
# Reuse the exact feature-pipeline logic (steps a, b, c) so it lives in one place.
from archcritic.core.image_score_pipeline import CATEGORY_KEYS, analyse_one
from archcritic.knowledge.retriever import PrinciplesRetriever

IMAGE_EXTS = (".png", ".jpg", ".jpeg")
DEFAULT_INPUT = os.path.join(_ROOT, "data", "images")
SEED_FROM = os.path.join(_ROOT, "data", "uploads")
DEFAULT_KEYWORDS = "Transparency, Duality, Circulation"

# Human-readable labels for the five categories (used in the prompt + output).
CATEGORY_LABELS = {
    "concept_originality": "Concept & originality",
    "spatial_hierarchy": "Spatial hierarchy & circulation",
    "transparency_light": "Transparency & light",
    "materiality_detailing": "Materiality & detailing",
    "alignment_keywords": "Alignment with keywords",
}


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
def ensure_input_dir(input_dir):
    """Create the input dir and, if it is empty, seed it from data/uploads."""
    os.makedirs(input_dir, exist_ok=True)
    have = [n for n in os.listdir(input_dir)
            if os.path.splitext(n)[1].lower() in IMAGE_EXTS]
    if have:
        return have
    if os.path.isdir(SEED_FROM) and os.path.abspath(SEED_FROM) != os.path.abspath(input_dir):
        seeded = []
        for n in sorted(os.listdir(SEED_FROM)):
            if os.path.splitext(n)[1].lower() in IMAGE_EXTS:
                shutil.copy2(os.path.join(SEED_FROM, n), os.path.join(input_dir, n))
                seeded.append(n)
        kw = os.path.join(SEED_FROM, "keywords.json")
        if os.path.isfile(kw):
            shutil.copy2(kw, os.path.join(input_dir, "keywords.json"))
        if seeded:
            print(f"Seeded {len(seeded)} image(s) into {input_dir} from {SEED_FROM}: "
                  f"{', '.join(seeded)}")
        return seeded
    return []


def find_images(input_dir):
    return [os.path.join(input_dir, n) for n in sorted(os.listdir(input_dir))
            if os.path.splitext(n)[1].lower() in IMAGE_EXTS]


def keywords_for(image_path, input_dir, explicit):
    """Explicit --keywords wins, else per-image keywords.json, else default."""
    if explicit:
        return explicit
    kmap_path = os.path.join(input_dir, "keywords.json")
    if os.path.isfile(kmap_path):
        try:
            kmap = json.load(open(kmap_path, encoding="utf-8"))
            stem = os.path.splitext(os.path.basename(image_path))[0]
            for key in (os.path.basename(image_path), stem):
                if key in kmap:
                    return kmap[key]
        except Exception:
            pass
    return DEFAULT_KEYWORDS


# ---------------------------------------------------------------------------
# Step d) Claude narrative via the authenticated `claude` CLI
# ---------------------------------------------------------------------------
def _strip_json(text):
    """Pull the first JSON object out of CLI output (tolerates ``` fences)."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]
    return json.loads(text)


def build_narrative_prompt(project_title, keywords, result):
    scores = result["category_scores"]
    scored_lines = "\n".join(
        f"  - {CATEGORY_LABELS[k]} ({k}): {scores[k]}/10 - {result['category_reasoning'][k]}"
        for k in CATEGORY_KEYS
    )
    principles = "\n".join(f"  {i+1}. {p}" for i, p in enumerate(result["retrieved_principles"])) \
        or "  (none retrieved)"
    feature_lines = "\n".join(f"  - {b}" for b in result["features"])

    return f"""You are a senior architecture studio critic writing a concise, professional, \
architecture-specific critique of a single student project, presented only as a \
representational image. Use precise architectural vocabulary (parti, threshold, \
datum, circulation spine, massing, fenestration, tectonics, poche). Do NOT invent \
program or context that is not implied by the data below.

PROJECT: {project_title}
DESIGN KEYWORDS: {keywords}

PRE-COMPUTED CATEGORY SCORES (0-10), with the visual evidence behind each:
{scored_lines}

OVERALL SCORE: {result['overall_score']}/10 (mean of the five categories)

VISUAL FEATURES EXTRACTED FROM THE IMAGE:
{feature_lines}

TOP RETRIEVED ARCHITECTURAL PRINCIPLES (Phase-3 RAG knowledge base) - your \
justification MUST reference these by their source where relevant:
{principles}

Return ONLY a single minified-or-pretty JSON object (no markdown, no prose outside \
the JSON) with EXACTLY this shape:
{{
  "headline": "<evocative 3-8 word title for the project>",
  "concept_statement": "<the parti / core idea in 1-2 sentences>",
  "category_critiques": {{
    "concept_originality": "<1-2 sentence critique; keep the given score in mind>",
    "spatial_hierarchy": "<1-2 sentences>",
    "transparency_light": "<1-2 sentences>",
    "materiality_detailing": "<1-2 sentences>",
    "alignment_keywords": "<1-2 sentences on how well it expresses the keywords>"
  }},
  "strengths": ["<short phrase>", "..."],
  "weaknesses": ["<short phrase>", "..."],
  "recommendations": ["<actionable studio-crit suggestion>", "..."],
  "justification": "<2-4 sentences justifying the overall score, explicitly citing \
at least one retrieved principle by its source>"
}}
Keep every field tight and specific to THIS project's data. No filler."""


def claude_narrative(prompt, model=None, timeout=240):
    """Run the prompt through the `claude` CLI in print mode (stdin)."""
    cmd = "claude -p"
    if model:
        cmd += f" --model {model}"
    # Force UTF-8 decoding of the CLI output. Without this, subprocess uses the
    # Windows default (cp1252) and Claude's em-dashes / smart quotes arrive as
    # mojibake ("â€"" instead of "-").
    proc = subprocess.run(
        cmd, shell=True, input=prompt,
        capture_output=True, text=True, timeout=timeout,
        encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"claude CLI failed (exit {proc.returncode}): {proc.stderr.strip()[:500]}"
        )
    return _strip_json(proc.stdout)


# ---------------------------------------------------------------------------
def process_one(image_path, keywords, retriever, top_k, model):
    stem = os.path.splitext(os.path.basename(image_path))[0]

    # Steps a + b + c: numeric features, category scores, RAG retrieval.
    result = analyse_one(image_path, keywords, retriever, top_k)

    # Output 1: numeric features + scores (+ RAG context / reasoning).
    features_doc = {
        "image_file": result["image_file"],
        "project_title": stem,
        "keywords": result["keywords"],
        "numeric_features": result["numeric_features"],
        "feature_notes": result["features"],
        "category_scores": result["category_scores"],
        "overall_score": result["overall_score"],
        "category_reasoning": result["category_reasoning"],
        "retrieved_principles": result["retrieved_principles"],
        "rag_query": result["rag_query"],
        "analysis_method": result["analysis_method"],
    }
    features_path = os.path.join(CRITIQUES_DIR, f"{stem}.json")
    json.dump(features_doc, open(features_path, "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)

    # Step d: Claude narrative critique (grounded in scores + principles).
    prompt = build_narrative_prompt(stem, keywords, result)
    narrative = claude_narrative(prompt, model=model)

    narrative_doc = {
        "image_file": result["image_file"],
        "project_title": stem,
        "keywords": result["keywords"],
        "category_scores": result["category_scores"],
        "overall_score": result["overall_score"],
        "retrieved_principles": result["retrieved_principles"],
        "narrative_critique": narrative,
        "generated_by": "claude CLI (print mode)",
    }
    narrative_path = os.path.join(CRITIQUES_DIR, f"{stem}.narrative.json")
    json.dump(narrative_doc, open(narrative_path, "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)

    return result, os.path.basename(features_path), os.path.basename(narrative_path)


def main():
    parser = argparse.ArgumentParser(
        description="Automate the full ArchCriticAI workflow over an image folder.")
    parser.add_argument("--input", default=DEFAULT_INPUT,
                        help="Folder of images (default: data/images).")
    parser.add_argument("--keywords", default=None,
                        help="Override keywords for ALL images (else per-image keywords.json).")
    parser.add_argument("--top-k", type=int, default=RETRIEVAL_TOP_K,
                        help=f"RAG principles to retrieve (default: {RETRIEVAL_TOP_K}).")
    parser.add_argument("--model", default=None,
                        help="Optional model name for the claude CLI (default: CLI default).")
    args = parser.parse_args()

    os.makedirs(CRITIQUES_DIR, exist_ok=True)
    ensure_input_dir(args.input)
    images = find_images(args.input)

    print(f"=== ArchCriticAI workflow: {len(images)} image(s) in {args.input} ===")
    if not images:
        print("No images found (PNG/JPG/JPEG). Drop images into the folder and re-run.")
        return

    # Phase 3: confirm the RAG index answers before the loop.
    retriever = PrinciplesRetriever()
    probe = retriever.retrieve("circulation and spatial order", k=1)
    if probe:
        print(f"[RAG] index OK (top hit: {probe[0].source}, score {probe[0].score:.3f})")
    else:
        print("[RAG] WARNING: retrieval returned nothing - run "
              "`python -m archcritic.core.rag_embed` to build the index.")

    processed, failed = [], []
    for image_path in images:
        name = os.path.basename(image_path)
        keywords = keywords_for(image_path, args.input, args.keywords)
        print(f"\n--- {name}  (keywords: {keywords}) ---")
        try:
            result, fjson, njson = process_one(
                image_path, keywords, retriever, args.top_k, args.model)
        except Exception as error:
            print(f"  ERROR: {error}")
            failed.append(name)
            continue
        scores = result["category_scores"]
        print(f"  scores: " + ", ".join(
            f"{CATEGORY_LABELS[k]}={scores[k]}" for k in CATEGORY_KEYS))
        print(f"  overall: {result['overall_score']}/10")
        print(f"  wrote: {fjson}, {njson}")
        processed.append((name, result["overall_score"]))

    # Step 4: final confirmation.
    print("\n" + "=" * 64)
    print("WORKFLOW COMPLETE")
    print(f"  processed: {len(processed)} / {len(images)}   failed: {len(failed)}")
    for name, overall in processed:
        print(f"    - {name}  -> overall {overall}/10")
    if failed:
        print(f"  FAILED: {', '.join(failed)}")
    print(f"  outputs in: {CRITIQUES_DIR}")
    print("    per image: <name>.json (features + scores) and "
          "<name>.narrative.json (Claude critique)")


if __name__ == "__main__":
    main()
