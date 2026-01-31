# Backtesting Engine - Professional Architecture

## Overview

This module provides **institutional-grade backtesting** with bias prevention, Monte Carlo simulation, and pluggable strategy framework.

**Grade:** A+ Professional
**Status:** Production Ready

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│              PROFESSIONAL BACKTEST PIPELINE              │
└─────────────────────────────────────────────────────────┘

1. DATA LAYER (Bias Prevention)
   ├── data_access.py
   │   ├── EventDataAccess - Loads events from input DB
   │   ├── get_past_prices() - Only shows historical data
   │   └── get_execution_price() - Simulates latency
   │
   └── Physical DB Separation
       ├── hedgemony.db (INPUT) - Bot can see
       └── hedgemony_validation.db (QA) - Bot cannot see ✓

2. STRATEGY LAYER (Decision Making)
   ├── strategy.py
   │   ├── EventStrategy (abstract base)
   │   ├── VerbatimSentimentStrategy (keyword analysis)
   │   └── SimpleEventStrategy (baseline)
   │
   └── Custom Strategies (user-defined)

3. EXECUTION LAYER (Simulation)
   ├── hardcore_engine.py
   │   ├── Monte Carlo (30-50 runs per event)
   │   ├── Synthetic tick generation
   │   ├── Dynamic slippage modeling
   │   ├── Fixed risk sizing (1-2% based on impact)
   │   └── Trailing stops (CHAOS BRACKET)
   │
   └── engine.py (DEPRECATED - simple simulation)

4. ANALYTICS LAYER (Performance)
   └── metrics.py
       ├── Win rate, Sharpe ratio
       ├── Max drawdown
       └── Trade-by-trade analysis
```

---

## Core Components

### 1. `data_access.py` - Bias-Free Data Loading

**Purpose:** Prevent look-ahead bias through physical database separation

**Key Features:**
- ✅ Only connects to `hedgemony.db` (input database)
- ✅ Security check prevents validation DB access
- ✅ `get_past_prices()` - Filters to show only historical data
- ✅ `get_execution_price()` - Simulates realistic latency

**Example:**
```python
from src.backtest import EventDataAccess

data_access = EventDataAccess()

# Load all events chronologically
events = data_access.load_all_events()

for event in events:
    # Get prices BEFORE event (what trader would have seen)
    past_prices = data_access.get_past_prices(event, lookback_seconds=300)

    # Strategy analyzes past data only
    signal = strategy.analyze_event(event, past_prices)

    # Get execution price AFTER event (simulates latency)
    entry_price = data_access.get_execution_price(event, delay_seconds=0)
```

**Why This Matters:**
- Prevents AI from "seeing the future" (no validation metrics during backtesting)
- Physical DB separation = impossible to cheat
- Realistic simulation of what trader sees at decision time

---

### 2. `strategy.py` - Strategy Framework

**Purpose:** Clean OOP framework for pluggable trading strategies

**Base Classes:**

#### `EventStrategy` (Modern - Event-Driven)
```python
class EventStrategy(ABC):
    @abstractmethod
    def analyze_event(
        self,
        event: Event,          # Verbatim event data
        past_prices: pd.DataFrame,  # Historical prices only
        symbol: str = 'SOL-USD'
    ) -> Optional[Signal]:
        """Analyze event and return trading signal."""
        pass
```

#### `Strategy` (Legacy - Candle-Based)
```python
class Strategy(ABC):
    @abstractmethod
    def on_candle(
        self,
        candle: dict,
        sentiment: Optional[dict] = None
    ) -> Optional[Signal]:
        """Process price candle and generate signal."""
        pass
