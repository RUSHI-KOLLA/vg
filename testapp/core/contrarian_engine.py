"""
VG Contrarian Engine — The Heart of Oracle Mode.

When all agents agree (consensus), this engine activates and does four things:
1. INVERSION THINKING: Forces the question "What if consensus is wrong?"
2. UPSET PATTERN MATCHING: Finds historical upsets that match
3. CONTRARIAN SEARCH SIGNALS: Generates queries for opposing viewpoints
4. SILENCE ANALYSIS: Detects what's NOT being said in the evidence

This is what separates VG from every other AI: when everyone agrees,
we don't celebrate — we investigate.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any

from vg.core.upset_patterns import get_upset_matcher, UpsetPatternMatcher


# ═══════════════════════════════════════════════════════════════════
#  1. INVERSION THINKER
# ═══════════════════════════════════════════════════════════════════

class InversionThinker:
    """
    Applies inversion thinking to consensus predictions.

    If consensus says X, this generates structured arguments for NOT-X.
    Inspired by Charlie Munger's "Invert, always invert" principle.
    """

    # Templates for generating inversions
    INVERSION_TEMPLATES = {
        "election": [
            "What hidden voter bloc is being missed by current polling methodology?",
            "What anti-incumbency signals exist that media is ignoring?",
            "What ground-level organizational strength does the underdog have?",
            "What last-mile events could flip voter calculus?",
            "Is there a 'silent voter' effect where social pressure hides true preferences?",
        ],
        "policy": [
            "What implementation barriers will the consensus ignore?",
            "Who are the hidden losers of this policy that will resist?",
            "What unintended consequences does history suggest?",
            "What institutional inertia will prevent the predicted outcome?",
            "Is the policy's public support surface-level or deeply rooted?",
        ],
        "geopolitical": [
            "What back-channel negotiations are invisible to open-source intelligence?",
            "Which smaller actors could disrupt the predicted outcome?",
            "What domestic political pressures might override international logic?",
            "What historical parallel suggests the consensus model is wrong?",
            "What technological or asymmetric capability is being underestimated?",
        ],
        "default": [
            "What would need to be true for the OPPOSITE of consensus to happen?",
            "What are ALL the assumptions behind the consensus — which one is weakest?",
            "Who benefits from the consensus narrative being accepted uncritically?",
            "What information is absent that, if present, would change the analysis?",
            "What structural forces oppose the consensus that operate slowly/invisibly?",
        ],
    }

    def generate_inversions(
        self,
        question: str,
        consensus_stance: str,
        question_type: str = "default",
    ) -> Dict[str, Any]:
        """
        Generate inversion analysis for a consensus prediction.

        Returns structured contrarian hypotheses.
        """
        # Detect question type
        q_lower = question.lower()
        if any(w in q_lower for w in ["election", "vote", "win", "poll", "seat"]):
            q_type = "election"
        elif any(w in q_lower for w in ["policy", "reform", "law", "bill", "act"]):
            q_type = "policy"
        elif any(w in q_lower for w in ["war", "alliance", "treaty", "sanction", "diplomat"]):
            q_type = "geopolitical"
        else:
            q_type = question_type

        templates = self.INVERSION_TEMPLATES.get(q_type, self.INVERSION_TEMPLATES["default"])

        # Generate the inverted prediction
        inverted_stance = self._invert_stance(consensus_stance)

        return {
            "question_type": q_type,
            "consensus": consensus_stance,
            "inverted_prediction": inverted_stance,
            "probing_questions": templates,
            "core_inversion": (
                f"INVERSION: If '{consensus_stance}' is WRONG, then: {inverted_stance}. "
                f"What evidence would support this alternative?"
            ),
        }

    def _invert_stance(self, stance: str) -> str:
        """Grammatically invert a prediction stance."""
        s = stance.strip()

        # Common inversions
        inversions = [
            ("will likely", "will likely NOT"),
            ("will succeed", "will FAIL"),
            ("will fail", "will SUCCEED"),
            ("will win", "will LOSE"),
            ("will lose", "will WIN"),
            ("likely to", "UNLIKELY to"),
            ("unlikely to", "LIKELY to"),
            ("will increase", "will DECREASE"),
            ("will decrease", "will INCREASE"),
            ("probable", "IMPROBABLE"),
            ("improbable", "PROBABLE"),
            ("stable", "UNSTABLE"),
            ("unstable", "STABLE"),
        ]

        for original, replacement in inversions:
            if original.lower() in s.lower():
                # Case-insensitive replacement
                pattern = re.compile(re.escape(original), re.IGNORECASE)
                return pattern.sub(replacement, s, count=1)

        # Default: prepend "The opposite is true"
        return f"CONTRARY: The opposite of '{s[:100]}' is more likely"


# ═══════════════════════════════════════════════════════════════════
#  2. SILENCE ANALYZER
# ═══════════════════════════════════════════════════════════════════

class SilenceAnalyzer:
    """
    Detects what's NOT being said in the evidence.

    In intelligence work, silence is data. What's absent often
    reveals more than what's present.
    """

    # What SHOULD be present for different question types
    EXPECTED_SIGNALS = {
        "election": {
            "ground_reports": [
                "booth level", "ground report", "village", "rural",
                "door to door", "grassroots", "local body",
            ],
            "demographic_data": [
                "voter turnout", "registration", "demographic",
                "youth vote", "women vote", "first-time voter",
            ],
            "organizational": [
                "party worker", "campaign", "rally attendance",
                "volunteer", "booth management",
            ],
            "anti_incumbency": [
                "anti-incumbency", "governance failure", "corruption",
                "unemployment", "price rise", "inflation",
            ],
        },
        "policy": {
            "implementation": [
                "implementation", "execution", "bureaucra",
                "timeline", "capacity", "institutional",
            ],
            "opposition": [
                "opposition", "resistance", "protest",
                "stakeholder", "affected part",
            ],
        },
        "geopolitical": {
            "back_channels": [
                "back channel", "secret", "unofficial",
                "intelligence", "diplomatic",
            ],
            "domestic_pressure": [
                "domestic", "public opinion", "protest",
                "parliament", "legislation",
            ],
        },
    }

    def analyze_silence(
        self, question: str, evidence: str, question_type: str = ""
    ) -> Dict[str, Any]:
        """
        Analyze what's missing from the evidence.

        Returns dict with missing signal categories and risk assessment.
        """
        # Auto-detect question type
        q_lower = question.lower()
        if not question_type:
            if any(w in q_lower for w in ["election", "vote", "win", "poll"]):
                question_type = "election"
            elif any(w in q_lower for w in ["policy", "reform", "law"]):
                question_type = "policy"
            elif any(w in q_lower for w in ["war", "alliance", "treaty"]):
                question_type = "geopolitical"

        expected = self.EXPECTED_SIGNALS.get(question_type, {})
        evidence_lower = evidence.lower()

        missing_categories = {}
        present_categories = {}

        for category, keywords in expected.items():
            present = [kw for kw in keywords if kw in evidence_lower]
            missing = [kw for kw in keywords if kw not in evidence_lower]

            if missing and len(missing) > len(present):
                missing_categories[category] = {
                    "missing_signals": missing,
                    "present_signals": present,
                    "coverage": len(present) / len(keywords) if keywords else 0,
                }
            elif present:
                present_categories[category] = {
                    "signals": present,
                    "coverage": len(present) / len(keywords) if keywords else 0,
                }

        # Calculate silence risk score
        total_categories = len(expected)
        missing_count = len(missing_categories)
        silence_risk = missing_count / total_categories if total_categories > 0 else 0

        return {
            "question_type": question_type,
            "missing_categories": missing_categories,
            "present_categories": present_categories,
            "silence_risk_score": round(silence_risk, 2),
            "critical_gaps": [
                cat for cat, info in missing_categories.items()
                if info["coverage"] < 0.3
            ],
        }

    def get_silence_summary(self, analysis: Dict) -> str:
        """Generate compact text summary of silence analysis."""
        if not analysis.get("missing_categories"):
            return ""

        lines = ["=== SILENCE ANALYSIS ==="]
        lines.append(f"Silence Risk: {analysis['silence_risk_score']:.0%}")

        if analysis.get("critical_gaps"):
            lines.append(f"CRITICAL GAPS: {', '.join(analysis['critical_gaps'])}")

        for cat, info in list(analysis["missing_categories"].items())[:3]:
            label = cat.replace("_", " ").title()
            missing = info["missing_signals"][:3]
            lines.append(
                f"  ⚠ {label}: Missing [{', '.join(missing)}] "
                f"(coverage: {info['coverage']:.0%})"
            )

        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
#  3. CONTRARIAN SEARCH QUERY GENERATOR
# ═══════════════════════════════════════════════════════════════════

class ContrarianSearchGenerator:
    """
    Generates search queries designed to find OPPOSING viewpoints.

    Instead of searching "who will win X election", it searches for:
    - "why Y could upset X election"
    - "ground reality X election"
    - "anti-incumbency signals X"
    """

    def generate_contrarian_queries(
        self,
        question: str,
        consensus_stance: str,
        question_type: str = "",
    ) -> List[str]:
        """
        Generate contrarian search queries that look for opposing evidence.
        """
        q_lower = question.lower()

        # Extract key entities from question
        entities = self._extract_entities(question)

        queries = []

        # 1. Direct contrarian query
        inverted = self._simple_invert(consensus_stance)
        if inverted:
            queries.append(f"why {inverted}")

        # 2. Ground reality query
        queries.append(f"{' '.join(entities)} ground report reality")

        # Election-specific queries
        if any(w in q_lower for w in ["election", "vote", "win"]):
            queries.append(f"{' '.join(entities)} anti-incumbency voter anger")
            queries.append(f"{' '.join(entities)} silent voter shift surprise")
            queries.append(f"{' '.join(entities)} rural ground report")
            queries.append(f"{' '.join(entities)} booth level analysis")

        # Policy-specific queries
        elif any(w in q_lower for w in ["policy", "reform", "succeed"]):
            queries.append(f"{' '.join(entities)} implementation failure risk")
            queries.append(f"{' '.join(entities)} opposition resistance")

        # Geopolitical queries
        elif any(w in q_lower for w in ["war", "alliance", "conflict"]):
            queries.append(f"{' '.join(entities)} back-channel negotiation")
            queries.append(f"{' '.join(entities)} unexpected outcome scenario")

        # 3. Always add: "what everyone is getting wrong about X"
        queries.append(f"what everyone is getting wrong about {' '.join(entities[:3])}")

        return queries[:5]  # Max 5 contrarian queries

    def _extract_entities(self, text: str) -> List[str]:
        """Extract key entities/noun phrases from text."""
        # Simple: capitalized words + key nouns
        words = text.split()
        entities = []
        for w in words:
            clean = re.sub(r'[^\w]', '', w)
            if not clean:
                continue
            # Keep capitalized words, proper nouns, and meaningful nouns
            if clean[0].isupper() or clean.lower() in [
                "election", "policy", "war", "economy", "market",
                "government", "party", "india", "modi", "bjp", "congress",
            ]:
                entities.append(clean)
        return entities[:5]

    def _simple_invert(self, stance: str) -> str:
        """Create a simple inverted search phrase."""
        s = stance.lower().strip()
        # Extract the core prediction
        for prefix in ["will likely ", "will ", "likely ", "expected to "]:
            if prefix in s:
                parts = s.split(prefix, 1)
                if len(parts) > 1:
                    action = parts[1].split()[0] if parts[1].split() else ""
                    subject = parts[0].strip()
                    if action in ["win", "succeed", "pass", "increase"]:
                        opposite = {
                            "win": "lose", "succeed": "fail",
                            "pass": "fail", "increase": "decrease",
                        }.get(action, f"not {action}")
                        return f"{subject} could {opposite}"
        return ""


# ═══════════════════════════════════════════════════════════════════
#  4. CONTRARIAN ENGINE (Main Orchestrator)
# ═══════════════════════════════════════════════════════════════════

@dataclass
class OracleReport:
    """Complete Oracle Mode analysis report."""
    activated: bool = False
    consensus_stance: str = ""
    consensus_agents_count: int = 0

    # Inversion analysis
    inversion: Dict[str, Any] = field(default_factory=dict)

    # Upset pattern matching
    upset_analysis: Dict[str, Any] = field(default_factory=dict)

    # Silence analysis
    silence_analysis: Dict[str, Any] = field(default_factory=dict)

    # Contrarian search queries
    contrarian_queries: List[str] = field(default_factory=list)

    # Final assessment
    upset_probability: int = 0  # 0-100
    upset_scenario: str = ""
    key_signals_to_watch: List[str] = field(default_factory=list)


class ContrarianEngine:
    """
    The heart of Oracle Mode.

    When consensus is too strong, this engine activates and hunts
    for reasons the consensus could be wrong.
    """

    def __init__(self):
        self.inversion_thinker = InversionThinker()
        self.silence_analyzer = SilenceAnalyzer()
        self.search_generator = ContrarianSearchGenerator()
        self.upset_matcher = get_upset_matcher()

    def analyze(
        self,
        question: str,
        consensus_stance: str,
        consensus_count: int,
        total_agents: int,
        evidence: str = "",
        news_text: str = "",
    ) -> OracleReport:
        """
        Run the full Contrarian Engine analysis.

        Args:
            question: The political question
            consensus_stance: What the majority of agents predicted
            consensus_count: How many agents agreed (e.g., 9 out of 10)
            total_agents: Total number of agents
            evidence: Combined evidence text
            news_text: Raw web news text

        Returns:
            OracleReport with contrarian analysis
        """
        report = OracleReport(
            activated=True,
            consensus_stance=consensus_stance,
            consensus_agents_count=consensus_count,
        )

        # 1. INVERSION THINKING
        report.inversion = self.inversion_thinker.generate_inversions(
            question, consensus_stance
        )

        # 2. UPSET PATTERN MATCHING
        report.upset_analysis = self.upset_matcher.get_upset_patterns_for_question(
            question, news_text
        )

        # 3. SILENCE ANALYSIS
        report.silence_analysis = self.silence_analyzer.analyze_silence(
            question, evidence or news_text
        )

        # 4. CONTRARIAN SEARCH QUERIES
        report.contrarian_queries = self.search_generator.generate_contrarian_queries(
            question, consensus_stance
        )

        # 5. CALCULATE UPSET PROBABILITY
        report.upset_probability = self._calculate_upset_probability(report)

        # 6. GENERATE UPSET SCENARIO
        report.upset_scenario = self._generate_upset_scenario(report)

        # 7. KEY SIGNALS TO WATCH
        report.key_signals_to_watch = self._extract_key_signals(report)

        return report

    def _calculate_upset_probability(self, report: OracleReport) -> int:
        """
        Calculate probability that the consensus is wrong.

        Factors:
        - Historical upset pattern matches
        - Silence risk (missing evidence categories)
        - Consensus strength (paradox: stronger consensus = higher upset risk)
        """
        base_probability = 15  # Base 15% — any prediction can be wrong

        # Historical pattern boost
        upset_boost = report.upset_analysis.get("upset_probability_boost", 0)
        base_probability += upset_boost

        # Silence risk boost (missing evidence = higher uncertainty)
        silence_risk = report.silence_analysis.get("silence_risk_score", 0)
        base_probability += int(silence_risk * 15)

        # Consensus paradox: the MORE agents agree, the MORE suspicious
        # (9/10 agreement is more suspicious than 8/10)
        if report.consensus_agents_count >= 9:
            base_probability += 5  # Extra boost for near-unanimous
        if report.consensus_agents_count >= 10:
            base_probability += 5  # Even more for unanimous

        # Cap at reasonable range
        return max(10, min(55, base_probability))

    def _generate_upset_scenario(self, report: OracleReport) -> str:
        """Generate a narrative description of the upset scenario."""
        parts = []

        # From inversion
        inverted = report.inversion.get("inverted_prediction", "")
        if inverted:
            parts.append(inverted)

        # From upset patterns
        hypotheses = report.upset_analysis.get("contrarian_hypotheses", [])
        if hypotheses:
            parts.append(
                f"Historical parallel: {hypotheses[0].get('source', 'Unknown')} — "
                f"{hypotheses[0].get('lesson', '')}"
            )

        # From silence
        critical_gaps = report.silence_analysis.get("critical_gaps", [])
        if critical_gaps:
            gaps_str = ", ".join(g.replace("_", " ") for g in critical_gaps)
            parts.append(f"Critical blind spots: {gaps_str}")

        return " | ".join(parts) if parts else "No specific upset scenario identified"

    def _extract_key_signals(self, report: OracleReport) -> List[str]:
        """Extract actionable signals the user should watch for."""
        signals = []

        # From silence analysis
        for gap in report.silence_analysis.get("critical_gaps", []):
            signals.append(
                f"Watch for: {gap.replace('_', ' ')} data — "
                f"currently missing from evidence"
            )

        # From upset patterns
        for hypothesis in report.upset_analysis.get("contrarian_hypotheses", [])[:2]:
            missed = hypothesis.get("missed_signals", [])
            if missed:
                signals.append(f"Historical miss: {missed[0]}")

        # From inversion
        probes = report.inversion.get("probing_questions", [])
        if probes:
            signals.append(f"Key question: {probes[0]}")

        return signals[:5]

    def get_oracle_context(self, report: OracleReport) -> str:
        """
        Generate compact Oracle Mode context for LLM injection.

        This is what gets fed to the Contrarian Agents and Oracle Judge.
        """
        lines = [
            "╔══════════════════════════════════════════════╗",
            "║  🔮 ORACLE MODE ACTIVATED — CONSENSUS ALERT  ║",
            "╚══════════════════════════════════════════════╝",
            f"\nCONSENSUS: {report.consensus_agents_count} agents agree: "
            f"\"{report.consensus_stance}\"",
            f"UPSET PROBABILITY: {report.upset_probability}%",
        ]

        # Inversion
        inverted = report.inversion.get("inverted_prediction", "")
        if inverted:
            lines.append(f"\nINVERSION: {inverted}")

        # Upset patterns
        upset_summary = self.upset_matcher.get_upset_summary(report.upset_analysis)
        if upset_summary:
            lines.append(f"\n{upset_summary}")

        # Silence
        silence_summary = self.silence_analyzer.get_silence_summary(
            report.silence_analysis
        )
        if silence_summary:
            lines.append(f"\n{silence_summary}")

        # Key probing questions
        probes = report.inversion.get("probing_questions", [])
        if probes:
            lines.append("\nPROBING QUESTIONS:")
            for q in probes[:3]:
                lines.append(f"  ? {q}")

        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
#  SINGLETON
# ═══════════════════════════════════════════════════════════════════

_contrarian_engine: Optional[ContrarianEngine] = None


def get_contrarian_engine() -> ContrarianEngine:
    """Get or create the global contrarian engine."""
    global _contrarian_engine
    if _contrarian_engine is None:
        _contrarian_engine = ContrarianEngine()
    return _contrarian_engine
