# 🦅 HedgemonyBot

**AI-Powered Event-Driven Crypto Trading System**

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![Status: Production Backtest](https://img.shields.io/badge/status-production%20backtest-green.svg)]()
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)]()

---

## What It Is

HedgemonyBot is a professional algorithmic trading system that:

- **Analyzes breaking crypto news in real-time** using ensemble AI sentiment analysis
- **Uses the Three Brains Council** (Groq LLM + FinBERT + DeBERTa) for high-confidence trading signals
- **Executes precision trades** with institutional-grade risk management (1-2% per trade)
- **Prevents look-ahead bias** through physical database separation
- **Validates strategies** with Monte Carlo backtesting (30-50 simulations per event)

Built for **event-driven trading** where milliseconds matter and bias-free backtesting is critical.

---

## Key Features

### ✅ Production-Ready

- **Event-Driven Architecture** - No future knowledge leakage, realistic backtesting
- **Three Brains Council** - Groq (reasoning) + FinBERT (finance) + DeBERTa (logic) voting system
- **Monte Carlo Backtesting** - 30-50 runs per event with dynamic slippage modeling
- **Physical Database Separation** - Input DB (hedgemony.db) vs Validation DB (hedgemony_validation.db)
- **Twitter Integration** - Precise timestamp correlation (<60s requirement)
- **Professional Risk Sizing** - 1%, 1.5%, or 2% based on event impact score (7-10)

### 🚧 In Development

- **Paper Trading** - Live simulation with real market data
- **Streamlit Dashboard** - Monitor trades, run backtests, view analytics

### 📋 Planned

- **Live Trading** - Binance and Hyperliquid connectors
- **Multi-Asset Support** - Beyond SOL/USDT
- **Advanced Order Types** - Limit orders, trailing stops, position scaling

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    NEWS EVENT DETECTED                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────────┐
         │   Three Brains Council      │
         │  ┌────────┬────────┬──────┐ │
         │  │ Groq   │FinBERT │DeBER │ │
         │  │ (LLM)  │(Finance)│(Logic)│ │
         │  └────┬───┴────┬───┴───┬──┘ │
         │       │        │       │    │
         │       └────────┴───────┘    │
         │      2/3 Majority Vote      │
         └──────────┬──────────────────┘
                    │
                    ▼
         ┌────────────────────────────┐
         │  Trading Signal Generated   │
         │  (if confidence > 0.75)     │
         └──────────┬─────────────────┘
                    │
                    ▼
         ┌────────────────────────────┐
         │   Risk-Sized Execution     │
         │   (1-2% based on impact)   │
         └────────────────────────────┘
```

**God Mode:** All three brains agree → Highest confidence → Maximum position size

---

## Quick Start

### Prerequisites

```bash
# Python 3.11+
python --version

# Install dependencies
pip install -r requirements.txt

# Download AI models
python -c "from transformers import AutoModel; AutoModel.from_pretrained('ProsusAI/finbert')"
python -c "from transformers import AutoModel; AutoModel.from_pretrained('microsoft/deberta-v3-base-mnli')"
```

### Environment Setup

```bash
# Copy example env
cp .env.example .env

# Add your API keys
GROQ_API_KEY=your_groq_key_here
BINANCE_API_KEY=your_binance_key
BINANCE_API_SECRET=your_binance_secret
```

### Run Your First Backtest

```bash
# Event-driven backtest with verbatim sentiment strategy
python scripts/backtest/run_event_backtest.py --strategy verbatim_sentiment

# With custom parameters
python scripts/backtest/run_event_backtest.py \
  --strategy verbatim_sentiment \
  --confidence-threshold 0.75 \
  --execution-delay 0 \
  --exit-delay 300 \
  --initial-balance 100000
```

### Launch Dashboard

```bash
# Start Streamlit dashboard
streamlit run src/dashboard/app.py

