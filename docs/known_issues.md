# Known Issues & Solutions

This document tracks bugs we've encountered, how we fixed them, and lessons learned to prevent future issues.

---

## Database & Schema Issues

### Issue #1: Manual Schema Migrations Failing Silently

**Date:** 2024-01-15  
**Severity:** Medium  
**Component:** `src/utils/db.py`

**Problem:**
The database initialization code used try/except to add columns:
```python
try:
    c.execute("ALTER TABLE news ADD COLUMN ingested_at TIMESTAMP")
except Exception:
    pass  # Silently fails if column exists
```

This made it impossible to know if migrations succeeded or failed.

**Solution:**
- **Short-term:** Added logging to catch failures
- **Long-term:** Implement proper migration system (see [ROADMAP.md](ROADMAP.md) Phase 1.3)

**Lesson Learned:** Never silently swallow exceptions in database operations.

---

### Issue #2: SQLite Database Locking in Async Context

**Date:** 2024-01-18  
**Severity:** High  
**Component:** `src/utils/db.py`

**Problem:**
When multiple async tasks tried to write to the database simultaneously, we got:
```
sqlite3.OperationalError: database is locked
```

**Root Cause:**
SQLite doesn't handle concurrent writes well, especially with `check_same_thread=False`.

**Solution:**
```python
# Added connection pooling with timeout
def get_connection(self):
    return sqlite3.connect(
        self.db_path, 
        check_same_thread=False,
        timeout=10.0  # Wait up to 10s for lock
    )
```

**Lesson Learned:** SQLite is not ideal for high-concurrency writes. Consider TimescaleDB for production.

---

## API & Data Fetching Issues

### Issue #3: Binance Rate Limiting

**Date:** 2024-01-20  
**Severity:** Medium  
**Component:** `src/chronos/binance.py`

**Problem:**
When fetching 1s data for 91 events, we hit Binance's rate limit:
```
429 Too Many Requests
```

**Rate Limits:**
- 1200 requests per minute (weight-based)
- 1s candles have weight of 10

**Solution:**
```python
# Added exponential backoff
import time

def fetch_with_retry(self, symbol, start, end, retries=3):
    for i in range(retries):
        try:
            return self.client.get_klines(...)
        except BinanceAPIException as e:
            if e.code == -1003:  # Rate limit
                wait = 2 ** i  # 1s, 2s, 4s
                time.sleep(wait)
            else:
                raise
```

**Lesson Learned:** Always implement exponential backoff for external APIs.

---

### Issue #4: Hyperliquid 1s Data Gaps

**Date:** 2024-01-22  
**Severity:** Low  
**Component:** `scripts/data_fetching/fetch_real_1s_data_smart.py`

**Problem:**
Hyperliquid's 1s candle API sometimes returns incomplete data (missing candles).

**Example:**
- Requested: 2024-01-15 14:30:00 to 14:32:00 (120 candles)
- Received: 115 candles (5 missing)

**Solution:**
```python
# Fill gaps with interpolation
def fill_missing_candles(df):
    df = df.set_index('timestamp')
    df = df.resample('1S').asfreq()  # Create 1s index
    df['close'] = df['close'].interpolate(method='linear')
    return df.reset_index()
```

**Lesson Learned:** Always validate data completeness before using in backtests.

---

## Backtesting Issues

### Issue #5: Look-Ahead Bias in Entry Logic

**Date:** 2024-01-25  
**Severity:** Critical  
**Component:** `src/backtest/test_strategy.py`

**Problem:**
Early version of the backtester used the event timestamp to find the "peak volatility" candle, but this created look-ahead bias:
```python
# BAD: Uses future data to find entry point
peak_idx = df['range'].idxmax()  # Scans entire dataset
```

**Solution:**
```python
# GOOD: Only scan 60s-7140s window (exclude first/last minute)
safe_window = df.iloc[60:-60]
peak_idx_safe = safe_window['range'].idxmax()
```

**Lesson Learned:** Always validate that backtest logic doesn't use future information.

---

### Issue #6: Slippage Model Too Optimistic

**Date:** 2024-01-26  
**Severity:** Medium  
**Component:** `src/backtest/test_strategy.py`

