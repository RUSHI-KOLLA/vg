"""
VG Prediction Feedback Loop — Track predictions vs. actual outcomes.

Stores every prediction with a timestamp and allows the user to input
actual outcomes later. Over time, this data is used to:
- Track which agents were right when consensus was wrong
- Weight agents based on their contrarian accuracy
- Improve the upset probability calibration
"""

import json
import os
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any


# ═══════════════════════════════════════════════════════════════════
#  DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════

@dataclass
class PredictionRecord:
    """A single prediction made by the system."""
    question: str
    timestamp: str
    prediction_id: str

    # System outputs
    consensus_prediction: str
    consensus_confidence: int
    oracle_mode_activated: bool = False
    upset_prediction: str = ""
    upset_probability: int = 0

    # Per-agent breakdown
    agent_stances: Dict[str, str] = field(default_factory=dict)
    agent_confidences: Dict[str, int] = field(default_factory=dict)

    # Patterns detected
    patterns_detected: List[str] = field(default_factory=list)
    upset_patterns_matched: List[str] = field(default_factory=list)

    # Outcome (filled in later by user)
    actual_outcome: str = ""
    outcome_recorded_at: str = ""
    consensus_was_correct: Optional[bool] = None
    upset_was_correct: Optional[bool] = None

    # Agents who got it right
    correct_agents: List[str] = field(default_factory=list)
    contrarian_correct_agents: List[str] = field(default_factory=list)


# ═══════════════════════════════════════════════════════════════════
#  FEEDBACK STORE
# ═══════════════════════════════════════════════════════════════════

