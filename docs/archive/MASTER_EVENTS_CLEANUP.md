# ✅ MASTER EVENTS CLEANUP - COMPLETE

## What We Did

Removed all low-quality event-first data from `master_events` table.

## Before Cleanup
```
Total Events: 144
├─ Quality Level 1 (event-first): 140 events ❌
└─ Quality Level 2 (spike-first): 4 events ✅
```

## After Cleanup
```
Total Events: 4
└─ Quality Level 2 (spike-first): 4 events ✅
```

## Your Clean Dataset

### master_events (4 high-quality events)

| Event | Date | Z-Score | Category | Methodology |
|-------|------|---------|----------|-------------|
| FTX Repayment Record Date | 2025-04-10 | 13.80σ | Crypto | spike-first |
| CME Futures Leaked Memo | 2025-03-03 | 13.70σ | Crypto | spike-first |
| BOJ Rate Hike + Carry Trade | 2024-08-05 | 12.75σ | Regulatory | spike-first |
| Trump Inauguration Selloff | 2025-01-20 | 9.35σ | Political | spike-first |

**All events have:**
- ✅ 1-second price data (10,000+ data points each)
- ✅ Verified via web research
- ✅ Z-score > 9.0σ (major volatility spikes)
- ✅ Spike-first methodology

**What they need:**
- ⏳ Exact announcement timestamps (currently using hourly)
- ⏳ Verbatim source text (headlines + paragraphs)
- ⏳ Measured lag (not assumed)

## Old Data Preserved

The removed data is still available in original tables:
- `curated_events` (80 events) - archived
- `gold_events` (91 events) - archived

**Don't delete these tables** - keep for comparison and learning.

## Next Steps

### Priority 1: Add Verbatim Source Text
```sql
ALTER TABLE master_events ADD COLUMN verbatim_headline TEXT;
ALTER TABLE master_events ADD COLUMN verbatim_text TEXT;
ALTER TABLE master_events ADD COLUMN source_url TEXT;
```

Then populate for each event:
1. Find original announcement (Twitter, press release, news wire)
2. Copy exact headline
3. Copy 2-3 paragraphs of source text word-for-word
4. Add source URL

### Priority 2: Find Exact Timestamps
For each event:
1. Research exact announcement time (to the second)
2. Update timestamp in database
3. Re-fetch 1s price data from exact time
4. Recalculate moves

### Priority 3: Measure Actual Lag
For each event:
1. Load 1s data from exact announcement time
2. Find first >0.1% move
3. Record lag in seconds
4. Calculate average across all events
5. Use measured lag in backtests (not assumed 15-30s)

### Priority 4: Grow Dataset
Continue manual research:
- Verify remaining 16 spikes from top 20
- Target: 20-50 high-quality events
- All must meet quality criteria (Z>5.0σ, verified, exact timestamps)

## Usage

### Query Master Events
```sql
-- All events (currently 4)
SELECT * FROM master_events;

-- High-impact only (quality level 2)
SELECT * FROM master_events WHERE quality_level = 2;

-- Spike-first methodology only
SELECT * FROM master_events WHERE methodology = 'spike-first';
```

### For Backtesting
```python
# Use only verified, high-quality events
events = db.query("SELECT * FROM master_events WHERE quality_level >= 2")
```

## Quality Standards Going Forward

**Every event added to master_events must have:**
1. ✅ Verified tier-1 source
2. ✅ Exact timestamp (±60 seconds)
3. ✅ 1-second price data
4. ✅ Verbatim headline and source text
5. ✅ Z-score > 5.0σ OR verified high-impact
6. ✅ Price move >0.5% in 5min OR >2% in 30min

**No exceptions.**

---

**Status:** ✅ Cleanup Complete  
**Quality:** 🟢 4 verified high-quality events  
**Next:** Add verbatim text + exact timestamps + measured lag
