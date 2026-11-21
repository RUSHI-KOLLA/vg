"""
VG Agent Implementations — async-first, JSON-structured output.

Each agent receives: question + web news + RAG wisdom (historical only) + other agents' stances.
Each agent returns structured JSON with stance, prediction, confidence, etc.
"""

import asyncio
import json
import re
from typing import List, Dict, Any, Optional

from vg.agents.config import AgentRole, AGENT_CONFIGS, JUDGE_CONFIG
from vg.config import config
from vg.core.llm_client import AsyncGroqLLMClient
from vg.search.web import has_real_news_content


# ──────────────────────────────────────────────────
#  Default "Abstain" response for failed agents
# ──────────────────────────────────────────────────
ABSTAIN_RESPONSE = {
    "stance": "Unable to analyze due to API rate limit. Please try again in 1 minute.",
    "key_pattern": "API rate limited",
    "historical_precedent": "N/A",
    "prediction": "N/A",
    "confidence": 0,
    "principle_applied": "N/A",
    "error": True,
}


NO_EVIDENCE_PHRASES = (
    "no evidence",
    "insufficient evidence",
    "lack of evidence",
    "cannot assess",
    "can't assess",
    "cannot determine",
    "can't determine",
    "unable to determine",
    "not enough information",
    "insufficient information",
    "cannot conclude",
    "can't conclude",
)


def _has_no_evidence_language(text: str) -> bool:
    """Detect refusal-style phrasing that should be rewritten in weak-signal mode."""
    lowered = (text or "").lower()
    return any(phrase in lowered for phrase in NO_EVIDENCE_PHRASES)


def _clamp_weak_signal_confidence(confidence: Any) -> int:
    """Clamp weak-signal mode confidence to the intended probabilistic range."""
    try:
        value = int(confidence)
    except (TypeError, ValueError):
        value = 45
    return max(20, min(80, value))


def _rewrite_weak_signal_stance(agent_name: str, stance: str, pattern: str = "") -> str:
    """Convert refusal-style stance text into a probabilistic weak-signal inference."""
    pattern_text = (pattern or "structural inertia").strip() or "structural inertia"
    name = agent_name or "This agent"
    if _has_no_evidence_language(stance):
        return (
            f"{name} infers from weak signals that the outcome remains uncertain, but "
            f"{pattern_text} suggests hidden pressure is still shaping the situation."
        )
    return stance


def _normalize_markdown_line(line: str) -> str:
    """Remove common markdown wrappers before structured parsing."""
    return re.sub(r"[*`#>-]+", "", line).strip()


def _extract_structured_lines(raw: str) -> tuple[Optional[str], Optional[int], Optional[str]]:
    """Recover structured fields from models that ignore the requested compact format."""
    lines = [_normalize_markdown_line(line) for line in raw.splitlines()]
    lines = [line for line in lines if line]
    stance = None
    confidence = None
    pattern = None

    for index, line in enumerate(lines):
        lowered = line.lower()
        if lowered.startswith("stance:"):
            stance = line.split(":", 1)[1].strip() or stance
        elif lowered.startswith("inference:"):
            value = line.split(":", 1)[1].strip()
            if value:
                stance = value
            elif index + 1 < len(lines):
                stance = lines[index + 1]
        elif lowered.startswith("confidence:"):
            match = re.search(r"(\d{1,3})", line)
            if match:
                confidence = int(match.group(1))
        elif lowered.startswith("pattern_type:") or lowered.startswith("pattern:"):
            pattern = line.split(":", 1)[1].strip() or pattern

    return stance, confidence, pattern


def _compact_fallback_stance(raw: str) -> str:
    """Recover a concise directional stance from a verbose model answer."""
    lines = [_normalize_markdown_line(line) for line in raw.splitlines()]
    for line in lines:
        lowered = line.lower()
        if not line:
            continue
        if lowered.startswith(("explanation:", "reasoning:", "question:", "today's facts:")):
            continue
        if lowered.startswith(("based on the", "given the", "i will")):
            continue
        if "directional inference" in lowered:
            continue
        if "confidence:" in lowered or "pattern_type:" in lowered:
            continue
        return line[:180]
    return raw.strip()[:180]


