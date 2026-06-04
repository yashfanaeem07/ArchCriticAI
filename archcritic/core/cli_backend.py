"""
core/cli_backend.py
-------------------
A keyless backend that reproduces `client.messages.parse(..., output_format=...)`
using the authenticated `claude` CLI instead of the Anthropic SDK.

It lets the whole app run with NO ANTHROPIC_API_KEY: the CLI uses the user's
existing Claude Code authentication. `core/llm.py` and `analysis/critic.py` fall
back to this whenever no API key is supplied.

How it works: we hand Claude the target Pydantic model's JSON Schema and ask for
a single JSON object that matches it, then validate the reply back into the model
- the same contract `messages.parse` gives us, just over the CLI. Vision works by
writing the image to a temp file and pointing the CLI at its path (the CLI reads
it with its built-in file tools).
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

from pydantic import BaseModel


def cli_available() -> bool:
    """True if the `claude` CLI is on PATH."""
    return shutil.which("claude") is not None


def _extract_json(text: str) -> dict:
    """Pull the first JSON object out of CLI output (tolerates ``` fences)."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end != -1 and end > start:
        text = text[start:end + 1]
    return json.loads(text)


def _run_cli(prompt: str, *, model: str | None = None,
             add_dir: str | None = None, timeout: int = 300) -> str:
    """Run `claude -p` in print mode, feeding the prompt via stdin.

    `add_dir` whitelists an extra directory the CLI may read from - needed when
    the image lives outside the launch directory (e.g. a temp file), since the
    CLI sandboxes file access to its working directory by default.
    """
    if not cli_available():
        raise RuntimeError(
            "The 'claude' CLI is not on PATH. Install Claude Code or set "
            "ANTHROPIC_API_KEY to use the SDK instead."
        )
    cmd = "claude -p"
    if model:
        cmd += f" --model {model}"
    if add_dir:
        cmd += f' --add-dir "{add_dir}"'
    # encoding='utf-8' so Claude's em-dashes / smart quotes are not mangled by
    # the Windows default code page.
    proc = subprocess.run(
        cmd, shell=True, input=prompt,
        capture_output=True, text=True, timeout=timeout,
        encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"claude CLI failed (exit {proc.returncode}): {proc.stderr.strip()[:500]}"
        )
    return proc.stdout


def cli_generate_structured(
    system_prompt: str,
    user_prompt: str,
    output_format: type[BaseModel],
    *,
    image_path: str | None = None,
    add_dir: str | None = None,
    model: str | None = None,
    timeout: int = 300,
) -> BaseModel:
    """
    Return a validated `output_format` instance produced via the `claude` CLI.

    Mirrors `core.llm.generate_structured` (and the critic's vision call) but uses
    the CLI rather than the SDK, so no API key is required.
    """
    schema = json.dumps(output_format.model_json_schema(), ensure_ascii=False)

    parts = [system_prompt.strip(), ""]
    if image_path:
        parts.append(
            f"First, read and visually analyse the image at this absolute path:\n"
            f"  {image_path}\n"
        )
    parts.append(user_prompt.strip())
    parts.append(
        "\nReturn ONLY a single JSON object (no markdown fences, no prose before "
        "or after) that strictly conforms to this JSON Schema:\n"
        f"{schema}\n"
        "Every required field must be present and correctly typed."
    )
    prompt = "\n".join(parts)

    raw = _run_cli(prompt, model=model, add_dir=add_dir, timeout=timeout)
    try:
        data = _extract_json(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            f"claude CLI did not return valid JSON: {exc}. First 300 chars: "
            f"{raw.strip()[:300]!r}"
        )
    return output_format.model_validate(data)


def cli_analyze_image(
    system_prompt: str,
    user_prompt: str,
    image_bytes: bytes,
    media_type: str,
    output_format: type[BaseModel],
    *,
    model: str | None = None,
    timeout: int = 300,
) -> BaseModel:
    """Vision variant: persist the image to a temp file and analyse it via the CLI."""
    ext = {
        "image/png": ".png", "image/jpeg": ".jpg", "image/jpg": ".jpg",
        "image/webp": ".webp", "image/gif": ".gif",
    }.get((media_type or "").lower(), ".png")

    fd, path = tempfile.mkstemp(suffix=ext, prefix="archcritic_")
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(image_bytes)
        # CLI reads files by path; use forward slashes so the path is unambiguous,
        # and whitelist the temp dir so the sandbox allows reading it.
        return cli_generate_structured(
            system_prompt, user_prompt, output_format,
            image_path=path.replace("\\", "/"),
            add_dir=os.path.dirname(path).replace("\\", "/"),
            model=model, timeout=timeout,
        )
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
