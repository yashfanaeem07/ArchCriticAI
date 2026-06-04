"""
archcritic/core/image_score_pipeline.py
----------------------------------------
Dynamic, image-specific critique driven by a numeric feature pipeline (no API
key required). It extracts named computer-vision features from the actual
pixels, maps them to five 0-10 category scores using BOTH the features and the
user's keywords, grounds the reasoning in Phase-3 RAG principles, and emits the
requested JSON.

    python archcritic/core/image_score_pipeline.py --image data/uploads/civic_plaza_hall.png
    python archcritic/core/image_score_pipeline.py --keywords "Transparency, Duality, Circulation"
    python -m archcritic.core.image_score_pipeline --image <path>

With no --image it processes every image in data/uploads. Output per image:
    data/critiques/{stem}_image_critique.json

NOTE: these scores are mechanical CV heuristics, not a vision model's
architectural judgement. The method is stamped into every JSON. Set
ANTHROPIC_API_KEY and use analyze_image.py for a true vision critique.
"""

import argparse
import json
import os
import re
import sys

# Allow running as a bare script (python archcritic/core/image_score_pipeline.py):
# add the repo root so `config` and `archcritic` import cleanly.
_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import numpy as np
from PIL import Image

from config import CRITIQUES_DIR, RETRIEVAL_TOP_K, get_api_key
from archcritic.knowledge.retriever import PrinciplesRetriever

CATEGORY_KEYS = [
    "concept_originality",
    "spatial_hierarchy",
    "transparency_light",
    "materiality_detailing",
    "alignment_keywords",
]
IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp", ".gif")


def _n(x, cap):
    """Normalise x into [0,1] against a soft cap."""
    return float(max(0.0, min(1.0, x / cap)))


def _score(v01):
    return int(max(0, min(10, round(v01 * 10))))


# ---------------------------------------------------------------------------
# 2) Numeric feature extraction
# ---------------------------------------------------------------------------
def extract_features(image_path):
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    arr = np.asarray(img, dtype=np.float64) / 255.0
    grey = arr.mean(axis=2)

    brightness_mean = float(grey.mean())
    white_ratio = float((grey > 0.85).mean())            # near-white area
    dark_ratio = float((grey < 0.20).mean())

    gy, gx = np.gradient(grey)
    grad = np.sqrt(gx ** 2 + gy ** 2)
    edge_density = float(grad.mean())
    edge_ratio = float((grad > 0.10).mean())             # fraction of strong edges
    open_space_ratio = float((grad < 0.02).mean())       # large smooth/open areas

    # Circulation hints: prominent straight lines (columns/rows of edge energy).
    col_e = np.abs(gx).mean(axis=0)
    row_e = np.abs(gy).mean(axis=1)
    v_lines = int((col_e > col_e.mean() * 2.5).sum()) if col_e.mean() > 0 else 0
    h_lines = int((row_e > row_e.mean() * 2.5).sum()) if row_e.mean() > 0 else 0
    circulation_hints = v_lines + h_lines

    saturation = float((arr.max(axis=2) - arr.min(axis=2)).mean())
    colour_variety = float(arr.reshape(-1, 3).std(axis=0).mean())

    # Duality / symmetry: mirror the left half onto the right.
    half = w // 2
    left = grey[:, :half]
    right = np.fliplr(grey[:, w - half:])
    symmetry = float(1.0 - np.abs(left - right).mean())

    dom = arr.reshape(-1, 3).mean(axis=0)
    dom_hex = "#{:02x}{:02x}{:02x}".format(*(int(c * 255) for c in dom))

    numeric = {
        "open_space_ratio": round(open_space_ratio, 3),
        "brightness_mean": round(brightness_mean, 3),
        "white_ratio": round(white_ratio, 3),
        "dark_ratio": round(dark_ratio, 3),
        "edge_density": round(edge_density, 3),
        "edge_ratio": round(edge_ratio, 3),
        "circulation_hints": circulation_hints,
        "vertical_lines": v_lines,
        "horizontal_lines": h_lines,
        "colour_variety": round(colour_variety, 3),
        "saturation": round(saturation, 3),
        "symmetry": round(symmetry, 3),
        "aspect_ratio": round(w / h, 2),
        "dominant_colour": dom_hex,
        "resolution": f"{w}x{h}",
    }

    light = "bright/glazed" if brightness_mean > 0.6 else "mid-tone" if brightness_mean > 0.35 else "dark"
    artic = "highly articulated" if edge_ratio > 0.08 else "moderately articulated" if edge_ratio > 0.03 else "largely open/uniform"
    bullets = [
        f"Open-space ratio {open_space_ratio:.2f}; {artic} surfaces (strong-edge ratio {edge_ratio:.3f}).",
        f"{light.capitalize()} (brightness {brightness_mean:.2f}, white ratio {white_ratio:.2f}) - transparency/daylight cue.",
        f"Circulation hints: {circulation_hints} dominant lines ({v_lines} vertical, {h_lines} horizontal).",
        f"Material palette: colour variety {colour_variety:.3f}, saturation {saturation:.2f}, dominant {dom_hex}.",
        f"Composition: symmetry {symmetry:.2f} (duality cue), framing {numeric['aspect_ratio']}:1.",
    ]
    return numeric, bullets