def _strip_wrapping_noise(text: str) -> str:
    """Remove leading/trailing quotes and whitespace from compact model fields."""
    return (text or "").strip().strip("\"' ")


def _build_structured_result(
    agent_name: str,
    stance: str,
    confidence: Any,
    key_pattern: str,
    weak_signal_mode: bool,
    historical_precedent: str = "N/A",
    prediction: str = "N/A",
    principle_applied: str = "N/A",
) -> Dict[str, Any]:
    """Build a normalized structured agent payload."""
    final_stance = _truncate_to_complete_sentence(_strip_wrapping_noise(stance))
    final_confidence = int(confidence) if str(confidence).isdigit() else 50
    final_pattern = _strip_wrapping_noise(key_pattern) or "unknown"
    if weak_signal_mode:
        final_stance = _rewrite_weak_signal_stance(agent_name, final_stance, final_pattern)
        final_confidence = _clamp_weak_signal_confidence(final_confidence)

    return {
        "agent_name": agent_name,
        "stance": final_stance or "Uncertain, but structural signals still matter.",
        "confidence": final_confidence,
        "key_pattern": final_pattern,
        "historical_precedent": historical_precedent,
        "prediction": prediction,
        "principle_applied": principle_applied,
        "error": False,
    }


def _build_agent_prompt(
    agent_config,
    question: str,
    web_news: str = "",
    rag_wisdom: str = "",
    other_stances: str = "",
    round_num: int = 1,
) -> tuple[str, str]:
    """Build system + user prompt for an agent."""

    system_prompt = agent_config.system_prompt

    has_news = has_real_news_content(web_news)

    if not has_news:
        pattern_hunter_prompt = f"""You are {agent_config.name}, PATTERN HUNTER. No direct news available. Infer from:
1. Absence: What should happen but doesn't?
2. Structure: What economic/political forces persist?
3. History: What similar case rhymes?

NEVER refuse. NEVER say 'no evidence', 'cannot assess', 'insufficient information', or similar.
ALWAYS infer from weak signals and hidden patterns with a probabilistic stance (confidence 20-80%).
Your first clause must state the directional inference, not a disclaimer.
Return ONLY one compact line in this exact format:
stance|confidence|pattern|precedent|prediction|quality"""

        user_parts = [f"QUESTION: {question}"]

        if rag_wisdom:
            user_parts.append(f"\nYOUR OWN WISDOM (from your texts):\n{rag_wisdom}")

        if other_stances and round_num > 1:
            user_parts.append(f"\nOTHER AGENTS SAID (Round {round_num - 1}):\n{other_stances}")

        user_parts.append(pattern_hunter_prompt)

        return system_prompt, "\n".join(user_parts)

    user_parts = [f"QUESTION: {question}"]

    if web_news:
        user_parts.append(f"\nTODAY'S REAL FACTS (from web search):\n{web_news}")

    if rag_wisdom:
        user_parts.append(f"\nYOUR OWN WISDOM (from your texts):\n{rag_wisdom}")

    if other_stances and round_num > 1:
        user_parts.append(f"\nOTHER AGENTS SAID (Round {round_num - 1}):\n{other_stances}")
    
    if has_news:
        user_parts.append(
            "Return exactly one clear sentence focused on your dimension. "
            "Keep it under 18 words and end with a period. "
            "Respond in JSON with: stance, key_pattern, historical_precedent, confidence. "
            "Analyze your dimension ONLY. Do NOT predict outcomes."
        )

    return system_prompt, "\n".join(user_parts)


def _truncate_to_complete_sentence(text: str) -> str:
    """Normalize to one compact readable sentence."""
    if not text:
        return text
    text = re.sub(r"\s+", " ", text).strip()
    text = _strip_wrapping_noise(text)

    if text.endswith((".", "!", "?")):
        sentence_match = re.search(r"(.+?[.!?])(?:\s|$)", text)
        if sentence_match:
            return sentence_match.group(1).strip()

    for delimiter in (";", " - ", " — "):
        if delimiter in text:
            candidate = text.split(delimiter, 1)[0].strip()
            if candidate:
                return candidate

    return text[:160].rstrip(" ,;:-")


