# HedgemonyBot System Architecture

**Last Updated:** 2026-01-31
**Status:** Production Backtest | Paper Trading In Development

---

## Overview

HedgemonyBot is an AI-powered event-driven algorithmic trading system that analyzes breaking crypto news in real-time, performs ensemble sentiment analysis via the **Three Brains Council**, and executes high-conviction trades with institutional-grade risk management.

**Core Philosophy:**
- Event-driven architecture (no look-ahead bias)
- Ensemble AI for high-confidence signals
- Fixed risk sizing based on event impact
- Physical database separation for bias prevention

---

## High-Level Architecture

```
News Event → Spike Detection → Event Discovery
                ↓
        master_events DB
                ↓
     Three Brains Council
    (Groq + FinBERT + DeBERTa)
                ↓
         2/3 Majority Vote
                ↓
        Trading Signal
                ↓
    Risk-Sized Execution
                ↓
         Exchange API
```

---

## Core Components

### 1. Event Discovery Layer

**Purpose:** Find high-quality market-moving events with precise timestamps

**Methodology:** **Spike-First Approach** (Critical!)

```
Step 1: Scan price data for volatility spikes (Z-score > 3.0σ)
Step 2: Search news sources at EXACT spike timestamp (±5 min window)
Step 3: Verify timestamp correlation (<60 seconds requirement)
Step 4: Extract verbatim text from tier-1 sources
Step 5: Add to master_events database
```

**Why Spike-First:**
- Prevents cherry-picking events that "worked"
- Ensures causation (news → price, not coincidence)
- Eliminates hindsight bias

**Key Files:**
- `.agent/skills/event_scraping/SKILL.md` - Complete methodology
- `TWITTER_SEARCH_PROTOCOL.md` - Twitter search for precise timestamps
- `scripts/spike_first_workflow.py` - Enforced workflow

**Data Sources:**
- **Tier 1:** Bloomberg, Reuters, CoinDesk, WSJ (official Twitter accounts)
- **Tier 2:** SEC.gov, court filings (official sources)
- **Twitter:** For precise timestamps (tweets have second precision)

### 2. Brain Layer - The Three Brains Council

**Purpose:** Ensemble sentiment analysis with voting mechanism for high-confidence signals

**The Three Agents:**

1. **Agent 1: Groq (The Reasoner)**
   - Model: Llama 3.1 70B via Groq API
   - Strengths: Contextual understanding, nuanced reasoning
   - Output: Sentiment + explanation
   - Weight: 1/3

2. **Agent 2: FinBERT (The Banker)**
   - Model: ProsusAI/finbert (fine-tuned BERT)
   - Strengths: Financial vocabulary, market-specific sentiment
   - Output: Positive/Negative/Neutral classification
   - Weight: 1/3

3. **Agent 3: DeBERTa (The Logician)**
   - Model: microsoft/deberta-v3-base-mnli
   - Strengths: Logical consistency, factual accuracy
   - Output: Entailment-based sentiment
   - Weight: 1/3

**Voting System:**
- **2/3 Majority Required:** At least 2 agents must agree
- **God Mode (3/3):** All three agree → Highest confidence (0.95+)
- **Split Vote:** No trade signal generated

**Output Format:**
```python
{
    "label": "positive",      # or "negative", "neutral"
    "score": 0.85,            # -1 to +1
    "confidence": 0.92,       # 0 to 1 (based on agreement)
    "reasoning": "SEC approval signals regulatory clarity..."
}
```

**Key Files:**
- `src/brain/sentiment.py` - Three Brains Council implementation
- `src/brain/llm_sentiment.py` - Groq integration
- `test_three_brains.py` - Voting system verification

### 3. Backtesting Layer - Event-Driven Simulation

**Purpose:** Validate strategies on historical data with ZERO look-ahead bias

**Architecture:**

