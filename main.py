"""
VG main entry point.

Default behavior:
  python -m vg.main
  python -m vg.main --web --port 8080

Legacy terminal mode:
  python -m vg.main --cli "Will India's semiconductor policy succeed?"
  python -m vg.main --cli "Your question" --basic --json
"""

import asyncio
import sys
import os
import json
import textwrap

if __package__ in (None, ""):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    # If the folder is named 'vg' (local development), parent_dir works perfectly.
    if os.path.basename(current_dir) == "vg":
        sys.path.insert(0, parent_dir)
    else:
        # On Railway, the folder is usually named '/app' or '/workspace'.
        # We must alias the current directory as 'vg' so imports work.
        sys.path.insert(0, current_dir)
        import importlib.util
        import importlib.machinery
        
        # Create a dynamic module for 'vg' pointing to the current directory
        if "vg" not in sys.modules:
            spec = importlib.machinery.PathFinder.find_spec("__init__", [current_dir])
            if spec is None:
                # Fallback if __init__.py is missing
                from types import ModuleType
                vg_mod = ModuleType("vg")
                vg_mod.__path__ = [current_dir]
                sys.modules["vg"] = vg_mod
            else:
                spec.name = "vg"
                vg_mod = importlib.util.module_from_spec(spec)
                sys.modules["vg"] = vg_mod
                spec.loader.exec_module(vg_mod)

from vg.config import config

# Default to enhanced coordinator if available
try:
    from vg.core.enhanced_debate import EnhancedDebateCoordinator as DebateCoordinator
    ENHANCED_MODE = True
except ImportError:
    from vg.core.debate import DebateCoordinator
    ENHANCED_MODE = False


async def analyze_async(question: str, use_enhanced: bool = True, api_key: str = None) -> dict:
    """Run the full VG analysis pipeline."""
    if use_enhanced and ENHANCED_MODE:
        coordinator = DebateCoordinator(enable_optimizations=True, api_key=api_key)
    else:
        coordinator = DebateCoordinator()
    return await coordinator.run_full_pipeline(question)


def analyze(question: str, case_name: str = None, use_enhanced: bool = True) -> dict:
    """Synchronous wrapper for the VG pipeline."""
    from vg.setup import run_async
    return run_async(analyze_async(question, use_enhanced=use_enhanced))


def print_report(result: dict):
    """Print the final VG intelligence report."""
    verdict = result.get("verdict", {})
    agents = result.get("agent_results", [])
    question = result.get("question", "Unknown")

    print()
    print("═" * 60)
    print("  VG POLITICAL INTELLIGENCE REPORT")
    print("═" * 60)
    print(f"\n  QUESTION: {question}")

    print(f"\n  MAJORITY VERDICT: {verdict.get('majority_verdict', verdict.get('primary_verdict', 'No verdict'))}")
    print(f"  CONFIDENCE: {verdict.get('confidence', verdict.get('primary_confidence', 0))}%")

    # 🔮 Oracle Mode — Upset Probability
    oracle_data = result.get("oracle_mode", {})
    upset_prob = verdict.get("upset_probability", oracle_data.get("upset_probability", 0))
    if upset_prob > 0:
        print(f"\n  🔮 UPSET PROBABILITY: {upset_prob}%")

        upset_scenario = verdict.get("upset_scenario", oracle_data.get("upset_scenario", ""))
        if upset_scenario:
            print(f"  🔮 UPSET SCENARIO:")
            for line in textwrap.wrap(str(upset_scenario), width=54):
                print(f"    {line}")

        key_signal = verdict.get("key_signal", "")
        if key_signal:
            print(f"  🔮 KEY SIGNAL TO WATCH:")
            print(f"    {key_signal}")

        signals = oracle_data.get("key_signals_to_watch", [])
        if signals:
            print(f"\n  🔮 SIGNALS TO WATCH:")
            for s in signals[:3]:
                print(f"    • {s}")

    key_pattern = verdict.get("key_pattern", verdict.get("upset_pattern", ""))
    if key_pattern:
        print(f"\n  KEY PATTERN IDENTIFIED:")
        print(f"    {key_pattern}")

    precedent = verdict.get("historical_precedent", verdict.get("historical_parallel", ""))
    if precedent:
        print(f"\n  HISTORICAL PRECEDENT:")
        print(f"    {precedent}")

    print(f"\n  AGENT BREAKDOWN:")
    for agent in agents:
        marker = "✗" if agent.get("error") else "✓"
        name = agent.get("agent_name", "Unknown")
        stance = agent.get("stance", "N/A")
        conf = agent.get("confidence", 0)
        wrapped = textwrap.wrap(str(stance), width=72) or ["N/A"]
        print(f"    {marker} {name:25} {wrapped[0]} [{conf}%]")
        for line in wrapped[1:]:
            print(f"      {'':25} {line}")

    # Show contrarian agents if Oracle Mode was active
    contrarian_agents = oracle_data.get("contrarian_agent_results", [])
    if contrarian_agents:
        print(f"\n  🔮 CONTRARIAN AGENTS (arguing against consensus):")
        for agent in contrarian_agents:
            if agent.get("error"):
                continue
            name = agent.get("agent_name", "Unknown")
            stance = agent.get("stance", "N/A")
            conf = agent.get("confidence", 0)
            wrapped = textwrap.wrap(str(stance), width=68) or ["N/A"]
            print(f"    🔮 {name:23} {wrapped[0]} [{conf}%]")
            for line in wrapped[1:]:
                print(f"      {'':25} {line}")

    dissent = verdict.get("strongest_dissent", verdict.get("strongest_contrarian_argument", ""))
    if dissent:
        print(f"\n  MINORITY DISSENT:")
        print(f"    {dissent}")

    reasoning = verdict.get("reasoning", "")
    if reasoning:
        print(f"\n  REASONING:")
        print(f"    {reasoning}")

    print(f"\n  {'─' * 56}")
    print("  DISCLAIMER: Speculative pattern analysis.")
    print("  Not verified intelligence. For research only.")
    print("═" * 60)
    print()