# ---------------------------------------------------------------------------
# 3) Map features (+ keywords) to category scores
# ---------------------------------------------------------------------------
# What each keyword "wants" to see in the image -> a function of the features.
def _keyword_expression(keyword, f):
    k = keyword.lower()
    table = {
        ("transparency", "light", "glaz", "open", "daylight"):
            lambda f: 0.6 * f["white_ratio"] + 0.4 * f["brightness_mean"],
        ("circulation", "path", "route", "spine", "movement", "flow"):
            lambda f: _n(f["circulation_hints"], 40),
        ("duality", "contrast", "binary", "two", "mirror", "symmetr"):
            lambda f: f["symmetry"],
        ("massing", "volume", "solid", "mass"):
            lambda f: 1.0 - f["open_space_ratio"],
        ("material", "timber", "concrete", "detail", "texture", "tecton"):
            lambda f: 0.5 * _n(f["colour_variety"], 0.30) + 0.5 * _n(f["saturation"], 0.5),
        ("hierarchy", "order", "axis", "datum"):
            lambda f: 0.5 * _n(f["edge_ratio"], 0.15) + 0.5 * f["symmetry"],
    }
    for keys, fn in table.items():
        if any(s in k for s in keys):
            return fn(f), True
    return None, False  # unknown keyword -> falls back to RAG-only


def map_scores(f, keyword_list, rag_sim01):
    complexity = (_n(f["edge_ratio"], 0.15) + _n(f["colour_variety"], 0.30)
                  + _n(f["circulation_hints"], 40)) / 3.0

    # Keyword-alignment: how well the image expresses each known keyword,
    # blended 50/50 with the RAG keyword<->principle similarity.
    exprs = []
    for kw in keyword_list:
        val, known = _keyword_expression(kw, f)
        if known:
            exprs.append(val)
    keyword_expr = sum(exprs) / len(exprs) if exprs else rag_sim01
    alignment01 = 0.5 * keyword_expr + 0.5 * rag_sim01

    scores = {
        "concept_originality": _score(complexity),
        "spatial_hierarchy": _score(0.6 * _n(f["circulation_hints"], 40) + 0.4 * _n(f["edge_ratio"], 0.15)),
        "transparency_light": _score(0.6 * f["brightness_mean"] + 0.4 * f["white_ratio"]),
        "materiality_detailing": _score(0.5 * _n(f["colour_variety"], 0.30) + 0.3 * _n(f["saturation"], 0.5) + 0.2 * _n(f["edge_ratio"], 0.15)),
        "alignment_keywords": _score(alignment01),
    }
    reasoning = {
        "concept_originality": f"Visual-complexity proxy (edge_ratio {f['edge_ratio']:.3f}, colour_variety {f['colour_variety']:.3f}, {f['circulation_hints']} lines).",
        "spatial_hierarchy": f"Circulation/articulation: {f['circulation_hints']} dominant lines, strong-edge ratio {f['edge_ratio']:.3f}.",
        "transparency_light": f"Brightness {f['brightness_mean']:.2f} and white ratio {f['white_ratio']:.2f} as daylight/transparency proxies.",
        "materiality_detailing": f"Colour variety {f['colour_variety']:.3f}, saturation {f['saturation']:.2f}, detail edges {f['edge_ratio']:.3f}.",
        "alignment_keywords": f"Keyword expression {keyword_expr:.2f} (image vs keywords) blended with RAG similarity {rag_sim01:.2f}.",
    }
    return scores, reasoning