def _parse_agent_response(
    raw: str,
    agent_name: str,
    expect_json: bool = True,
    weak_signal_mode: bool = False,
) -> Dict[str, Any]:
    """Parse agent response - handles JSON or pipe-delimited format."""
    raw = raw.strip()
    
    if expect_json:
        try:
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            data = json.loads(raw)
            return _build_structured_result(
                agent_name=agent_name,
                stance=str(data.get("stance", "")),
                confidence=data.get("confidence", 50),
                key_pattern=str(data.get("key_pattern", "unknown")),
                weak_signal_mode=weak_signal_mode,
                historical_precedent=str(data.get("historical_precedent", "N/A")),
                prediction=str(data.get("prediction", "N/A")),
                principle_applied=str(data.get("principle_applied", "N/A")),
            )
        except (json.JSONDecodeError, IndexError):
            pass
    
    stance, confidence, key_pattern = _extract_structured_lines(raw)
    if stance:
        return _build_structured_result(
            agent_name=agent_name,
            stance=stance,
            confidence=confidence if confidence is not None else 45,
            key_pattern=key_pattern or "unknown",
            weak_signal_mode=weak_signal_mode,
        )

    # Pipe-delimited fallback: stance|confidence|pattern|precedent|prediction|quality
    parts = raw.split("|")
    if len(parts) >= 3:
        try:
            return _build_structured_result(
                agent_name=agent_name,
                stance=parts[0].strip(),
                confidence=parts[1].strip(),
                key_pattern=parts[2].strip() if len(parts) > 2 else "unknown",
                weak_signal_mode=weak_signal_mode,
                historical_precedent=parts[3].strip() if len(parts) > 3 else "N/A",
                prediction=parts[4].strip() if len(parts) > 4 else "N/A",
                principle_applied=parts[5].strip() if len(parts) > 5 else "N/A",
            )
        except (ValueError, IndexError):
            pass
    
    # Final fallback
    cleaned = _compact_fallback_stance(raw) if raw else "No response"
    result = _build_structured_result(
        agent_name=agent_name,
        stance=cleaned,
        confidence=30,
        key_pattern="latent structural pressure" if weak_signal_mode else "unknown",
        weak_signal_mode=weak_signal_mode,
    )
    result["raw_text"] = True
    return result


# ──────────────────────────────────────────────────
#  Run a single agent (async)
# ──────────────────────────────────────────────────
async def run_agent(
    role: AgentRole,
    question: str,
    llm: AsyncGroqLLMClient,
    web_news: str = "",
    rag_wisdom: str = "",
    other_stances: str = "",
    round_num: int = 1,
) -> Dict[str, Any]:
    """Run one agent and return its structured response."""
    agent_config = AGENT_CONFIGS[role]

    system_prompt, user_prompt = _build_agent_prompt(
        agent_config, question, web_news, rag_wisdom, other_stances, round_num
    )

    has_news = has_real_news_content(web_news)
    use_json = has_news

    try:
        raw = await llm.chat(
            system_prompt, user_prompt,
            temperature=0.45 if has_news else 0.3,
            max_tokens=config.agent_max_tokens if has_news else 96,
            response_format={"type": "json_object"} if use_json else None,
            timeout_seconds=config.groq_request_timeout_seconds,
        )
        result = _parse_agent_response(
            raw,
            agent_config.name,
            expect_json=use_json,
            weak_signal_mode=not has_news,
        )
        result["role"] = role.value
        return result
    except Exception as e:
        print(f"  ✗ {agent_config.name} failed: {e}")
        resp = dict(ABSTAIN_RESPONSE)
        resp["agent_name"] = agent_config.name
        resp["role"] = role.value
        return resp


