# VG Intelligence — Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies

```bash
cd vg
pip install -r requirements.txt
```

### Step 2: Set Up API Keys

```bash
# Copy example env file
cp .env.example .env

# Edit .env with your keys
nano .env
```

**Required:**
- `GROQ_API_KEY` — Get free at https://console.groq.com

**Optional:**
- `TAVILY_API_KEY` — Get at https://tavily.com (for web search)

### Step 3: Run Your First Analysis

```bash
# Enhanced mode (default - recommended)
python -m vg.main "Will the Fed raise interest rates next month?"

# See optimization stats
python -m vg.main "Will India win the next election?" --json

# View full report
cat vg_report.json | python -m json.tool
```

---

## 📊 Understanding the Output

### Console Output

```
═" * 60
  VG POLITICAL INTELLIGENCE REPORT
═" * 60

  QUESTION: Will the Fed raise interest rates next month?

  MAJORITY VERDICT: Rates likely to hold steady; one cut possible if inflation cools
  CONFIDENCE: 72%

  KEY PATTERN IDENTIFIED:
    Data-dependent caution with political pressure

  HISTORICAL PRECEDENT:
    1994-95 Greenspan pause amid political uncertainty

  AGENT BREAKDOWN:
    ✓ Chanakya                  Economic leverage suggests caution [75%]
    ✓ Bose                      Hidden political pressure mounting [68%]
    ✓ Doval                     No immediate security threats [45%]
    ...

  MINORITY DISSENT:
    Skeptic and Devil's Advocate cite insufficient inflation data

  REASONING:
    Multiple dimensions point to caution, but data dependency remains

─" * 56
  DISCLAIMER: Speculative pattern analysis.
  Not verified intelligence. For research only.
═" * 60

⚡ OPTIMIZATION STATS:
   Cache hits: 0
   Pattern grounding: ✓
   Hallucinations flagged: 1
   Optimizations applied: intent_classification, pattern_grounding, ...
   Total time: 28.4s
```

### JSON Output

```json
{
  "question": "Will the Fed raise interest rates next month?",
  "verdict": {
    "majority_verdict": "Rates likely to hold steady; one cut possible if inflation cools",
    "confidence": 72,
    "key_pattern": "Data-dependent caution with political pressure",
    "historical_precedent": "1994-95 Greenspan pause amid political uncertainty",
    "strongest_dissent": "Inflation may reaccelerate, requiring continued hikes",
    "reasoning": "Economic, geopolitical, and network dimensions all suggest caution"
  },
  "agent_results": [...],
  "stats": {
    "cache_hits": 0,
    "pattern_grounding_applied": true,
    "hallucinations_flagged": 1,
    "tokens_saved_estimate": 4200
  },
  "elapsed_seconds": 28.4
}
```

---

## 🧪 Try These Example Questions

### Economic Analysis
```bash
python -m vg.main "Will China's economy overtake the US by 2030?"
```

### Geopolitical Prediction
```bash
python -m vg.main "Will NATO expand further into Eastern Europe?"
```

### Policy Evaluation
```bash
python -m vg.main "Will India's semiconductor manufacturing policy succeed?"
```

### Conflict Analysis
```bash
python -m vg.main "What's the likely outcome of the Israel-Palestine conflict?"
```

### Leadership Transition
```bash
python -m vg.main "What happens after Putin's rule ends?"
```

---

## 🔧 Configuration Options

### Environment Variables (.env)

```bash
# API Keys
GROQ_API_KEY=gsk_...
TAVILY_API_KEY=tvly_...

# Models
GROQ_MODEL_LARGE=llama-3.3-70b-versatile
GROQ_MODEL_SMALL=llama-3.1-8b-instant

# Rate Limits
GROQ_RPM_LIMIT=15
GROQ_MAX_CONCURRENT=5

# RAG
VG_RAG_TOP_K=2
VG_RAG_CHUNK_WORDS=300

# Debate
VG_MAX_DEBATE_ROUNDS=2
VG_CONVERGENCE_THRESHOLD=0.8
```

### CLI Flags

| Flag | Effect |
|------|--------|
| `--json` | Save full report to `vg_report.json` |
| `--basic` | Use basic pipeline (no optimizations) |
| `--enhanced` | Use enhanced pipeline (default) |

---

## 📈 Performance Tips

### 1. Enable Semantic Caching

```bash
# Install fastembed for semantic caching
pip install fastembed

# Subsequent similar queries will be instant!
```

### 2. Use RAG Wisdom

```bash
# Build RAG index first (one-time)
python -m vg.rag.builder

# Then run analysis with historical wisdom
python -m vg.main "Your question"
```

### 3. Check Cache Stats

```python
from vg.core.optimization import SemanticCache

cache = SemanticCache()
print(cache.stats())
# {"entries": 50, "total_accesses": 120, "avg_accesses": 2.4}
```

---

## 🐛 Troubleshooting

### "GROQ_API_KEY is not set"

```bash
# Add to .env file
echo "GROQ_API_KEY=your_key_here" >> .env
```

### "Tavily not installed"

```bash
# Optional - for web search
pip install tavily-python
```

### "No module named 'fastembed'"

```bash
# Optional - for semantic caching
pip install fastembed
```

### "Rate limit exceeded"

- Wait 1 minute between queries
- Reduce `GROQ_RPM_LIMIT` in `.env`
- Use semantic caching (reduces API calls)

---

## 📚 Next Steps

1. **Read the SPEC** — `SPEC.md` for architecture overview
2. **Read Optimization Guide** — `OPTIMIZATION_GUIDE.md` for advanced features
3. **Explore the Code** — `vg/core/enhanced_debate.py` for the main pipeline
4. **Add Custom Agents** — See `vg/agents/config.py` for agent definitions

---

## 🆘 Getting Help

- **Documentation:** `OPTIMIZATION_GUIDE.md`, `SPEC.md`
- **Examples:** Run `python -m vg.main --help`
- **Issues:** Check console output for detailed errors

---

**Happy analyzing! 🧠**
