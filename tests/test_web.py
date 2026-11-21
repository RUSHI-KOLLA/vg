#!/usr/bin/env python3
"""Unit tests for web search module."""

import pytest
import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT in sys.path:
    sys.path.remove(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

from vg.search.web import (
    has_real_news_content,
    NO_WEB_RESULTS_TEXT,
    NO_WEB_MARKERS,
)


class TestHasRealNewsContent:
    """Tests for has_real_news_content function."""

    def test_returns_false_for_empty_string(self):
        """Empty string should return False."""
        assert has_real_news_content("") is False
        assert has_real_news_content("   ") is False

    def test_returns_false_for_no_results_marker(self):
        """NO_WEB_RESULTS_TEXT should return False."""
        assert has_real_news_content(NO_WEB_RESULTS_TEXT) is False

    def test_returns_false_for_markers(self):
        """Text with no-results markers should return False."""
        for marker in NO_WEB_MARKERS:
            assert has_real_news_content(f"Some text {marker} more text") is False

    def test_returns_true_for_real_news(self):
        """Real news content should return True."""
        assert has_real_news_content("SUMMARY: Military factions are repositioning.") is True
        assert has_real_news_content("Breaking news from Reuters today...") is True
        assert has_real_news_content("[1] Article Title\n    Content here\n    Source: https://example.com") is True

    def test_handles_none_input(self):
        """None should return False."""
        assert has_real_news_content(None) is False


class TestWebSearchMarkers:
    """Tests for web search marker constants."""

    def test_no_web_markers_exist(self):
        """NO_WEB_MARKERS should contain expected markers."""
        assert "no web search results available" in NO_WEB_MARKERS
        assert "no relevant news found" in NO_WEB_MARKERS
        assert "web search failed" in NO_WEB_MARKERS

    def test_no_web_results_text_contains_marker(self):
        """NO_WEB_RESULTS_TEXT should contain a marker."""
        assert any(marker in NO_WEB_RESULTS_TEXT.lower() for marker in NO_WEB_MARKERS)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])