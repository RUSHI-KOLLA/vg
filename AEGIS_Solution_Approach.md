# AEGIS: Adaptive Enterprise Graph Intelligence System
## Solution Approach — AI-Powered Detection of Suspicious Transactions & Mule Accounts

**Team Submission | National AI/ML Hackathon 2026**

---

## Table of Contents
1. Problem Understanding
2. Core Idea of the Solution
3. System Architecture
4. AI/ML Components
5. Rule-Based + AI Hybrid Detection
6. Real-Time Data Pipeline
7. Innovation Section
8. Implementation Plan
9. Datasets & Data Sources
10. Tech Stack
11. Expected Impact
12. Future Scope

---

## 1. Problem Understanding

### 1.1 The Scale of the Threat

Mule accounts are the circulatory system of financial fraud. Every cyber fraud—phishing, ransomware, investment scams, loan fraud—ultimately requires **money movement through seemingly legitimate bank accounts** controlled by criminal networks. In India alone, the I4C (Indian Cyber Crime Coordination Centre) reported over ₹10,319 crore lost to cyber fraud in 2023, with mule accounts enabling 87% of successful fund exfiltration.

A single mule network can involve **50–200 accounts across 5–10 banks**, activated in coordinated bursts lasting 4–72 hours before going dormant. The accounts are typically:
- Rented from financially vulnerable individuals (students, daily-wage workers)
- Opened using synthetic/stolen identities
- Dormant savings accounts suddenly activated for high-velocity transfers
- Business accounts with fabricated merchant profiles used for layering

### 1.2 Why Current Systems Fail

**Static Rule-Based Systems** deployed in most Indian banks today suffer from fundamental limitations:

| Failure Mode | Root Cause | Impact |
|---|---|---|
| High False Positives (>95%) | Rigid threshold rules (e.g., "flag if amount > ₹50K") trigger on legitimate salary transfers, EMI payments | Alert fatigue—investigators ignore 9 out of 10 alerts |
| Siloed Detection | Each bank sees only its own transactions; mule networks span multiple banks | Only 12% of mule chains are detected end-to-end |
| No Behavioral Context | Rules don't model what "normal" looks like for each customer | Cannot distinguish between a customer's first UPI payment and a mule's first layering transaction |
| Batch Processing Delays | Most TMS systems run batch analysis every 4–6 hours | Fraudsters complete mule chains in <2 hours; money is withdrawn before alerts fire |
| No Network Awareness | Systems analyze transactions individually, not relationally | Cannot detect coordinated fan-out/fan-in patterns across accounts |
| Rule Decay | Fixed rules don't adapt as fraud typologies evolve quarterly | New mule recruitment via social media (Telegram, Instagram) bypasses all existing rules |

### 1.3 The Imperative for Real-Time, AI-Driven Detection

RBI's Master Direction on Fraud Risk Management (2024) mandates banks to implement **real-time transaction monitoring with ML capabilities**. The UPI ecosystem processes 12+ billion transactions/month with a median completion time of <5 seconds—meaning detection must happen in **sub-second latency** to enable meaningful intervention (hold, step-up authentication, or block).

The solution must bridge three critical gaps:
1. **Velocity Gap**: Detection speed must match transaction speed
2. **Intelligence Gap**: Individual transaction analysis must evolve to network-level intelligence
3. **Collaboration Gap**: Cross-institutional fraud intelligence must flow in real-time while preserving data privacy

---

## 2. Core Idea of the Solution

### 2.1 AEGIS — Adaptive Enterprise Graph Intelligence System

AEGIS is a **multi-layered, graph-native fraud detection platform** that treats the financial ecosystem not as a stream of independent transactions, but as a **continuously evolving graph of entities, relationships, and behaviors**.

**Core Thesis**: Mule accounts are invisible when examined individually but become unmistakable when viewed as nodes in a graph. AEGIS makes the invisible visible.

### 2.2 Three-Pillar Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    PILLAR 1: PERCEPTION                         │
│   Real-time ingestion of transactions, alerts, regulatory       │
│   feeds — building the live financial graph                     │
├─────────────────────────────────────────────────────────────────┤
│                    PILLAR 2: COGNITION                          │
│   Hybrid AI engine: Graph Neural Networks + Temporal Models     │
│   + Behavioral Profiling + Rule Engine — multi-signal fusion    │
├─────────────────────────────────────────────────────────────────┤
│                    PILLAR 3: ACTION                             │
│   Risk scoring, alert prioritization, automated intervention,   │
│   explainable decisions, regulatory reporting                   │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 What Makes AEGIS Different

Unlike conventional fraud detection systems that ask **"Is this transaction suspicious?"**, AEGIS asks three fundamentally different questions:

1. **"Does this account behave like a mule?"** — Behavioral divergence scoring using temporal autoencoders
2. **"Is this account part of a suspicious network?"** — Graph neural network analysis of transaction topology
3. **"Does this pattern match an evolving fraud campaign?"** — Campaign-level detection using fraud embeddings and similarity search

This shift from transaction-level to entity-level and network-level analysis is what enables AEGIS to detect mule accounts **before** they are used for fraud, not after.

---

## 3. System Architecture

### 3.1 High-Level Architecture

