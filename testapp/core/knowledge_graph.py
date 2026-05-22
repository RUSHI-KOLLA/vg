"""
VG Knowledge Graph Lite — Structured entity/relationship extraction from evidence.

MiroFish-inspired: Instead of feeding raw web text to agents, we first extract
structured intelligence (entities, relationships, factions, timeline) using
a cheap LLM call, then inject a compact knowledge graph that agents can
reason over.

This replaces noisy raw text with a clean intelligence briefing.
"""

import json
import asyncio
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


# ═══════════════════════════════════════════════════════════════════
#  DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════

@dataclass
class Entity:
    """A key actor/entity in the intelligence landscape."""
    name: str
    type: str  # person, party, organization, country, institution
    stance: str = ""  # their position on the question
    power: str = "medium"  # low, medium, high — influence level
    notes: str = ""


@dataclass
class Relationship:
    """A relationship between two entities."""
    source: str
    target: str
    type: str  # allies, opposes, controls, funds, competes_with
    strength: str = "moderate"  # weak, moderate, strong
    notes: str = ""


@dataclass
class KnowledgeGraph:
    """Structured intelligence extracted from evidence."""
    question: str = ""

    # Core graph
    entities: List[Entity] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)

    # Derived intelligence
    factions: Dict[str, List[str]] = field(default_factory=dict)  # faction_name -> [entity_names]
    timeline: List[str] = field(default_factory=list)  # key events in chronological order
    key_facts: List[str] = field(default_factory=list)  # verified factual claims
    unresolved: List[str] = field(default_factory=list)  # open questions / uncertainties
    missing_data: List[str] = field(default_factory=list)  # what data would help but is absent

    # Metadata
    evidence_quality: str = "unknown"  # poor, moderate, strong
    extraction_success: bool = False


# ═══════════════════════════════════════════════════════════════════
#  EXTRACTION PROMPT
# ═══════════════════════════════════════════════════════════════════

KG_EXTRACTION_PROMPT = """You are an intelligence analyst. Extract a structured knowledge graph from the evidence below.

QUESTION being analyzed: {question}

EVIDENCE:
{evidence}

Extract and return ONLY valid JSON with this exact structure:
{{
  "entities": [
    {{"name": "...", "type": "person|party|org|country|institution", "stance": "their position", "power": "low|medium|high"}}
  ],
  "relationships": [
    {{"source": "entity1", "target": "entity2", "type": "allies|opposes|controls|funds|competes_with", "strength": "weak|moderate|strong"}}
  ],
  "factions": {{
    "faction_name": ["entity1", "entity2"]
  }},
  "timeline": ["event1 (date)", "event2 (date)"],
  "key_facts": ["verified fact 1", "verified fact 2"],
  "unresolved": ["open question 1"],
  "missing_data": ["what data would help"],
  "evidence_quality": "poor|moderate|strong"
}}

Rules:
- Extract ONLY from the evidence given. Do not hallucinate entities.
- Include 3-8 entities, 2-5 relationships.
- Keep all values concise (under 15 words each).
- If evidence is thin, say so in evidence_quality and missing_data.
"""


# ═══════════════════════════════════════════════════════════════════
#  KNOWLEDGE GRAPH BUILDER
# ═══════════════════════════════════════════════════════════════════

