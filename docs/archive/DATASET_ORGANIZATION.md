# 📊 DATASET ORGANIZATION & QUALITY GUIDE

## Current State (As of 2026-01-30)

### Database Tables Overview

| Table | Count | Quality | Purpose | Status |
|-------|-------|---------|---------|--------|
| `curated_events` | 80 | 🟡 Mixed | Original hand-picked events | **ARCHIVE** - Keep for comparison |
| `gold_events` | 91 | 🟢 Good | Second batch - verified but low impact | **KEEP** - Valid for testing |
| `optimized_events` | 4 | 🟡 Needs Work | Spike-first methodology (NEW) | **ACTIVE** - Needs timestamp refinement |
| `hourly_volatility_spikes` | 357 | 🔵 Raw Data | Detected spikes (unverified) | **RESEARCH** - Source for new events |

## 📁 Recommended Organization Structure

### 1. Archive Old/Bad Data
```
data/
├── archive/
│   ├── hedgemony_v1_original.db          # Backup of original curated_events
│   ├── bad_data_analysis.md              # Why it was bad
│   └── lessons_learned.md                # What we learned
```

### 2. Keep Good Historical Data
```
data/
├── historical/
│   ├── gold_events_v2.db                 # The 91 "good but low impact" events
│   ├── gold_events_analysis.md           # Quality metrics
│   └── gold_events_backtest_results.md   # Performance on this dataset
```

### 3. Active Development Dataset
```
data/
├── hedgemony.db                          # MAIN DATABASE (keep all tables)
│   ├── optimized_events                  # Active: 4 verified, needs refinement
│   ├── hourly_volatility_spikes          # Active: 357 spikes for research
│   ├── gold_events                       # Reference: Good historical data
│   └── curated_events                    # Reference: Original dataset
```

### 4. Documentation Structure
```
docs/
├── datasets/
│   ├── DATASET_COMPARISON.md             # Side-by-side comparison
│   ├── QUALITY_CRITERIA.md               # What makes a good event
│   └── EVOLUTION_TIMELINE.md             # How we got here
├── backtests/
│   ├── v1_original_dataset.md            # Results from curated_events
│   ├── v2_gold_events.md                 # Results from gold_events
│   └── v3_optimized_events.md            # Results from optimized_events (pending)
└── methodology/
    ├── event_first_approach.md           # Old method (archived)
    ├── spike_first_approach.md           # New method (active)
    └── hybrid_discovery.md               # Current workflow
```

## 🏷️ Dataset Quality Levels

### 🔴 Level 0: Bad Data (Archive Only)
**Characteristics:**
- Events picked without price validation
- Poor timestamp accuracy (±hours)
- Low correlation with actual price moves
- Mixed data quality

**Example:** Original `curated_events` (first 40-50 events)

**Action:** Archive, don't delete (for comparison)

### 🟡 Level 1: Valid but Low Impact (Keep for Testing)
**Characteristics:**
- Events are real and properly timestamped
- 1-second price data available
- Just didn't cause major price moves
- Good for testing strategy on "normal" conditions

**Example:** `gold_events` (91 events)

**Action:** Keep in main DB, use for robustness testing

### 🟢 Level 2: High-Quality Verified (Active Development)
**Characteristics:**
- Spike-first methodology
- Verified via web research
- Z-score > 9.0σ
- 1-second price data
- Needs timestamp refinement

**Example:** `optimized_events` (4 events, growing to 20+)

**Action:** Active development, this is our production dataset

### 🔵 Level 3: Raw Research Data (Mining Source)
**Characteristics:**
- Detected volatility spikes
- Not yet verified with news
- Source for finding new events
- 357 candidates to investigate

**Example:** `hourly_volatility_spikes`

**Action:** Research source, gradually verify and promote to Level 2

## 📋 Proposed Database Schema Cleanup

### Add Quality Metadata to All Tables

