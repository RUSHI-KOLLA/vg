"""
VG Pattern Engine — Algorithmic Pattern Detection & Historical Correlation.

Lightweight statistical pattern detection that runs BEFORE LLM calls.
Reduces hallucination by grounding patterns in data, not just LLM intuition.
"""

import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import os


# ═══════════════════════════════════════════════════════════════════
#  1. LINGUISTIC PATTERN DETECTOR
# ═══════════════════════════════════════════════════════════════════

@dataclass
class LinguisticPattern:
    """Detected linguistic pattern from text."""
    pattern_type: str
    description: str
    confidence: float
    examples: List[str] = field(default_factory=list)
    frequency: int = 0


class LinguisticPatternDetector:
    """
    Detects linguistic patterns that reveal underlying dynamics.
    Works on news articles, reports, or any text corpus.
    """

    # Power dynamics indicators
    POWER_PATTERNS = {
        "control_language": [
            r"\bcontrol[s]??\b", r"\bdominat", r"\bmonopol", r"\bhold over\b",
            r"\bcommand\b", r"\bauthority over\b", r"\bpower over\b",
        ],
        "resistance_language": [
            r"\bresist\b", r"\bpush back\b", r"\boppos", r"\bdefy\b",
            r"\bchallenge\b", r"\bfight against\b", r"\bstand up\b",
        ],
        "alliance_language": [
            r"\bally\b", r"\bpartner\b", r"\bcoalition\b", r"\bunite\b",
            r"\bjoin forces\b", r"\bcollaborat", r"\bbacked by\b",
        ],
        "conflict_language": [
            r"\bclash\b", r"\bconfront\b", r"\btension\b", r"\brival\b",
            r"\bhostile\b", r"\badversar", r"\benemy\b",
        ],
    }

    # Economic signal patterns
    ECONOMIC_PATTERNS = {
        "financial_flow": [
            r"\binvest\b", r"\bfund\b", r"\bfinance\b", r"\bcapital\b",
            r"\bprofit\b", r"\brevenue\b", r"\billion\b",  # billions, millions
            r"\beconomic\b", r"\bmarket share\b", r"\btrade\b",
        ],
        "resource_control": [
            r"\bresource\b", r"\basset\b", r"\bproperty\b", r"\bterritory\b",
            r"\breserve\b", r"\bstockpile\b", r"\bsupply chain\b",
        ],
    }

    # Temporal patterns (timing reveals strategy)
    TEMPORAL_PATTERNS = [
        (r"\bbefore.*election\b", "pre_election_timing"),
        (r"\bafter.*scandal\b", "post_scandal_response"),
        (r"\bduring.*crisis\b", "crisis_exploitation"),
        (r"\bannounced.*friday\b", "friday_news_dump"),  # Bad news timing
        (r"\bquietly\b.*\bapproved\b", "stealth_action"),
    ]

    def detect_all(self, text: str) -> Dict[str, List[LinguisticPattern]]:
        """Run all pattern detectors on text."""
        results = {
            "power_dynamics": self._detect_power_patterns(text),
            "economic_signals": self._detect_economic_patterns(text),
            "temporal_signals": self._detect_temporal_patterns(text),
        }
        return results

    def _detect_power_patterns(self, text: str) -> List[LinguisticPattern]:
        """Detect power dynamics language."""
        patterns = []
        text_lower = text.lower()

        for category, regexes in self.POWER_PATTERNS.items():
            matches = []
            for regex in regexes:
                found = re.findall(regex, text_lower)
                matches.extend(found)

            if matches:
                patterns.append(LinguisticPattern(
                    pattern_type=f"power_{category}",
                    description=f"{category.replace('_', ' ').title()} language detected",
                    confidence=min(0.9, 0.3 + len(matches) * 0.1),
                    examples=matches[:5],
                    frequency=len(matches),
                ))

        return patterns

    def _detect_economic_patterns(self, text: str) -> List[LinguisticPattern]:
        """Detect economic signal patterns."""
        patterns = []
        text_lower = text.lower()

        for category, regexes in self.ECONOMIC_PATTERNS.items():
            matches = []
            for regex in regexes:
                found = re.findall(regex, text_lower)
                matches.extend(found)

            if matches:
                patterns.append(LinguisticPattern(
                    pattern_type=f"economic_{category}",
                    description=f"{category.replace('_', ' ').title()} detected",
                    confidence=min(0.9, 0.3 + len(matches) * 0.1),
                    examples=matches[:5],
                    frequency=len(matches),
                ))

        return patterns

    def _detect_temporal_patterns(self, text: str) -> List[LinguisticPattern]:
        """Detect timing-based patterns."""
        patterns = []
        text_lower = text.lower()

        for regex, pattern_name in self.TEMPORAL_PATTERNS:
            matches = re.findall(regex, text_lower)
            if matches:
                patterns.append(LinguisticPattern(
                    pattern_type=f"temporal_{pattern_name}",
                    description=f"Timing pattern: {pattern_name.replace('_', ' ').title()}",
                    confidence=0.7,
                    examples=matches[:3],
                    frequency=len(matches),
                ))

        return patterns


