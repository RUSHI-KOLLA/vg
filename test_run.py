#!/usr/bin/env python3
"""Smoke runner for the real VG package path."""

import asyncio
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT in sys.path:
    sys.path.remove(PROJECT_ROOT)
sys.path.insert(0, PROJECT_ROOT)

from vg.core.debate import DebateCoordinator


async def main() -> None:
    question = "Will there be a coup in Myanmar in 2026?"
    print(f"\n🧠 Question: {question}")

    coordinator = DebateCoordinator()
    result = await coordinator.run_full_pipeline(question)

    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

    agents = result.get("agent_results", [])
    print(f"\nAgents ({len(agents)}):")
    for agent in agents:
        stance = agent.get("stance", "N/A")[:80]
        conf = agent.get("confidence", 0)
        name = agent.get("agent_name", "?")
        print(f"  {name}: {stance} (conf: {conf}%)")

    print(f"\nVerdict: {result.get('verdict', {}).get('majority_verdict', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(main())