# ──────────────────────────────────────────────────
#  Run all 10 agents in parallel
# ──────────────────────────────────────────────────
async def run_all_agents(
    question: str,
    llm: AsyncGroqLLMClient,
    web_news: str = "",
    rag_wisdoms: Optional[Dict[str, str]] = None,
    other_stances: str = "",
    round_num: int = 1,
    agent_roles: Optional[List[AgentRole]] = None,
) -> List[Dict[str, Any]]:
    """Run multiple agents in parallel with graceful error handling."""
    if rag_wisdoms is None:
        rag_wisdoms = {}

    if agent_roles is None:
        agent_roles = [r for r in AgentRole if r not in (AgentRole.JUDGE, AgentRole.ORACLE)]

    tasks = []
    for role in agent_roles:
        wisdom = rag_wisdoms.get(role.value, "")
        tasks.append(
            run_agent(role, question, llm, web_news, wisdom, other_stances, round_num)
        )

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Filter out exceptions → replace with Abstain
    clean_results = []
    for i, r in enumerate(results):
        if isinstance(r, Exception):
            print(f"  ✗ Agent {agent_roles[i].value} raised: {r}")
            resp = dict(ABSTAIN_RESPONSE)
            resp["agent_name"] = AGENT_CONFIGS[agent_roles[i]].name
            resp["role"] = agent_roles[i].value
            clean_results.append(resp)
        else:
            clean_results.append(r)

    return clean_results


# ──────────────────────────────────────────────────
#  Shadow Round (8B — fast pre-filtering)
# ──────────────────────────────────────────────────
async def run_shadow_round(
    question: str,
    shadow_llm: AsyncGroqLLMClient,
    web_news: str = "",
) -> List[Dict[str, Any]]:
    """
    Run all 10 agents on the cheap 8B model.
    Output: pipe-delimited stance|confidence|pattern_type (128 tokens).
    """
    roles = [r for r in AgentRole if r not in (AgentRole.JUDGE, AgentRole.ORACLE)]
    tasks = []
    has_news = has_real_news_content(web_news)

    if not has_news:
        shadow_suffix = """INTELLIGENCE MODE: You are PATTERN HUNTER. No direct news available.

REAL INTELLIGENCE WORK means finding signals in NOISE. Infer from:
1. ABSENCES: What SHOULD happen but ISN'T? (This reveals hidden forces)
2. STRUCTURAL: What economic/political forces persist regardless?
3. HISTORICAL: What similar case rhymes? (History doesn't repeat but rhymes)
4. INCENTIVES: Who benefits? Who loses? Follow the money.

RULES:
- NEVER refuse. NEVER say "no evidence", "cannot assess", or "insufficient information"
- ALWAYS produce directional inference (20-80% confidence ONLY)
- ABSENCE of evidence IS evidence — use it
- SILENCE is data — analyze who isn't speaking

Return ONLY one line:
stance|confidence|pattern_type
Example: "Policy will fail due to treasury resistance | 45% | structural_inertia"
NOTE: Confidence must be 20-80. Never 100 or 0."""
    else:
        shadow_suffix = """INTELLIGENCE MODE: Return ONLY one line:
stance|confidence|pattern_type
Example: "Tariffs will harm consumers|75|economic_protectionism"
One sentence only. No JSON. No bullet points. No headings."""

    for role in roles:
        agent_config = AGENT_CONFIGS[role]
        system_prompt = agent_config.system_prompt
        user_prompt = f"QUESTION: {question}\n\nTODAY'S FACTS:\n{web_news}\n\n{shadow_suffix}"

        async def _call(sp=system_prompt, up=user_prompt, name=agent_config.name, r=role):
            try:
                raw = await shadow_llm.chat(
                    sp,
                    up,
                    temperature=0.2,
                    max_tokens=config.shadow_max_tokens,
                    timeout_seconds=config.groq_shadow_timeout_seconds,
                    max_retries=1,
                )
                data = _parse_agent_response(
                    raw,
                    name,
                    expect_json=False,
                    weak_signal_mode=not has_news,
                )
                data["role"] = r.value
                return data
            except Exception as e:
                return {"agent_name": name, "role": r.value, "stance": "abstain",
                        "confidence": 0, "key_pattern": str(e), "error": True}

        tasks.append(_call())

    return await asyncio.gather(*tasks)