# ═══════════════════════════════════════════════════════════════════
#  2. HISTORICAL ANALogy ENGINE
# ═══════════════════════════════════════════════════════════════════

@dataclass
class HistoricalAnalogy:
    """A historical analogy match."""
    historical_event: str
    current_situation: str
    similarity_score: float
    shared_patterns: List[str] = field(default_factory=list)
    outcome: str = ""
    lesson: str = ""


class HistoricalAnalogyEngine:
    """
    Matches current situations to historical precedents.
    Uses pattern-based similarity, not just keyword matching.
    """

    # Pre-defined historical patterns with outcomes
    HISTORICAL_PATTERNS = {
        "resource_nationalization": {
            "keywords": ["nationalize", "state control", "expropriate", "seize assets"],
            "historical_events": [
                "Iran oil nationalization 1951 → UK embargo, eventual reversal",
                "Chile copper nationalization 1971 → Compensation disputes",
                "Bolivia gas nationalization 2006 → Renegotiated contracts",
            ],
            "typical_outcome": "Short-term economic disruption, long-term sovereignty assertion",
            "pattern_confidence": 0.75,
        },
        "coalition_formation": {
            "keywords": ["alliance", "coalition", "bloc", "unite", "join forces"],
            "historical_events": [
                "NATO formation 1949 → Collective defense against USSR",
                "Non-Aligned Movement 1961 → Third bloc in Cold War",
                "BRICS formation 2009 → Alternative to Western institutions",
            ],
            "typical_outcome": "Shifts balance of power, creates new negotiation dynamics",
            "pattern_confidence": 0.70,
        },
        "leadership_transition": {
            "keywords": ["succession", "new leader", "transition", "handover", "resignation"],
            "historical_events": [
                "Stalin succession 1953 → Khrushchev emergence after power struggle",
                "Mao succession 1976 → Deng gradual rise through consolidation",
                "Thatcher succession 1990 → Major unexpected victory",
            ],
            "typical_outcome": "Initial uncertainty, factional maneuvering, policy shifts",
            "pattern_confidence": 0.65,
        },
        "economic_sanctions": {
            "keywords": ["sanctions", "embargo", "trade restriction", "economic pressure"],
            "historical_events": [
                "Iraq sanctions 1990-2003 → Humanitarian crisis, regime survived",
                "Iran sanctions 2012-2015 → Brought to negotiation table",
                "Russia sanctions 2022- → Economic adaptation, pivot to alternatives",
            ],
            "typical_outcome": "Variable effectiveness; depends on target's alternatives",
            "pattern_confidence": 0.60,
        },
        "proxy_conflict": {
            "keywords": ["proxy", "surrogate", "backed by", "supported by", "arms to"],
            "historical_events": [
                "Vietnam War 1955-75 → US-Soviet proxy, massive escalation",
                "Afghanistan 1980s → US-Pakistan-Saudi backing mujahideen",
                "Syria 2011- → Multiple proxies, complex fragmentation",
            ],
            "typical_outcome": "Prolonged conflict, external power influence, local devastation",
            "pattern_confidence": 0.70,
        },
    }

    def find_analogies(self, text: str, top_k: int = 3) -> List[HistoricalAnalogy]:
        """Find historical analogies for the given text."""
        text_lower = text.lower()
        analogies = []

        for pattern_name, pattern_data in self.HISTORICAL_PATTERNS.items():
            # Count keyword matches
            matches = sum(1 for kw in pattern_data["keywords"] if kw in text_lower)
            if matches == 0:
                continue

            # Calculate similarity score
            match_ratio = matches / len(pattern_data["keywords"])
            similarity = min(0.9, match_ratio * 1.5 * pattern_data["pattern_confidence"])

            if similarity >= 0.3:  # Threshold for relevance
                analogy = HistoricalAnalogy(
                    historical_event=pattern_data["historical_events"][0],
                    current_situation=text[:100] + "..." if len(text) > 100 else text,
                    similarity_score=similarity,
                    shared_patterns=pattern_data["keywords"][:5],
                    outcome=pattern_data["typical_outcome"],
                    lesson=f"History suggests: {pattern_data['typical_outcome']}",
                )
                analogies.append(analogy)

        # Sort by similarity
        analogies.sort(key=lambda a: a.similarity_score, reverse=True)
        return analogies[:top_k]


