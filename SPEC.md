# VG Intelligence System (formerly Veritas)

## Project Overview
- **Name**: VG (Veritas Generation) Political Intelligence Tool
- **Type**: Multi-agent reasoning system with RAG and Simulation Layer
- **Core Functionality**: Analyze political questions through a 10-agent debate (5 historical personalities + 5 AI researchers) using real-time search and personality-specific wisdom.
- **Target Users**: Geopolitical analysts, researchers, and strategic planners.

## Architecture

### The 10-Agent Roster
The system uses 10 distinct agents divided into two groups:

#### 1. Historical Personalities (RAG-Enhanced)
- **Chanakya**: Arthashastra-based realpolitik; follows the treasury and statecraft.
- **Subhash Chandra Bose**: Unconventional alliances and revolutionary strategy.
- **Ajit Doval**: Defensive-offense and preemptive vulnerability exploitation.
- **Henry Kissinger**: Balance of power, triangulation, and back-channel deals.
- **R.N. Kao**: Network mapping, funding trails, and invisible handler detection.

#### 2. AI Researcher Personalities (Logic-Enhanced)
- **The Investigator**: Focused on money trails and timing patterns.
- **The Skeptic**: Challenges every claim with evidence-based rigor.
- **The Pattern Analyst**: Finds historical precedents for current events.
- **The Network Mapper**: Maps institutional and interpersonal connections.
- **The Devil's Advocate**: Challenges the emerging consensus to avoid groupthink.

### Core Pipeline
1. **Web Search (Tavily)**: Fetches real-time current news and facts.
2. **RAG Retrieval (ChromaDB)**: Fetches relevant wisdom from each historical personality's text files.
3. **Simulation Layer (8B)**: A lightweight "shadow round" to detect early consensus.
4. **Main Debate (70B)**: Parallel rounds for dissenting agents to reach a refined verdict.
5. **Judge Self-Consistency**: A final judge runs 3x to ensure a majority-verified, bold prediction.

## Technical Stack
- **Language**: Python 3.12+
- **LLM**: Groq (Llama 3.3 70B & Llama 3.1 8B)
- **Search**: Tavily API
- **Vector DB**: ChromaDB (local persistence)
- **Embeddings**: SentenceTransformer (all-MiniLM-L6-v2)
- **UI**: Rich-based CLI with BYOK flow

## File Structure
```
veritas/
├── agents/             # 10 Agent configurations and implementations
├── core/               # Debate coordination, LLM client, and pipeline logic
├── rag/                # RAG builder, searcher, and personality text source
├── search/             # Web search wrappers
├── main.py             # Entry point with BYOK setup
├── cli.py              # Rich-formatted CLI interface
└── config.py           # Configuration and .env management
```
