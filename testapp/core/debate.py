"""
VG Debate Coordinator — orchestrates the full intelligence pipeline.

Flow:
1. Tavily web search → real news
2. ChromaDB RAG → personality wisdom
3. Shadow round (8B) → fast pre-filtering
4. Convergence check → if 80% agree, skip to judge
5. Full debate (70B) → only dissenters if split
6. Judge × 3 → self-consistency majority vote
"""

import asyncio
from typing import List, Dict, Any, Optional

from vg.config import config
from vg.agents.config import AgentRole
from vg.agents.implementations import (
    run_all_agents,
    run_shadow_round,
    run_judge,
    compress_to_stance_vectors,
    compress_to_stance_vectors_v3,
    expand_stance_vector_v3,
)
from vg.core.llm_client import get_async_llm_client
from vg.search.web import search_news


class DebateCoordinator:
    """Orchestrates the full VG debate pipeline."""

    def __init__(self, num_rounds: int = None):
        self.num_rounds = num_rounds or config.max_debate_rounds
        self.convergence_threshold = config.convergence_threshold
        self.judge_runs = config.judge_consistency_runs

    async def run_full_pipeline(self, question: str) -> Dict[str, Any]:
        """Execute the complete VG analysis pipeline."""

        # ── CHECK CACHE ────────────────────────────────
        from vg.cache import cache_get
        
        web_news = search_news(question)  # Get news for staleness check
        pipeline_log = {"question": question, "stages": []}
        
        cached = cache_get(question, web_news)
        if cached:
            print(f"\n💾 Cache HIT - returning cached result")
            return {
                "question": cached["question"],
                "verdict": cached["verdict"],
                "agent_results": cached["agent_results"],
                "pipeline": {"cached": True},
                "from_cache": True,
            }

        # ── STEP 1: Web Search (done for cache check) ──────────────────────────
        print("\n🔍 Step 1: Searching for real news...")
        pipeline_log["web_news"] = web_news[:500]

        # ── STEP 2: RAG Fetch ───────────────────────────
        print("📚 Step 2: Fetching personality wisdom (RAG)...")
        rag_wisdoms = self._fetch_rag_wisdoms(question)
        pipeline_log["rag_personalities_found"] = list(rag_wisdoms.keys())

        # ── STEP 3: Shadow Round (8B) ───────────────────
        print("⚡ Step 3: Running shadow round (fast pre-filter)...")
        shadow_llm = get_async_llm_client(model=config.model_small)
        shadow_results = await run_shadow_round(question, shadow_llm, web_news)

        for r in shadow_results:
            status = "✓" if not r.get("error") else "✗"
            print(f"  {status} {r['agent_name']}: {r.get('stance', 'N/A')[:60]}... "
                  f"(conf: {r.get('confidence', 0)}%)")

        pipeline_log["stages"].append({
            "stage": "shadow_round",
            "model": config.model_small,
            "results": shadow_results,
        })

        # ── STEP 4: Convergence Check ───────────────────
        converged, majority_stance, dissenters = self._check_convergence(shadow_results)

        if converged:
            print(f"\n🎯 Convergence reached in shadow round! ({len(shadow_results) - len(dissenters)}/10 agree)")
            print("   Skipping full debate → jumping to Judge...")
            pipeline_log["stages"].append({"stage": "convergence", "converged": True})

            # Jump to judge with shadow results
            full_results = shadow_results
        else:
            print(f"\n⚔  Split detected — {len(dissenters)} dissenters proceed to full debate")

            # ── STEP 5: Full Debate (70B, filtered agents) ──
            full_llm = get_async_llm_client(model=config.model_large)

            # Determine which agents debate: only dissenters + 2 strongest agreers for context
            debate_roles = self._select_debate_roster(shadow_results, dissenters)
            print(f"   Debating: {[AGENT_CONFIGS_NAMES.get(r, r.value) for r in debate_roles]}")

            all_round_results = list(shadow_results)  # Start with shadow results

            for round_num in range(1, self.num_rounds + 1):
                print(f"\n📢 Debate Round {round_num} (70B)...")
                # Use compressed StanceVector format for 88% token reduction
                stance_context = compress_to_stance_vectors_v3(all_round_results)

                round_results = await run_all_agents(
                    question, full_llm, web_news, rag_wisdoms,
                    other_stances=stance_context,
                    round_num=round_num + 1,
                    agent_roles=debate_roles,
                )

                for r in round_results:
                    status = "✓" if not r.get("error") else "✗"
                    print(f"  {status} {r['agent_name']}: {r.get('stance', 'N/A')[:60]}...")

                # Merge: update existing results with new positions
                all_round_results = self._merge_results(all_round_results, round_results)

                pipeline_log["stages"].append({
                    "stage": f"debate_round_{round_num}",
                    "model": config.model_large,
                    "agents": [r.value for r in debate_roles],
                    "results": round_results,
                })

                # Check convergence again
                conv2, _, _ = self._check_convergence(all_round_results)
                if conv2:
                    print(f"   🎯 Convergence reached in round {round_num}!")
                    break

            full_results = all_round_results

        # ── STEP 6: Judge ─────────────────────────────────────
        # Single call if converged in shadow, 3× otherwise
        if converged:
            print(f"\n⚖  Step 6: Judge validating (converged in shadow → 1x)...")
            judge_llm = get_async_llm_client(model=config.model_large)
            judge_result = await run_judge(question, full_results, judge_llm, runs=1)
        else:
            print(f"\n⚖  Step 6: Judge deliberating ({self.judge_runs}x self-consistency)...")
            judge_llm = get_async_llm_client(model=config.model_large)
            judge_result = await run_judge(question, full_results, judge_llm, runs=self.judge_runs)

        pipeline_log["stages"].append({"stage": "judge", "result": judge_result})

        # ── SAVE TO CACHE ───────────────────────────
        from vg.cache import cache_set
        final_web_news = pipeline_log.get("web_news", "")
        cache_set(question, final_web_news, shadow_results, judge_result, full_results, pipeline_log)

        # ── Build final output ──────────────────────────
        return {
            "question": question,
            "verdict": judge_result,
            "agent_results": full_results,
            "pipeline": pipeline_log,
        }

    def _fetch_rag_wisdoms(self, question: str) -> Dict[str, str]:
        """Fetch RAG wisdom for all historical personalities."""
        try:
            from vg.rag.searcher import search_all_wisdoms
            return search_all_wisdoms(question)
        except Exception as e:
            print(f"  ⚠ RAG not available: {e}")
            return {}

    @staticmethod
    def _normalize_stance_bucket(stance: str) -> str:
        """Map verbose stances into for/against/neutral buckets for convergence checks."""
        normalized = (stance or "").lower().strip()
        if any(
            token in normalized
            for token in (
                "yes",
                "support",
                "agree",
                "true",
                "success",
                "pass",
                "benefit",
                "likely",
                "probable",
                "possible",
                "advances",
                "improves",
            )
        ):
            return "for"
        if any(
            token in normalized
            for token in (
                "no",
                "reject",
                "disagree",
                "false",
                "fail",
                "against",
                "harm",
                "unlikely",
                "improbable",
                "risky",
                "danger",
                "worsens",
            )
        ):
            return "against"
        return "neutral"

    def _check_convergence(
        self, results: List[Dict[str, Any]]
    ) -> tuple[bool, str, List[Dict[str, Any]]]:
        """Check if enough agents agree on stance. Returns (converged, majority_stance, dissenters).
        
        Uses stance agreement: 8/10 or more agreeing = converged.
        """
        valid = [r for r in results if not r.get("error") and r.get("stance") != "abstain"]
        if not valid:
            return False, "", results

        # Group by stance (normalize to for/against/neutral)
        stance_groups: Dict[str, List[Dict[str, Any]]] = {}
        for r in valid:
            normalized = self._normalize_stance_bucket(r.get("stance", ""))
            
            if normalized not in stance_groups:
                stance_groups[normalized] = []
            stance_groups[normalized].append(r)

        # Find majority group
        max_count = 0
        majority_stance = ""
        for stance, agents in stance_groups.items():
            if len(agents) > max_count:
                max_count = len(agents)
                majority_stance = stance

        # Check convergence: 8/10 (80%) agree
        if max_count >= 8:
            all_agents = [r for stance_list in stance_groups.values() for r in stance_list]
            dissenters = [
                r for r in all_agents
                if self._normalize_stance_bucket(r.get("stance", "")) != majority_stance
            ]
            return True, majority_stance, dissenters
        
        return False, "", valid

    def _select_debate_roster(
        self, shadow_results: List[Dict[str, Any]], dissenters: List[Dict[str, Any]]
    ) -> List[AgentRole]:
        """Select which agents proceed to the full 70B debate.
        
        Strategy: top 5 highest-confidence dissenters + 2 strongest agreers = max 7
        Token reduction: 10 agents × full → 7 agents × full
        """
        valid = [r for r in shadow_results if not r.get("error")]
        
        # Separate into dissenters and agreers
        dissenter_stances = {
            self._normalize_stance_bucket(d.get("stance", ""))
            for d in dissenters
            if d.get("stance")
        }
        
        dissenters_list = [
            r for r in valid
            if self._normalize_stance_bucket(r.get("stance", "")) in dissenter_stances
        ]
        agreers_list = [
            r for r in valid
            if self._normalize_stance_bucket(r.get("stance", "")) not in dissenter_stances
        ]
        
        # Sort by confidence (highest first)
        dissenters_list.sort(key=lambda r: r.get("confidence", 0), reverse=True)
        agreers_list.sort(key=lambda r: r.get("confidence", 0), reverse=True)
        
        # Select: top 5 dissenters + top 2 agreers = max 7
        selected = dissenters_list[:5] + agreers_list[:2]
        
        # Always include Devil's Advocate if not already selected
        selected_roles = set(AgentRole(r["role"]) for r in selected if r.get("role"))
        
        if AgentRole.DEVILS_ADVOCATE not in selected_roles:
            # Find devil's advocate in original results
            for r in valid:
                if r.get("role") == AgentRole.DEVILS_ADVOCATE.value:
                    selected = [r] + selected[:6]  # Replace to keep max 7
                    break
        
        # Convert to AgentRole list
        roles = []
        for r in selected[:7]:
            try:
                roles.append(AgentRole(r["role"]))
            except (ValueError, KeyError):
                pass
        
        return roles if roles else [r for r in AgentRole if r != AgentRole.JUDGE][:7]

    def _merge_results(
        self, existing: List[Dict[str, Any]], new: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Merge new debate results into existing set (update agent positions)."""
        result_map = {r.get("role"): r for r in existing}
        for n in new:
            result_map[n.get("role")] = n
        return list(result_map.values())

    # Legacy interface for old code
    def run_debate(self, question, claims=None, evidence=None):
        """Synchronous wrapper for backwards compat."""
        from vg.setup import run_async
        result = run_async(self.run_full_pipeline(question))
        return {
            "question": question,
            "debate_rounds": result.get("pipeline", {}).get("stages", []),
            "final_synthesis": result.get("verdict", {}),
        }


# Helper for readable names
from vg.agents.config import AGENT_CONFIGS as _AC
AGENT_CONFIGS_NAMES = {role: cfg.name for role, cfg in _AC.items()}
