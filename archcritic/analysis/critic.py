"""
analysis/critic.py
------------------
Phase 1 orchestrator: take an image + project info, ask the AI, return a
validated `Critique`.

The `retriever` argument is the seam for Phase 3. Today it defaults to None and
the critic works on its own. In Phase 3 you pass a real Retriever and the critic
automatically grounds its feedback in retrieved architecture principles - this
function's body barely changes.
"""

from archcritic.analysis.prompts import build_system_prompt, build_user_prompt
from archcritic.core.images import encode_image_block
from archcritic.core.llm import get_client
from archcritic.core.schemas import Critique
from archcritic.knowledge.retriever import Retriever
from config import ANALYSIS_MODEL, MAX_TOKENS


def analyze_project(
    api_key: str,
    image_bytes: bytes,
    media_type: str,
    project_title: str,
    keywords: str,
    retriever: Retriever | None = None,
) -> Critique:
    """
    Analyse an architecture image and return a structured critique.

    Raises on bad API key or request failure - the UI catches and displays it.
    """
    # --- Phase 3 hook: pull in relevant design theory if a retriever is given ---
    principles = None
    if retriever is not None:
        query = f"{project_title} {keywords}".strip()
        passages = retriever.retrieve(query)
        principles = "\n\n".join(p.text for p in passages)

    # --- Keyless fallback: analyse via the authenticated `claude` CLI ---------
    if not api_key:
        from archcritic.core.cli_backend import cli_analyze_image

        return cli_analyze_image(
            build_system_prompt(principles),
            build_user_prompt(project_title, keywords),
            image_bytes,
            media_type,
            Critique,
            model=ANALYSIS_MODEL,
        )

    # --- Build the request ---------------------------------------------------
    client = get_client(api_key)
    response = client.messages.parse(
        model=ANALYSIS_MODEL,
        max_tokens=MAX_TOKENS,
        system=build_system_prompt(principles),
        messages=[
            {
                "role": "user",
                "content": [
                    encode_image_block(image_bytes, media_type),
                    {"type": "text", "text": build_user_prompt(project_title, keywords)},
                ],
            }
        ],
        # Forces the reply to match our Critique schema - no text parsing needed.
        output_format=Critique,
    )

    return response.parsed_output