```

**Built-in Strategies:**

1. **VerbatimSentimentStrategy** (Production)
   - Analyzes event title + description for keywords
   - Positive: approve, victory, win, success
   - Negative: reject, fraud, hack, crash, lawsuit
   - Source credibility weighting (Bloomberg=1.0, Twitter=0.7)

2. **SimpleEventStrategy** (Baseline)
   - Trades every event in same direction
   - Useful for benchmarking ("buy everything" vs smart strategy)

3. **SentimentStrategy** (Legacy - Deprecated)
   - Old candle-based approach

4. **MomentumStrategy** (Legacy - Deprecated)
   - Simple price momentum

---

### 3. `hardcore_engine.py` - Monte Carlo Simulation

**Purpose:** Institutional-grade backtesting with advanced features

**Features:**
- **Monte Carlo Simulation:** Runs 30-50 iterations per event with randomized parameters
- **Synthetic Tick Generation:** Brownian Bridge interpolation for intra-candle precision
- **Dynamic Slippage:** Volatility-adjusted execution costs
- **Fixed Risk Sizing:** 1%, 1.5%, or 2% based on impact score (7-10)
- **Drawdown Protection:** Reduces risk by 50% when in 5%+ drawdown
- **Trailing Stops (CHAOS BRACKET):**
  - Below 1.5% profit: Fixed stop
  - 1.5-3% profit: Breakeven stop
  - 3-6% profit: Trail 1% behind peak
  - Above 6% profit: Trail 0.5% behind peak

**Current Status:** ⚠️ Standalone implementation (future: integrate with Strategy framework)

**Example:**
```python
from src.backtest.hardcore_engine import StrategyTester

bt = StrategyTester()
bt.run_monte_carlo(runs=30)  # 30 simulations per event
```

---

### 4. `metrics.py` - Performance Analytics

**Purpose:** Professional performance metrics calculation

**Metrics Calculated:**
- Total P&L (dollars & percentage)
- Win rate (%)
- Sharpe ratio (annualized)
- Max drawdown (dollars & percentage)
- Best/worst/average trade
- Winning vs losing trades

**Example:**
```python
from src.backtest import calculate_metrics, format_metrics

metrics = calculate_metrics(
    trades=trade_list,
    initial_balance=100000.0
)

print(format_metrics(metrics))  # Pretty formatted output
```

---

## Usage Guide

### Quick Start - Event-Driven Backtest

```bash
# Run with verbatim sentiment strategy
python scripts/backtest/run_event_backtest.py --strategy verbatim_sentiment

# Custom parameters
python scripts/backtest/run_event_backtest.py \
  --strategy verbatim_sentiment \
  --confidence-threshold 0.75 \
  --execution-delay 0 \
  --exit-delay 300 \
  --initial-balance 100000
```

### Advanced - Monte Carlo Simulation

```bash
# Full Monte Carlo backtest (30 runs per event)
python src/backtest/hardcore_engine.py
```

### Programmatic Usage

```python
from src.backtest import (
    EventDataAccess,
    VerbatimSentimentStrategy,
    calculate_metrics
)

# 1. Load events
data_access = EventDataAccess()
events = data_access.load_all_events()

# 2. Initialize strategy
strategy = VerbatimSentimentStrategy({
    'confidence_threshold': 0.7,
    'position_size_pct': 0.1
})

# 3. Simulate trades
trades = []
for event in events:
    past_prices = data_access.get_past_prices(event)
    signal = strategy.analyze_event(event, past_prices)

    if signal:
        entry = data_access.get_execution_price(event, delay_seconds=0)
        exit = data_access.get_execution_price(event, delay_seconds=300)
        # ... record trade ...

# 4. Analyze performance
metrics = calculate_metrics(trades, initial_balance=100000.0)
```

---

## Creating Custom Strategies

### Step 1: Inherit from EventStrategy

```python
from src.backtest.strategy import EventStrategy, Signal
import pandas as pd

class MyCustomStrategy(EventStrategy):
    def __init__(self, config: dict = None):
        super().__init__(config)
        self.threshold = self.config.get('threshold', 0.8)

    def analyze_event(
        self,
        event,
        past_prices: pd.DataFrame,
        symbol: str = 'SOL-USD'
    ) -> Optional[Signal]:
        """Your custom logic here."""

        # Analyze event text
        text = f"{event.title} {event.description}".lower()

        # Your analysis logic...
        if "bullish_keyword" in text:
            return Signal(
                timestamp=event.timestamp,
                symbol=symbol,
                side='buy',
                confidence=0.85,
                reason="Custom logic detected bullish signal"
            )

        return None  # No trade

    def reset(self):
        """Reset strategy state between backtest runs."""
        pass
```

### Step 2: Test Your Strategy

```python
from scripts.backtest.run_event_backtest import run_event_backtest