class KnowledgeGraphBuilder:
    """
    Builds a lightweight knowledge graph from raw evidence using a single LLM call.

    Uses the cheap/fast model (8B) with JSON mode for structured extraction.
    Designed to be cost-efficient — one call, ~200 output tokens.
    """

    async def build(
        self,
        question: str,
        raw_evidence: str,
        llm: Any,
        timeout: int = 15,
    ) -> KnowledgeGraph:
        """
        Extract a knowledge graph from raw evidence text.

        Args:
            question: The political question being analyzed
            raw_evidence: Raw web search results / news text
            llm: Async LLM client (should be the cheap/fast model)
            timeout: Max seconds to wait for extraction

        Returns:
            KnowledgeGraph with extracted entities and relationships
        """
        kg = KnowledgeGraph(question=question)

        # Skip if no real evidence
        if not raw_evidence or len(raw_evidence.strip()) < 50:
            kg.missing_data = ["No web evidence available"]
            kg.evidence_quality = "poor"
            return kg

        # Truncate evidence to fit context
        evidence_trimmed = raw_evidence[:3000]

        prompt = KG_EXTRACTION_PROMPT.format(
            question=question,
            evidence=evidence_trimmed,
        )

        try:
            raw = await asyncio.wait_for(
                llm.chat(
                    "You are a structured intelligence extractor. Return ONLY valid JSON.",
                    prompt,
                    temperature=0.2,  # Low temp for factual extraction
                    max_tokens=512,
                    response_format={"type": "json_object"},
                ),
                timeout=timeout,
            )

            data = json.loads(raw.strip())
            kg = self._parse_response(data, question)
            kg.extraction_success = True

        except asyncio.TimeoutError:
            print("  ⚠ Knowledge graph extraction timed out")
            kg.evidence_quality = "unknown"
        except json.JSONDecodeError as e:
            print(f"  ⚠ Knowledge graph JSON parse failed: {e}")
        except Exception as e:
            print(f"  ⚠ Knowledge graph extraction failed: {e}")

        return kg

    def _parse_response(self, data: Dict[str, Any], question: str) -> KnowledgeGraph:
        """Parse LLM JSON response into a KnowledgeGraph."""
        kg = KnowledgeGraph(question=question)

        # Parse entities
        for e in data.get("entities", []):
            if isinstance(e, dict) and "name" in e:
                kg.entities.append(Entity(
                    name=str(e["name"]),
                    type=str(e.get("type", "unknown")),
                    stance=str(e.get("stance", "")),
                    power=str(e.get("power", "medium")),
                ))

        # Parse relationships
        for r in data.get("relationships", []):
            if isinstance(r, dict) and "source" in r and "target" in r:
                kg.relationships.append(Relationship(
                    source=str(r["source"]),
                    target=str(r["target"]),
                    type=str(r.get("type", "related")),
                    strength=str(r.get("strength", "moderate")),
                ))

        # Parse factions
        factions = data.get("factions", {})
        if isinstance(factions, dict):
            kg.factions = {
                str(k): [str(v) for v in vals] if isinstance(vals, list) else []
                for k, vals in factions.items()
            }

        # Parse lists
        kg.timeline = [str(x) for x in data.get("timeline", []) if x]
        kg.key_facts = [str(x) for x in data.get("key_facts", []) if x]
        kg.unresolved = [str(x) for x in data.get("unresolved", []) if x]
        kg.missing_data = [str(x) for x in data.get("missing_data", []) if x]
        kg.evidence_quality = str(data.get("evidence_quality", "moderate"))

        return kg


    # ═══════════════════════════════════════════════════════════════
    #  FORMATTERS — Compact text for injection into agent prompts
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def format_for_agents(kg: KnowledgeGraph) -> str:
        """
        Format knowledge graph as a compact intelligence briefing for agents.

        Target: ~200-300 tokens. Agents get structured facts, not raw noise.
        """
        if not kg.extraction_success:
            return ""

        lines = ["=== INTELLIGENCE GRAPH ==="]

        # Key actors
        if kg.entities:
            lines.append("\nKEY ACTORS:")
            for e in kg.entities[:6]:
                power_icon = {"high": "★", "medium": "●", "low": "○"}.get(e.power, "●")
                stance_part = f" → {e.stance}" if e.stance else ""
                lines.append(f"  {power_icon} {e.name} ({e.type}){stance_part}")

        # Relationships
        if kg.relationships:
            lines.append("\nRELATIONSHIPS:")
            for r in kg.relationships[:4]:
                arrow = {"allies": "⟷", "opposes": "⟺", "controls": "→",
                         "funds": "→$", "competes_with": "⟺"}.get(r.type, "—")
                lines.append(f"  {r.source} {arrow} {r.target} ({r.type})")

        # Factions
        if kg.factions:
            lines.append("\nFACTIONS:")
            for name, members in list(kg.factions.items())[:3]:
                lines.append(f"  [{name}]: {', '.join(members[:4])}")

        # Key facts
        if kg.key_facts:
            lines.append("\nVERIFIED FACTS:")
            for f in kg.key_facts[:4]:
                lines.append(f"  • {f}")

        # What's missing
        if kg.missing_data:
            lines.append("\n⚠ INTELLIGENCE GAPS:")
            for m in kg.missing_data[:3]:
                lines.append(f"  ? {m}")

        lines.append(f"\nEVIDENCE QUALITY: {kg.evidence_quality}")

        return "\n".join(lines)

    @staticmethod
    def format_for_judge(kg: KnowledgeGraph) -> str:
        """
        Format knowledge graph for the judge — includes timeline and unresolved questions.
        Slightly more detailed than the agent version.
        """
        if not kg.extraction_success:
            return ""

        agent_format = KnowledgeGraphBuilder.format_for_agents(kg)

        extra_lines = []

        # Timeline
        if kg.timeline:
            extra_lines.append("\nTIMELINE:")
            for t in kg.timeline[:5]:
                extra_lines.append(f"  → {t}")

        # Unresolved
        if kg.unresolved:
            extra_lines.append("\nUNRESOLVED QUESTIONS:")
            for u in kg.unresolved[:3]:
                extra_lines.append(f"  ? {u}")

        if extra_lines:
            return agent_format + "\n" + "\n".join(extra_lines)
        return agent_format


# ═══════════════════════════════════════════════════════════════════
#  SINGLETON
# ═══════════════════════════════════════════════════════════════════

_kg_builder: Optional[KnowledgeGraphBuilder] = None


def get_kg_builder() -> KnowledgeGraphBuilder:
    """Get or create the global knowledge graph builder."""
    global _kg_builder
    if _kg_builder is None:
        _kg_builder = KnowledgeGraphBuilder()
    return _kg_builder
