# Backtesting Engine - Bias-Free Historical Performance Testing

**Last Updated:** 2026-01-31
**Status:** Production-ready architecture
**Purpose:** Test trading strategies against historical events WITHOUT look-ahead bias

---

## Overview

This skill documents the methodology for backtesting trading strategies using the verified event dataset from the event_scraping skill. The architecture is designed with **one critical goal**: ensure the AI NEVER sees future data during decision-making.

### The Core Problem We Solve

**Look-Ahead Bias** = When your backtest accidentally uses information that wouldn't have been available at decision time.

**Examples of bias:**
- ❌ AI sees `tradeable=TRUE` field and uses it to decide whether to trade
- ❌ AI sees `move_5m=+3.2%` and decides to go long
- ❌ AI sees `impact_score=5` and sizes position larger
- ❌ Strategy uses tomorrow's prices to validate today's entry

**Our solution:**
- ✅ Physical database separation (bot CANNOT access validation DB)
- ✅ AI sees ONLY verbatim event text (what traders actually saw)
- ✅ Price data filtered to show ONLY past prices
- ✅ No pre-calculated metrics in decision-making code

---

## Architecture

### File Structure

```
.agent/skills/backtesting/
├── SKILL.md                    # This file - methodology documentation
└── templates/                  # Strategy templates (future)

src/backtest/
├── __init__.py                 # Module exports
├── data_access.py              # ONLY reads hedgemony.db (input data)
├── engine.py                   # Core backtest loop
├── strategy.py                 # Trading decision logic
├── metrics.py                  # Performance calculations
└── report.py                   # Results visualization

scripts/backtest/
└── run_backtest.py             # Entry point CLI script
```

### Separation of Concerns

**1. Data Access Layer (`data_access.py`)**
- **Purpose:** Provide clean, bias-free event data
- **Reads:** `data/hedgemony.db` (input database ONLY)
- **Never reads:** `data/hedgemony_validation.db` (forbidden)
- **Returns:** Event objects with ONLY input fields (title, description, timestamp, source, category, price_data)

**2. Strategy Layer (`strategy.py`)**
- **Purpose:** Make trading decisions based on event data
- **Receives:** Verbatim event text + past price data ONLY
- **Returns:** Trading signal (BUY/SELL/HOLD) with confidence and sizing
- **NO ACCESS TO:** Future prices, validation metrics, impact scores

**3. Engine Layer (`engine.py`)**
- **Purpose:** Orchestrate the backtest simulation
- **Loads:** Events chronologically from data_access
- **Feeds:** Events to strategy one-by-one (simulating real-time)
- **Executes:** Trades based on strategy signals
- **Tracks:** Portfolio state, positions, P&L

**4. Metrics Layer (`metrics.py`)**
- **Purpose:** Calculate performance statistics
- **Computes:** Total P&L, win rate, Sharpe ratio, max drawdown, etc.
- **Post-hoc analysis:** Can optionally JOIN with validation DB AFTER backtest completes
- **Use case:** "Which event types did we trade well vs poorly?"

**5. Report Layer (`report.py`)**
- **Purpose:** Visualize results
- **Outputs:** Trade log, equity curve, performance summary
- **Optional:** Correlation analysis between strategy and validation metrics

---

## How It Works

### Backtest Flow (Step-by-Step)