```
                                    AEGIS ARCHITECTURE
                                    
    ┌──────────────────────────────────────────────────────────────────┐
    │                     DATA INGESTION LAYER                         │
    │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────────┐  │
    │  │Core Bank │  │UPI/IMPS/ │  │Fraud Mon.│  │ Govt Feeds     │  │
    │  │Systems   │  │NEFT/RTGS │  │Alerts    │  │ (I4C/CERT-IN)  │  │
    │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └───────┬────────┘  │
    │       │              │             │                │            │
    │       ▼              ▼             ▼                ▼            │
    │  ┌─────────────────────────────────────────────────────────┐     │
    │  │              Apache Kafka (Event Streaming)             │     │
    │  │   Topics: txn-raw | alerts-raw | regulatory-feeds      │     │
    │  └──────────────────────┬──────────────────────────────────┘     │
    └─────────────────────────┼────────────────────────────────────────┘
                              │
    ┌─────────────────────────▼────────────────────────────────────────┐
    │                   STREAM PROCESSING LAYER                        │
    │  ┌────────────────────────────────────────────────────────┐      │
    │  │              Apache Flink / Kafka Streams              │      │
    │  │  • Transaction enrichment & normalization              │      │
    │  │  • Velocity calculations (sliding windows)             │      │
    │  │  • Entity resolution & deduplication                   │      │
    │  │  • Feature extraction (real-time feature store)        │      │
    │  └──────────────────────┬─────────────────────────────────┘      │
    │                         │                                        │
    │  ┌──────────────────────▼─────────────────────────────────┐      │
    │  │              Redis (Feature Store + Cache)              │      │
    │  │  • Rolling behavioral profiles per account             │      │
    │  │  • Velocity counters (1min, 5min, 1hr, 24hr windows)   │      │
    │  │  • Peer group statistics                               │      │
    │  │  • Hot entity cache (recently flagged accounts)         │      │
    │  └──────────────────────┬─────────────────────────────────┘      │
    └─────────────────────────┼────────────────────────────────────────┘
                              │
    ┌─────────────────────────▼────────────────────────────────────────┐
    │                   AI/ML DETECTION LAYER                          │
    │                                                                  │
    │  ┌─────────────┐  ┌──────────────┐  ┌───────────────────┐       │
    │  │ Behavioral   │  │ Graph Neural  │  │ Temporal Sequence │       │
    │  │ Anomaly      │  │ Network       │  │ Analyzer          │       │
    │  │ Detector     │  │ (GNN)         │  │ (TCN/Transformer) │       │
    │  │              │  │              │  │                   │       │
    │  │ Per-account  │  │ Mule network │  │ Time-series       │       │
    │  │ deviation    │  │ topology     │  │ pattern mining    │       │
    │  │ scoring      │  │ detection    │  │                   │       │
    │  └──────┬───────┘  └──────┬───────┘  └────────┬──────────┘       │
    │         │                 │                    │                  │
    │         ▼                 ▼                    ▼                  │
    │  ┌─────────────────────────────────────────────────────────┐      │
    │  │              ENSEMBLE RISK SCORING ENGINE               │      │
    │  │  • Weighted fusion of all model outputs                │      │
    │  │  • Calibrated probability scores (0.0 — 1.0)           │      │
    │  │  • Confidence intervals & model agreement metrics      │      │
    │  └──────────────────────┬─────────────────────────────────┘      │
    └─────────────────────────┼────────────────────────────────────────┘
                              │
    ┌─────────────────────────▼────────────────────────────────────────┐
    │                   DECISION & ACTION LAYER                        │
    │  ┌──────────────┐  ┌───────────────┐  ┌─────────────────┐       │
    │  │ Rule Engine   │  │ Alert         │  │ Explainability  │       │
    │  │ (Drools/      │  │ Prioritizer   │  │ Engine          │       │
    │  │  Custom DSL)  │  │ & Case Mgmt   │  │ (SHAP + LLM)   │       │
    │  └──────┬────────┘  └──────┬────────┘  └────────┬────────┘       │
    │         │                  │                     │               │
    │         ▼                  ▼                     ▼               │
    │  ┌─────────────────────────────────────────────────────────┐      │
    │  │           AUTOMATED RESPONSE ORCHESTRATOR              │      │
    │  │  Score 0.0–0.3: Pass | 0.3–0.7: Step-up Auth |         │      │
    │  │  0.7–0.9: Hold + Review | 0.9–1.0: Block + Report     │      │
    │  └──────────────────────┬─────────────────────────────────┘      │
    └─────────────────────────┼────────────────────────────────────────┘
                              │
    ┌─────────────────────────▼────────────────────────────────────────┐
    │                   INTELLIGENCE & MONITORING LAYER                 │
    │  ┌──────────────┐  ┌───────────────┐  ┌─────────────────┐       │
    │  │ Fraud Graph   │  │ Regulatory    │  │ Ops Dashboard   │       │
    │  │ Visualizer    │  │ Compliance    │  │ (Real-time      │       │
    │  │ (Neo4j +      │  │ Reporter      │  │  Monitoring)    │       │
    │  │  D3.js)       │  │ (STR/SAR)     │  │                 │       │
    │  └──────────────┘  └───────────────┘  └─────────────────┘       │
    └──────────────────────────────────────────────────────────────────┘
```

### 3.2 Component Deep-Dive

#### 3.2.1 Transaction Ingestion Pipeline

The ingestion layer handles heterogeneous data sources with different formats, velocities, and reliability characteristics:

**Source Connectors:**
- **Core Banking System (CBS)**: CDC (Change Data Capture) via Debezium from Oracle/SQL Server → Kafka. Captures account opens, closures, KYC updates, balance changes.
- **Payment Rails**: Direct API integration with UPI Switch (NPCI), IMPS/NEFT/RTGS gateways. Each transaction produces a standardized event within 100ms.
- **Fraud Monitoring Alerts**: Webhook receivers for existing TMS (Actimize/Mantas) alerts, mapped to AEGIS entity schema.
- **Government Cyber Fraud Feeds**: REST API polling (every 60s) from I4C Citizen Financial Cyber Fraud Reporting and Management System (CFCFRMS), CERT-In advisories, and RBI fraud registry.

**Kafka Topic Design:**
```
txn-raw              → Raw transaction events (partitioned by account_id)
txn-enriched         → Enriched with customer profile + historical features
alerts-internal      → TMS/fraud monitoring system alerts
alerts-regulatory    → Government/regulatory feeds
entity-events        → KYC changes, account status changes
model-scores         → ML model output scores
actions-audit        → All automated actions for audit trail
```

