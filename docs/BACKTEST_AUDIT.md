# Backtesting Engine Audit - January 2026

## Executive Summary

**Status:** Mixed architecture - Professional components exist but not fully integrated
**Grade:** B+ (Professional potential, needs integration)
**Action Required:** Integration + Legacy cleanup

---

## Current Architecture

### ✅ PROFESSIONAL COMPONENTS (Keep & Enhance)

#### 1. **src/backtest/data_access.py** - GOLD STANDARD
- **Purpose:** Bias-free event data loading
- **Quality:** Excellent - prevents look-ahead bias
- **Features:**
  - Physical DB separation (hedgemony.db vs hedgemony_validation.db)
  - Security checks prevent validation DB access
  - `get_past_prices()` - only shows historical data
  - `get_execution_price()` - simulates latency
- **Verdict:** ✅ KEEP - This is production-ready

#### 2. **src/backtest/strategy.py** - CLEAN FRAMEWORK
- **Purpose:** Strategy abstraction layer
- **Quality:** Good OOP design with proper interfaces
- **Includes:**
  - `Strategy` abstract base class (candle-based)
  - `EventStrategy` abstract base class (event-driven)
  - `VerbatimSentimentStrategy` - keyword analysis
  - `SimpleEventStrategy` - baseline testing
  - `SentimentStrategy` - legacy candle-based
  - `MomentumStrategy` - legacy candle-based
- **Verdict:** ✅ KEEP - Framework is solid

#### 3. **src/backtest/metrics.py** - PROFESSIONAL ANALYTICS
- **Purpose:** Performance metrics calculation
- **Features:**
  - Win rate, Sharpe ratio, max drawdown
  - Proper PnL tracking
  - Pretty formatted output
- **Verdict:** ✅ KEEP - Industry standard metrics

#### 4. **src/backtest/hardcore_engine.py** - ADVANCED SIMULATION
- **Purpose:** High-fidelity Monte Carlo backtesting
- **Quality:** Advanced - institutional-grade features
- **Features:**
  - Monte Carlo simulation (30-50 runs per event)
  - Synthetic tick generation (Brownian Bridge)
  - Dynamic slippage modeling
  - Fixed risk sizing (1%, 1.5%, 2% based on impact)
  - Trailing stops (CHAOS BRACKET)
  - Drawdown-based risk adjustment
