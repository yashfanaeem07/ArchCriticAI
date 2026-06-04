"""
tests/test_app_smoke.py
-----------------------
End-to-end smoke test of the Streamlit app via the official AppTest harness.
Runs the real app.py in Demo mode (no API key) and confirms every tab and all
four Phase 2 generators render without error.

This guards the wiring in app.py - the part the unit tests in test_generation.py
can't reach - including the session-state keys, which is where a real bug lived:
the keyword result was written to "keywords" (the design-intent key) instead of
"keywords_result", so it never rendered and clobbered the user's intent.
"""

import os
import sys

import pytest

# AppTest (unlike `streamlit run`) doesn't add the script dir to sys.path.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

AppTest = pytest.importorskip("streamlit.testing.v1").AppTest

_APP = os.path.join(_ROOT, "app.py")


def _demo_checkbox(at):
    """Find the Demo-mode checkbox by label (robust to other checkboxes existing)."""
    return next(c for c in at.checkbox if "Demo mode" in c.label)


def _demo_app_with_critique():
    """Boot the app, switch on Demo mode, and run a (sample) critique."""
    at = AppTest.from_file(_APP, default_timeout=30).run()
    _demo_checkbox(at).set_value(True).run()  # Demo mode on
    next(b for b in at.button if "Critique" in b.label).click().run()
    return at


def test_app_boots_with_all_tabs():
    at = AppTest.from_file(_APP, default_timeout=30).run()
    assert not at.exception
    assert [t.label for t in at.tabs] == [
        "🔍 Analyse (Phase 1)",
        "✨ Generate (Phase 2)",
        "📚 Knowledge (Phase 3)",
    ]


def test_demo_critique_renders_without_api_key():
    at = _demo_app_with_critique()
    assert not at.exception
    md = "\n".join(m.value for m in at.markdown)
    assert "Concept interpretation" in md
    assert "Category breakdown" in md
    assert any(m.label == "Overall score" for m in at.metric)


@pytest.mark.parametrize(
    "button_fragment, expected_markdown",
    [
        ("Generate presentation", "Design thesis"),
        ("Write design narrative", "Key design moves"),
        ("Extract keywords", "Parti"),  # regression: was written to wrong state key
    ],
)
def test_generators_render_in_demo_mode(button_fragment, expected_markdown):
    at = _demo_app_with_critique()
    next(b for b in at.button if button_fragment in b.label).click().run()
    assert not at.exception
    md = "\n".join(m.value for m in at.markdown)
    assert expected_markdown in md


def test_jury_defense_renders_without_error():
    # Jury defence renders into expanders, so assert on clean execution + state.
    at = _demo_app_with_critique()
    next(b for b in at.button if "Prepare jury defence" in b.label).click().run()
    assert not at.exception
    assert "jury" in at.session_state


def test_extract_keywords_does_not_clobber_design_intent():
    """The keyword result must not overwrite the stored design-intent text."""
    at = AppTest.from_file(_APP, default_timeout=30).run()
    _demo_checkbox(at).set_value(True).run()
    at.text_area[0].set_value("permeable ground floor, timber structure")
    next(b for b in at.button if "Critique" in b.label).click().run()

    next(b for b in at.button if "Extract keywords" in b.label).click().run()
    assert not at.exception
    # The result lands in its own key, and the intent text is preserved.
    assert "keywords_result" in at.session_state
    assert at.session_state["keywords"] == "permeable ground floor, timber structure"