**Why Kafka**: Kafka provides exactly-once semantics, replay capability for model retraining, and handles 500K+ events/second per cluster — essential for UPI-scale volumes.

#### 3.2.2 Real-Time Feature Engineering (Stream Processing)

Apache Flink jobs compute features in real-time with **exactly-once guarantees**:

**Velocity Features (Sliding Windows):**
- Transaction count/volume in 1min, 5min, 15min, 1hr, 6hr, 24hr, 7d windows
- Unique counterparty count per window
- Channel switching frequency (UPI → NEFT → ATM)
- Geographic velocity (distance between consecutive transaction locations / time delta)

**Behavioral Deviation Features:**
- Current transaction amount vs. 30-day rolling mean/std for this account
- Time-of-day deviation (transaction at 3AM when historical pattern is 9AM–6PM)
- Counterparty novelty score (% of counterparties never seen before)
- Round-amount ratio (mule transactions are disproportionately round numbers: ₹10,000, ₹25,000)

**Network Features (Computed Incrementally):**
- In-degree/out-degree of account in 24hr transaction graph
- Fan-out ratio (1 inbound → many outbound within 30min = layering signal)
- Funds-flow-through time (median time between credit and corresponding debit)
- Counterparty risk score aggregation (transacting with flagged accounts)

These features are written to **Redis** (for real-time model inference, <5ms lookup) and **Apache Hudi on S3** (for batch model training on historical data).

#### 3.2.3 Graph/Network Analysis Engine

This is the **core differentiator** of AEGIS. While competitors analyze transactions independently, AEGIS maintains a **live transaction graph** in Neo4j:

**Graph Schema:**
```
Nodes: Account, Customer, Device, IP, Merchant, Phone, Location
Edges: TRANSFERS_TO (amount, timestamp, channel),
       OWNS (customer→account),
       USES_DEVICE (account→device),
       LOGS_IN_FROM (account→IP),
       REGISTERED_WITH (account→phone)
```

**Graph Algorithms Running Continuously:**
1. **Community Detection (Louvain)**: Identifies clusters of accounts transacting primarily with each other — classic mule ring topology
2. **PageRank Variant**: "FraudRank" — propagates suspicion scores through the graph. If account A is confirmed fraud, accounts 1–2 hops away get elevated scores
3. **Temporal Motif Detection**: Identifies specific subgraph patterns that match known mule typologies:
   - **Fan-out**: 1 account → 5+ accounts within 1 hour
   - **Chain**: A→B→C→D→ATM withdrawal, each hop within 15 minutes
   - **Cycle**: A→B→C→A (circular layering)
   - **Funnel**: 5+ accounts → 1 account → cash withdrawal

#### 3.2.4 Risk Scoring Engine

The ensemble scoring engine fuses signals from all detection components:

```
Final_Score = w1 × Behavioral_Anomaly_Score
            + w2 × Graph_Network_Score  
            + w3 × Temporal_Pattern_Score
            + w4 × Rule_Engine_Score
            + w5 × Regulatory_Match_Score
            + w6 × Device_Intelligence_Score

where weights w1–w6 are learned via logistic regression on historical labeled data
```

**Score Calibration**: Raw model outputs are calibrated using Platt scaling to produce true probability estimates. A score of 0.85 means "85% probability this is a mule account" — not an arbitrary ranking.

**Confidence Layer**: Each score includes a confidence band based on model agreement. If all 6 components flag the account (high agreement), confidence is high. If only 1 component flags it, the alert is routed for human review with lower priority.

#### 3.2.5 Alert Prioritization & Case Management

Not all alerts are equal. AEGIS prioritizes alerts using a **multi-factor priority score**:

```
Priority = f(risk_score, amount_at_risk, network_size, time_sensitivity, regulatory_match)
```

- **Critical (P0)**: Risk >0.9 + active fund movement + regulatory match → Auto-block + immediate analyst notification
- **High (P1)**: Risk >0.7 + network involvement → Hold funds + queue for review within 15 minutes
- **Medium (P2)**: Risk >0.5 + behavioral anomaly → Step-up authentication + review within 2 hours
- **Low (P3)**: Risk >0.3 + single signal → Monitor + batch review

---

## 4. AI/ML Components

### 4.1 Component 1: Behavioral Anomaly Detector (Variational Autoencoder)

**Why VAE, not Isolation Forest**: Isolation Forest works on tabular features but cannot capture the sequential, temporal nature of account behavior. A VAE trained on sequences of transaction embeddings learns a latent "behavioral fingerprint" for each account. When new transactions deviate from this fingerprint, the reconstruction error spikes — indicating anomalous behavior.

**Architecture:**
```
Input: 90-day transaction sequence → Embedding (amount, time_delta, channel, 
       counterparty_category, location) → Encoder (2-layer LSTM, 128 units) 
       → Latent Space (32-dim) → Decoder (2-layer LSTM) → Reconstruction
       
Anomaly Score = Reconstruction Error (MSE) + KL Divergence from prior
```

**Training**: Trained on 6 months of legitimate transaction data per customer segment (salaried, business, student, senior citizen). Separate models per segment because "normal" behavior varies dramatically.

**Key Detection Capabilities:**
- Dormant account suddenly transacting (reconstruction error explodes because model has no behavioral baseline)
- Salary account suddenly receiving multiple small credits from unknown UPI IDs (behavioral shift from single employer credit)
- Business account with changed transaction velocity (10x increase in daily transactions)

### 4.2 Component 2: Graph Neural Network for Mule Network Detection

**Why GNN**: Traditional ML cannot capture relational/topological features. A GNN operates directly on the transaction graph, learning representations that encode both node features (account attributes) and structural position (how the account is connected).

**Architecture: GraphSAGE with Temporal Attention**
```
For each account node v:
  h_v^(0) = [account_features, behavioral_score, velocity_features]
  
  For each GNN layer k = 1..3:
    h_N(v)^(k) = ATTENTION_AGGREGATE({h_u^(k-1) : u ∈ N(v)}, edge_features)
    h_v^(k) = σ(W^(k) · CONCAT(h_v^(k-1), h_N(v)^(k)))
    
  mule_probability = σ(MLP(h_v^(3)))
```