# ═══════════════════════════════════════════════════════════════════
#  3. NETWORK STRUCTURE ANALYZER
# ═══════════════════════════════════════════════════════════════════

@dataclass
class NetworkNode:
    """A node in the influence network."""
    name: str
    node_type: str  # person, organization, country, institution
    centrality_score: float = 0.0
    connections: List[str] = field(default_factory=list)
    influence_indicators: List[str] = field(default_factory=list)


class NetworkAnalyzer:
    """
    Extracts and analyzes network structures from text.
    Identifies central actors, brokers, and peripheral players.
    """

    # Relationship extraction patterns
    RELATIONSHIP_PATTERNS = [
        (r"\b([A-Z][a-z]+)\s+appointed\s+([A-Z][a-z]+)", "appointment"),
        (r"\b([A-Z][a-z]+).*ally\s+of\s+([A-Z][a-z]+)", "alliance"),
        (r"\b([A-Z][a-z]+).*backed\s+by\s+([A-Z][a-z]+)", "backing"),
        (r"\b([A-Z][a-z]+).*supported\s+by\s+([A-Z][a-z]+)", "support"),
        (r"\b([A-Z][a-z]+).*opposed\s+by\s+([A-Z][a-z]+)", "opposition"),
        (r"\b([A-Z][a-z]+).*criticized\s+([A-Z][a-z]+)", "criticism"),
        (r"\b([A-Z][a-z]+).*met\s+with\s+([A-Z][a-z]+)", "meeting"),
        (r"\b([A-Z][a-z]+).*talks\s+with\s+([A-Z][a-z]+)", "negotiation"),
    ]

    # Influence indicator language
    INFLUENCE_INDICATORS = [
        r"\bkey\s+player\b", r"\bcentral\s+figure\b", r"\binfluential\b",
        r"\bpowerful\b", r"\bleading\s+role\b", r"\barchitect\b",
        r"\bmastermind\b", r"\bbehind\s+the\s+scenes\b", r"\bkingmaker\b",
    ]

    def extract_network(self, text: str) -> Dict[str, NetworkNode]:
        """Extract network structure from text."""
        nodes: Dict[str, NetworkNode] = {}
        edges: List[Tuple[str, str, str]] = []  # (source, target, type)

        # Extract relationships
        for regex, rel_type in self.RELATIONSHIP_PATTERNS:
            matches = re.findall(regex, text)
            for match in matches:
                if len(match) >= 2:
                    source, target = match[0], match[1]
                    edges.append((source, target, rel_type))

                    # Create nodes if they don't exist
                    for name in [source, target]:
                        if name not in nodes:
                            nodes[name] = NetworkNode(
                                name=name,
                                node_type=self._infer_type(name, text),
                            )

                    # Add connections
                    if source in nodes and target in nodes:
                        nodes[source].connections.append(target)
                        nodes[target].connections.append(source)

        # Detect influence indicators
        for name, node in nodes.items():
            for indicator_regex in self.INFLUENCE_INDICATORS:
                if re.search(indicator_regex, text, re.IGNORECASE):
                    # Check if near the name (within 50 chars)
                    pattern = f".{{0,50}}{re.escape(name)}.{{0,50}}{indicator_regex}"
                    if re.search(pattern, text, re.IGNORECASE):
                        node.influence_indicators.append(indicator_regex)

        # Calculate centrality scores
        self._calculate_centrality(nodes)

        return nodes

    def _infer_type(self, name: str, text: str) -> str:
        """Infer node type from context."""
        # Simple heuristics - can be enhanced with NER
        if any(title in text for title in ["PM", "President", "Minister", "Secretary"]):
            return "person"
        if any(org in text for org in ["Party", "Organization", "Foundation"]):
            return "organization"
        if name in ["US", "China", "Russia", "India", "UK", "EU"]:
            return "country"
        return "unknown"

    def _calculate_centrality(self, nodes: Dict[str, NetworkNode]):
        """Calculate degree centrality for each node."""
        if not nodes:
            return

        max_connections = max(len(n.connections) for n in nodes.values()) or 1

        for node in nodes.values():
            # Degree centrality: normalized connection count
            degree_score = len(node.connections) / max_connections

            # Influence bonus
            influence_bonus = len(node.influence_indicators) * 0.1

            node.centrality_score = min(1.0, degree_score + influence_bonus)

    def get_key_actors(self, nodes: Dict[str, NetworkNode], top_k: int = 3) -> List[NetworkNode]:
        """Return top-k most central actors."""
        sorted_nodes = sorted(
            nodes.values(),
            key=lambda n: n.centrality_score,
            reverse=True,
        )
        return sorted_nodes[:top_k]


