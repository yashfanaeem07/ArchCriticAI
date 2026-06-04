"""
analyze_image.py
----------------
Dynamic, image-specific critique with per-category scores, emitted in the exact
requested JSON shape.

Two analysis methods, selected automatically:

  * LIVE VISION  - when ANTHROPIC_API_KEY is set and the image is readable, the
    vision model extracts visible features and scores each category with real
    architectural reasoning, grounded in retrieved principles.

  * PIXEL HEURISTIC - fallback with no API key. Features and scores are derived
    from the actual image pixels (luminance, colour variety, edge density,
    framing) plus keyword/RAG alignment. These numbers ARE image-specific (they
    change with the pixels) but are a mechanical proxy, NOT a substitute for
    visual architectural judgement. The method is stamped into the JSON so the
    two can never be confused.

    python analyze_image.py --image data/uploads/riverside_library.png --keywords "timber, river view"
    python analyze_image.py --image <path>            # keywords pulled from data/uploads/keywords.json

Output: data/critiques/{stem}_image_critique.json
"""

import argparse
import json
import os
import re

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


def _clamp_score(x):
    return int(max(0, min(10, round(x))))


# ---------------------------------------------------------------------------
# Pixel-heuristic feature extraction (genuinely image-derived, not vision)
# ---------------------------------------------------------------------------
def heuristic_features(image_path):
    img = Image.open(image_path).convert("RGB")
    w, h = img.size
    arr = np.asarray(img, dtype=np.float64) / 255.0  # HxWx3 in [0,1]

    luminance = float(arr.mean())
    # Per-pixel saturation = max-min across channels; mean = colour vividness.
    saturation = float((arr.max(axis=2) - arr.min(axis=2)).mean())
    # Colour variety: spread of pixel colours (how many distinct tones).
    colour_variety = float(arr.reshape(-1, 3).std(axis=0).mean())
    # Edge density: mean gradient magnitude on greyscale -> articulation proxy.
    grey = arr.mean(axis=2)
    gy, gx = np.gradient(grey)
    edge_density = float(np.sqrt(gx ** 2 + gy ** 2).mean())
    aspect = round(w / h, 2)
    dom = arr.reshape(-1, 3).mean(axis=0)
    dom_hex = "#{:02x}{:02x}{:02x}".format(*(int(c * 255) for c in dom))

    stats = {
        "luminance": round(luminance, 3),
        "saturation": round(saturation, 3),
        "colour_variety": round(colour_variety, 3),
        "edge_density": round(edge_density, 3),
        "aspect_ratio": aspect,
        "dominant_colour": dom_hex,
        "resolution": f"{w}x{h}",
    }

    light_word = "bright/well-lit" if luminance > 0.6 else "mid-tone" if luminance > 0.35 else "dark/shadowed"
    edge_word = "highly articulated" if edge_density > 0.08 else "moderately articulated" if edge_density > 0.02 else "large uniform surfaces (few edges)"
    features = [
        f"Overall {light_word} composition (mean luminance {luminance:.2f}) - daylight/transparency read.",
        f"{edge_word.capitalize()} (edge density {edge_density:.3f}) - proxy for circulation/spatial cues.",
        f"Colour variety {colour_variety:.3f}, saturation {saturation:.2f}; dominant tone {dom_hex} - material palette cue.",
        f"{'Landscape' if aspect >= 1 else 'Portrait'} framing {aspect}:1 at {w}x{h} - massing/format cue.",
    ]
    return features, stats


def heuristic_scores(stats, keyword_alignment01):
    lum = stats["luminance"]
    edge = stats["edge_density"]
    variety = stats["colour_variety"]
    sat = stats["saturation"]

    # Documented, transparent mappings from pixel stats -> 0..10.
    scores = {
        # Visual complexity proxy (edges + colour spread).
        "concept_originality": _clamp_score((min(edge / 0.10, 1.0) * 0.6 + min(variety / 0.30, 1.0) * 0.4) * 10),
        # Articulation/edges proxy for spatial & circulation legibility.
        "spatial_hierarchy": _clamp_score(min(edge / 0.10, 1.0) * 10),
        # Brightness proxy for transparency & natural light.
        "transparency_light": _clamp_score(lum * 10),
        # Colour spread + saturation proxy for material richness/detailing.
        "materiality_detailing": _clamp_score((min(variety / 0.30, 1.0) * 0.5 + min(sat / 0.5, 1.0) * 0.5) * 10),
        # How well the keywords map onto known principles (RAG similarity).
        "alignment_keywords": _clamp_score(keyword_alignment01 * 10),
    }
    return scores


