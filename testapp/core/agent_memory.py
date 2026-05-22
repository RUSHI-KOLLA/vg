"""
VG Agent Memory — Injects past prediction track records into agent prompts.

MiroFish-inspired: Agents with memory produce better-calibrated predictions.
Instead of being stateless, each agent now "remembers" their past performance:
- How many predictions they've made
- Their accuracy rate
- Their most recent similar prediction and whether it was right
- Whether they were a successful contrarian

Uses the existing FeedbackStore as the data source.
"""

from typing import Dict, Optional, List, Any

from vg.core.feedback import get_feedback_store, FeedbackStore


# ═══════════════════════════════════════════════════════════════════
#  AGENT MEMORY
# ═══════════════════════════════════════════════════════════════════

class AgentMemory:
    """
    Provides per-agent memory blocks for prompt injection.

    Reads from the FeedbackStore to give each agent awareness of
    their own prediction history, accuracy, and past mistakes.
    """

    def __init__(self, feedback_store: FeedbackStore = None):
        self.store = feedback_store or get_feedback_store()
        self._agent_stats_cache: Optional[Dict[str, Dict]] = None
        self._similar_cache: Dict[str, list] = {}

    def _get_agent_stats(self) -> Dict[str, Dict]:
        """Get or cache agent accuracy stats."""
        if self._agent_stats_cache is None:
            self._agent_stats_cache = self.store.get_agent_accuracy()
        return self._agent_stats_cache

    def get_memory_for_agent(
        self,
        agent_name: str,
        question: str,
        max_similar: int = 2,
    ) -> str:
        """
        Generate a compact memory block for an agent.

        Returns a text block to inject into the agent's prompt, containing:
        - Their overall accuracy rate
        - Recent similar predictions they made
        - Whether they were right or wrong
        - Any calibration warnings

        Returns empty string if no history exists (first run).
        """
        stats = self._get_agent_stats()
        agent_stat = stats.get(agent_name)

        # Find similar past predictions
        similar = self.store.find_similar_predictions(question, top_k=max_similar)

        # No history at all → return empty
        if not agent_stat and not similar:
            return ""

        lines = ["=== YOUR TRACK RECORD ==="]

        # Overall stats
        if agent_stat:
            total = agent_stat["total_predictions"]
            accuracy = agent_stat["accuracy"]
            contrarian_acc = agent_stat["contrarian_accuracy"]

            lines.append(f"Predictions made: {total}")
            lines.append(f"Accuracy: {accuracy:.0%}")

            if contrarian_acc > 0:
                lines.append(f"Contrarian accuracy: {contrarian_acc:.0%}")

            # Calibration warnings
            if total >= 3 and accuracy < 0.4:
                lines.append("⚠ WARNING: Your accuracy is below 40%. Be more careful with bold claims.")
            elif total >= 3 and accuracy > 0.8:
                lines.append("✓ Strong track record. Your instincts have been reliable.")

            if agent_stat.get("contrarian_correct", 0) > 0:
                lines.append("✓ You have successfully predicted upsets before.")

        # Similar past predictions
        if similar:
            lines.append("\nSIMILAR PAST PREDICTIONS:")
            for pred in similar[:max_similar]:
                q_short = pred["question"][:80]
                lines.append(f"  Q: {q_short}")

                # What did this agent say?
                agent_stance = pred.get("agent_stances", {}).get(agent_name, "")
                if agent_stance:
                    lines.append(f"  You said: {agent_stance[:100]}")

                # What was the consensus?
                lines.append(f"  Consensus: {pred.get('consensus_prediction', '?')[:100]}")

                # What actually happened?
                outcome = pred.get("actual_outcome", "")
                if outcome:
                    lines.append(f"  Actual: {outcome[:100]}")
                    # Was agent right?
                    correct_agents = pred.get("correct_agents", [])
                    if agent_name in correct_agents:
                        lines.append("  → You were CORRECT ✓")
                    elif outcome:
                        lines.append("  → You were WRONG ✗")
                else:
                    lines.append("  Actual: (outcome not yet recorded)")

                lines.append("")

        # System-level lessons
        store_stats = self.store.get_stats()
        if store_stats.get("outcomes_recorded", 0) >= 3:
            consensus_acc = store_stats.get("consensus_accuracy", 0)
            if consensus_acc < 0.5:
                lines.append(
                    f"⚠ SYSTEM NOTE: Overall consensus accuracy is only {consensus_acc:.0%}. "
                    "Consider contrarian positions seriously."
                )

        return "\n".join(lines)

    def get_system_memory_summary(self) -> str:
        """
        Get a brief system-level summary of prediction history.
        Useful for the judge prompt.
        """
        stats = self.store.get_stats()
        total = stats.get("total_predictions", 0)

        if total == 0:
            return ""

        lines = ["=== PREDICTION HISTORY ==="]
        lines.append(f"Total past predictions: {total}")
        lines.append(f"Outcomes recorded: {stats.get('outcomes_recorded', 0)}")

        if stats.get("outcomes_recorded", 0) > 0:
            lines.append(f"Consensus accuracy: {stats.get('consensus_accuracy', 0):.0%}")
            lines.append(f"Oracle mode activations: {stats.get('oracle_mode_activations', 0)}")
            lines.append(f"Upset accuracy: {stats.get('upset_accuracy', 0):.0%}")

        # Agent leaderboard
        agent_stats = self._get_agent_stats()
        if agent_stats:
            # Sort by accuracy
            sorted_agents = sorted(
                agent_stats.items(),
                key=lambda x: x[1].get("accuracy", 0),
                reverse=True,
            )
            if sorted_agents:
                top = sorted_agents[0]
                lines.append(f"Best agent: {top[0]} ({top[1]['accuracy']:.0%} accuracy)")

        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════
#  SINGLETON
# ═══════════════════════════════════════════════════════════════════

_agent_memory: Optional[AgentMemory] = None


def get_agent_memory() -> AgentMemory:
    """Get or create the global agent memory instance."""
    global _agent_memory
    if _agent_memory is None:
        _agent_memory = AgentMemory()
    return _agent_memory