def byok_setup():
    """Check for API keys, prompt if missing."""
    from vg.setup import byok_setup as _byok
    _byok(interactive=True)


def _consume_option(argv: list[str], option: str, default: str) -> str:
    """Pop an option and its value from argv if present."""
    if option not in argv:
        return default
    index = argv.index(option)
    try:
        value = argv[index + 1]
    except IndexError as exc:
        raise SystemExit(f"{option} requires a value.") from exc
    del argv[index:index + 2]
    return value


def run_cli(argv: list[str]) -> None:
    """Run the legacy terminal interface."""
    byok_setup()

    save_json = "--json" in argv
    if save_json:
        argv = [arg for arg in argv if arg != "--json"]

    use_enhanced = "--basic" not in argv
    if "--basic" in argv:
        argv = [arg for arg in argv if arg != "--basic"]
    if "--enhanced" in argv:
        argv = [arg for arg in argv if arg != "--enhanced"]

    if argv:
        question = " ".join(argv)
    else:
        mode_str = " [ENHANCED]" if use_enhanced and ENHANCED_MODE else ""
        question = input(f"\n🧠 Enter your political analysis question{mode_str}: ")

    if not question.strip():
        print("No question provided. Exiting.")
        sys.exit(1)

    print(f"\n🚀 VG Intelligence Analysis{' (Enhanced Mode)' if use_enhanced and ENHANCED_MODE else ''}")
    print("=" * 56)

    result = analyze(question, use_enhanced=use_enhanced)
    print_report(result)

    # Show optimization stats if enhanced mode
    if use_enhanced and ENHANCED_MODE:
        stats = result.get("stats", {})
        pipeline = result.get("pipeline", {})
        optimizations = pipeline.get("optimizations_applied", [])

        print("\n⚡ OPTIMIZATION STATS:")
        print(f"   Cache hits: {stats.get('cache_hits', 0)}")
        print(f"   Pattern grounding: {'✓' if stats.get('pattern_grounding_applied') else '✗'}")
        print(f"   Hallucinations flagged: {stats.get('hallucinations_flagged', 0)}")
        print(f"   Optimizations applied: {', '.join(optimizations) if optimizations else 'None'}")
        print(f"   Total time: {result.get('elapsed_seconds', 'N/A')}s")

    # Optionally save JSON
    if save_json:
        output_path = "vg_report.json"
        with open(output_path, "w") as f:
            json.dump(result, f, indent=2, default=str)
        print(f"📄 Full report saved to {output_path}")


def run_web(argv: list[str]) -> None:
    """Run the browser-native web server."""
    host = _consume_option(argv, "--host", os.getenv("VG_HOST", "0.0.0.0"))
    port = int(_consume_option(argv, "--port", os.getenv("PORT", os.getenv("VG_PORT", "8080"))))
    from vg.api.server import run_server
    run_server(host=host, port=port)


if __name__ == "__main__":
    argv = sys.argv[1:]
    use_cli = "--cli" in argv
    if use_cli:
        argv = [arg for arg in argv if arg != "--cli"]
        run_cli(argv)
    else:
        if "--web" in argv:
            argv = [arg for arg in argv if arg != "--web"]
        run_web(argv)