```
1. Load Configuration
   ├─ Date range (e.g., 2023-01-01 to 2024-12-31)
   ├─ Symbol (e.g., SOL-USD)
   ├─ Initial balance (e.g., $100,000)
   └─ Strategy parameters (e.g., confidence_threshold=0.75)

2. Initialize Engine
   ├─ Create portfolio (starting balance)
   ├─ Load strategy
   └─ Connect to data_access (hedgemony.db ONLY)

3. Load Events (Chronological Order)
   ├─ Query: SELECT * FROM master_events WHERE timestamp BETWEEN ? AND ?
   ├─ Order by timestamp ASC (oldest first)
   └─ Returns: Clean event objects (no validation metadata)

4. Simulate Trading (Event Loop)
   For each event in chronological order:

   a) Filter Price Data to Past Only
      ├─ Get event timestamp
      ├─ Load price_data from event
      └─ Keep ONLY candles BEFORE event timestamp

   b) Feed to Strategy
      ├─ Pass: title, description, source, past_prices
      ├─ Strategy analyzes verbatim text
      └─ Strategy returns: signal (BUY/SELL/HOLD), confidence, size

   c) Execute Trade (if signal != HOLD)
      ├─ Get execution price (first candle AFTER event timestamp)
      ├─ Calculate position size (balance * size * confidence)
      ├─ Record trade: entry_time, entry_price, side, quantity
      └─ Update portfolio state

   d) Exit Management
      ├─ Check exit conditions (time-based, stop-loss, take-profit)
      ├─ Execute exit if triggered
      ├─ Calculate P&L
      └─ Update portfolio state

5. Calculate Metrics
   ├─ Total P&L ($ and %)
   ├─ Win rate (winning_trades / total_trades)
   ├─ Average win vs average loss
   ├─ Max drawdown
   ├─ Sharpe ratio
   └─ Trade distribution by event type

6. Generate Report
   ├─ Print summary to console
   ├─ Export trade log to CSV
   ├─ (Optional) Plot equity curve
   └─ (Optional) Correlation analysis with validation metrics
```

### Critical Implementation Details

**Price Data Filtering (Anti-Cheat Mechanism):**
```python
# ✅ CORRECT - Only show past prices
def get_past_prices(event_timestamp, price_data_json):
    """Return ONLY price candles before the event timestamp."""
    df = pd.DataFrame(json.loads(price_data_json))
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # CRITICAL: Filter to BEFORE event only
    past_df = df[df['timestamp'] < event_timestamp]
    return past_df

# ❌ WRONG - Shows future prices (cheating!)
def get_all_prices(price_data_json):
    return pd.DataFrame(json.loads(price_data_json))
```

**Execution Realism:**
```python
# ✅ CORRECT - Use first candle AFTER event (realistic slippage)
def get_execution_price(event_timestamp, price_data_json):
    """Get the first available price AFTER the event for execution."""
    df = pd.DataFrame(json.loads(price_data_json))
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # First candle after event
    future_df = df[df['timestamp'] >= event_timestamp]
    if len(future_df) > 0:
        return future_df.iloc[0]['close']  # Use close price
    return None

# ❌ WRONG - Uses event-time price (assumes instant execution)
def get_event_price(event_timestamp, price_data_json):
    df = pd.DataFrame(json.loads(price_data_json))
    return df[df['timestamp'] == event_timestamp]['close'].values[0]
```

---

## Strategy Development

### Base Strategy Interface

All strategies must implement:

```python
class BaseStrategy:
    def __init__(self, params: dict):
        """Initialize strategy with parameters."""
        self.params = params

    def analyze_event(self, event: Event, past_prices: pd.DataFrame) -> Signal:
        """
        Analyze event and return trading signal.

        Args:
            event: Event object with ONLY input fields (title, description, etc.)
            past_prices: Price data BEFORE event timestamp

        Returns:
            Signal object with:
                - action: "BUY" | "SELL" | "HOLD"
                - confidence: 0.0 to 1.0
                - size_pct: % of portfolio to risk (0.0 to 1.0)
                - reason: Human-readable explanation
        """
        raise NotImplementedError
```

### Example: Sentiment Strategy

```python
class SentimentStrategy(BaseStrategy):
    """
    Analyzes verbatim event text to determine sentiment and make trading decisions.

    Uses AI to analyze:
    - Emotional tone of title/description
    - Magnitude of news (regulatory vs minor announcement)
    - Source credibility (Bloomberg > random tweet)
    - Keyword signals (words like "approve", "reject", "fraud", etc.)
    """

    def analyze_event(self, event: Event, past_prices: pd.DataFrame) -> Signal:
        # 1. Analyze verbatim text (what traders actually saw)
        sentiment_score = self._analyze_text(event.title, event.description)

        # 2. Check source credibility
        source_weight = self._get_source_weight(event.source)

        # 3. Compute confidence
        confidence = abs(sentiment_score) * source_weight

        # 4. Determine action
        if confidence < self.params['confidence_threshold']:
            return Signal(action="HOLD", confidence=0, size_pct=0, reason="Low confidence")

        action = "BUY" if sentiment_score > 0 else "SELL"
        size_pct = self.params['position_size_pct']

        return Signal(
            action=action,
            confidence=confidence,
            size_pct=size_pct,
            reason=f"Sentiment: {sentiment_score:.2f}, Source: {event.source}"
        )

    def _analyze_text(self, title: str, description: str) -> float:
        """
        Analyze verbatim text to compute sentiment score.

        Returns: -1.0 (very negative) to +1.0 (very positive)
        """
        # Implementation: Could use AI model, keyword matching, etc.
        # CRITICAL: Only uses the verbatim text, no external data
        pass
```