class FeedbackStore:
    """
    Persistent store for prediction records.

    Tracks predictions and outcomes to improve future accuracy.
    """

    def __init__(self, store_dir: str = "./vg_cache/feedback"):
        self.store_dir = store_dir
        self._index_path = os.path.join(store_dir, "prediction_index.json")
        self._records: Dict[str, PredictionRecord] = {}
        self._ensure_dir()
        self._load_index()

    def _ensure_dir(self):
        os.makedirs(self.store_dir, exist_ok=True)

    def _load_index(self):
        """Load prediction index from disk."""
        if os.path.exists(self._index_path):
            try:
                with open(self._index_path, "r") as f:
                    data = json.load(f)
                for pid, entry in data.items():
                    self._records[pid] = PredictionRecord(**entry)
            except Exception:
                pass

    def _save_index(self):
        """Persist prediction index to disk."""
        try:
            data = {pid: asdict(rec) for pid, rec in self._records.items()}
            with open(self._index_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"  ⚠ Feedback save failed: {e}")

    def _generate_id(self, question: str) -> str:
        """Generate a unique prediction ID."""
        import hashlib
        ts = str(time.time())
        return hashlib.sha256(f"{question}|{ts}".encode()).hexdigest()[:12]

    # ─── PUBLIC API ──────────────────────────────────────────────

    def record_prediction(
        self,
        question: str,
        consensus_prediction: str,
        consensus_confidence: int,
        agent_stances: Dict[str, str],
        agent_confidences: Dict[str, int],
        oracle_mode_activated: bool = False,
        upset_prediction: str = "",
        upset_probability: int = 0,
        patterns_detected: List[str] = None,
        upset_patterns_matched: List[str] = None,
    ) -> str:
        """
        Record a new prediction. Returns prediction ID for later outcome recording.
        """
        pid = self._generate_id(question)

        record = PredictionRecord(
            question=question,
            timestamp=datetime.now().isoformat(),
            prediction_id=pid,
            consensus_prediction=consensus_prediction,
            consensus_confidence=consensus_confidence,
            oracle_mode_activated=oracle_mode_activated,
            upset_prediction=upset_prediction,
            upset_probability=upset_probability,
            agent_stances=agent_stances,
            agent_confidences=agent_confidences,
            patterns_detected=patterns_detected or [],
            upset_patterns_matched=upset_patterns_matched or [],
        )

        self._records[pid] = record
        self._save_index()
        return pid

    def record_outcome(
        self,
        prediction_id: str,
        actual_outcome: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Record the actual outcome for a prediction.
        Returns accuracy analysis.
        """
        record = self._records.get(prediction_id)
        if not record:
            return None

        record.actual_outcome = actual_outcome
        record.outcome_recorded_at = datetime.now().isoformat()

        # Simple accuracy check (can be enhanced)
        outcome_lower = actual_outcome.lower()
        consensus_lower = record.consensus_prediction.lower()

        # Check if consensus was correct (rough heuristic)
        consensus_keywords = set(consensus_lower.split())
        outcome_keywords = set(outcome_lower.split())
        overlap = consensus_keywords & outcome_keywords
        record.consensus_was_correct = len(overlap) > 3

        # Check if upset prediction was correct
        if record.upset_prediction:
            upset_lower = record.upset_prediction.lower()
            upset_keywords = set(upset_lower.split())
            upset_overlap = upset_keywords & outcome_keywords
            record.upset_was_correct = len(upset_overlap) > 3

        # Identify which agents were closest to actual outcome
        for agent_name, stance in record.agent_stances.items():
            stance_lower = stance.lower()
            stance_keywords = set(stance_lower.split())
            agent_overlap = stance_keywords & outcome_keywords
            if len(agent_overlap) > 2:
                record.correct_agents.append(agent_name)

                # Was this agent a contrarian?
                if record.oracle_mode_activated:
                    record.contrarian_correct_agents.append(agent_name)

        self._save_index()

        return {
            "prediction_id": prediction_id,
            "question": record.question,
            "consensus_correct": record.consensus_was_correct,
            "upset_correct": record.upset_was_correct,
            "correct_agents": record.correct_agents,
            "contrarian_correct_agents": record.contrarian_correct_agents,
        }

    def get_agent_accuracy(self) -> Dict[str, Dict[str, Any]]:
        """
        Calculate per-agent accuracy across all recorded outcomes.

        Returns dict mapping agent_name -> {total, correct, contrarian_correct, accuracy}
        """
        agent_stats: Dict[str, Dict[str, int]] = {}

        for record in self._records.values():
            if not record.actual_outcome:
                continue  # Skip predictions without outcomes

            for agent_name in record.agent_stances:
                if agent_name not in agent_stats:
                    agent_stats[agent_name] = {
                        "total": 0,
                        "correct": 0,
                        "contrarian_correct": 0,
                    }

                agent_stats[agent_name]["total"] += 1
                if agent_name in record.correct_agents:
                    agent_stats[agent_name]["correct"] += 1
                if agent_name in record.contrarian_correct_agents:
                    agent_stats[agent_name]["contrarian_correct"] += 1

        # Calculate accuracy
        result = {}
        for agent_name, stats in agent_stats.items():
            total = stats["total"]
            result[agent_name] = {
                "total_predictions": total,
                "correct": stats["correct"],
                "contrarian_correct": stats["contrarian_correct"],
                "accuracy": stats["correct"] / total if total > 0 else 0,
                "contrarian_accuracy": (
                    stats["contrarian_correct"] / total if total > 0 else 0
                ),
            }

        return result

    def find_similar_predictions(
        self,
        question: str,
        top_k: int = 3,
        min_overlap: int = 2,
    ) -> List[Dict[str, Any]]:
        """
        Find past predictions on similar topics using keyword overlap.

        Returns list of dicts with prediction details, sorted by relevance.
        """
        if not self._records:
            return []

        # Extract keywords from current question
        stop_words = {
            "the", "a", "an", "is", "are", "was", "were", "will", "would",
            "can", "could", "do", "does", "did", "in", "on", "at", "to",
            "for", "of", "with", "and", "or", "but", "not", "be", "have",
            "has", "had", "this", "that", "what", "who", "how", "why",
            "when", "where", "which", "if", "it", "its", "by", "from",
        }
        q_words = set(question.lower().split()) - stop_words
        q_words = {w for w in q_words if len(w) > 2}

        scored = []
        for record in self._records.values():
            # Calculate keyword overlap
            rec_words = set(record.question.lower().split()) - stop_words
            rec_words = {w for w in rec_words if len(w) > 2}
            overlap = len(q_words & rec_words)

            if overlap >= min_overlap:
                scored.append((overlap, record))

        # Sort by overlap descending
        scored.sort(key=lambda x: x[0], reverse=True)

        results = []
        for overlap, record in scored[:top_k]:
            results.append({
                "prediction_id": record.prediction_id,
                "question": record.question,
                "consensus_prediction": record.consensus_prediction,
                "consensus_confidence": record.consensus_confidence,
                "agent_stances": record.agent_stances,
                "agent_confidences": record.agent_confidences,
                "actual_outcome": record.actual_outcome,
                "correct_agents": record.correct_agents,
                "oracle_mode_activated": record.oracle_mode_activated,
                "upset_prediction": record.upset_prediction,
                "relevance_score": overlap,
            })

        return results

    def get_pending_outcomes(self) -> List[Dict[str, str]]:
        """Get predictions that don't have outcomes recorded yet."""
        pending = []
        for record in self._records.values():
            if not record.actual_outcome:
                pending.append({
                    "prediction_id": record.prediction_id,
                    "question": record.question,
                    "consensus_prediction": record.consensus_prediction,
                    "timestamp": record.timestamp,
                })
        return pending

    def get_stats(self) -> Dict[str, Any]:
        """Get overall feedback loop statistics."""
        total = len(self._records)
        with_outcomes = sum(
            1 for r in self._records.values() if r.actual_outcome
        )
        oracle_activated = sum(
            1 for r in self._records.values() if r.oracle_mode_activated
        )
        consensus_correct = sum(
            1 for r in self._records.values()
            if r.consensus_was_correct is True
        )
        upset_correct = sum(
            1 for r in self._records.values()
            if r.upset_was_correct is True
        )

        return {
            "total_predictions": total,
            "outcomes_recorded": with_outcomes,
            "oracle_mode_activations": oracle_activated,
            "consensus_accuracy": (
                consensus_correct / with_outcomes if with_outcomes > 0 else 0
            ),
            "upset_accuracy": (
                upset_correct / oracle_activated
                if oracle_activated > 0
                else 0
            ),
        }


# ═══════════════════════════════════════════════════════════════════
#  SINGLETON
# ═══════════════════════════════════════════════════════════════════

_feedback_store: Optional[FeedbackStore] = None


def get_feedback_store() -> FeedbackStore:
    """Get or create the global feedback store."""
    global _feedback_store
    if _feedback_store is None:
        _feedback_store = FeedbackStore()
    return _feedback_store
