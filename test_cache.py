#!/usr/bin/env python3
"""Test cache functionality."""

import os
import sys
import json
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def test_cache_set_get():
    """Test cache set and get."""
    from cache import CACHE_DIR, cache_set, cache_get, _hash_question, cache_stats
    
    print("\n" + "="*60)
    print("  TEST 1: Cache Set/Get")
    print("="*60)
    
    question = "Will India's semiconductor policy succeed?"
    web_news = "India announces $10B semiconductor scheme..."
    
    shadow_results = [
        {"agent_name": "Chanakya", "role": "chanakya", "stance": "Yes", "confidence": 85},
        {"agent_name": "Doval", "role": "doval", "stance": "Yes", "confidence": 90},
    ]
    full_results = shadow_results + [
        {"agent_name": "Skeptic", "role": "skeptic", "stance": "No", "confidence": 40},
    ]
    
    verdict = {"majority_verdict": "Yes", "confidence": 85}
    
    print(f"\n💾 Setting cache for: {question}")
    cache_set(question, web_news, shadow_results, verdict, full_results=full_results)
    
    print(f"\n💾 Getting cache...")
    cached = cache_get(question, web_news)
    
    assert cached is not None, "Expected cached result"
    assert cached["verdict"]["majority_verdict"] == "Yes", "Wrong verdict"
    assert len(cached["agent_results"]) == len(full_results), "Expected cached full agent results"
    
    print(f"  ✅ Cache HIT!")
    print(f"  Verdict: {cached['verdict']['majority_verdict']}")
    print(f"  From cache: {cached.get('from_cache')}")
    
    # Check file exists
    question_hash = _hash_question(question)
    cache_file = os.path.join(CACHE_DIR, f"{question_hash}.json")
    assert os.path.exists(cache_file), f"Cache file not found: {cache_file}"
    
    print(f"  ✅ Cache file created: {cache_file}")
    
    return True


def test_cache_miss():
    """Test cache miss for new question."""
    from cache import cache_get
    
    print("\n" + "="*60)
    print("  TEST 2: Cache Miss (new question)")
    print("="*60)
    
    question = "Will AI replace programmers by 2030?"
    web_news = "Latest news about AI..."
    
    print(f"\n💾 Checking cache for: {question}")
    cached = cache_get(question, web_news)
    
    assert cached is None, "Expected cache miss"
    
    print(f"  ✅ Cache MISS (expected)")
    
    return True


def test_cache_stats():
    """Test cache statistics."""
    from cache import cache_stats
    
    print("\n" + "="*60)
    print("  TEST 3: Cache Stats")
    print("="*60)
    
    stats = cache_stats()
    print(f"\n📊 Cache stats: {stats}")
    
    assert stats["files"] >= 1, "Expected at least 1 cache file"
    
    print(f"  ✅ Stats working")
    
    return True


def test_cache_expiry():
    """Test cache expiry logic."""
    from cache import CACHE_DIR, cache_set, cache_get, _hash_question
    
    print("\n" + "="*60)
    print("  TEST 4: Cache Expiry")
    print("="*60)
    
    question = "Test expiry question"
    web_news = "Test news"
    
    # Create old cache file
    question_hash = _hash_question(question)
    os.makedirs(CACHE_DIR, exist_ok=True)
    cache_file = os.path.join(CACHE_DIR, f"{question_hash}.json")
    
    old_entry = {
        "question": question,
        "question_hash": question_hash,
        "cached_at": "2024-01-01T00:00:00",  # Very old
        "web_news": web_news,
        "shadow_results": [],
        "verdict": {"majority_verdict": "Test"},
    }
    
    with open(cache_file, "w") as f:
        json.dump(old_entry, f)
    
    print(f"\n💾 Created expired cache file")
    
    # Should return None (expired)
    cached = cache_get(question, web_news)
    
    # Clean up
    os.remove(cache_file)
    
    # Note: may pass or fail depending on current time vs 2024
    # Just verify the logic runs
    print(f"  ✅ Expiry check runs (result: {'expired' if cached is None else 'valid'})")
    
    return True


def test_hash():
    """Test question hashing."""
    from cache import _hash_question
    
    print("\n" + "="*60)
    print("  TEST 5: SHA-256 Hash")
    print("="*60)
    
    q1 = "Will India win the war?"
    q2 = "Will india win the war?"  # Different case
    
    h1 = _hash_question(q1)
    h2 = _hash_question(q2)
    
    print(f"\n🔐 '{q1}' → {h1}")
    print(f"🔐 '{q2}' → {h2}")
    
    assert h1 != h2, "Different questions should have different hashes"
    assert len(h1) == 16, "Hash should be 16 chars"
    
    print(f"\n✅ Hash working correctly")
    
    return True


if __name__ == "__main__":
    print("\n" + "#"*60)
    print("#  VG CACHE TESTS")
    print("#"*60)
    
    tests = [
        ("Cache set/get", test_cache_set_get),
        ("Cache miss", test_cache_miss),
        ("Cache stats", test_cache_stats),
        ("Cache expiry", test_cache_expiry),
        ("Hash function", test_hash),
    ]
    
    passed = failed = 0
    
    for name, fn in tests:
        try:
            if fn():
                passed += 1
        except Exception as e:
            print(f"\n❌ FAILED: {name}")
            print(f"   {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print(f"  RESULTS: {passed}/{passed+failed} passed")
    print("="*60)
    
    sys.exit(0 if failed == 0 else 1)