---

## Database Access Rules

### ✅ ALLOWED (Input Database)

```python
import sqlite3

# Connect to input database
conn = sqlite3.connect('data/hedgemony.db')

# Query events
events = conn.execute("""
    SELECT id, title, description, timestamp, source, source_url, category, sol_price_data
    FROM master_events
    WHERE timestamp BETWEEN ? AND ?
    ORDER BY timestamp ASC
""", (start_date, end_date)).fetchall()

# This is SAFE - AI sees only what traders saw
```

### ❌ FORBIDDEN (Validation Database)

```python
# ❌ NEVER DO THIS IN BACKTEST CODE
validation_conn = sqlite3.connect('data/hedgemony_validation.db')

# ❌ NEVER query validation metrics during decision-making
metrics = validation_conn.execute("""
    SELECT move_5s, move_30s, time_to_impact_seconds, tradeable
    FROM event_metrics
    WHERE event_id = ?
""", (event_id,)).fetchone()

# This is CHEATING - you're seeing the future!
```

### ✅ ALLOWED (Post-Hoc Analysis Only)

```python
# After backtest completes, you CAN analyze correlation
def analyze_strategy_performance():
    """
    After backtest, compare our trades to validation metrics.
    This is OK because it's analysis, not decision-making.
    """
    input_conn = sqlite3.connect('data/hedgemony.db')
    validation_conn = sqlite3.connect('data/hedgemony_validation.db')

    # Join to see: "Did we trade the high-impact events?"
    results = input_conn.execute("""
        SELECT
            e.id,
            e.title,
            m.time_to_impact_seconds,
            m.move_5m,
            t.action,
            t.pnl
        FROM master_events e
        JOIN event_metrics m ON e.id = m.event_id
        LEFT JOIN backtest_trades t ON e.id = t.event_id
    """).fetchall()

    # Analyze: "We traded 80% of events with move_5m > 2%"
    # This helps improve strategy, but doesn't create bias
```

---

## Performance Metrics

### Core Metrics

**1. Total P&L**
- Absolute: `final_balance - initial_balance`
- Percentage: `(final_balance / initial_balance - 1) * 100`

**2. Win Rate**
- Formula: `winning_trades / total_trades * 100`
- Benchmark: >50% is good for event-driven strategies

**3. Average Win vs Average Loss**
- Avg Win: `sum(winning_pnls) / winning_trades`
- Avg Loss: `sum(losing_pnls) / losing_trades`
- Ratio: Should be >1.5 (winners bigger than losers)

**4. Max Drawdown**
- Largest peak-to-trough decline in portfolio value
- Critical for risk management

**5. Sharpe Ratio**
- Risk-adjusted return
- Formula: `(mean_return - risk_free_rate) / std_dev_return`
- Benchmark: >1.0 is decent, >2.0 is excellent

### Event-Specific Metrics (Post-Hoc Analysis)

**Correlation with Validation Metrics:**
- Trade rate by `time_to_impact_seconds` (did we trade fast events?)
- P&L by `move_5m` (did we profit more on bigger moves?)
- Win rate by `quality_level` (do we trade high-quality events better?)

**Strategy Insights:**
- Which event categories perform best? (regulatory, technical, partnership)
- Which sources have highest win rate? (Bloomberg, SEC, Twitter)
- Is there optimal confidence threshold?

---

## Usage Examples

### Basic Backtest

```bash
# Run backtest on all events in database
python3 scripts/backtest/run_backtest.py \
    --symbol SOL-USD \
    --strategy sentiment \
    --initial-balance 100000 \
    --confidence-threshold 0.75
```

### Custom Strategy

```bash
# Run with custom strategy parameters
python3 scripts/backtest/run_backtest.py \
    --strategy sentiment \
    --params '{"confidence_threshold": 0.8, "position_size_pct": 0.15}'
```