**Temporal Attention**: Edge attention weights are modulated by recency — transactions from the last hour get higher attention than transactions from last week. This allows the GNN to focus on the **active** network topology.

**Training Data**: Semi-supervised — a small set of confirmed mule accounts (positive labels from SAR filings) + large set of unlabeled accounts. Uses label propagation + contrastive learning to generalize from limited labels.

**Key Detection Capabilities:**
- Identifies accounts that are structurally positioned as "intermediaries" in fund flow chains
- Detects coordinated activation of previously unrelated accounts (community formation in real-time)
- Propagates suspicion: if 3 of your counterparties are flagged, your score elevates even if your individual behavior seems normal

### 4.3 Component 3: Temporal Convolutional Network (TCN) for Sequence Analysis

**Why TCN over LSTM**: TCNs provide **parallelizable training**, stable gradients over long sequences, and flexible receptive fields via dilated convolutions. For transaction sequences spanning months, TCNs outperform LSTMs.

**Architecture:**
```
Input: Sequence of transaction feature vectors (last 500 transactions)
       Each vector: [amount_normalized, time_delta, channel_onehot, 
                     counterparty_risk, is_round_amount, geo_distance]

TCN Layers: 4 residual blocks with dilated causal convolutions
            Dilation factors: [1, 2, 4, 8] → receptive field of 15 transactions
            
Output: Per-transaction suspicion score + sequence-level mule probability
```

**Key Detection Capabilities:**
- **Rapid succession patterns**: Credit-then-debit within minutes (pass-through behavior)
- **Structuring detection**: Multiple transactions just below reporting thresholds (₹49,999 repeated)
- **Temporal clustering**: Transactions concentrated in narrow time windows vs. natural spread
- **Sequence similarity**: New account's transaction sequence matches known mule sequence templates (via DTW similarity in embedding space)

### 4.4 Component 4: Fraud Campaign Clustering (HDBSCAN + Embeddings)

**Purpose**: Group individual suspicious transactions/accounts into **coordinated fraud campaigns**. A single fraud campaign may involve 50–200 mule accounts operating in parallel.

**Method:**
1. Generate transaction-graph embeddings for each suspicious account using Node2Vec
2. Concatenate with temporal behavioral embeddings from the TCN
3. Apply HDBSCAN clustering in this embedding space
4. Each cluster represents a potential fraud campaign

**Why HDBSCAN**: Unlike K-Means, HDBSCAN doesn't require specifying cluster count, handles noise (legitimate flagged accounts), and discovers clusters of varying density — matching real-world fraud campaigns that vary in size.

### 4.5 Component 5: LLM-Assisted Fraud Explanation Engine

**Purpose**: Generate human-readable, analyst-friendly explanations for every alert. This is critical for:
- Analyst efficiency (reduce investigation time from 45min to 10min per case)
- Regulatory compliance (STR filings require narrative explanations)
- Audit trail (explainable decisions withstand regulatory scrutiny)

**Architecture:**
```
Inputs to LLM:
  1. SHAP feature importance values from each ML model
  2. Graph context (counterparty relationships, network structure)
  3. Temporal pattern description (auto-generated from TCN attention weights)
  4. Matching regulatory alerts (if any)
  5. Historical case similarity (retrieved from vector DB)

Prompt Template:
  "Given the following fraud detection signals for account {id}:
   - Behavioral anomaly: {shap_explanation}
   - Network analysis: {graph_context}  
   - Transaction patterns: {temporal_description}
   - Regulatory matches: {regulatory_context}
   
   Generate a concise investigation summary explaining:
   1. Why this account is flagged
   2. The most likely fraud typology
   3. Recommended investigation steps
   4. Risk assessment (with confidence level)"
```

**Model**: Fine-tuned Llama-3 8B (on-premise deployment for data privacy) or Gemini API with PII-stripped inputs.

### 4.6 Component 6: Adaptive Learning System

**Problem**: Fraud patterns evolve continuously. A model trained on last year's mule typologies will miss this quarter's new tactics.

**Solution — Continuous Learning Pipeline:**
1. **Feedback Loop**: Analyst dispositions (true positive/false positive) flow back as labels
2. **Online Learning**: Behavioral models update incrementally using online gradient descent (no full retraining required)
3. **Concept Drift Detection**: Monitor model performance metrics (precision, recall, score distributions) with statistical tests (Page-Hinkley, ADWIN). Alert when drift exceeds threshold.
4. **Champion-Challenger Framework**: New model versions are deployed as "challengers" scoring transactions in shadow mode. Promoted to "champion" only when they demonstrate improvement on a 2-week holdout.
5. **Fraud Typology Evolution Tracker**: Cluster new confirmed fraud cases and compare to known typology library. New clusters trigger automated alerts to the fraud intelligence team.
## 5. Rule-Based + AI Hybrid Detection

### 5.1 Why Hybrid, Not Pure AI

Pure ML systems suffer from three critical issues in production banking environments:

1. **Regulatory Non-Negotiables**: Certain rules are mandated by law (e.g., CTR filing for cash transactions >₹10 lakh). These cannot be probabilistic.
2. **Zero-Day Fraud**: When a new fraud typology emerges (e.g., first-time exploitation of a new UPI feature), there's no training data. Rules can be deployed in minutes; models take weeks.
3. **Explainability Floor**: Regulators require deterministic explanations for certain actions. "The model said so" is insufficient for blocking a customer's account.

### 5.2 Architecture of Hybrid Detection

