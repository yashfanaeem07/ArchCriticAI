"""
tests/test_demo.py
------------------
Confirms the demo sample is a valid critique covering every defined category,
so Demo mode always renders correctly. No API key needed.
"""

from archcritic.analysis.categories import category_names
from archcritic.analysis.demo import sample_critique
from archcritic.core.schemas import Critique


def test_sample_is_a_valid_critique():
    critique = sample_critique()
    assert isinstance(critique, Critique)
    assert 0 <= critique.overall_score <= 10


def test_sample_covers_every_category():
    critique = sample_critique()
    sample_categories = [c.category for c in critique.categories]
    # The demo should score exactly the categories the app defines.
    assert sample_categories == category_names()