### Post-Hoc Analysis

```bash
# Generate correlation report after backtest
python3 scripts/backtest/analyze_results.py \
    --backtest-id 20240131_153045 \
    --compare-validation-metrics
```

---

## Anti-Bias Checklist

Before running ANY backtest, verify:

- [ ] Strategy ONLY reads from `hedgemony.db` (input database)
- [ ] Strategy NEVER imports or references `hedgemony_validation.db`
- [ ] Price data is filtered to ONLY show candles before event timestamp
- [ ] Execution price uses FIRST candle AFTER event (realistic slippage)
- [ ] No validation metrics (move_5s, tradeable, impact_score) in strategy code
- [ ] Event text is verbatim from source (verified by validate_verbatim_text.py)
- [ ] All events passed correlation validation (time_to_impact < 60s)

**If ANY item is unchecked, your backtest results are INVALID.**

---

## Common Pitfalls

### Pitfall 1: Using Pre-Calculated Sentiment
**Problem:** Strategy uses `sentiment_score` field from old `news` table
**Why it's bias:** Sentiment calculated with hindsight knowledge of outcome
**Solution:** Strategy must analyze verbatim text in real-time

### Pitfall 2: Peeking at Future Prices
**Problem:** Not filtering price_data to past-only
**Why it's bias:** Strategy can see price movement that hasn't happened yet
**Solution:** Always filter `price_data` to `timestamp < event_timestamp`

### Pitfall 3: Using Validation Metrics
**Problem:** Strategy checks `tradeable` or `impact_score` fields
**Why it's bias:** These are post-hoc judgments made after seeing outcomes
**Solution:** Physically separate databases - bot CAN'T access validation DB

### Pitfall 4: Instant Execution Assumption
**Problem:** Using price at exact event timestamp
**Why it's unrealistic:** Real execution has latency (1-60 seconds)
**Solution:** Use first candle AFTER event, add configurable execution delay

### Pitfall 5: Overfitting to Small Dataset
**Problem:** Optimizing strategy on same 4 events used for validation
**Why it's bias:** Strategy learns specific events, not general patterns
**Solution:** Use train/test split, or out-of-sample validation

---

## Integration with Event Scraping Skill

This backtesting skill is **downstream** from the event_scraping skill:

```
Event Scraping Skill (Upstream)
    ↓
    Validated Events (data/hedgemony.db)
    ↓
Backtesting Skill (This Skill)
    ↓
    Performance Metrics
    ↓
Strategy Refinement → Loop back to data collection
```

**Data Flow:**
1. Event scraping finds high-quality events (spike-first methodology)
2. Validation scripts ensure events are accurate and verbatim
3. Migration script separates input data from validation metadata
4. Backtest engine reads ONLY input data
5. Strategy makes decisions based on verbatim text
6. Results inform whether we need more/better events

---

## Future Enhancements

**Phase 2: Live Trading Integration**
- Real-time event detection
- Strategy execution on live markets
- Performance monitoring vs backtest expectations

**Phase 3: Multi-Strategy Portfolio**
- Run multiple strategies in parallel
- Allocate capital based on historical performance
- Ensemble approaches

**Phase 4: Machine Learning Strategies**
- Train models on verbatim text + outcomes
- Ensure training data ONLY uses input fields
- Cross-validation to prevent overfitting

**Phase 5: Risk Management**
- Position sizing based on Kelly criterion
- Portfolio-level stop-losses
- Correlation-based hedging

---

## Key Principles

1. **Separation is physical, not logical** - Bot can't access validation DB at all
2. **Verbatim text is sacred** - AI needs exact words traders saw
3. **Execution realism matters** - Account for latency and slippage
4. **Small, perfect dataset beats large, messy one** - Quality over quantity
5. **Post-hoc analysis is OK** - Correlation analysis AFTER backtest is fine
6. **Trust, but verify** - Always run anti-bias checklist before accepting results

---

**Last Updated:** 2026-01-31
**Status:** Production-ready methodology
**Next Review:** 2026-04-30

**Related Documentation:**
- [Event Scraping Skill](../event_scraping/SKILL.md)
- [Database Separation](../../docs/DATABASE_SEPARATION.md)
- [Event Data Schemas](../../docs/event_data_schemas.md)