# Open browser to http://localhost:8501
# Navigate to Backtesting tab
```

---

## Documentation

### Getting Started
- [Architecture Overview](docs/architecture.md) - System design and components
- [Quick Start Checklist](QUICK_START_CHECKLIST.md) - Step-by-step setup guide

### Core Systems
- [Backtesting Methodology](docs/backtesting_methodology.md) - How bias-free backtesting works
- [Backtest Audit](docs/BACKTEST_AUDIT.md) - Professional setup verification
- [Database Separation](docs/DATABASE_SEPARATION.md) - Why we use two databases
- [Event Scraping Guide](.agent/skills/event_scraping/SKILL.md) - How to find and validate events

### Development
- [Roadmap](docs/ROADMAP.md) - Future enhancements
- [Known Issues](docs/known_issues.md) - Current limitations
- [Contributing Guidelines](docs/contributing.md) - How to contribute

### Module-Specific
- [Backtest Module](src/backtest/README.md) - Complete backtesting API reference

---

## Project Status

### ✅ Complete (Production-Ready)

**Backtesting Engine**
- Event-driven simulation with zero look-ahead bias
- Monte Carlo testing (30-50 runs per event)
- Dynamic slippage based on volatility
- Professional metrics (Sharpe ratio, max drawdown, win rate)

**Three Brains Council**
- Groq (Llama 3.1 70B) for contextual reasoning
- FinBERT for financial sentiment
- DeBERTa for logical consistency
- Voting system with "God Mode" (unanimous agreement)

**Event Data Pipeline**
- Spike-first methodology (find price spikes → search for news)
- Twitter integration for precise timestamps
- Tier-1 source verification (Bloomberg, Reuters, CoinDesk)
- Verbatim text extraction (no AI summaries)

**Database Infrastructure**
- Physical separation (input vs validation)
- Security checks prevent validation DB access during backtesting
- SQLite with plans for TimescaleDB migration

### 🚧 In Development

**Paper Trading**
- Live market data integration
- Real-time signal generation
- Position tracking without real money

**Dashboard**
- Streamlit interface for backtesting
- Event-driven strategy selection
- Results visualization

### 📋 Planned (Q1-Q2 2026)

**Live Trading**
- Binance connector
- Hyperliquid connector
- Risk management hooks
- Telegram alerts

**Advanced Features**
- Multi-asset portfolio
- Walk-forward optimization
- Strategy A/B testing
- Performance attribution

---

## How It Works

### 1. Event Discovery (Spike-First)

```
Price Spike Detected → Search News at Exact Time → Verify Timestamp (<60s) → Add to master_events
```

**Critical:** We search for news AFTER finding price spikes, not the other way around. This prevents cherry-picking events that happened to work.

### 2. Sentiment Analysis (Three Brains)

```python
# Each brain votes independently
groq_vote = "positive"      # Contextual reasoning
finbert_vote = "positive"   # Financial sentiment
deberta_vote = "positive"   # Logical consistency

# 2/3 majority required
if votes.count("positive") >= 2:
    signal = "BUY"
    confidence = 0.92  # All three agree = God Mode
```

### 3. Risk-Sized Execution

```python
# Impact score determines risk allocation
if impact == 10:  # God-tier event
    risk_pct = 0.02  # 2.0%
elif impact == 9:  # Power event
    risk_pct = 0.015  # 1.5%
else:  # impact 7-8
    risk_pct = 0.01  # 1.0%

# Position size = Risk / Stop Distance
position_size = (equity * risk_pct) / stop_distance
```

### 4. Bias-Free Backtesting

```
master_events (input DB)     validated_events (QA DB)
├── title ✓                  ├── move_5s ❌
├── timestamp ✓              ├── move_30s ❌
├── source ✓                 ├── tradeable ❌
└── price_data ✓             └── quality_level ❌
    (filtered to past only)      (bot CANNOT access)
```

**Strategy sees ONLY:**
- Event title and description (verbatim text)
- Timestamp
- Price data BEFORE the event

**Strategy NEVER sees:**
- Future price movements
- Validation metrics (quality scores, tradeable flags)
- Post-hoc analysis

This physical separation makes it **impossible to cheat**.

---

## Performance Benchmarks

**Target Metrics (SOL/USDT Event Trading):**
- Win Rate: >55%
- Sharpe Ratio: >1.0
- Max Drawdown: <15%
- Risk per Trade: 1-2%

**Baseline (Buy All Events):**
- Acts as sanity check
- Your strategy should beat this

**Note:** Past performance does not guarantee future results. Crypto markets are highly volatile.

---

## Technology Stack

**Core:**
- Python 3.11+
- SQLite (migration to TimescaleDB planned)
- Asyncio for concurrent operations

**AI/ML:**
- Groq API (Llama 3.1 70B)
- HuggingFace Transformers (FinBERT, DeBERTa)
- PyTorch

**Data:**
- Binance API (price data)
- Hyperliquid API (price data)
- Twitter API (event timestamps)

**Visualization:**
- Streamlit (dashboard)
- Plotly (charts)

---

## Security & Safety

### Bias Prevention
- Physical database separation (input vs validation)
- Security checks in code
- get_past_prices() filters to historical data only
- Impossible to access validation metrics during backtesting

### API Key Safety
- Never commit .env files
- Use environment variables
- API keys stored locally only

### Risk Management
- Fixed risk sizing (1-2% per trade)
- Drawdown cutoff (reduce risk by 50% at 5% drawdown)
- Position limits
- Stop losses on all trades

---

## Contributing

Contributions welcome! Please read [contributing guidelines](docs/contributing.md) first.

**Areas needing help:**
- Event data curation (finding high-quality events)
- Strategy development (new trading logic)
- Exchange connectors (additional platforms)
- Testing (more coverage needed)

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Credits

**Built by:** [Your Name/Team]

**Powered by:**
- [Groq](https://groq.com) - Fast LLM inference
- [HuggingFace](https://huggingface.co) - Transformer models
- [Binance](https://binance.com) - Price data
- [Hyperliquid](https://hyperliquid.xyz) - DEX data

---

## Disclaimer

**This software is for educational and research purposes only.**

- Cryptocurrency trading involves substantial risk of loss
- Past performance does not indicate future results
- Never trade with money you cannot afford to lose
- This is not financial advice
- Always do your own research (DYOR)

**Use at your own risk.** The authors are not responsible for any financial losses incurred.

---

## Contact & Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/hedgemonybot/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/hedgemonybot/discussions)
- **Email:** your.email@example.com

---

**Built with ❤️ for the crypto trading community**
