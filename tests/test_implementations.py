#!/usr/bin/env python3
"""Unit tests for agent implementations."""

import pytest
import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT in sys.path:
    sys.path.remove(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

from vg.agents.implementations import (
    _parse_agent_response,
    _has_no_evidence_language,
    _clamp_weak_signal_confidence,
    _truncate_to_complete_sentence,
    compress_to_stance_vectors_v3,
    expand_stance_vector_v3,
    ABSTAIN_RESPONSE,
)


class TestParseAgentResponse:
    """Tests for _parse_agent_response function."""

    def test_parse_json_response(self):
        """Parse valid JSON response."""
        raw = '{"stance": "Yes, will succeed", "confidence": 75, "key_pattern": "economic_pattern"}'
        result = _parse_agent_response(raw, "TestAgent", expect_json=True)
        assert result["stance"] == "Yes, will succeed"
        assert result["confidence"] == 75
        assert result["key_pattern"] == "economic_pattern"
        assert result["error"] is False

    def test_parse_json_with_markdown(self):
        """Parse JSON wrapped in markdown code blocks."""
        raw = '```json\n{"stance": "No", "confidence": 60, "key_pattern": "test"}\n```'
        result = _parse_agent_response(raw, "TestAgent", expect_json=True)
        assert result["stance"] == "No"
        assert result["confidence"] == 60

    def test_parse_pipe_delimited_response(self):
        """Parse pipe-delimited response format."""
        raw = "Yes, will succeed|75|economic_pattern"
        result = _parse_agent_response(raw, "TestAgent", expect_json=False)
        assert result["stance"] == "Yes, will succeed"
        assert result["confidence"] == 75
        assert result["key_pattern"] == "economic_pattern"

    def test_parse_labeled_lines(self):
        """Parse response with labeled lines."""
        raw = """
        Stance: This will likely succeed
        Confidence: 70
        Pattern: structural_inertia
        """
        result = _parse_agent_response(raw, "TestAgent", expect_json=False)
        assert "succeed" in result["stance"].lower()
        assert result["confidence"] == 70
        assert "structural" in result["key_pattern"].lower()

    def test_weak_signal_mode_rewrites_refusal(self):
        """Weak signal mode should rewrite refusal language."""
        raw = "No evidence available"
        result = _parse_agent_response(raw, "Chanakya", expect_json=False, weak_signal_mode=True)
        # Should be rewritten with weak signal inference
        assert "no evidence" not in result["stance"].lower()
        assert 20 <= result["confidence"] <= 80

    def test_fallback_for_unparseable(self):
        """Fallback for unparseable response."""
        raw = "This is some random text that doesn't match any format"
        result = _parse_agent_response(raw, "TestAgent", expect_json=False)
        assert result["error"] is False
        assert "stance" in result


class TestNoEvidenceLanguage:
    """Tests for _has_no_evidence_language function."""

    def test_detects_no_evidence(self):
        """Detect 'no evidence' phrase."""
        assert _has_no_evidence_language("No evidence available") is True
        assert _has_no_evidence_language("Insufficient evidence to determine") is True
        assert _has_no_evidence_language("Cannot assess without data") is True

    def test_allows_valid_analysis(self):
        """Allow valid analysis text."""
        assert _has_no_evidence_language("This will likely succeed") is False
        assert _has_no_evidence_language("Based on the pattern, success is probable") is False
        assert _has_no_evidence_language("Historical precedents suggest this approach works") is False


class TestWeakSignalConfidence:
    """Tests for _clamp_weak_signal_confidence function."""

    def test_clamps_high_confidence(self):
        """High confidence should be clamped to 80 max."""
        assert _clamp_weak_signal_confidence(100) == 80
        assert _clamp_weak_signal_confidence(95) == 80

    def test_clamps_low_confidence(self):
        """Low confidence should be clamped to 20 min."""
        assert _clamp_weak_signal_confidence(10) == 20
        assert _clamp_weak_signal_confidence(5) == 20

    def test_accepts_valid_range(self):
        """Valid confidence should pass through."""
        assert _clamp_weak_signal_confidence(50) == 50
        assert _clamp_weak_signal_confidence(60) == 60

    def test_handles_invalid_input(self):
        """Invalid input should return default."""
        assert _clamp_weak_signal_confidence("invalid") == 45
        assert _clamp_weak_signal_confidence(None) == 45


class TestTruncateToCompleteSentence:
    """Tests for _truncate_to_complete_sentence function."""

    def test_truncates_to_period(self):
        """Truncate to first complete sentence."""
        result = _truncate_to_complete_sentence("This is a test. More text here.")
        assert result == "This is a test."

    def test_handles_semicolon(self):
        """Truncate at semicolon."""
        result = _truncate_to_complete_sentence("First part; Second part")
        assert result == "First part"

    def test_handles_dash(self):
        """Truncate at dash."""
        result = _truncate_to_complete_sentence("Main point - additional detail")
        assert result == "Main point"

    def test_handles_long_text(self):
        """Truncate long text to 160 chars."""
        long_text = "x" * 200
        result = _truncate_to_complete_sentence(long_text)
        assert len(result) <= 160


class TestStanceVectorCompression:
    """Tests for stance vector compression/decompression."""

    def test_compress_stance_vectors(self):
        """Compress results to stance vector format."""
        results = [
            {"role": "chanakya", "stance": "Yes, will succeed", "confidence": 80, "error": False},
            {"role": "bose", "stance": "No, will fail", "confidence": 70, "error": False},
            {"role": "doval", "stance": "Uncertain about outcome", "confidence": 50, "error": False},
        ]
        compressed = compress_to_stance_vectors_v3(results)
        # Should contain role indices with signs
        assert "1:" in compressed  # chanakya is index 1
        assert "2:" in compressed  # bose is index 2
        assert "3:" in compressed  # doval is index 3

    def test_expand_stance_vector(self):
        """Expand compressed stance vector back to agent names."""
        compressed = "1:+0.8|2:-0.7|3:00.5"
        expanded = expand_stance_vector_v3(compressed)
        assert "Chanakya" in expanded
        assert "Bose" in expanded
        assert "Doval" in expanded

    def test_handles_empty_results(self):
        """Handle empty results list."""
        assert compress_to_stance_vectors_v3([]) == ""

    def test_excludes_error_results(self):
        """Exclude results with errors."""
        results = [
            {"role": "chanakya", "stance": "Yes", "confidence": 80, "error": True},
        ]
        compressed = compress_to_stance_vectors_v3(results)
        assert compressed == ""


class TestAbstainResponse:
    """Tests for ABSTAIN_RESPONSE constant."""

    def test_has_required_fields(self):
        """Abstain response should have all required fields."""
        assert "stance" in ABSTAIN_RESPONSE
        assert "confidence" in ABSTAIN_RESPONSE
        assert "error" in ABSTAIN_RESPONSE
        assert ABSTAIN_RESPONSE["error"] is True
        assert ABSTAIN_RESPONSE["confidence"] == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])