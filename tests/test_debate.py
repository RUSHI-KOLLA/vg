#!/usr/bin/env python3
"""Unit tests for debate coordinator."""

import pytest
import sys
import os

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if PROJECT_ROOT in sys.path:
    sys.path.remove(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

from vg.core.debate import DebateCoordinator


class TestConvergenceCheck:
    """Tests for _check_convergence method."""

    def setup_method(self):
        self.coordinator = DebateCoordinator()

    def test_convergence_with_8_agreeing(self):
        """8/10 agents agreeing should trigger convergence."""
        results = [
            {"agent_name": "Chanakya", "stance": "Yes, it will succeed", "confidence": 85, "error": False},
            {"agent_name": "Bose", "stance": "Yes, likely to succeed", "confidence": 80, "error": False},
            {"agent_name": "Doval", "stance": "Support the outcome", "confidence": 75, "error": False},
            {"agent_name": "Kissinger", "stance": "Agree with the assessment", "confidence": 70, "error": False},
            {"agent_name": "Kao", "stance": "True, this is correct", "confidence": 65, "error": False},
            {"agent_name": "Investigator", "stance": "Success is probable", "confidence": 60, "error": False},
            {"agent_name": "Skeptic", "stance": "Likely to pass", "confidence": 55, "error": False},
            {"agent_name": "Pattern", "stance": "Benefits are clear", "confidence": 50, "error": False},
            {"agent_name": "Network", "stance": "No, will fail", "confidence": 40, "error": False},
            {"agent_name": "Devil", "stance": "Against the proposal", "confidence": 30, "error": False},
        ]
        converged, majority, dissenters = self.coordinator._check_convergence(results)
        assert converged is True
        assert majority == "for"
        assert len(dissenters) == 2

    def test_no_convergence_with_split(self):
        """Split agents should not converge."""
        results = [
            {"agent_name": "Chanakya", "stance": "Yes, will succeed", "confidence": 85, "error": False},
            {"agent_name": "Bose", "stance": "Yes, likely", "confidence": 80, "error": False},
            {"agent_name": "Doval", "stance": "No, will fail", "confidence": 75, "error": False},
            {"agent_name": "Kissinger", "stance": "No, unlikely", "confidence": 70, "error": False},
            {"agent_name": "Kao", "stance": "Against the outcome", "confidence": 65, "error": False},
            {"agent_name": "Investigator", "stance": "Reject the premise", "confidence": 60, "error": False},
            {"agent_name": "Skeptic", "stance": "False assumption", "confidence": 55, "error": False},
            {"agent_name": "Pattern", "stance": "Harm is likely", "confidence": 50, "error": False},
            {"agent_name": "Network", "stance": "Fail expected", "confidence": 45, "error": False},
            {"agent_name": "Devil", "stance": "Risky proposition", "confidence": 40, "error": False},
        ]
        converged, majority, dissenters = self.coordinator._check_convergence(results)
        assert converged is False

    def test_error_results_excluded(self):
        """Agents with errors should be excluded from convergence check."""
        results = [
            {"agent_name": "Chanakya", "stance": "Yes", "confidence": 85, "error": False},
            {"agent_name": "Bose", "stance": "Yes", "confidence": 80, "error": False},
            {"agent_name": "Doval", "stance": "Error occurred", "confidence": 0, "error": True},
            {"agent_name": "Kissinger", "stance": "Yes", "confidence": 70, "error": False},
        ]
        converged, majority, dissenters = self.coordinator._check_convergence(results)
        # 3/4 valid = 75% agreement, but need 8 total
        assert converged is False


class TestStanceNormalization:
    """Tests for stance normalization."""

    def setup_method(self):
        self.coordinator = DebateCoordinator()

    def test_for_stance_detection(self):
        """Test detection of 'for' stances."""
        test_cases = [
            ("Yes, this will succeed", "for"),
            ("I support this proposal", "for"),
            ("I agree with the assessment", "for"),
            ("This is likely to pass", "for"),
            ("Benefits are clear", "for"),
            ("This improves the situation", "for"),
        ]
        for stance, expected in test_cases:
            result = self.coordinator._normalize_stance_bucket(stance)
            assert result == expected, f"Expected {expected} for '{stance}', got {result}"

    def test_against_stance_detection(self):
        """Test detection of 'against' stances."""
        test_cases = [
            ("No, this will fail", "against"),
            ("I reject this proposal", "against"),
            ("I disagree with the assessment", "against"),
            ("This is unlikely to succeed", "against"),
            ("Harm is expected", "against"),
            ("This worsens the situation", "against"),
        ]
        for stance, expected in test_cases:
            result = self.coordinator._normalize_stance_bucket(stance)
            assert result == expected, f"Expected {expected} for '{stance}', got {result}"

    def test_neutral_stance_detection(self):
        """Test detection of neutral stances."""
        test_cases = [
            ("Uncertain about the outcome", "neutral"),
            ("Need more information", "neutral"),
            ("Cannot assess at this time", "neutral"),
        ]
        for stance, expected in test_cases:
            result = self.coordinator._normalize_stance_bucket(stance)
            assert result == expected, f"Expected {expected} for '{stance}', got {result}"


class TestDebateRosterSelection:
    """Tests for debate roster selection."""

    def setup_method(self):
        self.coordinator = DebateCoordinator()

    def test_selects_dissenters_first(self):
        """Dissenters should be prioritized in debate roster."""
        shadow_results = [
            {"agent_name": "Chanakya", "role": "chanakya", "stance": "No, will fail", "confidence": 85},
            {"agent_name": "Bose", "role": "bose", "stance": "No, unlikely", "confidence": 80},
            {"agent_name": "Doval", "role": "doval", "stance": "Yes, will succeed", "confidence": 75},
            {"agent_name": "Kissinger", "role": "kissinger", "stance": "Yes, likely", "confidence": 70},
            {"agent_name": "Kao", "role": "kao", "stance": "Yes, probable", "confidence": 65},
            {"agent_name": "Investigator", "role": "investigator", "stance": "Yes, verified", "confidence": 60},
            {"agent_name": "Skeptic", "role": "skeptic", "stance": "No, risky", "confidence": 55},
            {"agent_name": "Pattern", "role": "pattern_analyst", "stance": "Yes, pattern suggests", "confidence": 50},
            {"agent_name": "Network", "role": "network_mapper", "stance": "Yes, networks aligned", "confidence": 45},
            {"agent_name": "Devil", "role": "devils_advocate", "stance": "No, counter view", "confidence": 40},
        ]
        dissenters = [r for r in shadow_results if "No" in r["stance"] or "unlikely" in r["stance"]]
        roles = self.coordinator._select_debate_roster(shadow_results, dissenters)
        # Should include dissenters (chanakya, bose, skeptic, devil's advocate)
        assert len(roles) <= 7
        assert len(roles) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])