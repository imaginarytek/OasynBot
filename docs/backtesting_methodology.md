# Backtesting Methodology

This document explains how HedgemonyBot validates trading strategies using historical data.

## Philosophy

Our backtesting approach prioritizes **realism over speed**. We use event-driven simulation (not vectorized) to ensure the backtest behaves identically to live trading.

### Key Principles

1. **No Look-Ahead Bias** - Never use information that wouldn't be available at trade time
2. **Realistic Execution** - Model slippage, latency, and market impact
3. **Monte Carlo Validation** - Run 30-50 simulations per event to account for randomness
4. **Walk-Forward Testing** - Validate on out-of-sample data (planned)

---

## Architecture

### Event-Driven vs Vectorized

**We use Event-Driven** because:
- Prevents look-ahead bias (can't accidentally peek at future data)
- Shares code with live trading (same execution logic)
- Handles complex stop logic (trailing stops, breakeven)

**We avoid Vectorized** because:
- Easy to introduce look-ahead bias (all data in one matrix)
- Hard to model path-dependent logic (stops, trailing)
- Doesn't match live execution flow

---

## Data Requirements

### High-Fidelity Events

We only backtest on **curated events** that meet these criteria:

1. **Unique, First-Mover News** - Not duplicates or follow-up articles
2. **Tier 1 Source** - Bloomberg, Reuters, official announcements
3. **Verbatim Text** - Exact headline from source (not paraphrased)
4. **High Impact** - Score 7-10 (significant market-moving potential)
5. **1s Price Data** - Real 1-second candles for 120 minutes post-event

**Current Dataset:** 91 events (2024-2026)

### Price Data Quality

**Preferred:** Real 1s candles from Hyperliquid/Binance
- Captures intra-minute volatility
- Allows realistic entry timing
- Shows actual slippage conditions

**Fallback:** Synthetic ticks from 1m OHLC (Brownian Bridge)
- Used when 1s data unavailable
- Less accurate but better than nothing
- Currently disabled in production backtests

---

## Backtest Workflow

### Phase 1: Event Selection

```python
# Load curated events with 1s price data
events = db.query("SELECT * FROM curated_events WHERE sol_price_data IS NOT NULL")

# Sort chronologically (simulate real-time)
events.sort(key=lambda x: x['timestamp'])
```

### Phase 2: AI Signal Generation

For each event:
1. Extract sentiment from verbatim text
2. Calculate confidence score (0-1)
3. Assign impact score (7-10)
4. **Filter:** Only trade if confidence > 0.75

```python
if ai_confidence < 0.75:
    return {"status": "skipped"}
```

### Phase 3: Entry Logic

**Confirmation Window:** 300 seconds (5 minutes)

```python
# Find the volatility spike (proxy for when news "hit")
safe_window = df.iloc[60:-60]  # Exclude first/last minute
peak_idx = safe_window['range'].idxmax()
start_price = df.loc[peak_idx]['open']

# Wait for price to move ≥0.20% in predicted direction
for i in range(300):  # 300 seconds
    current_price = ticks[i]
    move = (current_price - start_price) / start_price
    
    if move >= 0.002:  # 0.20% threshold
        entry_price = current_price * (1 + slippage)
        break
```

**If no confirmation:** Skip trade (no entry)

### Phase 4: Position Sizing

**Fixed Risk Model:**

```python
# Risk per trade based on impact score
if impact >= 10:
    risk_pct = 0.02  # 2% of equity
elif impact >= 9:
    risk_pct = 0.015  # 1.5%
else:
    risk_pct = 0.01  # 1%

# Adjust for drawdown
if current_drawdown > 0.05:  # 5% DD
    risk_pct *= 0.5  # Cut risk in half

# Calculate position size
risk_dollars = equity * risk_pct
notional_size = risk_dollars / stop_distance
```

**Example:**
- Equity: $100,000
- Impact: 9
- Risk: 1.5% = $1,500
- Stop: 3.5%
- Position: $1,500 / 0.035 = $42,857 notional

### Phase 5: Trade Management

**Chaos Bracket (Trailing Stop):**

```python
# Initial stop: 3.5% below entry
stop_price = entry_price * 0.965

# Dynamic adjustments:
if pnl > 6%:
    stop_price = current_price * 0.995  # Trail by 0.5%
elif pnl > 3%:
    stop_price = current_price * 0.99   # Trail by 1%
elif pnl > 1.5%:
    stop_price = entry_price * 1.002    # Breakeven +0.2%
```

**Exit Conditions:**
1. Stop hit (price crosses stop_price)
2. Time limit (30 minutes / 1800 seconds)

### Phase 6: Slippage Modeling

**Dynamic Slippage:**

```python
# Base slippage
slippage = 0.002  # 0.2% for SOL

# Volatility adjustment
recent_vol = (max(last_5_ticks) - min(last_5_ticks)) / min(last_5_ticks)
slippage += recent_vol * 0.2  # Add 20% of volatility

# Apply to entry
entry_price = market_price * (1 + slippage)  # Long
entry_price = market_price * (1 - slippage)  # Short
```

**Typical Slippage:**
- Low volatility: 0.2%
- Medium volatility: 0.3-0.4%
- High volatility: 0.5-0.8%

---

## Monte Carlo Simulation

To account for execution randomness, we run **30-50 simulations per event** with varied parameters:

```python
for seed in range(30):
    # Randomize slippage (±50%)
    slippage = base_slippage * random.uniform(0.8, 1.5)
    
    # Randomize confirmation window (±50%)
    confirm_window = 300 * random.uniform(0.8, 1.5)
    
    # Run simulation
    result = run_event(event, slippage, confirm_window)
    pnl_samples.append(result['pnl'])

# Use average PnL
avg_pnl = mean(pnl_samples)
```

**Why Monte Carlo?**
- Real execution varies (slippage, timing, fills)
- Single run can be lucky/unlucky
- Average of 30 runs is more realistic

---

## Bias Prevention

### 1. Look-Ahead Bias

**Problem:** Using future data to make past decisions.

**Prevention:**
- Only scan 60s-7140s window (exclude first/last minute)
- Never use `df.idxmax()` on full dataset
- Validate that entry_time > event_time

### 2. Survivorship Bias

**Problem:** Only testing on events we know were "good."

**Prevention:**
- Include all events in time period (not just winners)
- Track skipped trades (no confirmation)
- Report % of events that didn't trade

### 3. Data Snooping

**Problem:** Over-optimizing parameters to fit historical noise.

**Prevention:**
- Use walk-forward testing (planned)
- Limit parameter tuning to <5 variables
- Require out-of-sample validation

---

## Performance Metrics

### Primary Metrics

**Total Return:**
```python
roi = (final_equity - initial_equity) / initial_equity
```

**Win Rate:**
```python
win_rate = winning_trades / total_trades
```

**Sharpe Ratio:**
```python
sharpe = mean(returns) / std(returns) * sqrt(252)
```

**Max Drawdown:**
```python
peak = max(equity_curve)
trough = min(equity_curve[peak_idx:])
max_dd = (peak - trough) / peak
```

### Secondary Metrics

- **Average Win:** Mean PnL of winning trades
- **Average Loss:** Mean PnL of losing trades
- **Profit Factor:** Gross profit / Gross loss
- **Expectancy:** (Win% × Avg Win) - (Loss% × Avg Loss)

---

## Validation Process

### Step 1: In-Sample Testing

Run backtest on curated dataset:
```bash
python3 src/backtest/test_strategy.py
```

**Expected Results:**
- Win rate: 60-70%
- Sharpe: >1.5
- Max DD: <15%

### Step 2: Parameter Sensitivity

Test with varied parameters:
- Confirmation threshold: 0.1%, 0.2%, 0.3%
- Stop loss: 3%, 3.5%, 4%
- Risk per trade: 1%, 1.5%, 2%

**Goal:** Ensure results are stable (not over-fitted).

### Step 3: Walk-Forward Testing (Planned)

- Train on 6 months
- Test on next 1 month
- Roll forward
- Validate consistent performance

---

## Current Limitations

1. **No Transaction Costs** - Not modeling exchange fees (0.05-0.1%)
2. **Static Slippage** - Not using order book depth
3. **Single Asset** - Primarily tuned for SOL/USD
4. **No Multi-Event Handling** - Assumes one trade at a time
5. **Manual Event Curation** - Dataset requires human verification

---

## Comparison to Live Trading

| Aspect | Backtest | Live |
|--------|----------|------|
| Entry Logic | Hindsight volatility spike | Real-time confirmation |
| Slippage | Modeled (0.2-0.8%) | Actual (varies) |
| Latency | Instant | 1-5s API delay |
| Data | 1s candles | Tick-by-tick |
| Stops | Simulated | Exchange orders |

**Goal:** Minimize gap between backtest and live performance.

---

## Future Enhancements

See [ROADMAP.md](ROADMAP.md) for planned improvements:

- Walk-forward testing (Phase 2.2)
- Bias detection framework (Phase 2.1)
- Performance attribution (Phase 2.3)
- Realistic slippage model (Phase 3.3)
- Unified event loop (Phase 4.4)

---

**Last Updated:** 2026-01-30  
**Backtest Version:** 2.5 (High Fidelity Simulation)
