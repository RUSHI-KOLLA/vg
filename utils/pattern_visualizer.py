"""
VG Pattern Visualizer — ASCII/Text visualization of pattern analysis results.

Provides readable output for:
- Linguistic patterns detected
- Historical analogies
- Network structures
- Agent stance evolution
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


class PatternVisualizer:
    """Generate ASCII visualizations for pattern analysis."""

    # ASCII box drawing characters
    BOX = {
        "tl": "┌", "tr": "┐", "bl": "└", "br": "┘",
        "h": "─", "v": "│", "cross": "┼",
        "t_down": "┬", "t_up": "┴", "t_left": "├", "t_right": "┤",
    }

    @classmethod
    def draw_box(cls, title: str, content: List[str], width: int = 60) -> str:
        """Draw a bordered box with title and content."""
        lines = []
        top = f"{cls.BOX['tl']}{cls.BOX['h'] * (width - 2)}{cls.BOX['tr']}"
        title_line = f"{cls.BOX['v']} {title.center(width - 4)} {cls.BOX['v']}"
        separator = f"{cls.BOX['v']}{cls.BOX['h'] * (width - 2)}{cls.BOX['v']}"

        lines.append(top)
        lines.append(title_line)
        lines.append(separator)

        for line in content:
            # Truncate or pad
            line = line[: width - 4].ljust(width - 4)
            lines.append(f"{cls.BOX['v']} {line} {cls.BOX['v']}")

        bottom = f"{cls.BOX['bl']}{cls.BOX['h'] * (width - 2)}{cls.BOX['br']}"
        lines.append(bottom)

        return "\n".join(lines)

    @classmethod
    def visualize_linguistic_patterns(
        cls, patterns: Dict[str, List[Dict]], max_width: int = 60
    ) -> str:
        """Visualize linguistic pattern detection results."""
        lines = ["LINGUISTIC PATTERN ANALYSIS", "=" * 40]

        for category, pattern_list in patterns.items():
            if not pattern_list:
                continue

            category_name = category.replace("_", " ").title()
            lines.append(f"\n{category_name}:")

            for p in pattern_list[:5]:  # Top 5
                freq = p.get("frequency", 0)
                conf = p.get("confidence", 0)
                conf_bar = cls._confidence_bar(conf, length=10)

                lines.append(f"  • {p.get('pattern_type', 'unknown')}")
                lines.append(f"    Frequency: {freq} | Confidence: {conf_bar} {conf:.0%}")

        return "\n".join(lines)

    @classmethod
    def visualize_historical_analogies(cls, analogies: List[Dict], max_width: int = 60) -> str:
        """Visualize historical analogy matches."""
        lines = ["HISTORICAL ANALOGIES", "=" * 40]

        if not analogies:
            lines.append("  No strong historical parallels detected")
            return "\n".join(lines)

        for i, analogy in enumerate(analogies[:3], 1):
            event = analogy.get("historical_event", "Unknown event")
            similarity = analogy.get("similarity_score", 0)
            lesson = analogy.get("lesson", "")

            sim_bar = cls._confidence_bar(similarity, length=15)

            lines.append(f"\n{i}. {event}")
            lines.append(f"   Similarity: {sim_bar} {similarity:.0%}")
            if lesson:
                lines.append(f"   Lesson: {lesson[: max_width - 12]}")

        return "\n".join(lines)

    @classmethod
    def visualize_network(cls, actors: List[Dict], max_width: int = 60) -> str:
        """Visualize network structure (key actors)."""
        lines = ["NETWORK STRUCTURE", "=" * 40]

        if not actors:
            lines.append("  No clear network structure detected")
            return "\n".join(lines)

        # Header
        lines.append(f"{'Actor':<25} {'Centrality':<12} {'Connections'}")
        lines.append("-" * 50)

        for actor in actors[:5]:
            name = actor.get("name", "Unknown")[:24]
            centrality = actor.get("centrality_score", 0)
            connections = len(actor.get("connections", []))

            cent_bar = cls._confidence_bar(centrality, length=8)
            lines.append(f"{name:<25} {cent_bar} {centrality:.2f}  {connections}")

        return "\n".join(lines)

    @classmethod
    def visualize_stance_evolution(
        cls, rounds: List[List[Dict]], max_width: int = 70
    ) -> str:
        """Visualize how agent stances evolved across rounds."""
        lines = ["STANCE EVOLUTION ACROSS ROUNDS", "=" * 50]

        if not rounds:
            return "\n".join(lines)

        # Collect all agents
        all_agents = set()
        for round_results in rounds:
            for r in round_results:
                all_agents.add(r.get("agent_name", "Unknown"))

        # Header
        agent_header = "Agent".ljust(20)
        round_headers = "".join([f"R{i+1}".center(10) for i in range(len(rounds))])
        lines.append(f"{agent_header} {round_headers}")
        lines.append("-" * (20 + 10 * len(rounds)))

        for agent in sorted(all_agents):
            row = agent[:19].ljust(20)
            for round_results in rounds:
                # Find this agent in this round
                stance = "N/A"
                for r in round_results:
                    if r.get("agent_name") == agent:
                        conf = r.get("confidence", 0)
                        s = r.get("stance", "")
                        # Extract sentiment
                        if any(w in s.lower() for w in ["yes", "support", "likely"]):
                            stance = f"+{conf}"
                        elif any(w in s.lower() for w in ["no", "reject", "unlikely"]):
                            stance = f"-{conf}"
                        else:
                            stance = f"0{conf}"
                        break
                row += stance.center(10)
            lines.append(row)

        return "\n".join(lines)

    @classmethod
    def visualize_confidence_distribution(cls, results: List[Dict], max_width: int = 50) -> str:
        """Visualize distribution of agent confidences."""
        lines = ["CONFIDENCE DISTRIBUTION", "=" * 40]

        if not results:
            return "\n".join(lines)

        # Bucket confidences: 0-20, 21-40, 41-60, 61-80, 81-100
        buckets = {
            "0-20%": 0,
            "21-40%": 0,
            "41-60%": 0,
            "61-80%": 0,
            "81-100%": 0,
        }

        for r in results:
            conf = r.get("confidence", 0)
            if conf <= 20:
                buckets["0-20%"] += 1
            elif conf <= 40:
                buckets["21-40%"] += 1
            elif conf <= 60:
                buckets["41-60%"] += 1
            elif conf <= 80:
                buckets["61-80%"] += 1
            else:
                buckets["81-100%"] += 1

        max_count = max(buckets.values()) or 1

        for bucket, count in buckets.items():
            bar_len = int((count / max_count) * 20)
            bar = "█" * bar_len
            lines.append(f"{bucket:>8}: {bar} ({count})")

        return "\n".join(lines)

    @classmethod
    def visualize_hallucination_flags(cls, flagged: List[Dict], max_width: int = 60) -> str:
        """Visualize hallucination warnings."""
        lines = ["HALLUCINATION RISK ASSESSMENT", "=" * 40]

        if not flagged:
            lines.append("  ✓ No high-risk claims detected")
            return "\n".join(lines)

        lines.append(f"⚠ {len(flagged)} claim(s) flagged for review:\n")

        for item in flagged[:5]:
            agent = item.get("agent_name", "Unknown")
            risk = item.get("risk_analysis", {})
            risk_score = risk.get("risk_score", 0)

            risk_bar = cls._confidence_bar(risk_score, length=15, invert=True)

            lines.append(f"• {agent}")
            lines.append(f"  Risk: {risk_bar} {risk_score:.0%}")

            flags = []
            if risk.get("speculation"):
                flags.append("speculation")
            if risk.get("overconfidence"):
                flags.append("overconfidence")
            if risk.get("fallacies"):
                flags.append(f"fallacies ({len(risk['fallacies'])})")
            if risk.get("evidence_gap"):
                flags.append("evidence gap")

            if flags:
                lines.append(f"  Flags: {', '.join(flags)}")
            lines.append("")

        return "\n".join(lines)

    @classmethod
    def _confidence_bar(cls, value: float, length: int = 10, invert: bool = False) -> str:
        """Generate a confidence bar visualization."""
        if invert:
            value = 1.0 - value
        filled = int(value * length)
        empty = length - filled
        return "█" * filled + "░" * empty

    @classmethod
    def generate_full_report(cls, pattern_report: Dict, agent_results: List[Dict]) -> str:
        """Generate a complete visual report."""
        sections = []

        # Linguistic patterns
        if pattern_report.get("linguistic_patterns"):
            sections.append(cls.visualize_linguistic_patterns(
                pattern_report["linguistic_patterns"]
            ))

        # Historical analogies
        if pattern_report.get("historical_analogies"):
            sections.append(cls.visualize_historical_analogies(
                pattern_report["historical_analogies"]
            ))

        # Network structure
        if pattern_report.get("key_actors"):
            sections.append(cls.visualize_network(
                pattern_report["key_actors"]
            ))

        # Confidence distribution
        sections.append(cls.visualize_confidence_distribution(agent_results))

        # Hallucination flags
        flagged = [r for r in agent_results if r.get("hallucination_warning")]
        sections.append(cls.visualize_hallucination_flags(flagged))

        return "\n\n".join(sections)


def quick_visualize(data: Dict[str, Any]) -> str:
    """Quick visualization helper for common data structures."""
    viz = PatternVisualizer()

    if "pattern_report" in data and "agent_results" in data:
        return viz.generate_full_report(data["pattern_report"], data["agent_results"])

    if "linguistic_patterns" in data:
        return viz.visualize_linguistic_patterns(data["linguistic_patterns"])

    if "historical_analogies" in data:
        return viz.visualize_historical_analogies(data["historical_analogies"])

    if "key_actors" in data:
        return viz.visualize_network(data["key_actors"])

    if "agent_results" in data:
        return viz.visualize_confidence_distribution(data["agent_results"])

    return "No recognizable data structure for visualization"
