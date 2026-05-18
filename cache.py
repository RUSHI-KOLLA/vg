"""
VG Cache — file-based result caching with SHA-256 hashing.

Usage:
    from vg.cache import cache_get, cache_set
    
    # Check cache before running pipeline
    cached = cache_get(question, web_news)
    if cached:
        return cached  # Skip all API calls
    
    # After pipeline runs
    cache_set(question, web_news, shadow_results, verdict)
"""

import hashlib
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
CACHE_TTL_HOURS = 24


def _hash_question(question: str) -> str:
    """Create SHA-256 hash of question."""
    return hashlib.sha256(question.encode()).hexdigest()[:16]


def cache_get(question: str, web_news: str = "") -> Optional[Dict[str, Any]]:
    """
    Check cache for question.
    
    Returns cached result if:
    - Question hash exists in cache
    - Cache file < 24 hours old
    - News content matches (not significantly different)
    
    Args:
        question: The analysis question
        web_news: Current web news (to check staleness)
    
    Returns:
        Cached result dict or None if not found/stale
    """
    question_hash = _hash_question(question)
    cache_file = os.path.join(CACHE_DIR, f"{question_hash}.json")
    
    if not os.path.exists(cache_file):
        return None
    
    try:
        with open(cache_file, "r") as f:
            cached = json.load(f)
    except (json.JSONDecodeError, IOError):
        return None
    
    # Check TTL
    cached_at = cached.get("cached_at", "")
    if cached_at:
        try:
            cached_time = datetime.fromisoformat(cached_at)
            age = datetime.now() - cached_time
            if age > timedelta(hours=CACHE_TTL_HOURS):
                print(f"  ⏳ Cache expired (age: {age.total_seconds()/3600:.1f}h)")
                return None
        except (ValueError, OSError):
            return None
    
    # Check news staleness (simple: compare first 200 chars)
    cached_news = cached.get("web_news", "")[:200]
    current_news = web_news[:200]
    
    if current_news and cached_news:
        # If news changed significantly, invalidate cache
        if abs(len(current_news) - len(cached_news)) > 100:
            print(f"  ⏳ Cache stale (news changed)")
            return None
    
    print(f"  💾 Cache HIT ({question_hash})")
    agent_results = cached.get("full_results") or cached.get("shadow_results") or cached.get("agent_results")
    return {
        "question": cached.get("question"),
        "verdict": cached.get("verdict"),
        "agent_results": agent_results,
        "pipeline": cached.get("pipeline"),
        "from_cache": True,
    }


def cache_set(
    question: str,
    web_news: str,
    shadow_results: list,
    verdict: Dict[str, Any],
    full_results: list = None,
    pipeline: Dict[str, Any] = None,
) -> None:
    """
    Save pipeline result to cache.
    
    Args:
        question: The analysis question
        web_news: Current web news snapshot
        shadow_results: Shadow round results
        verdict: Final judge verdict
        full_results: Full debate results (if different from shadow)
        pipeline: Pipeline log
    """
    question_hash = _hash_question(question)
    cache_file = os.path.join(CACHE_DIR, f"{question_hash}.json")
    
    # Clean results for storage (remove error details)
    def clean_results(results: list) -> list:
        return [
            {
                "agent_name": r.get("agent_name"),
                "role": r.get("role"),
                "stance": r.get("stance"),
                "confidence": r.get("confidence"),
                "key_pattern": r.get("key_pattern"),
                "error": r.get("error", False),
            }
            for r in (results or [])
        ]
    
    cache_entry = {
        "question": question,
        "question_hash": question_hash,
        "cached_at": datetime.now().isoformat(),
        "web_news": web_news[:1000] if web_news else "",  # Snapshot
        "shadow_results": clean_results(shadow_results),
        "verdict": verdict,
        "full_results": clean_results(full_results) if full_results else clean_results(shadow_results),
        "pipeline": {
            "stages": [
                s.get("stage") for s in (pipeline.get("stages", []) if pipeline else [])
            ]
        } if pipeline else {},
    }
    
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cache_file, "w") as f:
            json.dump(cache_entry, f, indent=2, default=str)
        print(f"  💾 Cache SET ({question_hash})")
    except IOError as e:
        print(f"  ⚠ Cache write failed: {e}")


def cache_clear() -> None:
    """Clear all cache files."""
    if os.path.exists(CACHE_DIR):
        for f in os.listdir(CACHE_DIR):
            if f.endswith(".json"):
                os.remove(os.path.join(CACHE_DIR, f))
    print(f"  🗑 Cache cleared")


def cache_stats() -> Dict[str, int]:
    """Return cache statistics."""
    if not os.path.exists(CACHE_DIR):
        return {"files": 0, "total_size": 0}
    
    files = [f for f in os.listdir(CACHE_DIR) if f.endswith(".json")]
    total_size = sum(
        os.path.getsize(os.path.join(CACHE_DIR, f))
        for f in files
    )
    
    return {"files": len(files), "total_size": total_size}
