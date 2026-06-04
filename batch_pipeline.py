"""
batch_pipeline.py
-----------------
Batch ArchCriticAI over a folder of images. Fully automatic and idempotent:
re-running only processes images that are new or changed since their last report.

    python batch_pipeline.py
    python batch_pipeline.py --input data/uploads --force

Per image it runs Phase 1 (critique), Phase 3 (retrieval) and Phase 2
(presentation + narrative), then writes, linked to the image:
    data/critiques/{image}_critique.json     (Phase 1 + RAG retrieval)
    data/critiques/{image}_presentation.md    (presentation + narrative)
    data/critiques/{image}_report.json        (full combined record)

Keywords per image come from <input>/keywords.json ({filename: "kw"}) or a
sidecar {stem}.keywords.txt, falling back to a default.

The knowledge base is embedded ONCE up front (the principles are identical for
every image, so per-image re-embedding would be pure waste) and retrieval is
confirmed before the loop. Live Anthropic mode kicks in automatically when an
API key is set; otherwise every image falls back to the built-in sample so the
batch always completes.
"""

import argparse
import json
import os

from config import CRITIQUES_DIR, RETRIEVAL_TOP_K, get_api_key
from archcritic.knowledge.retriever import PrinciplesRetriever
# Reuse the single-project phase functions so logic lives in one place.
from pipeline import analyse, embed_principles, generate, render_markdown, retrieve

IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif")
DEFAULT_KEYWORDS = "architecture, spatial order, circulation, concept"


def find_images(input_dir):
    if not os.path.isdir(input_dir):
        return []
    return [
        os.path.join(input_dir, n)
        for n in sorted(os.listdir(input_dir))
        if os.path.splitext(n)[1].lower() in IMAGE_EXTS
    ]


def keywords_for(image_path, input_dir):
    stem = os.path.splitext(os.path.basename(image_path))[0]
    # 1) keywords.json map
    kmap_path = os.path.join(input_dir, "keywords.json")
    if os.path.isfile(kmap_path):
        try:
            kmap = json.load(open(kmap_path, encoding="utf-8"))
            for key in (os.path.basename(image_path), stem):
                if key in kmap:
                    return kmap[key]
        except Exception:
            pass
    # 2) sidecar {stem}.keywords.txt
    sidecar = os.path.join(input_dir, f"{stem}.keywords.txt")
    if os.path.isfile(sidecar):
        return open(sidecar, encoding="utf-8").read().strip()
    # 3) default
    return DEFAULT_KEYWORDS


def needs_processing(image_path, report_path, force):
    """Process if forced, no prior report, or the image is newer than its report."""
    if force or not os.path.exists(report_path):
        return True
    return os.path.getmtime(image_path) > os.path.getmtime(report_path)


def process_one(image_path, keywords, api_key, retriever, top_k):
    stem = os.path.splitext(os.path.basename(image_path))[0]

    # Phase 1 - analyse (grounded in retrieval when live)
    critique, p1_mode = analyse(image_path, keywords, stem, api_key, retriever)

    # Phase 3 - retrieve relevant principles for THIS image's keywords
    query, principles = retrieve(retriever, keywords, stem, top_k)

    # Phase 2 - presentation + narrative
    slides, narrative, p2_mode = generate(critique, keywords, stem, api_key, principles)

    report = {
        "schema_version": 1,
        "image": image_path,
        "image_name": os.path.basename(image_path),
        "project_title": stem,
        "keywords": keywords,
        "mode": "live" if (p1_mode == "live" and p2_mode == "live") else "demo",
        "phase1_mode": p1_mode,
        "phase2_mode": p2_mode,
        "phase1_critique": {**critique.model_dump(), "overall_score": critique.overall_score},
        "phase3_retrieval": {
            "query": query,
            "top_k_requested": top_k,
            "results_returned": len(principles),
            "principles": principles,
        },
        "phase2_presentation": {"slides": slides, "narrative": narrative},
    }

    # Outputs, each named after and linked to the image
    crit_out = os.path.join(CRITIQUES_DIR, f"{stem}_critique.json")
    pres_out = os.path.join(CRITIQUES_DIR, f"{stem}_presentation.md")
    rep_out = os.path.join(CRITIQUES_DIR, f"{stem}_report.json")

    critique_doc = {
        "image": image_path,
        "project_title": stem,
        "keywords": keywords,
        "overall_score": critique.overall_score,
        "critique": critique.model_dump(),
        "rag_retrieval": report["phase3_retrieval"],
    }
    json.dump(critique_doc, open(crit_out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    open(pres_out, "w", encoding="utf-8").write(render_markdown(report))
    json.dump(report, open(rep_out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)

    return report["mode"], (os.path.basename(crit_out), os.path.basename(pres_out), os.path.basename(rep_out))


def main():
    parser = argparse.ArgumentParser(description="Batch-run ArchCriticAI over an image folder.")
    parser.add_argument("--input", default=os.getenv("ARCHCRITIC_UPLOADS", "data/uploads"))
    parser.add_argument("--top-k", type=int, default=RETRIEVAL_TOP_K)
    parser.add_argument("--force", action="store_true", help="Reprocess even if up to date.")
    args = parser.parse_args()

    api_key = get_api_key()
    os.makedirs(CRITIQUES_DIR, exist_ok=True)

    # Phase 3 (once) - build the knowledge base and confirm retrieval works.
    print("=== Phase 3: embedding knowledge base (once for the whole batch) ===")
    index_info = embed_principles()
    retriever = PrinciplesRetriever()
    probe = retriever.retrieve("circulation and spatial order", k=1)
    if probe:
        print(f"[Phase 3] Retrieval OK (top hit: {probe[0].source}, score {probe[0].score:.3f}).")
    else:
        print("[Phase 3] WARNING: retrieval returned nothing - is the knowledge base empty?")

    images = find_images(args.input)
    print(f"\n=== Found {len(images)} image(s) in {args.input} ===")
    if not images:
        print("Nothing to do. Drop images into the folder and re-run.")
        return

    processed, skipped = [], []
    for image_path in images:
        stem = os.path.splitext(os.path.basename(image_path))[0]
        report_path = os.path.join(CRITIQUES_DIR, f"{stem}_report.json")
        if not needs_processing(image_path, report_path, args.force):
            print(f"- SKIP {os.path.basename(image_path)} (up to date)")
            skipped.append(stem)
            continue

        print(f"\n--- Processing {os.path.basename(image_path)} ---")
        keywords = keywords_for(image_path, args.input)
        mode, outs = process_one(image_path, keywords, api_key, retriever, args.top_k)
        print(f"  mode={mode}  keywords={keywords!r}")
        print(f"  wrote: {', '.join(outs)}")
        processed.append((stem, mode))

    # Final confirmation
    print("\n" + "=" * 60)
    print("BATCH COMPLETE")
    print(f"  processed: {len(processed)}   skipped (up to date): {len(skipped)}")
    for stem, mode in processed:
        print(f"    - {stem}  [{mode}]")
    print(f"  outputs in: {CRITIQUES_DIR}")
    if processed and all(m == "demo" for _, m in processed):
        print("  NOTE: all runs were DEMO (no ANTHROPIC_API_KEY). In demo mode the")
        print("        critique is the same sample for every image; retrieval, keywords,")
        print("        naming and file linkage are per-image. Set a key for live critiques.")


if __name__ == "__main__":
    main()
