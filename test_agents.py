#!/usr/bin/env python3
"""Focused tests for agent parsing and weak-signal mode."""

import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT in sys.path:
    sys.path.remove(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

from vg.agents.implementations import _parse_agent_response
from vg.search.web import NO_WEB_RESULTS_TEXT, has_real_news_content


def test_weak_signal_parser_recovers_labeled_output():
    raw = """
    Based on the available weak signals, I will make a directional inference.

    Stance: Coup possible
    Confidence: 45
    Pattern_type: absence_of_transparency

    Explanation:
    - The military remains structurally dominant.
    """
    parsed = _parse_agent_response(
        raw,
        "Chanakya",
        expect_json=False,
        weak_signal_mode=True,
    )

    assert parsed["stance"] == "Coup possible..."
    assert parsed["confidence"] == 45
    assert parsed["key_pattern"] == "absence_of_transparency"


def test_weak_signal_parser_rewrites_refusal_language():
    raw = "No evidence|10|unknown"
    parsed = _parse_agent_response(
        raw,
        "The Skeptic",
        expect_json=False,
        weak_signal_mode=True,
    )

    assert "no evidence" not in parsed["stance"].lower()
    assert 20 <= parsed["confidence"] <= 80


def test_no_web_markers_are_not_treated_as_real_news():
    assert has_real_news_content(NO_WEB_RESULTS_TEXT) is False
    assert has_real_news_content("Web search failed: timeout") is False
    assert has_real_news_content("SUMMARY: Military factions are repositioning.") is True


if __name__ == "__main__":
    test_weak_signal_parser_recovers_labeled_output()
    test_weak_signal_parser_rewrites_refusal_language()
    test_no_web_markers_are_not_treated_as_real_news()
    print("agent tests passed")
