"""
VG Upset Pattern Database — Historical cases where consensus was spectacularly wrong.

This is the knowledge base that powers Oracle Mode. Each entry documents:
- What the consensus predicted
- What actually happened
- What signals were missed
- What structural patterns caused the upset

The engine matches current questions against these patterns to estimate
upset probability and surface contrarian hypotheses.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import re


# ═══════════════════════════════════════════════════════════════════
#  DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════

class UpsetCategory:
    """Categories of political upsets."""
    ELECTION = "election_upset"
    POLICY_REVERSAL = "policy_reversal"
    GEOPOLITICAL_SURPRISE = "geopolitical_surprise"
    ECONOMIC_SHOCK = "economic_shock"
    SOCIAL_MOVEMENT = "social_movement"


class UpsetPattern:
    """Structural patterns that cause upsets."""
    ANTI_INCUMBENCY = "anti_incumbency"
    SILENT_VOTER = "silent_voter"
    POLLING_BIAS = "polling_bias"
    ELITE_DISCONNECT = "elite_disconnect"
    RURAL_URBAN_DIVIDE = "rural_urban_divide"
    MEDIA_BUBBLE = "media_bubble"
    LAST_MILE_SHIFT = "last_mile_shift"
    ECONOMIC_ANXIETY = "economic_anxiety"
    IDENTITY_CONSOLIDATION = "identity_consolidation"
    ORGANIZATIONAL_GROUND_GAME = "organizational_ground_game"
    VOTER_FATIGUE = "voter_fatigue"
    SECURITY_OVERRIDE = "security_override"
    BACKLASH_EFFECT = "backlash_effect"
    SOCIAL_MOVEMENT = "social_movement"


@dataclass
class UpsetEntry:
    """A single historical upset case."""
    name: str
    year: int
    region: str
    category: str

    # What happened
    consensus_prediction: str
    actual_outcome: str

    # Why consensus was wrong
    patterns: List[str]
    missed_signals: List[str]
    structural_cause: str

    # Matching keywords — used to find similar current situations
    keywords: List[str]

    # Lessons learned
    lesson: str

    # How confident the consensus was (higher = more shocking upset)
    consensus_confidence: int = 80

    # Similarity weight (how often this pattern recurs)
    recurrence_weight: float = 0.5


# ═══════════════════════════════════════════════════════════════════
#  THE UPSET DATABASE
# ═══════════════════════════════════════════════════════════════════

UPSET_DATABASE: List[UpsetEntry] = [
    # ─── INDIA ───────────────────────────────────────────────────
    UpsetEntry(
        name="West Bengal 2025",
        year=2025,
        region="india",
        category=UpsetCategory.ELECTION,
        consensus_prediction="TMC (Mamata Banerjee) will retain West Bengal comfortably",
        actual_outcome="BJP won West Bengal in a major upset",
        patterns=[
            UpsetPattern.ANTI_INCUMBENCY,
            UpsetPattern.SILENT_VOTER,
            UpsetPattern.MEDIA_BUBBLE,
            UpsetPattern.RURAL_URBAN_DIVIDE,
        ],
        missed_signals=[
            "Rural anger over governance failures not captured by urban-focused polls",
            "Silent BJP voter base unwilling to reveal preference to pollsters",
            "National media focused on Kolkata narrative, missed district-level shifts",
            "Anti-incumbency fatigue after prolonged TMC dominance",
            "Ground-level organizational strength of BJP not reflected in surveys",
        ],
        structural_cause="Media and polling infrastructure concentrated in urban areas "
                         "systematically missed rural voter sentiment shift",
        keywords=["bengal", "west bengal", "mamata", "tmc", "trinamool", "kolkata",
                  "state election", "incumbent", "bjp", "opposition"],
        lesson="When ALL polls agree on an incumbent winning, look for "
               "anti-incumbency signals in rural/semi-urban areas that polls don't reach",
        consensus_confidence=85,
        recurrence_weight=0.8,
    ),

    UpsetEntry(
        name="India General Election 2004",
        year=2004,
        region="india",
        category=UpsetCategory.ELECTION,
        consensus_prediction="BJP-led NDA will win comfortably under 'India Shining' campaign",
        actual_outcome="Congress-led UPA won; Sonia Gandhi became kingmaker",
        patterns=[
            UpsetPattern.ELITE_DISCONNECT,
            UpsetPattern.RURAL_URBAN_DIVIDE,
            UpsetPattern.ECONOMIC_ANXIETY,
            UpsetPattern.ANTI_INCUMBENCY,
        ],
        missed_signals=[
            "Rural India did not experience 'India Shining' economic boom",
            "Farmer distress was widespread but not in mainstream media narrative",
            "Urban elite celebration disconnected from ground reality",
            "Exit polls showed BJP winning — methodology was urban-biased",
        ],
        structural_cause="Economic growth was real but concentrated in urban/IT sectors. "
                         "Rural majority felt left behind. Polls measured urban sentiment.",
        keywords=["india", "general election", "bjp", "congress", "nda", "upa",
                  "india shining", "economic growth", "rural", "farmer"],
        lesson="Economic narratives that don't reach the majority voter base will fail. "
               "Always check: who is actually experiencing the claimed success?",
        consensus_confidence=90,
        recurrence_weight=0.9,
    ),

    UpsetEntry(
        name="Delhi Election 2013 — AAP Emergence",
        year=2013,
        region="india",
        category=UpsetCategory.ELECTION,
        consensus_prediction="Congress or BJP will form government in Delhi",
        actual_outcome="AAP won 28 seats from zero, formed government with Congress support",
        patterns=[
            UpsetPattern.SOCIAL_MOVEMENT,
            UpsetPattern.ANTI_INCUMBENCY,
            UpsetPattern.VOTER_FATIGUE,
        ],
        missed_signals=[
            "Anti-corruption movement energy converted to political capital",
            "New voter registration surge among young, urban voters",
            "Social media mobilization underestimated by traditional pollsters",
        ],
        structural_cause="Social movement energy channeled into electoral politics; "
                         "traditional parties and pollsters couldn't model new party dynamics",
        keywords=["delhi", "aap", "arvind kejriwal", "new party", "anti-corruption",
                  "movement", "protest"],
        lesson="Social movements that build organizational structure can "
               "surprise established parties. Watch protest-to-party conversions.",
        consensus_confidence=75,
        recurrence_weight=0.6,
    ),

    # ─── UNITED STATES ───────────────────────────────────────────
    UpsetEntry(
        name="US Presidential Election 2016",
        year=2016,
        region="us",
        category=UpsetCategory.ELECTION,
        consensus_prediction="Hillary Clinton will win the presidency",
        actual_outcome="Donald Trump won the Electoral College",
        patterns=[
            UpsetPattern.SILENT_VOTER,
            UpsetPattern.POLLING_BIAS,
            UpsetPattern.RURAL_URBAN_DIVIDE,
            UpsetPattern.ELITE_DISCONNECT,
            UpsetPattern.ECONOMIC_ANXIETY,
        ],
        missed_signals=[
            "Rust Belt economic anxiety not captured by national polls",
            "Social desirability bias: Trump voters underreported preference",
            "Turnout models based on 2012 demographics were wrong",
            "Late-breaking Comey letter impact underestimated",
            "Rural voter enthusiasm gap vs urban voter complacency",
        ],
        structural_cause="National polling aggregates masked state-level vulnerabilities. "
                         "Turnout models assumed 2012 demographics would hold.",
        keywords=["us election", "president", "trump", "clinton", "hillary",
                  "polls", "electoral", "swing state", "rust belt", "america"],
        lesson="National poll averages hide state-level vulnerabilities. "
               "Enthusiasm gaps matter more than preference polls.",
        consensus_confidence=85,
        recurrence_weight=0.9,
    ),

    UpsetEntry(
        name="US Midterms 2022 — No Red Wave",
        year=2022,
        region="us",
        category=UpsetCategory.ELECTION,
        consensus_prediction="Republicans will sweep midterms in a massive 'red wave'",
        actual_outcome="Democrats held the Senate, lost House by thin margin — no red wave",
        patterns=[
            UpsetPattern.MEDIA_BUBBLE,
            UpsetPattern.BACKLASH_EFFECT,
            UpsetPattern.IDENTITY_CONSOLIDATION,
        ],
        missed_signals=[
            "Dobbs abortion decision mobilized Democratic base",
            "Candidate quality mattered more than party wave",
            "Youth voter surge underestimated",
            "Issue-specific motivation (abortion rights) overrode economic concerns",
        ],
        structural_cause="Single-issue mobilization (abortion rights) overrode "
                         "traditional midterm dynamics. Media extrapolated from "
                         "presidential approval without accounting for issue motivation.",
        keywords=["midterm", "red wave", "republican", "democrat", "senate",
                  "house", "congress", "abortion", "roe"],
        lesson="Single-issue mobilization can override structural advantages. "
               "Watch for galvanizing events that change turnout calculus.",
        consensus_confidence=75,
        recurrence_weight=0.7,
    ),

    # ─── UNITED KINGDOM ──────────────────────────────────────────
    UpsetEntry(
        name="Brexit Referendum 2016",
        year=2016,
        region="uk",
        category=UpsetCategory.ELECTION,
        consensus_prediction="Remain will win the EU referendum",
        actual_outcome="Leave won 51.9% to 48.1%",
        patterns=[
            UpsetPattern.SILENT_VOTER,
            UpsetPattern.ELITE_DISCONNECT,
            UpsetPattern.RURAL_URBAN_DIVIDE,
            UpsetPattern.IDENTITY_CONSOLIDATION,
        ],
        missed_signals=[
            "Immigration anxiety in Leave-voting areas underpolled",
            "London-centric media missed English town sentiment",
            "Voter registration surge among older, Leave-leaning voters",
            "'Shy Leave' effect: social pressure to say Remain",
        ],
        structural_cause="Urban cosmopolitan polling and media infrastructure "
                         "systematically underweighted non-metropolitan England",
        keywords=["brexit", "referendum", "eu", "european union", "leave", "remain",
                  "uk", "britain", "england", "immigration"],
        lesson="Referendums on identity issues are especially prone to "
               "silent voter effects. Social pressure suppresses true preferences.",
        consensus_confidence=80,
        recurrence_weight=0.8,
    ),

    UpsetEntry(
        name="UK General Election 2017 — Hung Parliament",
        year=2017,
        region="uk",
        category=UpsetCategory.ELECTION,
        consensus_prediction="Theresa May will win a massive majority",
        actual_outcome="Hung parliament; Conservatives lost majority",
        patterns=[
            UpsetPattern.VOTER_FATIGUE,
            UpsetPattern.BACKLASH_EFFECT,
            UpsetPattern.ORGANIZATIONAL_GROUND_GAME,
        ],
        missed_signals=[
            "Labour's ground game mobilization underestimated",
            "Youth voter surge driven by social media campaigns",
            "Theresa May's campaign was robotic and uninspiring",
            "Manifesto backlash ('dementia tax') shifted momentum late",
        ],
        structural_cause="Snap election called from position of strength but "
                         "poor campaign execution + opposition mobilization closed gap",
        keywords=["uk election", "theresa may", "corbyn", "labour", "conservative",
                  "tory", "snap election", "hung parliament"],
        lesson="Calling elections from perceived strength can backfire. "
               "Campaign quality and ground mobilization can close any poll gap.",
        consensus_confidence=80,
        recurrence_weight=0.6,
    ),

    # ─── MIDDLE EAST / GEOPOLITICAL ──────────────────────────────
    UpsetEntry(
        name="Israel Election 1996",
        year=1996,
        region="middle_east",
        category=UpsetCategory.ELECTION,
        consensus_prediction="Shimon Peres will win Israeli PM election",
        actual_outcome="Benjamin Netanyahu won narrowly",
        patterns=[
            UpsetPattern.SECURITY_OVERRIDE,
            UpsetPattern.SILENT_VOTER,
            UpsetPattern.LAST_MILE_SHIFT,
        ],
        missed_signals=[
            "Bus bombing attacks shifted security-focused voters",
            "Mizrahi voter consolidation behind Likud underestimated",
            "Last-week security events changed voter calculus",
        ],
        structural_cause="Security events in the final weeks overrode "
                         "peace process momentum that polls had been tracking",
        keywords=["israel", "netanyahu", "peres", "election", "security",
                  "terrorism", "peace process"],
        lesson="Security events close to election day can override all prior polling. "
               "Watch for crisis events in the final week.",
        consensus_confidence=75,
        recurrence_weight=0.7,
    ),

    UpsetEntry(
        name="Arab Spring 2011",
        year=2011,
        region="middle_east",
        category=UpsetCategory.SOCIAL_MOVEMENT,
        consensus_prediction="Authoritarian regimes in MENA are stable",
        actual_outcome="Tunisia, Egypt, Libya regimes fell; Syria civil war",
        patterns=[
            UpsetPattern.ELITE_DISCONNECT,
            UpsetPattern.ECONOMIC_ANXIETY,
            UpsetPattern.SOCIAL_MOVEMENT,
        ],
        missed_signals=[
            "Youth unemployment at crisis levels across region",
            "Social media organizing capability underestimated",
            "Single triggering event (Bouazizi) catalyzed latent anger",
            "Western intelligence agencies rated all regimes as stable",
        ],
        structural_cause="Decades of suppressed grievances + youth bulge + "
                         "social media organizing tools = latent revolution waiting for trigger",
        keywords=["arab spring", "revolution", "protest", "regime", "authoritarian",
                  "stable", "middle east", "uprising", "youth"],
        lesson="Authoritarian stability is often an illusion. Look for: "
               "youth unemployment, suppressed civil society, and digital organizing capacity.",
        consensus_confidence=90,
        recurrence_weight=0.7,
    ),

    # ─── ECONOMIC / POLICY ───────────────────────────────────────
    UpsetEntry(
        name="2008 Global Financial Crisis",
        year=2008,
        region="global",
        category=UpsetCategory.ECONOMIC_SHOCK,
        consensus_prediction="Housing market is fundamentally sound; contained subprime issues",
        actual_outcome="Global financial system nearly collapsed; worst crisis since 1929",
        patterns=[
            UpsetPattern.ELITE_DISCONNECT,
            UpsetPattern.MEDIA_BUBBLE,
        ],
        missed_signals=[
            "Mortgage default rates rising in subprime sector",
            "CDO complexity hid systemic interconnectedness",
            "Rating agencies compromised by conflicts of interest",
            "A few contrarians (Burry, Paulson) saw it clearly",
        ],
        structural_cause="Complexity of financial instruments hid risk accumulation. "
                         "Incentive structures rewarded ignoring risk.",
        keywords=["financial", "crisis", "economy", "housing", "market", "crash",
                  "recession", "bank", "collapse", "bubble"],
        lesson="When experts unanimously say a complex system is safe, "
               "look for hidden interconnections and misaligned incentives.",
        consensus_confidence=85,
        recurrence_weight=0.6,
    ),

    UpsetEntry(
        name="Demonetization India 2016",
        year=2016,
        region="india",
        category=UpsetCategory.POLICY_REVERSAL,
        consensus_prediction="Demonetization will cripple BJP's rural support base",
        actual_outcome="BJP won UP 2017 with massive majority; rural voters supported Modi",
        patterns=[
            UpsetPattern.ELITE_DISCONNECT,
            UpsetPattern.MEDIA_BUBBLE,
            UpsetPattern.IDENTITY_CONSOLIDATION,
        ],
        missed_signals=[
            "Rural voters saw demonetization as anti-corruption, not anti-poor",
            "Elite/media class projected their inconvenience onto rural masses",
            "Ideological consolidation around Modi's 'strong leader' image",
            "Opposition failed to provide credible alternative narrative",
        ],
        structural_cause="Elite media narrative (demonetization hurts poor) "
                         "diverged from actual voter interpretation (PM fighting corruption)",
        keywords=["demonetization", "modi", "bjp", "rural", "economic policy",
                  "currency", "black money", "corruption"],
        lesson="Media narrative about policy impact ≠ voter interpretation. "
               "Always check how the affected population actually perceives the policy.",
        consensus_confidence=80,
        recurrence_weight=0.7,
    ),
]


# ═══════════════════════════════════════════════════════════════════
#  UPSET PATTERN MATCHER
# ═══════════════════════════════════════════════════════════════════

class UpsetPatternMatcher:
    """
    Matches current political questions against the historical upset database.

    Uses keyword overlap + structural pattern matching to find relevant precedents.
    """

    def __init__(self, database: List[UpsetEntry] = None):
        self.database = database or UPSET_DATABASE

    def find_matching_upsets(
        self,
        question: str,
        news_text: str = "",
        top_k: int = 3,
        min_score: float = 0.15,
    ) -> List[Tuple[UpsetEntry, float]]:
        """
        Find historical upsets that match the current question + news context.

        Returns list of (UpsetEntry, similarity_score) tuples, sorted by score.
        """
        combined = f"{question} {news_text}".lower()
        matches = []

        for entry in self.database:
            score = self._calculate_match_score(combined, entry)
            if score >= min_score:
                matches.append((entry, score))

        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:top_k]

    def _calculate_match_score(self, text: str, entry: UpsetEntry) -> float:
        """Calculate similarity between text and an upset entry."""

        # Keyword overlap (primary signal)
        keyword_hits = sum(1 for kw in entry.keywords if kw in text)
        keyword_ratio = keyword_hits / len(entry.keywords) if entry.keywords else 0

        # Region match bonus
        region_bonus = 0.1 if entry.region in text else 0

        # Category-specific keyword boost
        category_bonus = 0
        if entry.category == UpsetCategory.ELECTION:
            election_words = ["election", "vote", "poll", "win", "seat", "majority"]
            if any(w in text for w in election_words):
                category_bonus = 0.1

        # Recurrence weight (how often this pattern type repeats in history)
        recurrence_factor = entry.recurrence_weight * 0.2

        score = (keyword_ratio * 0.6) + region_bonus + category_bonus + recurrence_factor

        return min(1.0, score)

    def get_upset_patterns_for_question(
        self, question: str, news_text: str = ""
    ) -> Dict:
        """
        Get structured upset analysis for a question.

        Returns dict with:
        - matching_upsets: list of relevant historical upsets
        - dominant_patterns: which upset patterns appear most
        - upset_probability_boost: how much to increase upset probability
        - contrarian_hypotheses: generated from matched patterns
        """
        matches = self.find_matching_upsets(question, news_text)

        if not matches:
            return {
                "matching_upsets": [],
                "dominant_patterns": [],
                "upset_probability_boost": 0,
                "contrarian_hypotheses": [],
            }

        # Count pattern frequencies across matches
        pattern_counts: Dict[str, int] = {}
        for entry, score in matches:
            for pattern in entry.patterns:
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

        # Sort by frequency
        dominant_patterns = sorted(
            pattern_counts.items(), key=lambda x: x[1], reverse=True
        )

        # Calculate upset probability boost based on match quality
        avg_score = sum(s for _, s in matches) / len(matches)
        max_consensus_conf = max(e.consensus_confidence for e, _ in matches)
        upset_boost = min(30, int(avg_score * 40 * (max_consensus_conf / 100)))

        # Generate contrarian hypotheses from matched patterns
        hypotheses = []
        for entry, score in matches[:3]:
            hypotheses.append({
                "source": entry.name,
                "hypothesis": f"Like {entry.name}: {entry.structural_cause}",
                "missed_signals": entry.missed_signals[:3],
                "lesson": entry.lesson,
                "relevance_score": round(score, 2),
            })

        return {
            "matching_upsets": [
                {
                    "name": e.name,
                    "year": e.year,
                    "consensus": e.consensus_prediction,
                    "actual": e.actual_outcome,
                    "score": round(s, 2),
                }
                for e, s in matches
            ],
            "dominant_patterns": [
                {"pattern": p, "frequency": c} for p, c in dominant_patterns[:5]
            ],
            "upset_probability_boost": upset_boost,
            "contrarian_hypotheses": hypotheses,
        }

    def get_upset_summary(self, analysis: Dict) -> str:
        """Generate a compact text summary for LLM context injection."""
        if not analysis.get("matching_upsets"):
            return ""

        lines = ["=== ORACLE MODE: UPSET PATTERN ANALYSIS ==="]

        lines.append("\nHISTORICAL UPSETS MATCHED:")
        for upset in analysis["matching_upsets"][:3]:
            lines.append(
                f"  • {upset['name']} (relevance: {upset['score']:.0%})"
            )
            lines.append(f"    Consensus said: {upset['consensus']}")
            lines.append(f"    Actually happened: {upset['actual']}")

        if analysis.get("dominant_patterns"):
            lines.append("\nDOMINANT UPSET PATTERNS:")
            for p in analysis["dominant_patterns"][:3]:
                pattern_label = p["pattern"].replace("_", " ").title()
                lines.append(f"  • {pattern_label} (seen in {p['frequency']} cases)")

        if analysis.get("contrarian_hypotheses"):
            lines.append("\nCONTRARIAN HYPOTHESES:")
            for h in analysis["contrarian_hypotheses"][:2]:
                lines.append(f"  • {h['hypothesis']}")
                lines.append(f"    Lesson: {h['lesson']}")

        boost = analysis.get("upset_probability_boost", 0)
        if boost > 0:
            lines.append(f"\n⚠ UPSET PROBABILITY BOOST: +{boost}%")
            lines.append("  (Based on historical pattern similarity)")

        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
#  SINGLETON
# ═══════════════════════════════════════════════════════════════════

_matcher: Optional[UpsetPatternMatcher] = None


def get_upset_matcher() -> UpsetPatternMatcher:
    """Get or create the global upset pattern matcher."""
    global _matcher
    if _matcher is None:
        _matcher = UpsetPatternMatcher()
    return _matcher