# ═══════════════════════════════════════════════════════════════════
#  4. CLAIM VERIFICATION LAYER
# ═══════════════════════════════════════════════════════════════════

class ClaimVerifier:
    """
    Verifies claims against evidence sources.
    Reduces hallucination by grounding claims in evidence.
    """

    def verify(self, claim: str, evidence: str) -> Dict[str, Any]:
        """
        Verify a claim against available evidence.

        Returns:
            Dict with: verified, contradicted, evidence_gaps, confidence
        """
        claim_lower = claim.lower()
        evidence_lower = evidence.lower()

        # Extract key entities from claim (simple: capitalized words, numbers)
        claim_entities = set(re.findall(r'\b[A-Z][a-z]+\b', claim))
        claim_numbers = set(re.findall(r'\b\d+(?:\.\d+)?(?:\s*(?:percent|billion|million))?\b', claim_lower))

        # Check entity presence in evidence
        entities_found = [e for e in claim_entities if e.lower() in evidence_lower]
        entity_coverage = len(entities_found) / len(claim_entities) if claim_entities else 0

        # Check number presence (critical for factual claims)
        numbers_found = [n for n in claim_numbers if n.replace(" ", "") in evidence_lower.replace(" ", "")]
        number_coverage = len(numbers_found) / len(claim_numbers) if claim_numbers else 0

        # Check for contradiction markers
        contradiction_markers = ["but", "however", "despite", "contrary to", "not"]
        has_contradiction = any(
            marker in evidence_lower and claim_lower.split()[0:3] != evidence_lower.split()[0:3]
            for marker in contradiction_markers
        )

        # Calculate verification score
        verification_score = (entity_coverage * 0.5 + number_coverage * 0.5)

        return {
            "verified": verification_score >= 0.6,
            "contradicted": has_contradiction and verification_score < 0.4,
            "entity_coverage": entity_coverage,
            "number_coverage": number_coverage,
            "entities_found": entities_found,
            "evidence_gaps": list(claim_entities - set(entities_found)),
            "confidence": verification_score,
        }


# ═══════════════════════════════════════════════════════════════════
#  5. PATTERN SYNTHESIZER (Main Interface)
# ═══════════════════════════════════════════════════════════════════

