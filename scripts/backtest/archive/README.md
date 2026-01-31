# Archived Backtest Scripts

This directory contains **deprecated backtesting scripts** that have been archived as of January 2026.

## Why These Files Were Archived

These scripts used an older database schema and simpler backtesting approach that has been superseded by the professional event-driven architecture.

---

## Archived Files

### 1. `run_backtest.py`
**Original Purpose:** Run candle-based backtest using simple engine
**Deprecated Because:**
- Uses old `engine.py` (superseded by `hardcore_engine.py`)
- References deprecated `news` table (now using `master_events`)
- Hardcoded to January 2024 test data
- Simple position management (no Monte Carlo, no slippage modeling)

**Modern Alternative:** `run_event_backtest.py` (parent directory)

---

### 2. `prepare_backtest_data.py`
**Original Purpose:** Create synthetic test data for January 2024
**Deprecated Because:**
- Creates fake news entries for old `news` table schema
- Hardcoded synthetic events (not real market data)
- Used for initial testing, now have real `master_events` dataset

**Modern Alternative:** Real event data in `master_events` table populated via event scraping

---

### 3. `export_training_data.py`
**Original Purpose:** Export news sentiment data to JSONL for AI fine-tuning
**Deprecated Because:**
- Exports from old `news` table (deprecated schema)
- Simple format without rich metadata

**Modern Alternative:** If needed for AI training, should be rewritten to export from `master_events` with full event metadata

---

## Migration Guide

If you need functionality from these scripts:

### For Backtesting
Use the modern event-driven approach:
```bash
# Professional backtesting with bias prevention
python scripts/backtest/run_event_backtest.py --strategy verbatim_sentiment

# With custom parameters
python scripts/backtest/run_event_backtest.py \
  --strategy verbatim_sentiment \
  --confidence-threshold 0.75 \
  --execution-delay 0 \
  --exit-delay 300
```

### For Training Data Export
Rewrite using modern schema:
```python
from src.backtest.data_access import EventDataAccess

data_access = EventDataAccess()
events = data_access.load_all_events()

# Export to your preferred format
for event in events:
    # event.title, event.description, event.source, etc.
    pass
```

### For Synthetic Test Data
Not needed - use real `master_events` data:
```python
from src.backtest.data_access import EventDataAccess

data_access = EventDataAccess()
events = data_access.load_all_events()
print(f"Available events: {len(events)}")
```

---

## Modern Architecture

The current professional backtesting setup:

```
src/backtest/
├── data_access.py          # Bias-free event loading (DB separation)
├── strategy.py             # Strategy framework (OOP)
├── metrics.py              # Performance analytics
├── hardcore_engine.py      # Monte Carlo simulation
└── README.md               # Architecture docs

scripts/backtest/
└── run_event_backtest.py   # Event-driven backtest runner
```

---

## Recovery

These files are kept in archive (not deleted) in case you need to reference the old implementation. They are **not maintained** and may not work with the current database schema.

To use them, you would need to:
1. Restore the old `news` table schema
2. Update imports for moved modules
3. Accept that they lack modern features (Monte Carlo, slippage, bias prevention)

**Recommendation:** Use modern components instead.

---

**Archived:** January 31, 2026
**Reason:** Migration to professional event-driven architecture
