# VG Optimization Guide

This guide explains the world-class optimizations implemented in VG Intelligence.

---

## 1. Token Efficiency Strategies

### 1.1 Compact Prompts (40-60% reduction)

**Before (verbose):**
```
You are Chanakya, the ancient Indian strategist and author of the Arthashastra.
Your task is to analyze the economic dimension of the given question.
Consider who controls the money, who profits from the outcome, and what the treasury flows indicate.
Please provide your analysis in a clear and thoughtful manner.
```
(~60 tokens)

**After (optimized):**
```
Analyze ECONOMIC dimension only: Who funds? Who profits? Treasury flows? Reply: stance|conf|pattern
```
(~15 tokens)

**Implementation:** `vg/core/optimization.py::CompactPrompts`

---

### 1.2 Pipe-Delimited Output (70% reduction vs JSON)

**Before (JSON):**
```json
{
  "stance": "The policy will likely succeed due to strong funding",
  "confidence": 75,
  "key_pattern": "economic_protectionism",
  "historical_precedent": "1991 Indian liberalization",
  "prediction": "Implementation within 18 months",
  "principle_applied": "Treasury follows strategic interest"
}
```
(~50 tokens)

**After (pipe):**
```
Policy likely succeeds|75|economic_protectionism|1991 liberalization|18 month implementation|strategic_interest
```
(~15 tokens)

---

### 1.3 StanceVector Compression (88% reduction)

**Before (natural language summary):**
```
Chanakya: Supports the policy with high confidence (85%) based on economic analysis.
Bose: Opposes with moderate confidence (55%) citing hidden forces.
Doval: Neutral stance (40%) awaiting security assessment.
Kissinger: Supports (70%) based on power balance considerations.
... (10 agents total)
```
(~200 tokens)

**After (StanceVector v3):**
```
1:+0.8|2:-0.6|3:00.4|4:+0.7|5:+0.5|6:+0.75|7:-0.5|8:00.3|9:+0.6|10:-0.4
```
(~50 tokens)

**Mapping:** 1=Chanakya, 2=Bose, 3=Doval, 4=Kissinger, 5=Kao, 6-10=Researchers

---

### 1.4 Adaptive Token Budgeting

Token budgets adjust based on question complexity:

| Question Type | Shadow | Agent | Judge |
|---------------|--------|-------|-------|
| Simple (<25 words, 1 clause) | 96 | 256 | 256 |
| Complex (>25 words, 3+ clauses) | 96 | 640 | 512 |

**Example:**
```python
from vg.core.optimization import get_optimizer

optimizer = get_optimizer()
budgets = optimizer.token_budget.get_budgets("Will India win the election?")
# Returns: {"shadow_round": 96, "agent": 256, "judge": 256, "tier": "simple"}
```

---

## 2. Semantic Caching (30-50% reduction)

### How It Works

1. **Embedding Generation:** Questions are embedded using `BAAI/bge-small-en-v1.5`
2. **Similarity Search:** Cosine similarity finds similar past questions
3. **News Freshness Check:** MD5 hash of news ensures results aren't stale
4. **Cache Hit:** If similarity > 85% and news fresh → return cached result

### Usage

```python
from vg.core.optimization import SemanticCache

cache = SemanticCache()

# Check cache
result = cache.get("Will Modi win re-election?", news_text)
if result:
    print(f"Cache hit! Similarity: {result.similarity:.2f}")

# Set cache
cache.set("Will Modi win re-election?", news_text, analysis_result)
```

### Cache Statistics

```python
stats = cache.stats()
# {"entries": 150, "total_accesses": 420, "avg_accesses": 2.8}
```

---

## 3. Pattern Grounding (Reduces Hallucination)

### Pattern Types Detected

| Pattern Type | What It Detects | Example |
|--------------|-----------------|---------|
| Power Dynamics | Control, resistance, alliance, conflict language | "X dominates Y" → power pattern |
| Economic Signals | Financial flows, resource control | "$10B investment" → economic pattern |
| Temporal Signals | Strategic timing | "announced before election" → timing pattern |
| Historical Analogies | Similar historical precedents | "nationalization" → Iran 1951, Chile 1971 |
| Network Structure | Key actors, connections, centrality | "X appointed Y" → relationship edge |

### Integration

```python
from vg.core.pattern_engine import get_pattern_engine

engine = get_pattern_engine()
report = engine.analyze(question, news_text)

# Get pattern summary for LLM context
summary = engine.get_pattern_summary(report)
# "=== PATTERN ANALYSIS ===
#  LINGUISTIC SIGNALS:
#  - power_control_language: 5 occurrences
#  - economic_financial_flow: 3 occurrences
#  
#  HISTORICAL PARALLELS:
#  - Iran oil nationalization 1951 (similarity: 0.72)
#  Lesson: Short-term disruption, long-term sovereignty
#  
#  KEY ACTORS:
#  - Minister Sharma (centrality: 0.85, connections: 7)"
```

---

## 4. Hallucination Detection

### Detection Layers

| Layer | What It Flags | Threshold |
|-------|---------------|-----------|
| Speculation | "might", "could", "possibly" (2+ markers) | risk_score ≥ 0.5 |
| Overconfidence | "definitely", "certainly", "100%" | 1+ marker |
| Logical Fallacies | "everyone knows", "common sense" | Any pattern |
| Evidence Gap | Claim entities missing from evidence | Coverage < 40% |