# ---------------------------------------------------------------------------
# 4) RAG retrieval using features + keywords
# ---------------------------------------------------------------------------
def retrieve(retriever, keywords, bullets, top_k):
    query = (keywords + " " + " ".join(bullets)).strip()
    passages = retriever.retrieve(query, k=top_k)
    principles = [f"{p.source}: {' '.join(p.text.split())[:200]}" for p in passages]
    top_sim = max((p.score for p in passages), default=0.0)
    return query, principles, max(0.0, min(1.0, top_sim))


# ---------------------------------------------------------------------------
def analyse_one(image_path, keywords, retriever, top_k):
    keyword_list = [k.strip() for k in re.split(r"[,\n]", keywords) if k.strip()]
    numeric, bullets = extract_features(image_path)
    query, principles, rag_sim = retrieve(retriever, keywords, bullets, top_k)
    scores, reasoning = map_scores(numeric, keyword_list, rag_sim)
    overall = round(sum(scores[k] for k in CATEGORY_KEYS) / len(CATEGORY_KEYS), 1)

    justification = (
        f"Overall {overall}/10 = mean of the five category scores. Computed by the "
        f"numeric feature pipeline (CV heuristics, no vision model): a "
        f"{'bright/glazed' if numeric['brightness_mean'] > 0.6 else 'lower-light'} "
        f"image (brightness {numeric['brightness_mean']:.2f}) with "
        f"{numeric['circulation_hints']} circulation lines and open-space ratio "
        f"{numeric['open_space_ratio']:.2f}. Keyword alignment reflects how the "
        f"pixels express {keyword_list} blended with RAG similarity {rag_sim:.2f}. "
        f"For architectural judgement, run a live vision critique (ANTHROPIC_API_KEY)."
    )

    return {
        "image_file": os.path.basename(image_path),
        "keywords": keyword_list,
        "features": bullets,
        "retrieved_principles": principles,
        "category_scores": {k: scores[k] for k in CATEGORY_KEYS},
        "overall_score": overall,
        "justification": justification,
        "category_reasoning": reasoning,
        "numeric_features": numeric,
        "analysis_method": "python-feature-pipeline (CV heuristics; no vision model)",
        "rag_query": query,
    }


def main():
    parser = argparse.ArgumentParser(description="Numeric feature-pipeline image critique.")
    parser.add_argument("--image", default="")
    parser.add_argument("--input", default="data/uploads")
    parser.add_argument("--keywords", default=None,
                        help="Explicit keywords win over keywords.json. "
                             "Default: 'Transparency, Duality, Circulation'.")
    parser.add_argument("--top-k", type=int, default=RETRIEVAL_TOP_K)
    args = parser.parse_args()
    explicit_kw = args.keywords is not None
    default_kw = "Transparency, Duality, Circulation"

    if get_api_key():
        print("NOTE: ANTHROPIC_API_KEY is set - for a true vision critique use analyze_image.py. "
              "This pipeline always uses CV heuristics by design.")

    retriever = PrinciplesRetriever()
    if args.image:
        images = [args.image]
    elif os.path.isdir(args.input):
        images = [os.path.join(args.input, n) for n in sorted(os.listdir(args.input))
                  if os.path.splitext(n)[1].lower() in IMAGE_EXTS]
    else:
        images = []

    if not images:
        print("No images found. Pass --image <path> or drop images in", args.input)
        return

    os.makedirs(CRITIQUES_DIR, exist_ok=True)
    for image_path in images:
        # Explicit --keywords always wins. Otherwise use per-image keywords.json
        # if present, falling back to the default keyword set.
        if explicit_kw:
            keywords = args.keywords
        else:
            keywords = default_kw
            kmap = os.path.join(os.path.dirname(image_path) or ".", "keywords.json")
            if not args.image and os.path.isfile(kmap):
                try:
                    m = json.load(open(kmap, encoding="utf-8"))
                    keywords = m.get(os.path.basename(image_path), keywords)
                except Exception:
                    pass

        result = analyse_one(image_path, keywords, retriever, args.top_k)
        stem = os.path.splitext(os.path.basename(image_path))[0]
        out_path = os.path.join(CRITIQUES_DIR, f"{stem}_image_critique.json")
        json.dump(result, open(out_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
        print(f"{result['image_file']:24} overall {result['overall_score']}/10  "
              f"{result['category_scores']}")
        print(f"  saved {os.path.basename(out_path)}")


if __name__ == "__main__":
    main()
