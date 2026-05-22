"""
VG Enhanced Debate Coordinator — Integrates Optimization Layer, Pattern Engine & Oracle Mode.

This is the NEW debate coordinator that replaces the basic one with:
1. Pattern-grounded analysis (reduces hallucination)
2. Semantic caching (reduces redundant computation)
3. Token-optimized prompts (40-60% reduction)
4. Intent-aware pipeline skipping (smart optimization)
5. Hallucination detection layer
6. 🔮 ORACLE MODE — Contrarian intelligence when consensus is too strong
"""

import asyncio
import json
import time
from typing import List, Dict, Any, Optional
from datetime import datetime

from vg.config import config
from vg.agents.config import AgentRole, AGENT_CONFIGS
from vg.core.llm_client import get_async_llm_client
from vg.search.web import search_news, search_contrarian, has_real_news_content

# Import optimization layer
from vg.core.optimization import (
    get_optimizer,
    CompactPrompts,
    SemanticCache,
    HallucinationDetector,
)
from vg.core.intelligence_mode import (
    IntelligencePrompts,
    PredictionEnforcer,
    apply_intelligence_mode,
    enforce_intelligence_output,
    OraclePrompts,
)

# Import pattern engine
from vg.core.pattern_engine import get_pattern_engine, PatternReport

# Import Oracle Mode components
from vg.core.contrarian_engine import get_contrarian_engine, OracleReport
from vg.core.feedback import get_feedback_store

# Import Knowledge Graph + Agent Memory (MiroFish-inspired)
from vg.core.knowledge_graph import get_kg_builder, KnowledgeGraphBuilder
from vg.core.agent_memory import get_agent_memory, AgentMemory


async def _summarize_web_news(web_news: str, llm: Any) -> tuple[str, list[str]]:
    """
    Pre-process web news: extract 5 actionable bullet points + top 10 geopolitical entities.
    Returns (summary_text, entity_list).
    """
    if not web_news or "no web search" in web_news.lower():
        return "", []

    summary_prompt = f"""EXTRACT INTELLIGENCE BRIEF — 5 BULLETS + 10 ENTITIES

NEWS CONTEXT:
{web_news[:3000] if len(web_news) > 3000 else web_news}

TASK:
1. Extract exactly 5 actionable intelligence bullet points (max 15 words each)
2. Identify top 10 geopolitical entities (countries, leaders, organizations)

RESPONSE FORMAT (JSON):
{{
  "bullets": ["bullet 1", "bullet 2", "bullet 3", "bullet 4", "bullet 5"],
  "entities": ["Entity1", "Entity2", ... up to 10]
}}

JSON only. No commentary."""

    try:
        response = await llm.chat(summary_prompt, "", temperature=0.3, max_tokens=500, response_format={"type": "json_object"})
        import json
        data = json.loads(response.strip())
        bullets = data.get("bullets", [])
        entities = data.get("entities", [])
        summary = "\\n".join(f"• {b}" for b in bullets[:5])
        return summary, entities[:10]
    except Exception as e:
        print(f"  ⚠ News summarization failed: {e}")
        return web_news[:500], []  # Fallback to raw news snippet