result = run_event_backtest(
    strategy_class=MyCustomStrategy,
    strategy_config={'threshold': 0.8},
    initial_balance=100000.0
)
```

---

## Bias Prevention (Critical)

### The Problem: Look-Ahead Bias

Traditional backtests often have "future knowledge" leaking into decisions:
- ❌ AI sees move_5s (future price movement) when deciding to trade
- ❌ Strategy accesses validation metrics (quality_level, tradeable)
- ❌ Perfect hindsight on optimal entry/exit times

**Result:** Unrealistic performance that fails in live trading

### Our Solution: Physical Database Separation

```
hedgemony.db (INPUT)              hedgemony_validation.db (QA)
├── master_events                 ├── validated_events
│   ├── title ✓                   │   ├── move_5s ❌
│   ├── description ✓             │   ├── move_30s ❌
│   ├── timestamp ✓               │   ├── tradeable ❌
│   ├── source ✓                  │   └── quality_level ❌
│   └── sol_price_data ✓          └── (Bot CANNOT access)
└── (Bot can read)
```

**Enforcement:**
1. `data_access.py` has security check - raises error if validation DB path detected
2. `get_past_prices()` filters price_data to show ONLY timestamps before event
3. Strategies receive `Event` object with ONLY input fields (no validation metrics)

**Verification:**
```python
from src.backtest.data_access import validate_no_validation_db_access

# Run at startup to ensure no validation DB leaks
validate_no_validation_db_access()
```

---

## File Reference

### Production Files (Use These)

| File | Purpose | Status |
|------|---------|--------|
| [data_access.py](data_access.py) | Bias-free event loading | ✅ Production |
| [strategy.py](strategy.py) | Strategy framework | ✅ Production |
| [metrics.py](metrics.py) | Performance analytics | ✅ Production |
| [hardcore_engine.py](hardcore_engine.py) | Monte Carlo simulation | ✅ Production |
| [__init__.py](__init__.py) | Module exports | ✅ Production |

### Legacy Files (Deprecated)

| File | Status | Alternative |
|------|--------|-------------|
| [engine.py](engine.py) | Deprecated | Use `hardcore_engine.py` |

### Scripts

| Script | Purpose | Status |
|--------|---------|--------|
| `scripts/backtest/run_event_backtest.py` | Event-driven demo | ✅ Active |
| `scripts/backtest/archive/*` | Old scripts | 🗑️ Archived |

---

## Future Enhancements

### Planned (Not Yet Implemented)

1. **Extract HardcoreEventStrategy**
   - Pull trading logic from `hardcore_engine.py` into Strategy class
   - Make hardcore_engine accept Strategy objects
   - Benefits: Swap strategies while keeping Monte Carlo features

2. **Portfolio-Level Backtesting**
   - Currently: One event at a time
   - Future: Multiple concurrent positions

3. **Live Trading Integration**
   - Use same Strategy classes for live trading
   - Seamless transition from backtest to production

4. **Walk-Forward Optimization**
   - Train on period 1, test on period 2
   - Prevent overfitting to single dataset

---

## Best Practices

### ✅ Do

- Use `EventDataAccess` for all data loading
- Call `get_past_prices()` to ensure no future data
- Test strategies on 2023-2026 data range
- Run Monte Carlo (30+ runs) for robust results
- Compare against `SimpleEventStrategy` baseline

### ❌ Don't

- Access `hedgemony_validation.db` directly
- Use future price data in strategy logic
- Hardcode strategy parameters without testing ranges
- Trust single backtest run (use Monte Carlo)
- Ignore slippage/latency in simulations

---

## Performance Benchmarks

**Target Metrics (SOL/USDT Event Trading):**
- Win Rate: >55%
- Sharpe Ratio: >1.0
- Max Drawdown: <15%
- Risk per Trade: 1-2%

**Baseline Strategy (Buy All Events):**
- Acts as sanity check
- Your strategy should beat this

---

## Support

**Documentation:**
- [BACKTEST_AUDIT.md](../../docs/BACKTEST_AUDIT.md) - Comprehensive audit
- [event_scraping/SKILL.md](../.agent/skills/event_scraping/SKILL.md) - Event data methodology

**Examples:**
- `scripts/backtest/run_event_backtest.py` - Reference implementation
- `src/backtest/strategy.py` - Strategy examples

**Questions:**
- Check audit for architecture decisions
- Review strategy.py for implementation patterns