**Problem:**
Initial slippage was fixed at 0.05%, which is unrealistic for volatile events.

**Real-World Observation:**
- During high-impact news, slippage can be 0.2-0.5%
- Volume spikes cause wider spreads

**Solution:**
```python
# Dynamic slippage based on volatility
vol = (max(vol_window) - min(vol_window)) / min(vol_window)
actual_slippage = slippage_base + (vol * slippage_vol_adj)
```

**Lesson Learned:** Model slippage based on market conditions, not fixed %.

---

## Live Trading Issues

### Issue #7: Hyperliquid Wallet Address Mismatch

**Date:** 2024-01-28  
**Severity:** High  
**Component:** `src/trading/hyperliquid.py`

**Problem:**
Orders were rejected with:
```
Error: Wallet address does not match private key
```

**Root Cause:**
The `.env` file had the wrong wallet address (copy-paste error).

**Solution:**
```python
# Added validation on startup
def validate_credentials(self):
    derived_address = self.derive_address_from_key(self.private_key)
    if derived_address != self.wallet_address:
        raise ValueError("Wallet address mismatch!")
```

**Lesson Learned:** Always validate credentials before attempting live trades.

---

### Issue #8: Telegram Alerts Not Sending

**Date:** 2024-01-29  
**Severity:** Low  
**Component:** `src/alerts/telegram.py`

**Problem:**
Telegram bot was configured but alerts weren't sending.

**Root Cause:**
The `TELEGRAM_CHAT_ID` in `.env` was a string, but the API expects an integer:
```python
# BAD
chat_id = os.getenv("TELEGRAM_CHAT_ID")  # Returns "123456"

# GOOD
chat_id = int(os.getenv("TELEGRAM_CHAT_ID"))
```

**Solution:**
Added type conversion in settings loader.

**Lesson Learned:** Always validate environment variable types.

---

## Data Quality Issues

### Issue #9: Duplicate Events in Dataset

**Date:** 2024-01-27  
**Severity:** Medium  
**Component:** `scripts/utilities/curated_events_list.py`

**Problem:**
The same news event appeared multiple times in `curated_events` with slightly different timestamps.

**Example:**
- Event A: "Fed Raises Rates" @ 14:30:00
- Event B: "Fed Raises Rates" @ 14:30:15 (same event, different source)

**Solution:**
```python
# Deduplicate by title similarity + time window
def is_duplicate(new_event, existing_events, time_window=300):
    for event in existing_events:
        time_diff = abs((new_event['timestamp'] - event['timestamp']).total_seconds())
        title_sim = fuzz.ratio(new_event['title'], event['title'])
        if time_diff < time_window and title_sim > 85:
            return True
    return False
```

**Lesson Learned:** Always deduplicate events before adding to curated dataset.

---

## Configuration Issues

### Issue #10: Hardcoded Parameters in Code

**Date:** 2024-01-30  
**Severity:** Low  
**Component:** `src/backtest/test_strategy.py`

**Problem:**
Risk parameters were hardcoded in the backtester:
```python
self.RISK_CONFIG = {
    'base_risk_pct': 0.01,
    'god_risk_pct': 0.02,
    ...
}
```

This made it hard to run experiments with different configs.

**Solution:**
Planned for Phase 3.1: Move to YAML config files.

**Lesson Learned:** Configuration should be external, not hardcoded.

---

## Best Practices Established

### 1. Database Operations
- ✅ Always use transactions for multi-step writes
- ✅ Add timeouts to prevent deadlocks
- ✅ Log all schema changes

### 2. API Calls
- ✅ Implement exponential backoff
- ✅ Validate responses before using
- ✅ Cache when possible

### 3. Backtesting
- ✅ Never use future data
- ✅ Model realistic slippage
- ✅ Validate data completeness

### 4. Live Trading
- ✅ Validate credentials on startup
- ✅ Test with small positions first
- ✅ Always have kill switch

### 5. Data Quality
- ✅ Deduplicate events
- ✅ Verify timestamps
- ✅ Manual review for high-impact events

---

**Last Updated:** 2026-01-30  
**Total Issues Tracked:** 10