```sql
-- Add quality tracking columns
ALTER TABLE curated_events ADD COLUMN quality_level INTEGER DEFAULT 0;
ALTER TABLE curated_events ADD COLUMN archived BOOLEAN DEFAULT 0;
ALTER TABLE curated_events ADD COLUMN notes TEXT;

ALTER TABLE gold_events ADD COLUMN quality_level INTEGER DEFAULT 1;
ALTER TABLE gold_events ADD COLUMN verified BOOLEAN DEFAULT 1;

ALTER TABLE optimized_events ADD COLUMN quality_level INTEGER DEFAULT 2;
ALTER TABLE optimized_events ADD COLUMN timestamp_refined BOOLEAN DEFAULT 0;

-- Create a master events view
CREATE VIEW all_events_quality AS
SELECT 
    'curated' as source,
    title,
    timestamp,
    0 as quality_level,
    'Archived - Original dataset' as status
FROM curated_events
UNION ALL
SELECT 
    'gold' as source,
    title,
    timestamp,
    1 as quality_level,
    'Valid - Low impact events' as status
FROM gold_events
UNION ALL
SELECT 
    'optimized' as source,
    title,
    timestamp,
    2 as quality_level,
    'Active - High quality, needs refinement' as status
FROM optimized_events;
```

## 🎯 Recommended Actions

### Immediate (Today)
1. ✅ Create this documentation
2. ✅ Tag all events with quality levels
3. ✅ Create comparison report
4. ⏳ Run backtest on each dataset separately

### Short-term (This Week)
1. Archive original bad data with documentation
2. Create separate backtest results for each quality level
3. Refine timestamps on optimized_events
4. Verify 16 more events from hourly_volatility_spikes

### Long-term (Production)
1. Maintain only 2 active tables:
   - `production_events` (verified, refined, ready for live trading)
   - `research_spikes` (candidates for verification)
2. Archive everything else
3. Quarterly quality audits

## 📊 Quick Reference: Which Dataset to Use?

### For Backtesting Strategy Logic
**Use:** `gold_events` (91 events)
- **Why:** Large sample size, verified quality, diverse conditions
- **Limitation:** Low impact events, won't show full profit potential

### For Validating High-Impact Trading
**Use:** `optimized_events` (4 events, growing)
- **Why:** Major market movers, spike-first methodology
- **Limitation:** Small sample size, needs timestamp refinement

### For Finding New Events
**Use:** `hourly_volatility_spikes` (357 candidates)
- **Why:** Comprehensive volatility detection
- **Process:** Verify → Add to optimized_events

### For Comparison/Learning
**Use:** `curated_events` (80 events)
- **Why:** Shows what NOT to do
- **Purpose:** Validate that spike-first is better

## 🔄 Migration Path

### Phase 1: Organization (Now)
- Document all datasets
- Tag with quality levels
- Create comparison reports

### Phase 2: Validation (This Week)
- Backtest each dataset separately
- Document performance differences
- Prove spike-first methodology

### Phase 3: Consolidation (Next Week)
- Grow optimized_events to 20-50 events
- Refine all timestamps
- Archive old datasets
- Create single production table

### Phase 4: Production (2 Weeks)
- Deploy with production_events table
- Real-time spike detection
- Automated quality monitoring

## 📝 File Naming Convention

### Scripts
- `fetch_*.py` - Data fetching scripts
- `analyze_*.py` - Analysis scripts
- `backtest_*.py` - Backtesting scripts
- `archive_*.py` - Archival/cleanup scripts

### Documentation
- `DATASET_*.md` - Dataset documentation
- `BACKTEST_*.md` - Backtest results
- `METHODOLOGY_*.md` - Process documentation
- `ARCHIVE_*.md` - Historical records

### Databases
- `hedgemony.db` - Main production database
- `hedgemony_backup_YYYYMMDD.db` - Daily backups
- `archive/hedgemony_v1_*.db` - Archived versions

---

**Status:** 🟢 Organization plan ready
**Next Action:** Implement quality tagging and create comparison report