```
1. DATA ACCESS LAYER (Bias Prevention)
   ├── EventDataAccess
   │   ├── Loads from hedgemony.db (INPUT ONLY)
   │   ├── Security check blocks hedgemony_validation.db access
   │   └── get_past_prices() filters to historical data only
   │
   └── Physical DB Separation
       ├── hedgemony.db (INPUT) - Bot can see
       └── hedgemony_validation.db (QA) - Bot CANNOT see

2. STRATEGY LAYER (Decision Making)
   ├── VerbatimSentimentStrategy (keyword analysis)
   ├── SimpleEventStrategy (baseline: buy/sell all)
   └── Custom strategies (user-defined)

3. EXECUTION LAYER (Monte Carlo Simulation)
   ├── HardcoreEngine (hardcore_engine.py)
   │   ├── Monte Carlo (30-50 runs per event)
   │   ├── Synthetic tick generation (Brownian Bridge)
   │   ├── Dynamic slippage (volatility-adjusted)
   │   ├── Fixed risk sizing (1-2% based on impact)
   │   └── Trailing stops (CHAOS BRACKET)
   │
   └── Simple backtest runner (run_event_backtest.py)

4. ANALYTICS LAYER (Performance Metrics)
   └── metrics.py - Win rate, Sharpe, drawdown
```

**Bias Prevention:**
- Physical DB separation (input vs validation)
- get_past_prices() filters to historical data only
- Strategies never see validation metrics
- Impossible to cheat (databases are separate files)

**Key Files:**
- `src/backtest/data_access.py` - Bias-free data loading
- `src/backtest/strategy.py` - Strategy framework
- `src/backtest/hardcore_engine.py` - Monte Carlo simulation
- `src/backtest/metrics.py` - Performance analytics

### 4. Trading Layer (In Development)

**Purpose:** Execute trades and manage positions

**Key Modules:**
- `src/trading/live_executor.py` - Execution engine
- `src/trading/exchange.py` - Abstract exchange interface
- `src/trading/binance.py` - Binance connector
- `src/trading/hyperliquid.py` - Hyperliquid connector

**Risk Management:**

```python
RISK_CONFIG = {
    'base_risk_pct': 0.01,    # 1.0% for impact 7-8
    'power_risk_pct': 0.015,  # 1.5% for impact 9
    'god_risk_pct': 0.02,     # 2.0% for impact 10
    'drawdown_limit': 0.05,   # Reduce risk if DD > 5%
}
```

### 5. Data Layer

**Database Schema:**

**hedgemony.db (INPUT - Bot can access):**
```sql
master_events:
  - title, description, timestamp, source
  - sol_price_data (1s candles, JSON)

price_history:
  - symbol, timestamp, OHLC, volume

trades:
  - timestamp, side, entry, exit, pnl
```

**hedgemony_validation.db (QA - Bot CANNOT access):**
```sql
validated_events:
  - move_5s, move_30s (future price moves) ❌
  - tradeable, impact_score (post-hoc) ❌
  - quality_level (QA metadata) ❌
```

### 6. Dashboard (Streamlit)

**Features:**
- **Live Trading Tab:** Real-time news sentiment
- **Backtesting Tab:** Event-driven backtests
- **Portfolio Tab:** Position tracking
- **Settings Tab:** Strategy configuration

**Key Files:**
- `src/dashboard/app.py` - Streamlit application

---

## Configuration

**Environment Variables (`.env`):**
```bash
GROQ_API_KEY=gsk_...                  # Groq LLM
BINANCE_API_KEY=...                   # Exchange APIs
TWITTER_ACCESS_TOKEN=...              # Twitter API
TELEGRAM_BOT_TOKEN=...                # Alerts
```

---

## Deployment Modes

### 1. Backtesting ✅ Production-Ready
- Historical event simulation
- Zero look-ahead bias
- Monte Carlo testing

### 2. Paper Trading 🚧 In Development
- Real-time signal generation
- Simulated execution

### 3. Live Trading 📋 Planned
- Real exchange execution
- Full risk management

---

## Key Design Decisions

1. **Event-Driven Architecture** - No look-ahead bias
2. **Physical Database Separation** - Impossible to cheat
3. **Ensemble AI (Three Brains)** - High-confidence signals
4. **Spike-First Discovery** - Prevents cherry-picking
5. **Fixed Risk Sizing** - Based on event impact (7-10)

---

## Performance Targets

- Win Rate: >55%
- Sharpe Ratio: >1.0
- Max Drawdown: <15%
- Risk per Trade: 1-2%

---

## Known Limitations

1. Manual event curation required
2. SQLite (migration to TimescaleDB planned)
3. Single asset focus (SOL/USDT)
4. Static slippage model

---

## Additional Resources

- [Backtest Audit](BACKTEST_AUDIT.md)
- [Database Separation](DATABASE_SEPARATION.md)
- [Backtesting Methodology](backtesting_methodology.md)
- [Event Scraping Skill](.agent/skills/event_scraping/SKILL.md)

---

**Last Updated:** 2026-01-31