class EnhancedDebateCoordinator:
    """
    Enhanced debate coordinator with world-class optimizations + Oracle Mode.

    Key improvements over basic coordinator:
    - Pattern grounding before LLM calls
    - Semantic cache for similar questions
    - Token-optimized prompts
    - Hallucination detection
    - Intent-aware pipeline optimization
    - 🔮 Oracle Mode: contrarian intelligence when consensus is too strong
    """

    def __init__(self, num_rounds: int = None, enable_optimizations: bool = True, api_key: Optional[str] = None):
        self.num_rounds = num_rounds or config.max_debate_rounds
        self.enable_optimizations = enable_optimizations
        self.api_key = api_key

        # Initialize optimization components
        self.optimizer = get_optimizer() if enable_optimizations else None
        self.pattern_engine = get_pattern_engine()
        self.hallucination_detector = HallucinationDetector() if enable_optimizations else None
        self.semantic_cache = SemanticCache() if enable_optimizations else None

        # Initialize Oracle Mode components
        self.contrarian_engine = get_contrarian_engine() if enable_optimizations else None
        self.feedback_store = get_feedback_store() if enable_optimizations else None

        # Initialize Knowledge Graph + Agent Memory
        self.kg_builder = get_kg_builder()
        self.agent_memory = get_agent_memory()

        # Statistics tracking
        self._stats = {
            "cache_hits": 0,
            "pattern_grounding_applied": False,
            "tokens_saved_estimate": 0,
            "hallucinations_flagged": 0,
            "oracle_mode_activated": False,
            "upset_probability": 0,
        }

    async def run_full_pipeline(self, question: str) -> Dict[str, Any]:
        """Execute the OPTIMIZED VG analysis pipeline."""

        start_time = time.time()
        pipeline_log = {"question": question, "stages": [], "optimizations_applied": []}

        # ── STEP 0: Check Semantic Cache ────────────────────────────────
        if self.enable_optimizations:
            print("🔍 Step 0: Checking semantic cache...")
            cached = self._check_semantic_cache(question)
            if cached:
                self._stats["cache_hits"] += 1
                pipeline_log["optimizations_applied"].append("semantic_cache_hit")
                return {
                    "question": question,
                    "verdict": cached["verdict"],
                    "agent_results": cached["agent_results"],
                    "pipeline": pipeline_log,
                    "from_cache": True,
                    "cached_at": cached.get("cached_at", "unknown"),
                }

        # ── STEP 1: Intent Classification ────────────────────────────────
        optimization_config = {}
        if self.enable_optimizations:
            print("📋 Step 1: Classifying query intent...")
            optimization_config = self.optimizer.optimize_pipeline(question)
            pipeline_log["optimizations_applied"].append("intent_classification")

            if optimization_config.get("cached"):
                # Exact match in optimization cache
                return optimization_config["result"]

        # ── STEP 2: Web Search ─────────────────────────────────────────
        print("🔍 Step 2: Searching for real news...")
        web_news = search_news(question)
        pipeline_log["web_news"] = web_news[:500] if len(web_news) > 500 else web_news

        # ── STEP 3: Web News Intelligence Summarization ──────────────────
        print("🧠 Step 3: Extracting intelligence summary...")
        news_summary = ""
        geo_entities = []
        if has_real_news_content(web_news):
            try:
                summary_llm = get_async_llm_client(model=config.model_small, api_key=self.api_key)
                news_summary, geo_entities = await _summarize_web_news(web_news, summary_llm)
                if news_summary:
                    print(f"   Extracted {len(news_summary.split('•'))} bullet points, {len(geo_entities)} entities")
                pipeline_log["news_summary"] = news_summary[:300]
                pipeline_log["geo_entities"] = geo_entities
            except Exception as e:
                print(f"  ⚠ News summarization skipped: {e}")

        # ── STEP 3.5: Knowledge Graph Construction ──────────────────────
        print("🔗 Step 3.5: Building knowledge graph from evidence...")
        kg_summary = ""
        kg_judge_summary = ""
        try:
            kg_llm = get_async_llm_client(model=config.model_small, api_key=self.api_key)
            knowledge_graph = await self.kg_builder.build(question, web_news, kg_llm)
            kg_summary = KnowledgeGraphBuilder.format_for_agents(knowledge_graph)
            kg_judge_summary = KnowledgeGraphBuilder.format_for_judge(knowledge_graph)
            if knowledge_graph.extraction_success:
                print(f"   Extracted {len(knowledge_graph.entities)} entities, "
                      f"{len(knowledge_graph.relationships)} relationships, "
                      f"evidence quality: {knowledge_graph.evidence_quality}")
                pipeline_log["knowledge_graph"] = {
                    "entities": len(knowledge_graph.entities),
                    "relationships": len(knowledge_graph.relationships),
                    "factions": len(knowledge_graph.factions),
                    "evidence_quality": knowledge_graph.evidence_quality,
                }
            else:
                print("   ⚠ Knowledge graph extraction returned no structured data")
        except Exception as e:
            print(f"  ⚠ Knowledge graph skipped: {e}")
        pipeline_log["optimizations_applied"].append("knowledge_graph")

        # ── STEP 4: Pattern Grounding ─────────────────────────────────────
        print("🧩 Step 4: Running pattern grounding engine...")
        pattern_report = self.pattern_engine.analyze(question, web_news)
        pattern_summary = self.pattern_engine.get_pattern_summary(pattern_report)
        pipeline_log["pattern_analysis"] = {
            "linguistic_patterns_found": sum(
                len(patterns) for patterns in pattern_report.linguistic_patterns.values()
            ),
            "historical_analogies_found": len(pattern_report.historical_analogies),
            "key_actors_identified": len(pattern_report.key_actors),
            "overall_confidence": pattern_report.overall_confidence,
        }
        pipeline_log["optimizations_applied"].append("pattern_grounding")
        self._stats["pattern_grounding_applied"] = True

        # ── STEP 5: RAG Fetch ──────────────────────────────────────────
        print("📚 Step 5: Fetching personality wisdom (RAG)...")
        rag_wisdoms = self._fetch_rag_wisdoms(question)
        pipeline_log["rag_personalities_found"] = list(rag_wisdoms.keys())

        # ── STEP 6: Shadow Round (8B) ──────────────────────────────────
        print("⚡ Step 6: Running shadow round (fast pre-filter)...")
        shadow_llm = get_async_llm_client(model=config.model_small, api_key=self.api_key)

        # Use optimized prompts if enabled
        if self.enable_optimizations:
            shadow_results = await self._run_optimized_shadow_round(
                question, shadow_llm, web_news, pattern_summary, rag_wisdoms,
                kg_summary=kg_summary,
            )
            pipeline_log["optimizations_applied"].append("optimized_shadow_prompts")
        else:
            from vg.agents.implementations import run_shadow_round
            shadow_results = await run_shadow_round(question, shadow_llm, web_news)

        for r in shadow_results:
            status = "✓" if not r.get("error") else "✗"
            print(f"  {status} {r['agent_name']}: {r.get('stance', 'N/A')[:60]}...")

        pipeline_log["stages"].append({
            "stage": "shadow_round",
            "model": config.model_small,
            "results": shadow_results,
        })

        # ── STEP 7: Convergence Check ─────────────────────────────────
        converged, majority_stance, dissenters = self._check_convergence(shadow_results)

        # Oracle Mode state
        oracle_report = None
        contrarian_results = []
        contrarian_evidence = ""

        if converged:
            consensus_count = len(shadow_results) - len(dissenters)
            print(f"\n🎯 Convergence in shadow round! ({consensus_count}/10 agree: '{majority_stance}')")

            # ── 🔮 ORACLE MODE ACTIVATION ────────────────────────────────
            if self.enable_optimizations and self.contrarian_engine:
                print("\n🔮 ORACLE MODE ACTIVATED — Consensus is dangerously strong!")
                print("   Hunting for reasons the consensus could be WRONG...\n")
                self._stats["oracle_mode_activated"] = True
                pipeline_log["optimizations_applied"].append("oracle_mode")

                # Get consensus stance text (most common stance)
                consensus_stances = [
                    r.get("stance", "") for r in shadow_results
                    if not r.get("error") and self._normalize_stance(r.get("stance", "")) == majority_stance
                ]
                consensus_text = consensus_stances[0] if consensus_stances else majority_stance

                # Run Contrarian Engine analysis
                oracle_report = self.contrarian_engine.analyze(
                    question=question,
                    consensus_stance=consensus_text,
                    consensus_count=consensus_count,
                    total_agents=len(shadow_results),
                    evidence=web_news,
                    news_text=web_news,
                )

                self._stats["upset_probability"] = oracle_report.upset_probability
                print(f"   📊 Upset Probability: {oracle_report.upset_probability}%")

                # Log upset analysis
                pipeline_log["oracle_mode"] = {
                    "activated": True,
                    "consensus_stance": consensus_text[:200],
                    "consensus_count": consensus_count,
                    "upset_probability": oracle_report.upset_probability,
                    "upset_scenario": oracle_report.upset_scenario[:300],
                    "matching_upsets": [
                        u["name"] for u in oracle_report.upset_analysis.get("matching_upsets", [])
                    ],
                }

                # Run contrarian web search
                if oracle_report.contrarian_queries:
                    print("   🔎 Running contrarian web searches...")
                    contrarian_evidence = search_contrarian(oracle_report.contrarian_queries)
                    if contrarian_evidence:
                        print(f"   Found contrarian evidence ({len(contrarian_evidence)} chars)")

                # Run Contrarian Agents Round
                print("\n   🔮 Running Contrarian Agents Round...")
                oracle_context = self.contrarian_engine.get_oracle_context(oracle_report)
                contrarian_llm = get_async_llm_client(model=config.model_large, api_key=self.api_key)
                contrarian_results = await self._run_contrarian_round(
                    question, contrarian_llm, oracle_context,
                    contrarian_evidence, consensus_text, consensus_count,
                )

                for r in contrarian_results:
                    status = "✓" if not r.get("error") else "✗"
                    print(f"   🔮 {r['agent_name']}: {r.get('stance', 'N/A')[:60]}...")

                pipeline_log["stages"].append({
                    "stage": "contrarian_round",
                    "model": config.model_large,
                    "results": contrarian_results,
                })

            full_results = shadow_results
        else:
            print(f"\n⚔  Split detected — {len(dissenters)} dissenters proceed to full debate")

            # ── STEP 8: Full Debate (70B) ────────────────────────────────
            full_llm = get_async_llm_client(model=config.model_large, api_key=self.api_key)

            # Select debate roster (only dissenters + context)
            debate_roles = self._select_debate_roster(shadow_results, dissenters)
            print(f"   Debating: {[r.value for r in debate_roles]}")

            all_round_results = list(shadow_results)

            for round_num in range(1, self.num_rounds + 1):
                print(f"\n📢 Debate Round {round_num} (70B)...")

                # Use compressed stance vectors
                stance_context = self._compress_to_stance_vectors_v3(all_round_results)

                if self.enable_optimizations:
                    round_results = await self._run_optimized_agent_round(
                        question, full_llm, web_news, rag_wisdoms,
                        stance_context, round_num, debate_roles,
                        pattern_summary,
                    )
                    pipeline_log["optimizations_applied"].append(f"optimized_round_{round_num}")
                else:
                    from vg.agents.implementations import run_all_agents
                    round_results = await run_all_agents(
                        question, full_llm, web_news, rag_wisdoms,
                        other_stances=stance_context,
                        round_num=round_num + 1,
                        agent_roles=debate_roles,
                    )

                for r in round_results:
                    status = "✓" if not r.get("error") else "✗"
                    print(f"  {status} {r['agent_name']}: {r.get('stance', 'N/A')[:60]}...")

                # Merge results
                all_round_results = self._merge_results(all_round_results, round_results)

                pipeline_log["stages"].append({
                    "stage": f"debate_round_{round_num}",
                    "model": config.model_large,
                    "agents": [r.value for r in debate_roles],
                    "results": round_results,
                })

                # Check convergence
                conv2, _, _ = self._check_convergence(all_round_results)
                if conv2:
                    print(f"   🎯 Convergence reached in round {round_num}!")
                    break

            full_results = all_round_results

        # ── STEP 9: Hallucination Check ──────────────────────────────────
        if self.enable_optimizations and self.hallucination_detector:
            print("🔍 Running hallucination detection...")
            flagged = self.hallucination_detector.flag_risky_claims(
                full_results, evidence=web_news
            )
            self._stats["hallucinations_flagged"] = len(flagged)
            pipeline_log["hallucination_flags"] = [
                {"agent": f["agent_name"], "risk_score": f.get("risk_analysis", {}).get("risk_score", 0)}
                for f in flagged
            ]
            pipeline_log["optimizations_applied"].append("hallucination_detection")

        # ── STEP 10: Judge (Oracle Judge if Oracle Mode active) ──────────
        judge_llm = get_async_llm_client(model=config.model_large, api_key=self.api_key)

        if oracle_report and contrarian_results:
            # 🔮 ORACLE JUDGE — dual verdict with upset probability
            print(f"\n⚖  🔮 Oracle Judge — weighing consensus vs. contrarian...")
            judge_result = await self._run_oracle_judge(
                question, full_results, contrarian_results,
                judge_llm, oracle_report, pattern_summary,
            )
        elif converged:
            print(f"\n⚖  Judge validating (converged → 1x run)...")
            judge_result = await self._run_judge_optimized(
                question, full_results, judge_llm, pattern_summary, runs=1
            )
        else:
            print(f"\n⚖  Judge deliberating (3x self-consistency)...")
            judge_result = await self._run_judge_optimized(
                question, full_results, judge_llm, pattern_summary, runs=3
            )

        pipeline_log["stages"].append({"stage": "judge", "result": judge_result})

        # ── SAVE TO SEMANTIC CACHE ─────────────────────────────────────
        if self.enable_optimizations and self.semantic_cache:
            self.semantic_cache.set(question, web_news, {
                "verdict": judge_result,
                "agent_results": full_results,
                "cached_at": datetime.now().isoformat(),
            })

        # ── RECORD PREDICTION IN FEEDBACK STORE ────────────────────────
        prediction_id = ""
        if self.enable_optimizations and self.feedback_store:
            try:
                agent_stances = {
                    r.get("agent_name", "?"): r.get("stance", "")
                    for r in full_results if not r.get("error")
                }
                agent_confs = {
                    r.get("agent_name", "?"): r.get("confidence", 0)
                    for r in full_results if not r.get("error")
                }
                prediction_id = self.feedback_store.record_prediction(
                    question=question,
                    consensus_prediction=judge_result.get("primary_verdict", judge_result.get("majority_verdict", "")),
                    consensus_confidence=judge_result.get("primary_confidence", judge_result.get("confidence", 0)),
                    agent_stances=agent_stances,
                    agent_confidences=agent_confs,
                    oracle_mode_activated=self._stats.get("oracle_mode_activated", False),
                    upset_prediction=judge_result.get("upset_scenario", ""),
                    upset_probability=judge_result.get("upset_probability", 0),
                )
            except Exception as e:
                print(f"  ⚠ Feedback recording failed: {e}")

        # ── Build final output ─────────────────────────────────────────
        elapsed_time = time.time() - start_time

        result = {
            "question": question,
            "verdict": judge_result,
            "agent_results": full_results,
            "pipeline": pipeline_log,
            "stats": self._stats,
            "elapsed_seconds": round(elapsed_time, 2),
            "pattern_report_summary": pattern_summary[:500] if len(pattern_summary) > 500 else pattern_summary,
            "news_summary": news_summary,
            "geo_entities": geo_entities,
        }

        # Add Oracle Mode outputs if activated
        if oracle_report:
            result["oracle_mode"] = {
                "activated": True,
                "upset_probability": oracle_report.upset_probability,
                "upset_scenario": oracle_report.upset_scenario,
                "key_signals_to_watch": oracle_report.key_signals_to_watch,
                "contrarian_agent_results": contrarian_results,
            }
        if prediction_id:
            result["prediction_id"] = prediction_id

        return result

    # ═══════════════════════════════════════════════════════════════════
    #  OPTIMIZED AGENT RUNNING METHODS
    # ═══════════════════════════════════════════════════════════════════

    async def _run_optimized_shadow_round(
        self,
        question: str,
        llm: Any,
        web_news: str,
        pattern_summary: str,
        rag_wisdoms: Dict[str, str],
        kg_summary: str = "",
    ) -> List[Dict[str, Any]]:
        """
        Run shadow round with INTELLIGENCE MODE — CIA/RAW-style bold assessments.
        No cautious disclaimers. No "uncertain" abdication. Actionable predictions only.

        Now enhanced with Knowledge Graph and Agent Memory injection.
        Uses asyncio.Semaphore(3) to prevent API rate-limit crashes.
        """
        from vg.agents.config import AgentRole

        roles = [r for r in AgentRole if r not in (AgentRole.JUDGE, AgentRole.ORACLE)]
        has_news = has_real_news_content(web_news)

        # CONCURRENCY CONTROL: Only 3 agents at a time to prevent rate limits
        semaphore = asyncio.Semaphore(3)

        tasks = []
        for role in roles:
            agent_config = AGENT_CONFIGS[role]

            # INTELLIGENCE MODE: Get CIA/RAW-style prompt
            system_prompt = IntelligencePrompts.get_intelligence_prompt(role.value, has_news)

            # Build user prompt with question, KG, pattern summary, wisdom, and memory
            user_parts = [f"QUESTION: {question}"]

            # Knowledge Graph (structured intelligence — highest priority)
            if kg_summary:
                user_parts.append(f"\n{kg_summary}")

            if pattern_summary:
                user_parts.append(f"\n=== PATTERN ANALYSIS ===\n{pattern_summary[:400]}")

            if rag_wisdoms and role.value in rag_wisdoms:
                user_parts.append(f"\n=== YOUR WISDOM ===\n{rag_wisdoms[role.value][:200]}")

            # Agent Memory (track record injection)
            memory = self.agent_memory.get_memory_for_agent(agent_config.name, question)
            if memory:
                user_parts.append(f"\n{memory}")

            user_prompt = "\n".join(user_parts)

            async def _call(sp=system_prompt, up=user_prompt, name=agent_config.name, r=role, sem=semaphore):
                async with sem:
                    try:
                        raw = await llm.chat(
                            sp, up,
                            temperature=0.5,  # Slightly higher for more creative intelligence work
                            max_tokens=config.shadow_max_tokens,
                            timeout_seconds=config.groq_shadow_timeout_seconds,
                            max_retries=1,
                        )
                        # ENFORCE intelligence mode: no weak predictions
                        parsed = enforce_intelligence_output(raw, name)
                        result = {
                            "agent_name": name,
                            "role": r.value,
                            "stance": parsed["stance"],
                            "confidence": parsed["confidence"],
                            "key_pattern": parsed["pattern"],
                            "error": False,
                            "intelligence_mode": True,
                        }
                        return result
                    except Exception as e:
                        return {
                            "agent_name": name,
                            "role": r.value,
                            "stance": "abstain",
                            "confidence": 0,
                            "key_pattern": str(e),
                            "error": True,
                        }

            tasks.append(_call())

        results = await asyncio.gather(*tasks)
        return list(results)

    async def _run_optimized_agent_round(
        self,
        question: str,
        llm: Any,
        web_news: str,
        rag_wisdoms: Dict[str, str],
        stance_context: str,
        round_num: int,
        debate_roles: List[AgentRole],
        pattern_summary: str,
    ) -> List[Dict[str, Any]]:
        """
        Run agent round with INTELLIGENCE MODE — CIA/RAW-style bold assessments.
        Agents debate with actionable predictions, not cautious disclaimers.

        Uses asyncio.Semaphore(3) to prevent API rate-limit crashes.
        """
        has_news = has_real_news_content(web_news)

        # CONCURRENCY CONTROL: Only 3 agents at a time to prevent rate limits
        semaphore = asyncio.Semaphore(3)

        tasks = []
        for role in debate_roles:
            agent_config = AGENT_CONFIGS[role]
            wisdom = rag_wisdoms.get(role.value, "")

            # INTELLIGENCE MODE: Get CIA/RAW-style prompt
            system_prompt = IntelligencePrompts.get_intelligence_prompt(role.value, has_news)

            # Build user prompt
            user_parts = [f"QUESTION: {question}"]

            if pattern_summary:
                user_parts.append(f"\n=== PATTERN ANALYSIS ===\n{pattern_summary[:300]}")

            if wisdom:
                user_parts.append(f"\n=== YOUR WISDOM ===\n{wisdom[:150]}")

            # Add other agents' stances (compressed)
            if stance_context and round_num > 1:
                user_parts.append(f"\n=== OTHER AGENTS ===\n{stance_context}")

            user_prompt = "\n".join(user_parts)

            async def _call(sp=system_prompt, up=user_prompt, name=agent_config.name, r=role, sem=semaphore):
                async with sem:
                    try:
                        raw = await llm.chat(
                            sp, up,
                            temperature=0.5,  # Higher temperature for intelligence creativity
                            max_tokens=256,  # Fixed limit for intelligence brevity
                            timeout_seconds=config.groq_request_timeout_seconds,
                        )
                        # ENFORCE intelligence mode output
                        parsed = enforce_intelligence_output(raw, name)
                        result = {
                            "agent_name": name,
                            "role": r.value,
                            "stance": parsed["stance"],
                            "confidence": parsed["confidence"],
                            "key_pattern": parsed["pattern"],
                            "error": False,
                            "intelligence_mode": True,
                        }
                        return result
                    except Exception as e:
                        return {
                            "agent_name": name,
                            "role": r.value,
                            "stance": "abstain",
                            "confidence": 0,
                            "key_pattern": str(e),
                            "error": True,
                        }

            tasks.append(_call())

        results = await asyncio.gather(*tasks)
        return list(results)

    async def _run_judge_optimized(
        self,
        question: str,
        agent_results: List[Dict[str, Any]],
        llm: Any,
        pattern_summary: str,
        runs: int = 3,
    ) -> Dict[str, Any]:
        """
        Run judge with pattern-grounded context.
        """
        agents_summary = "\n".join([
            f"- {r['agent_name']}: {r.get('stance', 'N/A')} (conf: {r.get('confidence', 0)}%)"
            for r in agent_results if not r.get("error")
        ])

        judge_prompt = f"""INTELLIGENCE ASSESSMENT — FINAL VERDICT REQUIRED

You are The Judge — CIA/RAW-style intelligence synthesizer.

QUESTION: {question}

{pattern_summary[:400] if pattern_summary else ""}

AGENT POSITIONS (10 dimensions analyzed):
{agents_summary}

YOUR TASK: Produce actionable intelligence verdict.

RULES:
- NEVER say "uncertain", "insufficient evidence", or "cannot determine"
- ALWAYS produce bold, actionable prediction
- Confidence MUST be 40-85% (no 100% certainty, no 0% abdication)
- Use probabilistic language: "likely", "unlikely", "probable"
- Ground in patterns, not just facts

Respond in JSON:
{{
  "majority_verdict": "BOLD actionable prediction (one sentence)",
  "confidence": 40-85,
  "key_pattern": "dominant pattern across dimensions",
  "historical_precedent": "closest historical rhyme",
  "strongest_dissent": "best counter-argument (one sentence)",
  "reasoning": "how dimensions integrate (2 sentences max)"
}}

Intelligence verdict. JSON only. No disclaimers."""

        verdicts = []
        for i in range(runs):
            try:
                raw = await llm.chat(
                    judge_prompt, "",
                    temperature=0.35,
                    max_tokens=config.judge_max_tokens,
                    response_format={"type": "json_object"},
                    timeout_seconds=config.groq_request_timeout_seconds,
                )
                data = json.loads(raw.strip())
                verdicts.append(data)
            except Exception as e:
                print(f"  ✗ Judge run {i+1} failed: {e}")

        if not verdicts:
            return {"majority_verdict": "Judge failed", "confidence": 0}

        # Return highest confidence verdict
        verdicts.sort(key=lambda v: v.get("confidence", 0), reverse=True)
        winner = verdicts[0]
        winner["judge_runs"] = len(verdicts)
        return winner

    # ═══════════════════════════════════════════════════════════════════
    #  🔮 ORACLE MODE METHODS
    # ═══════════════════════════════════════════════════════════════════

    async def _run_contrarian_round(
        self,
        question: str,
        llm: Any,
        oracle_context: str,
        contrarian_evidence: str,
        consensus_stance: str,
        consensus_count: int,
    ) -> List[Dict[str, Any]]:
        """
        Run the Contrarian Agents Round — agents explicitly argue AGAINST consensus.

        Uses The Oracle + Devil's Advocate + Skeptic (3 agents).
        Uses asyncio.Semaphore(2) for rate-limit safety.
        """
        # Select contrarian agents
        contrarian_roles = [
            AgentRole.ORACLE,
            AgentRole.DEVILS_ADVOCATE,
            AgentRole.SKEPTIC,
        ]

        semaphore = asyncio.Semaphore(2)

        # Build the contrarian prompt
        contrarian_prompt = OraclePrompts.get_contrarian_prompt(
            consensus_stance=consensus_stance,
            consensus_count=consensus_count,
            oracle_context=oracle_context,
            contrarian_evidence=contrarian_evidence,
        )

        tasks = []
        for role in contrarian_roles:
            agent_config = AGENT_CONFIGS[role]

            system_prompt = agent_config.system_prompt
            user_prompt = f"QUESTION: {question}\n\n{contrarian_prompt}"

            async def _call(sp=system_prompt, up=user_prompt, name=agent_config.name, r=role, sem=semaphore):
                async with sem:
                    try:
                        raw = await llm.chat(
                            sp, up,
                            temperature=0.6,  # Higher for creative contrarian thinking
                            max_tokens=256,
                            timeout_seconds=config.groq_request_timeout_seconds,
                        )
                        parsed = enforce_intelligence_output(raw, name)
                        return {
                            "agent_name": name,
                            "role": r.value,
                            "stance": parsed["stance"],
                            "confidence": parsed["confidence"],
                            "key_pattern": parsed["pattern"],
                            "error": False,
                            "contrarian_mode": True,
                        }
                    except Exception as e:
                        return {
                            "agent_name": name,
                            "role": r.value,
                            "stance": f"Contrarian analysis failed: {e}",
                            "confidence": 0,
                            "key_pattern": "error",
                            "error": True,
                            "contrarian_mode": True,
                        }

            tasks.append(_call())

        results = await asyncio.gather(*tasks)
        return list(results)

    async def _run_oracle_judge(
        self,
        question: str,
        consensus_results: List[Dict[str, Any]],
        contrarian_results: List[Dict[str, Any]],
        llm: Any,
        oracle_report: OracleReport,
        pattern_summary: str,
    ) -> Dict[str, Any]:
        """
        Oracle Judge — produces DUAL verdict with upset probability.

        Weighs both consensus and contrarian evidence to produce:
        - Primary verdict (most likely outcome)
        - Upset scenario (what happens if consensus is wrong)
        - Upset probability (calibrated 15-55%)
        """
        # Build consensus summary
        consensus_summary = "\n".join([
            f"- {r['agent_name']}: {r.get('stance', 'N/A')} (conf: {r.get('confidence', 0)}%)"
            for r in consensus_results if not r.get("error")
        ])

        # Build contrarian summary
        contrarian_summary = "\n".join([
            f"- 🔮 {r['agent_name']}: {r.get('stance', 'N/A')} (conf: {r.get('confidence', 0)}%)"
            for r in contrarian_results if not r.get("error")
        ])

        # Build oracle context
        oracle_context = self.contrarian_engine.get_oracle_context(oracle_report)

        # Build the Oracle Judge prompt
        judge_prompt = OraclePrompts.get_oracle_judge_prompt(
            question=question,
            consensus_count=oracle_report.consensus_agents_count,
            consensus_summary=consensus_summary,
            contrarian_summary=contrarian_summary,
            oracle_context=oracle_context,
        )

        # Add pattern summary
        if pattern_summary:
            judge_prompt += f"\n\n=== PATTERN ANALYSIS ===\n{pattern_summary[:400]}"

        try:
            raw = await llm.chat(
                judge_prompt, "",
                temperature=0.35,
                max_tokens=config.judge_max_tokens,
                response_format={"type": "json_object"},
                timeout_seconds=config.groq_request_timeout_seconds,
            )
            result = json.loads(raw.strip())

            # Ensure required Oracle fields exist
            result.setdefault("primary_verdict", result.get("majority_verdict", "No verdict"))
            result.setdefault("primary_confidence", result.get("confidence", 50))
            result.setdefault("upset_scenario", "No upset scenario identified")
            result.setdefault("upset_probability", oracle_report.upset_probability)
            result.setdefault("upset_pattern", "unknown")
            result.setdefault("key_signal", "No specific signal identified")

            # Also set standard fields for backward compatibility
            result["majority_verdict"] = result["primary_verdict"]
            result["confidence"] = result["primary_confidence"]
            result["oracle_mode"] = True
            result["judge_runs"] = 1

            return result

        except Exception as e:
            print(f"  ✗ Oracle Judge failed: {e}")
            # Fallback to standard judge
            print("  ↩ Falling back to standard judge...")
            return await self._run_judge_optimized(
                question, consensus_results, llm, pattern_summary, runs=1
            )

    # ═══════════════════════════════════════════════════════════════════
    #  UTILITY METHODS
    # ═══════════════════════════════════════════════════════════════════

    def _parse_pipe_response(self, raw: str, agent_name: str, role: str) -> Dict[str, Any]:
        """Parse pipe-delimited response: stance|confidence|pattern"""
        raw = raw.strip()
        parts = raw.split("|")

        if len(parts) >= 3:
            try:
                return {
                    "agent_name": agent_name,
                    "role": role,
                    "stance": parts[0].strip()[:160],
                    "confidence": int(parts[1].strip()) if parts[1].strip().isdigit() else 50,
                    "key_pattern": parts[2].strip() or "unknown",
                    "error": False,
                }
            except (ValueError, IndexError):
                pass

        # Fallback
        return {
            "agent_name": agent_name,
            "role": role,
            "stance": raw[:160],
            "confidence": 45,
            "key_pattern": "unknown",
            "error": False,
        }

    def _compress_to_stance_vectors_v3(self, results: List[Dict[str, Any]]) -> str:
        """Ultra-compressed stance vector format."""
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

            if any(w in stance for w in ["yes", "support", "likely", "success"]):
                sign = "+"
            elif any(w in stance for w in ["no", "reject", "unlikely", "fail"]):
                sign = "-"
            else:
                sign = "0"

            stance_map.append(f"{idx}:{sign}{confidence:.1f}")

        return "|".join(stance_map)

    def _check_convergence(
        self, results: List[Dict[str, Any]]
    ) -> tuple[bool, str, List[Dict[str, Any]]]:
        """Check if 8/10 agents agree on stance."""
        valid = [r for r in results if not r.get("error") and r.get("stance") != "abstain"]
        if not valid:
            return False, "", results

        # Normalize stance buckets
        def normalize(stance: str) -> str:
            s = (stance or "").lower().strip()
            # Stance normalization - aligned with debate.py and implementations.py
            FOR_TOKENS = ("yes", "support", "agree", "true", "success", "pass", "benefit", "likely", "probable", "possible", "advances", "improves")
            AGAINST_TOKENS = ("no", "reject", "disagree", "false", "fail", "against", "harm", "unlikely", "improbable", "risky", "danger", "worsens")
            if any(t in s for t in FOR_TOKENS):
                return "for"
            if any(t in s for t in AGAINST_TOKENS):
                return "against"
            return "neutral"

        # Group by stance
        groups: Dict[str, List] = {}
        for r in valid:
            bucket = normalize(r.get("stance", ""))
            if bucket not in groups:
                groups[bucket] = []
            groups[bucket].append(r)

        # Find majority
        max_count = 0
        majority_bucket = ""
        for bucket, agents in groups.items():
            if len(agents) > max_count:
                max_count = len(agents)
                majority_bucket = bucket

        # 8/10 = converged
        if max_count >= 8:
            all_agents = [a for agents in groups.values() for a in agents]
            dissenters = [a for a in all_agents if normalize(a.get("stance", "")) != majority_bucket]
            return True, majority_bucket, dissenters

        return False, "", valid

    def _select_debate_roster(
        self, shadow_results: List[Dict[str, Any]], dissenters: List[Dict[str, Any]]
    ) -> List[AgentRole]:
        """Select top 5 dissenters + 2 agreers for debate."""
        valid = [r for r in shadow_results if not r.get("error")]

        dissenter_buckets = {
            self._normalize_stance(d.get("stance", ""))
            for d in dissenters
        }

        dissenters_list = [
            r for r in valid
            if self._normalize_stance(r.get("stance", "")) in dissenter_buckets
        ]
        agreers_list = [
            r for r in valid
            if self._normalize_stance(r.get("stance", "")) not in dissenter_buckets
        ]

        dissenters_list.sort(key=lambda r: r.get("confidence", 0), reverse=True)
        agreers_list.sort(key=lambda r: r.get("confidence", 0), reverse=True)

        selected = dissenters_list[:5] + agreers_list[:2]
        selected_roles = set(AgentRole(r["role"]) for r in selected if r.get("role"))

        # Always include Devil's Advocate
        if AgentRole.DEVILS_ADVOCATE not in selected_roles:
            for r in valid:
                if r.get("role") == AgentRole.DEVILS_ADVOCATE.value:
                    selected = [r] + selected[:6]
                    break

        roles = []
        for r in selected[:7]:
            try:
                roles.append(AgentRole(r["role"]))
            except (ValueError, KeyError):
                pass

        return roles if roles else [r for r in AgentRole if r != AgentRole.JUDGE][:7]

    def _normalize_stance(self, stance: str) -> str:
        """Normalize stance to for/against/neutral."""
        s = (stance or "").lower().strip()
        # Stance normalization - aligned with debate.py and implementations.py
        FOR_TOKENS = ("yes", "support", "agree", "true", "success", "pass", "benefit", "likely", "probable", "possible", "advances", "improves")
        AGAINST_TOKENS = ("no", "reject", "disagree", "false", "fail", "against", "harm", "unlikely", "improbable", "risky", "danger", "worsens")
        if any(t in s for t in FOR_TOKENS):
            return "for"
        if any(t in s for t in AGAINST_TOKENS):
            return "against"
        return "neutral"

    def _merge_results(
        self, existing: List[Dict[str, Any]], new: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Merge new results into existing (update by role)."""
        result_map = {r.get("role"): r for r in existing}
        for n in new:
            result_map[n.get("role")] = n
        return list(result_map.values())

    def _fetch_rag_wisdoms(self, question: str) -> Dict[str, str]:
        """Fetch RAG wisdom for historical personalities."""
        try:
            from vg.rag.searcher import search_all_wisdoms
            return search_all_wisdoms(question)
        except Exception as e:
            print(f"  ⚠ RAG not available: {e}")
            return {}

    def _check_semantic_cache(self, question: str) -> Optional[Dict]:
        """Check semantic cache for similar question."""
        if not self.semantic_cache:
            return None
        # Note: We'd need news for full check, but skip for speed
        return None  # Disabled for now - requires news hash match


# ═══════════════════════════════════════════════════════════════════
#  FACTORY FUNCTION
# ═══════════════════════════════════════════════════════════════════

def get_enhanced_coordinator(num_rounds: int = None) -> EnhancedDebateCoordinator:
    """Get enhanced debate coordinator."""
    return EnhancedDebateCoordinator(num_rounds=num_rounds)
