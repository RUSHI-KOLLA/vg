"""
VG Pipeline — Question decomposition, evidence collection, knowledge graph.
Updated to use Tavily for live evidence and Groq for LLM calls.
"""

from typing import List, Dict, Any
from vg.core.llm_client import get_llm_client


class QuestionDecomposer:
    """Decomposes complex political questions into factual claims."""

    def __init__(self):
        self.llm = get_llm_client()

    def decompose(self, question: str) -> List[Dict[str, Any]]:
        """Break question into testable factual claims."""
        system_prompt = """You are a political analyst. Decompose the question into 3-5 specific, testable factual claims.
Output as a numbered list. Each claim should be verifiable with evidence."""

        user_prompt = f"Decompose this question into factual claims:\n{question}"

        response = self.llm.chat(system_prompt, user_prompt)
        return self._parse_response(response, question)

    def _parse_response(self, response: str, question: str) -> List[Dict[str, Any]]:
        import re
        claims = []
        lines = re.split(r'[\n\d\.]+', response)
        for i, line in enumerate(lines):
            line = line.strip().strip('"').strip("'").strip(':').strip(',')
            if len(line) > 15 and len(line) < 300:
                claims.append({"claim_id": i + 1, "claim_text": line, "needs_evidence": ["verify"]})
        if not claims:
            claims = [{"claim_id": 1, "claim_text": question, "needs_evidence": ["general"]}]
        return claims[:5]


class EvidenceCollector:
    """Collects evidence from Tavily web search."""

    def __init__(self):
        pass

    def collect(self, claims: List[Dict[str, Any]], max_sources: int = 10) -> List[Dict[str, Any]]:
        """Collect evidence using Tavily search."""
        from vg.search.web import search_news

        evidence = []
        for claim in claims[:3]:
            query = claim.get("claim_text", "")
            news = search_news(query, max_results=3)
            evidence.append({
                "id": f"ev_{claim['claim_id']}",
                "claim_id": claim["claim_id"],
                "content": news,
                "source_name": "Tavily Web Search",
                "source_type": "news",
                "relevance": 0.8,
            })
        return evidence


class KnowledgeGraph:
    """Builds knowledge graph from evidence (simplified)."""

    def __init__(self):
        self.entities = {}
        self.relationships = []

    def build_from_evidence(self, evidence: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract entities and relationships from evidence using LLM."""
        llm = get_llm_client()

        system_prompt = """Extract entities and relationships from the evidence.
Identify: People, Organizations, Countries, Events.
Output JSON: {"entities": [...], "relationships": [...]}"""

        evidence_text = "\n".join([e.get("content", "")[:500] for e in evidence])
        response = llm.chat(system_prompt, f"Evidence:\n{evidence_text}")

        import json
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            return {"entities": [], "relationships": []}
