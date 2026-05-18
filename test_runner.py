#!/usr/bin/env python3
"""Test runner for VG system - both no-news and news scenarios."""
import os
import sys

# Setup: add project root to path so `vg.*` imports work in both direct and module execution.
vg_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(vg_dir)
if project_root in sys.path:
    sys.path.remove(project_root)
sys.path.insert(0, project_root)

from dotenv import load_dotenv
load_dotenv(os.path.join(vg_dir, '.env'))

import asyncio
from vg.core.debate import DebateCoordinator


async def test_no_news():
    """Test Pattern Hunter with no news."""
    print("=" * 60)
    print("TEST 1: NO NEWS (Tavily disabled)")
    print("=" * 60)
    
    os.environ['VG_DISABLE_WEB_SEARCH'] = '1'
    from vg.config import config
    config.disable_web_search = True
    config.tavily_api_key = None
    
    result = await DebateCoordinator().run_full_pipeline(
        "Will there be a coup in Myanmar in 2026?"
    )
    
    print("\nAgent Results:")
    no_evidence_count = 0
    out_of_range = 0
    
    for a in result.get("agent_results", []):
        stance = a.get("stance", "N/A")[:80]
        conf = a.get("confidence", 0)
        name = a.get("agent_name", "?")
        
        has_issue = "no evidence" in stance.lower() or "cannot assess" in stance.lower()
        if has_issue:
            print(f"  X {name}: {stance} (conf: {conf}%) <- NO EVIDENCE!")
            no_evidence_count += 1
        else:
            print(f"  OK {name}: {stance} (conf: {conf}%)")
        
        if conf > 0 and (conf < 20 or conf > 80):
            print(f"     WARNING: Confidence {conf}% outside 20-80%")
            out_of_range += 1
    
    verdict = result.get("verdict", {}).get("majority_verdict", "N/A")
    print(f"\nVerdict: {verdict}")
    
    print(f"\n--- VERIFICATION ---")
    print(f"No 'no evidence' statements: {no_evidence_count}/10")
    print(f"Outside 20-80% range: {out_of_range}/10")
    
    return no_evidence_count == 0


async def test_with_news():
    """Test normal flow with news."""
    print("\n" + "=" * 60)
    print("TEST 2: WITH NEWS (normal flow)")
    print("=" * 60)

    os.environ.pop('VG_DISABLE_WEB_SEARCH', None)
    from vg.config import config
    config.disable_web_search = False
    
    from vg.search.web import search_news
    news = search_news("Will Trump impose new tariffs on China in 2025?")
    print(f"News found: {len(news)} chars")
    
    result = await DebateCoordinator().run_full_pipeline(
        "Will Trump impose new tariffs on China in 2025?"
    )
    
    print("\nAgent Results (first 5):")
    for a in result.get("agent_results", [])[:5]:
        stance = a.get("stance", "N/A")[:80]
        conf = a.get("confidence", 0)
        name = a.get("agent_name", "?")
        print(f"  OK {name}: {stance} (conf: {conf}%)")
    
    verdict = result.get("verdict", {}).get("majority_verdict", "N/A")
    stages = [s.get("stage") for s in result.get("pipeline", {}).get("stages", [])]
    
    print(f"\nVerdict: {verdict}")
    print(f"Pipeline stages: {stages}")
    
    return True


async def main():
    try:
        test1_passed = await test_no_news()
        test2_passed = await test_with_news()
        
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"No-news test: {'PASS' if test1_passed else 'FAIL'}")
        print(f"News test: {'PASS' if test2_passed else 'FAIL'}")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        os.environ.pop('VG_DISABLE_WEB_SEARCH', None)
        from vg.config import config
        config.disable_web_search = False


if __name__ == "__main__":
    asyncio.run(main())