```
Transaction Event
       │
       ▼
┌──────────────────┐     ┌──────────────────────────┐
│  RULE ENGINE     │     │  ML SCORING ENGINE        │
│  (Deterministic) │     │  (Probabilistic)          │
│                  │     │                            │
│  Layer 1: Hard   │     │  Behavioral Anomaly: 0.72 │
│  blocks (sanction│     │  Graph Network:      0.85 │
│  lists, frozen   │     │  Temporal Pattern:   0.68 │
│  accounts)       │     │  Campaign Match:     0.91 │
│                  │     │                            │
│  Layer 2: Reg.   │     │  Ensemble Score:     0.82 │
│  rules (CTR,     │     │                            │
│  structuring)    │     │                            │
│                  │     │                            │
│  Layer 3: Heur-  │     │                            │
│  istic rules     │     │                            │
│  (velocity, geo) │     │                            │
└────────┬─────────┘     └────────────┬───────────────┘
         │                            │
         ▼                            ▼
┌──────────────────────────────────────────────────────┐
│              DECISION FUSION ENGINE                   │
│                                                       │
│  Priority Logic:                                      │
│  1. Hard block rules → ALWAYS BLOCK (no override)     │
│  2. ML score > 0.9 + any rule trigger → AUTO-BLOCK    │
│  3. ML score > 0.7 + no rules → HOLD + REVIEW         │
│  4. ML score < 0.3 + rule trigger → REVIEW (likely FP)│
│  5. ML score < 0.3 + no rules → PASS                  │
│                                                       │
│  Key Insight: ML score REDUCES false positives from    │
│  rules. Rules ENSURE zero false negatives on           │
│  regulatory requirements.                              │
└──────────────────────────────────────────────────────┘
```

### 5.3 Dynamic Rule Management

Rules are not static. AEGIS includes a **Rule Lifecycle Manager**:

- **Rule Authoring**: Domain experts define rules via a low-code DSL (Domain Specific Language):
  ```
  RULE "rapid_fan_out"
  WHEN account.txn_count_1hr > 10
   AND account.unique_counterparties_1hr > 5
   AND account.avg_hold_time_minutes < 10
  THEN SET risk_signal = "fan_out_layering", severity = HIGH
  ```
- **Rule Backtesting**: Before deployment, every rule is backtested against 90 days of historical data. System reports projected alert volume, false positive rate, and overlap with existing rules.
- **Rule Performance Monitoring**: Production rules are continuously evaluated. Rules with >98% false positive rate are auto-flagged for review.
- **AI-Suggested Rules**: The system analyzes confirmed fraud cases not caught by existing rules and suggests new rule candidates to analysts.

---

## 6. Real-Time Data Pipeline

### 6.1 End-to-End Latency Budget

```
Event occurs → Kafka ingestion:       10ms
Kafka → Flink processing:             20ms
Feature computation + Redis write:     15ms
ML model inference (all models):       30ms
Graph query (Neo4j):                   25ms
Decision engine + action:             10ms
                                    ────────
Total end-to-end latency:           ~110ms
Target SLA:                          <200ms (P99)
```

### 6.2 Technology Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    INGESTION TIER                            │
│  Debezium CDC ──┐                                           │
│  REST Webhooks ─┼──→ Apache Kafka (3-broker cluster)        │
│  gRPC Streams ──┘    • 50 partitions per topic              │
│                      • 7-day retention (replay for retrain) │
│                      • Schema Registry (Avro)               │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    PROCESSING TIER                           │
│  Apache Flink (Kubernetes-deployed)                         │
│  • Stateful stream processing with RocksDB state backend    │
│  • Windowed aggregations (tumbling, sliding, session)       │
│  • Watermark-based event-time processing                    │
│  • Checkpoint interval: 30 seconds                          │
│                                                              │
│  Feature outputs → Redis Cluster (16 shards)                │
│  • Rolling window counters (HyperLogLog for unique counts)  │
│  • Sorted sets for recent transaction history               │
│  • TTL-based expiry (90 days for behavioral profiles)       │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    INFERENCE TIER                             │
│  FastAPI Microservices (Kubernetes, 3 replicas each)         │
│                                                              │
│  /api/v1/score/behavioral    → VAE model (ONNX Runtime)     │
│  /api/v1/score/temporal      → TCN model (ONNX Runtime)     │
│  /api/v1/score/graph         → GNN + Neo4j graph queries    │
│  /api/v1/score/ensemble      → Score fusion + decision      │
│  /api/v1/explain/{case_id}   → LLM explanation generation   │
│                                                              │
│  Model serving: ONNX Runtime (CPU) for <10ms inference      │
│  Graph queries: Neo4j Bolt protocol with connection pooling  │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    STORAGE TIER                               │
│  PostgreSQL: Case management, audit trails, user management  │
│  Neo4j: Live transaction graph (last 90 days)                │
│  Redis: Feature store, session cache, rate limiting          │
│  Milvus (Vector DB): Fraud pattern embeddings for similarity │
│  MinIO/S3: Model artifacts, training data, regulatory docs   │
│  Apache Hudi: Historical feature store (on S3, Parquet)      │
└─────────────────────────────────────────────────────────────┘
```

### 6.3 Regulatory Feed Integration

```python
# Pseudo-code: Government feed ingestion service
class RegulatoryFeedService:
    """
    Consumes feeds from I4C CFCFRMS, CERT-In, RBI Fraud Registry
    """
    
    def ingest_i4c_alerts(self):
        """Poll I4C API every 60 seconds for new cyber fraud tickets"""
        alerts = i4c_client.get_new_alerts(since=last_poll_timestamp)
        for alert in alerts:
            # Extract account numbers, UPI IDs, phone numbers
            entities = extract_entities(alert)
            # Update hot-list in Redis (O(1) lookup during transaction scoring)
            redis.sadd("regulatory:flagged_accounts", *entities.accounts)
            redis.sadd("regulatory:flagged_upi", *entities.upi_ids)
            # Publish to Kafka for graph update
            kafka.produce("alerts-regulatory", {
                "source": "I4C",
                "alert_id": alert.id,
                "entities": entities,
                "severity": alert.severity,
                "fraud_type": alert.category,
                "timestamp": datetime.utcnow()
            })
            # Trigger re-scoring of all accounts linked to flagged entities
            trigger_rescore(entities)
    
    def ingest_rbi_fraud_registry(self):
        """Daily sync of confirmed fraud accounts from RBI registry"""
        # Used as ground truth labels for model retraining
        # Also used to update graph with confirmed fraud nodes
        pass