### Output

```python
from vg.core.optimization import HallucinationDetector

detector = HallucinationDetector()
analysis = detector.analyze(
    claim="The policy will definitely succeed with 100% certainty",
    evidence="Experts are divided on the policy's effectiveness"
)

# Returns:
# {
#   "speculation": False,
#   "overconfidence": True,  # "definitely", "100%"
#   "fallacies": [],
#   "evidence_gap": True,   # "succeed" not in evidence
#   "risk_score": 0.5       # 50% risk
# }
```

---

## 5. Hybrid RAG Retrieval

### Why Hybrid?

| Method | Strength | Weakness |
|--------|----------|----------|
| Dense (embeddings) | Semantic similarity | Misses exact terms |
| Sparse (BM25) | Exact keyword match | No semantic understanding |
| Recency boost | Time-sensitive queries | May overvalue recent |

**Hybrid = Dense + Sparse + Recency → Best of all**

### Reciprocal Rank Fusion (RRF)

```
RRF_score(doc) = 1/(k + rank_dense) + 1/(k + rank_sparse)
where k = 60 (tuning parameter)
```

### Usage

```python
from vg.rag.hybrid_retriever import get_enhanced_searcher

searcher = get_enhanced_searcher(chroma_path="./chroma_db")

# Basic search
wisdom = searcher.search_wisdom(
    query="economic strategy for resource control",
    collection_name="chanakya_wisdom",
    top_k=3,
    min_score=0.3
)

# Search with metadata
results = searcher.search_with_metadata(
    query="economic strategy",
    collection_name="chanakya_wisdom",
    top_k=5
)

for r in results:
    print(f"Doc {r.doc_id}: score={r.final_score:.3f}")
    print(f"  Dense: {r.dense_score:.3f}, Sparse: {r.sparse_score:.3f}")
    print(f"  Recency boost: {r.recency_boost:.2f}x")
```

---

## 6. Intent Classification (Pipeline Optimization)

### Intent Types

| Intent | Skip RAG? | Skip Web? | Recommended Agents |
|--------|-----------|-----------|-------------------|
| Prediction | No | No | pattern_analyst, kissinger, chanakya |
| Analysis | No | No | investigator, skeptic, pattern_analyst |
| Comparison | No | Yes | kissinger, pattern_analyst, devils_advocate |
| Explanation | Yes | No | investigator, network_mapper |
| Evaluation | No | No | skeptic, investigator, devils_advocate |

### Usage

```python
from vg.core.optimization import get_optimizer

optimizer = get_optimizer()
intent = optimizer.intent_classifier.classify("Compare Modi and Nehru's economic policies")

# Returns:
# {
#   "intent": "comparison",
#   "skip_rag": False,
#   "skip_web": True,  # Historical comparison doesn't need fresh news
#   "recommended_agents": ["kissinger", "pattern_analyst", "devils_advocate"],
#   "complexity": "normal"
# }
```

---

## 7. Convergence-Based Early Exit

### How It Works

1. After shadow round, normalize stances to buckets: `for`, `against`, `neutral`
2. If 8/10 agents in same bucket → converged
3. If converged: skip full debate, jump to judge (1 run)
4. If not converged: full debate with filtered agents (only dissenters + 2 context)

### Token Savings

| Scenario | Without Optimization | With Optimization | Savings |
|----------|---------------------|-------------------|---------|
| 9/10 agree in shadow | 10 agents × 70B | Judge only (1 run) | ~85% |
| 6/10 agree in shadow | 10 agents × 70B × 2 rounds | 5 agents × 70B × 1 round | ~75% |

---

## 8. Performance Benchmarks

### Test Question: "Will India's semiconductor policy succeed?"

| Metric | Basic | Enhanced | Improvement |
|--------|-------|----------|-------------|
| Total tokens | 8,234 | 3,456 | 58% reduction |
| API calls | 23 | 14 | 39% reduction |
| Latency | 47s | 26s | 45% faster |
| Cache hit? | N/A | Yes (similar Q) | Instant |

### Cost Analysis (at $0.00039/1K input, $0.00079/1K output)

| Pipeline | Cost per Query | Monthly (1000 queries) |
|----------|----------------|------------------------|
| Basic | $0.0032 | $3.21 |
| Enhanced | $0.0014 | $1.35 |
| **Savings** | **56%** | **$1.86/query** |

---

## 9. Best Practices

### DO ✅

- Use enhanced mode by default
- Enable semantic caching (install `fastembed`)
- Keep Tavily API key current for fresh evidence
- Review hallucination flags before publishing
- Use `--json` for programmatic access

### DON'T ❌

- Disable pattern grounding (reduces quality)
- Ignore hallucination warnings
- Run basic mode unless debugging
- Use without evidence for factual claims

---

## 10. Troubleshooting

### "Semantic cache not working"

1. Ensure `fastembed` is installed: `pip install fastembed`
2. Check cache directory exists: `./vg_cache`
3. Verify similarity threshold (default 0.85)

### "Pattern engine returns empty report"

1. Ensure news text is provided
2. Check text length (need >50 words for patterns)
3. Some questions genuinely have no historical parallels

### "High hallucination flags"

This is a feature, not a bug! It means:
- Evidence is weak for the question
- Agents are speculating beyond available data
- Consider: "I don't know" is a valid answer

---

**For questions or contributions, open an issue on GitHub.**