# ──────────────────────────────────────────────────
#  Judge (self-consistency × 3)
# ──────────────────────────────────────────────────
async def run_judge(
    question: str,
    agent_results: List[Dict[str, Any]],
    llm: AsyncGroqLLMClient,
    runs: int = 3,
) -> Dict[str, Any]:
    """Run the Judge N times and return majority verdict."""

    agents_summary = "\n".join([
        f"- {r['agent_name']}: {r.get('stance', 'N/A')} (confidence: {r.get('confidence', 0)}%)"
        for r in agent_results if not r.get("error")
    ])

    system_prompt = JUDGE_CONFIG.system_prompt
    user_prompt = f"""QUESTION: {question}

AGENT POSITIONS:
{agents_summary}

Make your final bold prediction. Output ONLY valid JSON."""

    verdicts = []
    for _ in range(runs):
        try:
            raw = await llm.chat(
                system_prompt, user_prompt,
                temperature=0.35,
                max_tokens=config.judge_max_tokens,
                response_format={"type": "json_object"},
                timeout_seconds=config.groq_request_timeout_seconds,
            )
            data = json.loads(raw.strip())
            verdicts.append(data)
        except Exception as e:
            print(f"  ✗ Judge run failed: {e}")

    if not verdicts:
        return {"majority_verdict": "Judge failed to produce a verdict", "confidence": 0}

    # Majority vote by highest-confidence verdict
    verdicts.sort(key=lambda v: v.get("confidence", 0), reverse=True)
    winner = verdicts[0]
    winner["judge_runs"] = len(verdicts)
    return winner


# ──────────────────────────────────────────────────
#  Utility: compress results into StanceVectors
# ──────────────────────────────────────────────────
def compress_to_stance_vectors(results: List[Dict[str, Any]]) -> str:
    """Create a compact summary of agent positions for the next round."""
    lines = []
    for r in results:
        if r.get("error"):
            continue
        lines.append(
            f"{r['agent_name']}: {r.get('stance', 'N/A')} "
            f"(Confidence: {r.get('confidence', 0)}%, "
            f"Pattern: {r.get('key_pattern', 'N/A')})"
        )
    return "\n".join(lines)


ROLE_ORDER = [
    "chanakya", "bose", "doval", "kissinger", "kao",
    "investigator", "skeptic", "pattern_analyst", "network_mapper", "devils_advocate"
]


def expand_stance_vector_v3(compressed: str) -> Dict[str, str]:
    """Expand compressed v3 format back to agent names.
    
    Input: "1:+0.8|2:-0.6|3:+0.7"
    Output: {"Chanakya": "+0.8", "Bose": "-0.6", "Doval": "+0.7"}
    """
    INDEX_TO_NAME = {i + 1: name.capitalize() for i, name in enumerate(ROLE_ORDER)}
    
    result = {}
    for part in compressed.split("|"):
        if ":" not in part:
            continue
        idx_str, score = part.split(":", 1)
        try:
            idx = int(idx_str)
            name = INDEX_TO_NAME.get(idx, f"Agent{idx}")
            result[name] = score
        except ValueError:
            continue
    return result


def compress_to_stance_vectors_v3(results: List[Dict[str, Any]]) -> str:
    """Ultra-compressed StanceVector format.
    
    Format: 1:+0.8|2:-0.6|3:+0.7|... (agent index: numeric score)
    Where index maps to AgentRole order (1=Chanakya, 2=Bose, ...)
    
    Reduction: ~1800 tokens → ~100 tokens
    """
    ROLE_ORDER = [
        "chanakya", "bose", "doval", "kissinger", "kao",
        "investigator", "skeptic", "pattern_analyst", "network_mapper", "devils_advocate"
    ]
    role_to_index = {role: i + 1 for i, role in enumerate(ROLE_ORDER)}
    
    stance_map = []
    for r in results:
        if r.get("error"):
            continue
        role = r.get("role", "")
        idx = role_to_index.get(role)
        if idx is None:
            continue
        stance = r.get("stance", "").lower().strip()
        confidence = r.get("confidence", 0) / 100.0

        # Stance normalization - aligned with debate.py
        FOR_TOKENS = ("yes", "support", "agree", "true", "success", "pass", "benefit", "likely", "probable", "possible", "advances", "improves")
        AGAINST_TOKENS = ("no", "reject", "disagree", "false", "fail", "against", "harm", "unlikely", "improbable", "risky", "danger", "worsens")

        if any(w in stance for w in FOR_TOKENS):
            sign = "+"
        elif any(w in stance for w in AGAINST_TOKENS):
            sign = "-"
        else:
            sign = "0"

        stance_map.append(f"{idx}:{sign}{confidence:.1f}")
    
    return "|".join(stance_map)