```

---

## 7. Innovation Section

### 7.1 Multi-Agent Fraud Investigation System

**Concept**: Deploy specialized LLM-powered agents that collaborate to investigate complex fraud cases, mimicking a real fraud investigation team.

```
┌──────────────────────────────────────────────────────────┐
│            MULTI-AGENT INVESTIGATION FRAMEWORK            │
│                                                           │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ BEHAVIORAL   │  │ NETWORK      │  │ REGULATORY     │  │
│  │ ANALYST      │  │ ANALYST      │  │ COMPLIANCE     │  │
│  │ AGENT        │  │ AGENT        │  │ AGENT          │  │
│  │              │  │              │  │                │  │
│  │ Analyzes     │  │ Maps fund    │  │ Cross-refs     │  │
│  │ transaction  │  │ flow paths,  │  │ with govt      │  │
│  │ patterns,    │  │ identifies   │  │ databases,     │  │
│  │ lifestyle    │  │ network      │  │ checks         │  │
│  │ consistency  │  │ topology     │  │ sanctions,     │  │
│  │              │  │              │  │ PEP lists      │  │
│  └──────┬───────┘  └──────┬───────┘  └───────┬────────┘  │
│         │                 │                   │           │
│         ▼                 ▼                   ▼           │
│  ┌─────────────────────────────────────────────────────┐  │
│  │           LEAD INVESTIGATOR AGENT                   │  │
│  │  • Synthesizes findings from all specialist agents  │  │
│  │  • Identifies contradictions and gaps               │  │
│  │  • Generates unified investigation report           │  │
│  │  • Recommends action with confidence level          │  │
│  │  • Drafts STR narrative for regulatory filing       │  │
│  └─────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

Each agent has access to different tools (graph queries, transaction history APIs, regulatory databases) and reasons independently before the Lead Investigator synthesizes a final report. This reduces investigation time from **45 minutes to under 5 minutes** per case.

### 7.2 Synthetic Fraud Simulation Engine

**Problem**: Real fraud data is scarce (mule accounts represent <0.1% of all accounts) and heavily imbalanced.

**Solution**: A GAN-based fraud simulation engine that generates realistic synthetic mule transaction sequences:

```
Generator: Conditioned on fraud typology (fan-out, chain, cycle, funnel)
           Produces synthetic transaction sequences with realistic:
           - Amount distributions (learned from real mule cases)
           - Temporal patterns (inter-transaction intervals)
           - Network topology (counterparty relationships)

Discriminator: Trained to distinguish real mule sequences from synthetic ones.
               When the discriminator can't tell the difference, the generator
               is producing training-quality synthetic fraud data.

Application:
  1. Augment training data (10x increase in positive samples)
  2. Red-team testing: Run synthetic mule campaigns against AEGIS to find blind spots
  3. Analyst training: Generate realistic scenarios for fraud investigator training
```

### 7.3 Cross-Bank Fraud Intelligence Sharing (Privacy-Preserving)

**Challenge**: Mule networks span multiple banks, but banks cannot share customer data due to privacy regulations.

**Solution — Federated Fraud Intelligence Protocol:**
```
Bank A                    Central Intelligence Hub              Bank B
   │                              │                               │
   │  Hash(account_features)      │                               │
   │  + encrypted_risk_score  ──► │ ◄── Hash(account_features)    │
   │                              │      + encrypted_risk_score   │
   │                              │                               │
   │                         ┌────┴────┐                          │
   │                         │ Compute │                          │
   │                         │ on      │                          │
   │                         │ Encrypted│                          │
   │                         │ Data    │                          │
   │                         └────┬────┘                          │
   │                              │                               │
   │  ◄── cross_bank_risk_score ──┤──  cross_bank_risk_score ──►  │
   │      (no raw data exposed)   │    (no raw data exposed)      │
```

**Technical Implementation:**
- **Bloom Filter Sharing**: Banks share Bloom filters of flagged account hashes. Other banks can check if their accounts appear in the filter without revealing the actual flagged accounts.
- **Secure Multi-Party Computation (SMPC)**: Compute aggregate fraud statistics across banks without any single party seeing raw data.
- **Federated Learning**: Train a shared mule detection model across banks without centralizing data. Each bank trains on local data and shares only model gradient updates.

### 7.4 Dynamic Fraud Evolution Tracker

```
Timeline View:
═══════════════════════════════════════════════════════════════
2024 Q1 │ Typology A: UPI collect scams via mule chains      
        │ Pattern: Phishing → Collect request → Mule fan-out  
────────┼──────────────────────────────────────────────────────
2024 Q2 │ Typology B: Same + now using business accounts      
        │ Evolution: Added merchant mule layer for legitimacy  
────────┼──────────────────────────────────────────────────────
2024 Q3 │ Typology C: Crypto off-ramp via P2P + mules         
        │ New pattern: Crypto exchange → P2P transfer → Mule  
────────┼──────────────────────────────────────────────────────
2024 Q4 │ Typology D: AI-generated KYC for synthetic mules    
        │ Evolution: Deepfake video KYC for account opening    
═══════════════════════════════════════════════════════════════

AEGIS tracks this evolution using:
  1. Embedding drift in fraud cluster space
  2. New cluster emergence detection (HDBSCAN on rolling windows)
  3. Automated typology documentation (LLM-generated reports)
  4. Model performance segmented by typology (detect degradation early)
```

### 7.5 Fraud Relationship Graph Visualization