@dataclass
class PatternReport:
    """Complete pattern analysis report."""
    linguistic_patterns: Dict[str, List[LinguisticPattern]] = field(default_factory=dict)
    historical_analogies: List[HistoricalAnalogy] = field(default_factory=list)
    key_actors: List[NetworkNode] = field(default_factory=list)
    verified_claims: List[Dict] = field(default_factory=list)
    unverified_claims: List[Dict] = field(default_factory=list)
    overall_confidence: float = 0.0


class PatternEngine:
    """
    Main pattern detection engine combining all analysis layers.
    Call this BEFORE LLM agents to ground their analysis in data.
    """

    def __init__(self):
        self.linguistic_detector = LinguisticPatternDetector()
        self.analogy_engine = HistoricalAnalogyEngine()
        self.network_analyzer = NetworkAnalyzer()
        self.claim_verifier = ClaimVerifier()

    def analyze(self, question: str, news: str = "", evidence: str = "") -> PatternReport:
        """
        Run full pattern analysis pipeline.

        Args:
            question: The analysis question
            news: Web search results (optional)
            evidence: Additional evidence text (optional)
        """
        combined_text = f"{question}\n{news}\n{evidence}"

        report = PatternReport()

        # 1. Linguistic pattern detection
        report.linguistic_patterns = self.linguistic_detector.detect_all(combined_text)

        # 2. Historical analogy matching
        report.historical_analogies = self.analogy_engine.find_analogies(combined_text)

        # 3. Network structure extraction
        nodes = self.network_analyzer.extract_network(combined_text)
        report.key_actors = self.network_analyzer.get_key_actors(nodes)

        # 4. Claim verification (if evidence provided)
        # Extract potential claims from question (simple: treat question as claim template)
        verification = self.claim_verifier.verify(question, evidence or news)
        if verification["verified"]:
            report.verified_claims.append(verification)
        else:
            report.unverified_claims.append(verification)

        # 5. Calculate overall confidence
        confidence_factors = [
            len(report.historical_analogies) > 0,  # Has historical precedent
            len(report.key_actors) > 0,  # Identified key actors
            len(report.verified_claims) > 0,  # Some claims verified
            any(p for patterns in report.linguistic_patterns.values() for p in patterns),  # Patterns detected
        ]
        report.overall_confidence = sum(confidence_factors) / len(confidence_factors)

        return report

    def get_pattern_summary(self, report: PatternReport) -> str:
        """Generate a compact pattern summary for LLM context."""
        lines = ["=== PATTERN ANALYSIS ==="]

        # Linguistic patterns
        all_patterns = []
        for category, patterns in report.linguistic_patterns.items():
            for p in patterns:
                all_patterns.append(f"- {p.pattern_type}: {p.frequency} occurrences")

        if all_patterns:
            lines.append("LINGUISTIC SIGNALS:")
            lines.extend(all_patterns[:5])  # Top 5

        # Historical analogies
        if report.historical_analogies:
            lines.append("\nHISTORICAL PARALLELS:")
            for analogy in report.historical_analogies[:2]:
                lines.append(f"- {analogy.historical_event} (similarity: {analogy.similarity_score:.2f})")
                lines.append(f"  Lesson: {analogy.lesson}")

        # Key actors
        if report.key_actors:
            lines.append("\nKEY ACTORS:")
            for actor in report.key_actors[:3]:
                lines.append(f"- {actor.name} (centrality: {actor.centrality_score:.2f}, connections: {len(actor.connections)})")

        # Verification status
        if report.unverified_claims:
            lines.append("\n⚠ UNVERIFIED CLAIMS:")
            for claim in report.unverified_claims[:2]:
                gaps = claim.get("evidence_gaps", [])
                if gaps:
                    lines.append(f"- Missing evidence for: {', '.join(gaps[:3])}")

        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
#  GLOBAL PATTERN ENGINE INSTANCE
# ═══════════════════════════════════════════════════════════════════

_pattern_engine: Optional[PatternEngine] = None


def get_pattern_engine() -> PatternEngine:
    """Get or create the global pattern engine instance."""
    global _pattern_engine
    if _pattern_engine is None:
        _pattern_engine = PatternEngine()
    return _pattern_engine