# ---------------------------------------------------------------------------
# Live vision path (runs only with an API key + readable image)
# ---------------------------------------------------------------------------
def live_analysis(image_path, keywords, principles_text):
    import mimetypes

    from pydantic import BaseModel, Field

    from config import ANALYSIS_MODEL, MAX_TOKENS
    from archcritic.core.images import encode_image_block
    from archcritic.core.llm import get_client

    class CategoryScore(BaseModel):
        score: int = Field(description="0-10 score for this category.")
        reasoning: str = Field(description="Why this score, citing what is visible.")

    class ImageCritique(BaseModel):
        features: list[str] = Field(description="Bullet list of visible architectural elements.")
        concept_originality: CategoryScore
        spatial_hierarchy: CategoryScore
        transparency_light: CategoryScore
        materiality_detailing: CategoryScore
        alignment_keywords: CategoryScore
        justification: str = Field(description="Short justification of the overall score.")

    system = (
        "You are an architecture studio critic. Look at the image and judge the "
        "design. Extract visible elements (open spaces, circulation, materials, "
        "transparency, massing, natural light). Score each category 0-10 with "
        "concrete reasoning tied to what is visible, and assess alignment with the "
        "student's stated keywords. Ground your reasoning in these retrieved "
        f"principles where relevant:\n\n{principles_text}"
    )
    media_type = mimetypes.guess_type(image_path)[0] or "image/png"
    with open(image_path, "rb") as fh:
        block = encode_image_block(fh.read(), media_type)

    client = get_client(get_api_key())
    resp = client.messages.parse(
        model=ANALYSIS_MODEL,
        max_tokens=MAX_TOKENS,
        system=system,
        messages=[{"role": "user", "content": [
            block,
            {"type": "text", "text": f"Design keywords: {keywords}. Critique this project."},
        ]}],
        output_format=ImageCritique,
    )
    r = resp.parsed_output
    scores = {k: getattr(r, k).score for k in CATEGORY_KEYS}
    reasoning = {k: getattr(r, k).reasoning for k in CATEGORY_KEYS}
    return r.features, scores, reasoning, r.justification


# ---------------------------------------------------------------------------
def retrieve_principles(retriever, keywords, features, top_k):
    feature_text = " ".join(features)
    query = f"{keywords} {feature_text}".strip()
    passages = retriever.retrieve(query, k=top_k)
    principles = [f"{p.source}: {' '.join(p.text.split())[:200]}" for p in passages]
    top_score01 = max((p.score for p in passages), default=0.0)
    return query, principles, max(0.0, min(1.0, top_score01))


def main():
    parser = argparse.ArgumentParser(description="Dynamic image-specific critique.")
    parser.add_argument("--image", required=True)
    parser.add_argument("--keywords", default="")
    parser.add_argument("--top-k", type=int, default=RETRIEVAL_TOP_K)
    args = parser.parse_args()

    image_path = args.image
    stem = os.path.splitext(os.path.basename(image_path))[0]

    # Keywords: arg, else keywords.json next to the image, else empty.
    keywords = args.keywords
    if not keywords:
        kmap_path = os.path.join(os.path.dirname(image_path) or ".", "keywords.json")
        if os.path.isfile(kmap_path):
            kmap = json.load(open(kmap_path, encoding="utf-8"))
            keywords = kmap.get(os.path.basename(image_path), kmap.get(stem, ""))
    keyword_list = [k.strip() for k in re.split(r"[,\n]", keywords) if k.strip()]

    retriever = PrinciplesRetriever()
    api_key = get_api_key()
    can_live = bool(api_key) and os.path.isfile(image_path)

    if can_live:
        # Features come from vision; retrieve with keywords first for grounding.
        _, principles, _ = retrieve_principles(retriever, keywords, [], args.top_k)
        features, scores, reasoning, justification = live_analysis(
            image_path, keywords, "\n".join(principles)
        )
        # Re-retrieve using extracted features + keywords for the final list.
        query, principles, _ = retrieve_principles(retriever, keywords, features, args.top_k)
        method = "live-vision (claude vision model)"
    else:
        features, stats = heuristic_features(image_path)
        query, principles, kw_align = retrieve_principles(retriever, keywords, features, args.top_k)
        scores = heuristic_scores(stats, kw_align)
        reasoning = {
            "concept_originality": f"Heuristic: visual-complexity proxy from edge density {stats['edge_density']:.3f} and colour variety {stats['colour_variety']:.3f}.",
            "spatial_hierarchy": f"Heuristic: edge/articulation density {stats['edge_density']:.3f} as a circulation-legibility proxy.",
            "transparency_light": f"Heuristic: mean luminance {stats['luminance']:.2f} as a daylight/transparency proxy.",
            "materiality_detailing": f"Heuristic: colour variety {stats['colour_variety']:.3f} + saturation {stats['saturation']:.2f} as a material-richness proxy.",
            "alignment_keywords": f"Heuristic: top RAG similarity {kw_align:.2f} between keywords and indexed principles.",
        }
        justification = (
            "PIXEL-HEURISTIC estimate (no vision model). Scores are mechanically "
            "derived from image statistics and keyword/RAG alignment, not from "
            "architectural judgement. Set ANTHROPIC_API_KEY for a real vision critique. "
            f"Image stats: {stats}."
        )
        method = "pixel-heuristic (no vision model)"

    overall = round(sum(scores[k] for k in CATEGORY_KEYS) / len(CATEGORY_KEYS), 1)

    out = {
        "image_file": os.path.basename(image_path),
        "keywords": keyword_list,
        "features": features,
        "retrieved_principles": principles,
        "category_scores": {k: scores[k] for k in CATEGORY_KEYS},
        "overall_score": overall,
        "justification": justification,
        # extras (requested "explain reasoning for each category" + provenance)
        "category_reasoning": reasoning,
        "analysis_method": method,
        "rag_query": query,
    }

    os.makedirs(CRITIQUES_DIR, exist_ok=True)
    out_path = os.path.join(CRITIQUES_DIR, f"{stem}_image_critique.json")
    json.dump(out, open(out_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print(f"[{method}] {os.path.basename(image_path)} -> overall {overall}/10  "
          f"scores={out['category_scores']}")
    print(f"  saved {os.path.basename(out_path)}")
    return out


if __name__ == "__main__":
    main()