An interactive Neo4j + D3.js visualization layer for fraud analysts:
- **Entity-centric view**: Click on any account to see all connections, transaction flows, and risk scores
- **Campaign view**: Visualize entire mule networks as force-directed graphs with color-coded risk levels
- **Temporal playback**: Animate fund flows over time to see how money moves through the network
- **What-if analysis**: Analysts can hypothetically "block" a node and see how it disrupts the network

---

## 8. Implementation Plan

### 8.1 Phase 1: MVP (Hackathon Demo — 4 weeks)

| Week | Deliverable | Details |
|------|------------|---------|
| 1 | Data pipeline + synthetic data | Kafka setup, synthetic transaction generator, data schema design |
| 2 | Core ML models | Behavioral anomaly detector (VAE), basic rule engine, feature engineering |
| 3 | Graph analysis + scoring | Neo4j integration, community detection, ensemble risk scoring |
| 4 | Dashboard + demo | React dashboard, alert viewer, graph visualization, LLM explanations |

**MVP Scope:**
- Process synthetic transaction stream (10K transactions/minute)
- Detect 3 mule typologies (fan-out, chain, rapid pass-through)
- Generate explainable alerts with risk scores
- Interactive graph visualization of detected mule networks
- REST API for all scoring endpoints

### 8.2 Phase 2: Production-Ready (3–6 months)

- Kafka cluster scaling (multi-AZ, 500K events/sec)
- Model hardening (A/B testing framework, champion-challenger)
- Integration with real CBS systems via adapter layer
- Regulatory reporting automation (STR generation)
- SOC2/PCI-DSS compliance for infrastructure
- Load testing to 1M+ transactions/minute
- Alert fatigue reduction pipeline (auto-close low-risk alerts)

### 8.3 Phase 3: National Platform (6–12 months)

- Federated learning across participating banks
- Cross-bank Bloom filter intelligence sharing
- Integration with NPCI fraud registry, I4C CFCFRMS API
- Multi-tenant SaaS deployment for smaller banks
- Regulatory dashboard for RBI supervisory review

### 8.4 Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    KUBERNETES CLUSTER                         │
│                    (AWS EKS / On-Premise)                     │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Ingestion   │  │ Processing  │  │ Inference Services   │  │
│  │ Services    │  │ Services    │  │ (FastAPI pods)       │  │
│  │ (3 pods)    │  │ (Flink, 5   │  │ • behavioral (3)    │  │
│  │             │  │  task mgrs) │  │ • graph (3)          │  │
│  │             │  │             │  │ • temporal (3)       │  │
│  │             │  │             │  │ • ensemble (3)       │  │
│  │             │  │             │  │ • explainer (2)      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Kafka       │  │ Redis       │  │ Neo4j               │  │
│  │ (3 brokers) │  │ (16 shards) │  │ (3-node causal      │  │
│  │             │  │             │  │  cluster)            │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ PostgreSQL  │  │ Milvus      │  │ Monitoring           │  │
│  │ (Primary +  │  │ (Vector DB) │  │ (Prometheus+Grafana) │  │
│  │  Replica)   │  │             │  │                      │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. Datasets & Data Sources

### 9.1 Public Datasets for Training & Benchmarking

| Dataset | Source | Records | Use Case |
|---------|--------|---------|----------|
| IEEE-CIS Fraud Detection | Kaggle | 590K | Transaction-level fraud classification |
| PaySim | Kaggle (synthetic) | 6.3M | Mobile money fraud simulation |
| Elliptic Bitcoin | Kaggle | 203K | Graph-based fraud detection in financial networks |
| Bank Account Fraud (BAF) | NeurIPS 2022 | 1M | Realistic tabular fraud with temporal shifts |
| AML-World (HK) | IBM | 5M+ | Anti-money laundering with synthetic mule networks |
| Credit Card Fraud | Kaggle (ULB) | 284K | Anomaly detection baseline |

### 9.2 Synthetic Data Generation for Indian Banking Context

```python
class IndianBankingDataGenerator:
    """
    Generates realistic synthetic transaction data mimicking Indian banking patterns.
    """
    
    def generate_legitimate_account(self, segment):
        """
        Segments: salaried, business, student, senior_citizen, rural
        Each has distinct transaction patterns:
        - Salaried: Monthly credit (salary), EMI debits, UPI spending
        - Business: High-volume NEFT/RTGS, GST payments, vendor payments
        - Student: Small UPI P2P, education fee payments, low balance
        """
        pass
    
    def generate_mule_account(self, typology):
        """
        Typologies:
        - fan_out: 1 large credit → multiple small debits within 2 hours
        - chain: A→B→C→D, each hop within 15 minutes
        - dormant_activation: Account dormant 6+ months, sudden burst
        - round_tripping: A→B→C→A circular pattern
        - structuring: Multiple transactions just below ₹50,000
        """
        pass
    
    def generate_mule_network(self, size=50, typology="mixed"):
        """Generate a complete mule network with realistic topology"""
        pass
```

**Data Volume for MVP**: 10M synthetic transactions, 500 mule accounts, 20 mule networks.

---

## 10. Tech Stack

| Layer | Technology | Justification |
|-------|-----------|---------------|
| **Ingestion** | Apache Kafka 3.x | Industry standard for event streaming, exactly-once semantics |
| **CDC** | Debezium | Real-time change capture from banking databases |
| **Stream Processing** | Apache Flink | Stateful processing, event-time semantics, exactly-once |
| **Feature Store** | Redis Cluster + Apache Hudi | Redis for online (<5ms), Hudi for offline (training) |
| **ML Framework** | PyTorch + PyG (Graph) | Best ecosystem for GNN research + production |
| **Model Serving** | ONNX Runtime + FastAPI | <10ms inference, language-agnostic model format |
| **Graph Database** | Neo4j Enterprise | Native graph storage, Cypher query language, proven at scale |
| **Vector Database** | Milvus | Fraud pattern similarity search, ANN indexing |
| **Rule Engine** | Custom Python DSL + Drools | Flexible rule authoring with backtesting capability |
| **LLM** | Llama-3 8B (on-premise) / Gemini API | Explainability engine, investigation reports |
| **Backend API** | FastAPI (Python) | Async, high-performance, auto-documented APIs |
| **Frontend** | React + D3.js + Deck.gl | Interactive dashboards, graph visualization |
| **Database** | PostgreSQL 16 | Case management, audit trails, ACID compliance |
| **Orchestration** | Kubernetes (EKS/GKE) | Auto-scaling, rolling deployments, service mesh |
| **Monitoring** | Prometheus + Grafana + ELK | Metrics, alerting, log aggregation |
| **CI/CD** | GitHub Actions + ArgoCD | GitOps deployment, automated model validation |
| **Data Quality** | Great Expectations | Data validation for ingestion pipeline integrity |