- **Issues:**
  - ❌ Hardcoded trading logic (doesn't use Strategy framework)
  - ❌ Not integrated with data_access.py
  - ❌ Standalone script, not modular
- **Verdict:** ⚠️ REFACTOR - Extract logic into Strategy classes

#### 5. **scripts/backtest/run_event_backtest.py** - WORKING DEMO
- **Purpose:** Event-driven backtest runner
- **Quality:** Good - demonstrates proper workflow
- **Uses:** data_access.py + strategy.py correctly
- **Verdict:** ✅ KEEP - Reference implementation

---

### ⚠️ LEGACY COMPONENTS (Review/Archive)

#### 1. **src/backtest/engine.py** - OLD SIMPLE ENGINE
- **Purpose:** Original candle-based backtest engine
- **Issues:**
  - Simple position management (only 1 position at a time)
  - No Monte Carlo, no slippage modeling
  - Uses old sentiment_data format
  - Superseded by hardcore_engine.py
- **Used By:** run_backtest.py (legacy script)
- **Verdict:** 🗑️ DEPRECATE - hardcore_engine is superior

#### 2. **scripts/backtest/run_backtest.py** - OLD SCRIPT
- **Purpose:** Legacy candle-based backtest
- **Issues:**
  - Uses deprecated engine.py
  - References old DB schema (news table, not master_events)
  - Hardcoded dates (Jan 2024)
- **Verdict:** 🗑️ ARCHIVE - Replaced by run_event_backtest.py

#### 3. **scripts/backtest/prepare_backtest_data.py** - UNKNOWN
- **Size:** 3.2KB
- **Need to review:** Check if still needed
- **Verdict:** 🔍 REVIEW

#### 4. **scripts/backtest/export_training_data.py** - UNKNOWN
- **Size:** 1.9KB
- **Need to review:** Check if AI training related
- **Verdict:** 🔍 REVIEW

#### 5. **src/backtest/__init__.py** - OUTDATED EXPORTS
- **Issues:**
  - Only exports old components (BacktestEngine, SentimentStrategy)
  - Doesn't export new components (data_access, EventStrategy, hardcore_engine)
  - Missing modern API surface
- **Verdict:** ⚠️ UPDATE - Export new components

---

## Critical Issues Found

### 🔴 Issue #1: hardcore_engine.py Not Using Strategy Framework
**Problem:** Trading logic hardcoded in `run_event()` method instead of using Strategy classes

**Impact:**
- Can't swap strategies
- Can't A/B test different approaches
- Violates DRY principle

**Solution:**
1. Extract hardcoded logic into `HardcoreEventStrategy` class
2. Make hardcore_engine accept Strategy object
3. Keep advanced features (Monte Carlo, slippage) in engine

### 🔴 Issue #2: Disconnected Architecture
**Problem:** Three separate backtesting approaches that don't work together:
- Simple engine (engine.py) + Strategy
- Event backtest (run_event_backtest.py) + Strategy
- Hardcore engine (standalone, no Strategy)

**Solution:** Unified architecture:
```
data_access.py → Strategy → hardcore_engine.py → metrics.py
```

### 🟡 Issue #3: Legacy DB Schema References
**Problem:** Old scripts reference deprecated tables (news instead of master_events)

**Solution:** Archive legacy scripts, update docs

---

## Recommended Architecture (Pro Setup)

```
┌─────────────────────────────────────────────────────────┐
│                   PROFESSIONAL ARCHITECTURE              │
└─────────────────────────────────────────────────────────┘

1. DATA LAYER
   ├── data_access.py (bias-free event loading)
   └── Database separation (input vs validation)

2. STRATEGY LAYER
   ├── strategy.py (abstract interfaces)
   ├── VerbatimSentimentStrategy (keyword analysis)
   ├── HardcoreEventStrategy (NEW - extracted from hardcore_engine)
   └── Custom strategies (user-defined)

3. EXECUTION LAYER
   ├── hardcore_engine.py (Monte Carlo simulation)
   ├── Risk sizing (1-2% based on impact)
   ├── Slippage modeling (dynamic)
   └── Position management (trailing stops)

4. ANALYTICS LAYER
   ├── metrics.py (performance calculation)
   └── Reporting (formatted output)

5. CLI/SCRIPTS
   ├── run_event_backtest.py (simple runner)
   └── run_hardcore_backtest.py (NEW - full Monte Carlo)
```

---

## Action Plan

### Phase 1: Cleanup (Immediate)
- [ ] Archive legacy files to `scripts/backtest/archive/`
  - engine.py → archive (keep for reference)
  - run_backtest.py → archive
  - prepare_backtest_data.py → review first, then archive/delete
  - export_training_data.py → review first, then archive/delete

### Phase 2: Integration (High Priority)
- [ ] Extract trading logic from hardcore_engine.py into HardcoreEventStrategy
- [ ] Refactor hardcore_engine to accept Strategy objects
- [ ] Update __init__.py to export modern components
- [ ] Create run_hardcore_backtest.py demo script

### Phase 3: Documentation (Medium Priority)
- [ ] Update README with new architecture
- [ ] Add strategy development guide
- [ ] Document hardcore_engine parameters

### Phase 4: Testing (Before Live Trading)
- [ ] Run all strategies on same dataset
- [ ] Compare results (simple vs hardcore)
- [ ] Validate Monte Carlo convergence
- [ ] Stress test with 2023-2026 data

---

## File Disposition Matrix

| File | Status | Action | Reason |
|------|--------|--------|--------|
| data_access.py | ✅ Keep | None | Production-ready |
| strategy.py | ✅ Keep | Minor cleanup | Solid framework |
| metrics.py | ✅ Keep | None | Professional |
| hardcore_engine.py | ⚠️ Refactor | Extract to Strategy | Needs integration |
| run_event_backtest.py | ✅ Keep | None | Reference impl |
| engine.py | ✅ Deleted | Removed | Superseded by hardcore_engine.py |
| run_backtest.py | ✅ Archived | scripts/backtest/archive/ | Legacy schema |
| prepare_backtest_data.py | ✅ Archived | scripts/backtest/archive/ | Fake test data generator |
| export_training_data.py | ✅ Archived | scripts/backtest/archive/ | Old schema export |
| __init__.py | ✅ Updated | Exports modern API | Completed |

---

## Professional Grade Checklist

### Current State
- [x] Bias-free data access
- [x] Strategy framework (OOP)
- [x] Professional metrics
- [x] Monte Carlo simulation
- [x] Dynamic slippage
- [x] Risk management
- [ ] Integrated architecture (hardcore + strategy)
- [ ] Clean API surface (__init__.py)
- [ ] No legacy code in main path
- [ ] Comprehensive testing

### After Cleanup
- [x] All above
- [x] Unified architecture
- [x] Clean codebase (no redundancy)
- [x] Ready for production

---

## Conclusion

**You have all the components of a professional backtesting engine, they just need to be properly integrated.**

The hardcore_engine.py is institutional-quality but standalone. Once we extract its logic into the Strategy framework, you'll have a truly professional setup that rivals hedge fund infrastructure.

**Grade after cleanup: A+ (Institutional-grade)**
