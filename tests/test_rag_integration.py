"""
tests/test_rag_integration.py
-----------------------------
Proves the RAG wiring end-to-end WITHOUT an API key or the heavy embedding stack:

  retriever -> analyze_project -> system prompt sent to Claude

We use a fake retriever (returns sentinel principle text) and a fake Anthropic
client (captures the request, returns a canned critique). This deterministically
verifies requirement 5: retrieval is invoked and the retrieved principle text
appears in the prompt the critic sends - i.e. it grounds the generated critique.

It also confirms requirement 4 - Phase 1 core is untouched: the critic still
works with retriever=None exactly as before.
"""

from archcritic.analysis import critic as critic_module
from archcritic.analysis.critic import analyze_project
from archcritic.analysis.prompts import build_system_prompt
from archcritic.analysis.demo import sample_critique
from archcritic.knowledge.retriever import Passage

_SENTINEL = "SENTINEL PRINCIPLE: expose the main stair near the entry"


class _FakeRetriever:
    """A Retriever that records its query and returns fixed sentinel passages."""

    def __init__(self):
        self.received_query = None
        self.received_k = None

    def retrieve(self, query: str, k: int = 5) -> list[Passage]:
        self.received_query = query
        self.received_k = k
        return [
            Passage(text=_SENTINEL, source="circulation.md", score=0.9),
            Passage(text="Hierarchy is made with light and ceiling height.",
                    source="hierarchy.md", score=0.8),
        ]


class _FakeMessages:
    """Captures the kwargs of messages.parse and returns a canned critique."""

    def __init__(self, captured: dict):
        self._captured = captured

    def parse(self, **kwargs):
        self._captured.update(kwargs)

        class _Response:
            parsed_output = sample_critique()

        return _Response()


class _FakeClient:
    def __init__(self, captured: dict):
        self.messages = _FakeMessages(captured)


def _patch_client(monkeypatch) -> dict:
    """Replace the critic's Anthropic client with a capturing fake. Returns the
    dict that will hold the captured request kwargs."""
    captured: dict = {}
    monkeypatch.setattr(critic_module, "get_client", lambda api_key: _FakeClient(captured))
    return captured


# --- Requirement 5: principle text appears in the critique prompt ------------
def test_retrieved_principles_reach_the_prompt(monkeypatch):
    captured = _patch_client(monkeypatch)
    retriever = _FakeRetriever()

    critique = analyze_project(
        api_key="unused",
        image_bytes=b"fake-image-bytes",
        media_type="image/png",
        project_title="Riverside Library",
        keywords="circulation, threshold",
        retriever=retriever,
    )

    # Retrieval was invoked with the title+keywords query and default top-k = 5.
    assert retriever.received_query == "Riverside Library circulation, threshold"
    assert retriever.received_k == 5

    # The retrieved principle text is embedded in the system prompt sent to Claude.
    assert _SENTINEL in captured["system"]

    # And a valid critique still comes back out of the pipeline.
    assert critique.concept_summary


def test_no_retriever_means_no_principles_in_prompt(monkeypatch):
    """Requirement 4: with RAG off, Phase 1 behaves exactly as before."""
    captured = _patch_client(monkeypatch)

    analyze_project(
        api_key="unused",
        image_bytes=b"img",
        media_type="image/png",
        project_title="Riverside Library",
        keywords="circulation",
        retriever=None,
    )

    # System prompt is the bare critic prompt - no principles section appended.
    assert captured["system"] == build_system_prompt(None)
    assert _SENTINEL not in captured["system"]


# --- The prompt builder actually embeds principles (pure unit) ---------------
def test_build_system_prompt_embeds_principles():
    prompt = build_system_prompt(_SENTINEL)
    assert _SENTINEL in prompt
    # And the grounding instruction is present so the model uses them.
    assert "architecture principles" in prompt.lower()