---

## 11. Expected Impact

### 11.1 Quantified Outcomes (Based on Industry Benchmarks)

| Metric | Current State (Rule-Based) | With AEGIS | Improvement |
|--------|---------------------------|------------|-------------|
| **False Positive Rate** | 95–97% | 25–35% | ~70% reduction |
| **Mule Detection Rate** | 15–20% | 75–85% | ~4x improvement |
| **Detection Latency** | 4–6 hours (batch) | <200ms (real-time) | ~100,000x faster |
| **Investigation Time/Case** | 45 minutes | 8–12 minutes | ~75% reduction |
| **Network Detection** | 0% (no capability) | 70% of mule networks | Net new capability |
| **Alert Volume** | 10,000/day | 2,500/day (actionable) | 75% reduction |
| **Fund Recovery Rate** | 8–12% | 35–45% | ~3.5x improvement |

### 11.2 Regulatory Compliance

- **RBI Master Direction on Fraud Risk Management**: Full compliance with real-time monitoring mandate
- **PMLA (Prevention of Money Laundering Act)**: Automated STR generation with LLM-drafted narratives
- **I4C Integration**: Direct feed consumption and bidirectional intelligence sharing
- **Data Privacy**: On-premise deployment option, PII encryption at rest and in transit, RBAC access controls

### 11.3 Operational Benefits

- **Analyst Productivity**: 4x increase in cases handled per analyst per day
- **Cost Reduction**: ₹15–20 crore annual savings in fraud losses for a mid-size bank
- **Customer Experience**: 70% reduction in false blocks on legitimate transactions
- **Trust**: Transparent, explainable AI decisions build customer and regulator trust

---

## 12. Future Scope

### 12.1 National Fraud Intelligence Platform (NFIP)

AEGIS can evolve from a single-bank solution to a **national-scale fraud intelligence platform**:

```
┌─────────────────────────────────────────────────────────────┐
│              NATIONAL FRAUD INTELLIGENCE PLATFORM            │
│                                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Bank A   │ │ Bank B   │ │ Bank C   │ │ Bank D   │       │
│  │ (AEGIS   │ │ (AEGIS   │ │ (AEGIS   │ │ (AEGIS   │       │
│  │  Node)   │ │  Node)   │ │  Node)   │ │  Node)   │       │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘       │
│       │             │            │             │             │
│       ▼             ▼            ▼             ▼             │
│  ┌─────────────────────────────────────────────────────┐     │
│  │           FEDERATED INTELLIGENCE HUB               │     │
│  │  • Privacy-preserving fraud signal sharing          │     │
│  │  • Cross-bank mule network detection               │     │
│  │  • National fraud typology tracking                 │     │
│  │  • Federated model training (no data sharing)       │     │
│  │  • Real-time cross-bank fund freeze coordination    │     │
│  └─────────────────────────────────────────────────────┘     │
│                          │                                    │
│                          ▼                                    │
│  ┌─────────────────────────────────────────────────────┐     │
│  │              REGULATORY LAYER                       │     │
│  │  • RBI supervisory dashboard                        │     │
│  │  • I4C bidirectional intelligence exchange          │     │
│  │  • Automated SAR/STR filing across banks            │     │
│  │  • National fraud trend analytics                   │     │
│  └─────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

### 12.2 Advanced Capabilities Roadmap

| Timeline | Capability | Description |
|----------|-----------|-------------|
| 6 months | **Voice Biometric Mule Detection** | Detect mule accounts opened via call centers using voice pattern analysis |
| 9 months | **Deepfake KYC Detection** | Identify synthetic identities used for mule account opening via video KYC |
| 12 months | **Cross-Border Intelligence** | Extend to SWIFT/correspondent banking for international mule networks |
| 18 months | **Predictive Mule Identification** | Predict accounts likely to become mules BEFORE they are recruited |
| 24 months | **Autonomous Investigation** | Fully autonomous AI investigation with human-in-the-loop for final decisions |

### 12.3 Open-Source Contribution

AEGIS components can be open-sourced to strengthen the entire banking ecosystem:
- **Transaction graph schema standard** — Common graph model for financial networks
- **Synthetic fraud data generator** — Enable smaller banks to build ML capabilities
- **Federated fraud intelligence protocol** — Standardize cross-bank intelligence sharing
- **Fraud typology taxonomy** — Living classification of Indian banking fraud patterns

---

## Appendix: Key API Endpoints

```
POST   /api/v1/transactions/score          → Score a single transaction
POST   /api/v1/accounts/risk-profile       → Get account risk profile
GET    /api/v1/accounts/{id}/graph          → Get account network graph
GET    /api/v1/alerts?priority=P0&status=open → List alerts with filters
POST   /api/v1/alerts/{id}/investigate      → Trigger multi-agent investigation
GET    /api/v1/campaigns                    → List detected fraud campaigns
POST   /api/v1/rules/validate              → Backtest a rule before deployment
GET    /api/v1/analytics/dashboard          → Dashboard metrics
POST   /api/v1/regulatory/submit-str        → Submit Suspicious Transaction Report
GET    /api/v1/models/performance           → Model performance metrics
```

---

*AEGIS: Making mule networks visible. Making fraud detection real-time. Making financial systems trustworthy.*
