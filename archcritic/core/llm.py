"""
core/llm.py
-----------
A thin wrapper around the Anthropic client.

Every phase that talks to the AI goes through here, so if we ever change how we
authenticate or configure the client, we change it in one spot.
"""

from typing import TypeVar

import anthropic
from pydantic import BaseModel

from config import GENERATION_MODEL, MAX_TOKENS

SchemaT = TypeVar("SchemaT", bound=BaseModel)


def get_client(api_key: str) -> anthropic.Anthropic:
    """Create an Anthropic client for the given API key."""
    return anthropic.Anthropic(api_key=api_key)


def generate_structured(
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    output_format: type[SchemaT],
    *,
    model: str = GENERATION_MODEL,
    max_tokens: int = MAX_TOKENS,
) -> SchemaT:
    """
    Run a text-only request and return a validated instance of `output_format`.

    This is the Phase 2 counterpart to the Phase 1 critic: same `messages.parse`
    mechanism that forces the reply to match a Pydantic schema, but with no image
    attached. Every Phase 2 generator (presentation, narrative, keywords, jury
    defence) routes through here.

    With no API key, it falls back to the authenticated `claude` CLI so the app
    works keyless (the CLI uses the user's existing Claude Code login).
    """
    if not api_key:
        from archcritic.core.cli_backend import cli_generate_structured

        return cli_generate_structured(
            system_prompt, user_prompt, output_format, model=model
        )

    client = get_client(api_key)
    response = client.messages.parse(
        model=model,
        max_tokens=max_tokens,
        system=system_prompt,
        messages=[
            {"role": "user", "content": user_prompt},
        ],
        output_format=output_format,
    )
    return response.parsed_output
