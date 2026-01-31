# Event Validation Scripts

**Purpose:** Enforce the Gold Standard for backtesting data quality automatically.

These scripts close the gaps between methodology and implementation, ensuring that every event in `master_events` meets the strict quality requirements documented in the [event_scraping skill](../../.agent/skills/event_scraping/SKILL.md).

---

## 🎯 Why These Scripts Exist

**Problem:** The original workflow relied on manual diligence to ensure:
- News timestamps correlate with price spikes
- Events aren't duplicates
- Spike timing is precise (minute-level, not just hourly)

**Solution:** Automated validation that catches bad data **before it contaminates backtests**.

---

## 📁 Scripts Overview

### 1. `refine_spike_timing.py`
**When:** After `mine_events_professional.py` detects hourly spikes
**What:** Narrows down from 60-minute window to exact minute of spike

```bash
python3 scripts/validation/refine_spike_timing.py
```

**Input:** `potential_event_spikes` table (hourly timestamps)
**Output:** Same table with `refined_timestamp` (exact minute)

**Why it matters:** You can't search for news without knowing the exact minute the market moved.

---

### 2. `generate_research_guide.py`
**When:** After spike refinement
**What:** Creates markdown guide with pre-filled search links

```bash
python3 scripts/validation/generate_research_guide.py
```

**Input:** `potential_event_spikes` with refined timestamps
**Output:**
- `data/research_guide.md` - Research checklist with Twitter/Google News links
- `data/verified_events_template.json` - Template for manual entry

**Why it matters:** Reduces manual research time from 10min → 2min per event.

---

### 3. `validate_correlation.py` ⚠️ CRITICAL
**When:** After building dataset, BEFORE backtesting
**What:** Verifies news timestamp actually correlates with price spike

```bash
python3 scripts/validation/validate_correlation.py
```

**Validation Rules:**
- ✅ Price must move >0.1% to count as impact
- ✅ News→Price lag must be -10s to +60s
- ✅ Events outside this range are flagged INVALID

**Output:**
- Validation report showing which events passed/failed
- Updates `time_to_impact_seconds` in database
- Exit code 0 if all events valid, 1 if any failed

**Why it matters:** Prevents false correlations from creating "phantom" profitable trades in backtests.

---

### 4. `detect_duplicates.py`
**When:** Before finalizing dataset
**What:** Finds related events and applies Material Escalation logic

```bash
python3 scripts/validation/detect_duplicates.py
```

**Detection Rules:**
- Events within 24h with >60% title similarity
- Both must cause distinct Z>3.0 spike
- Later event must contain NEW information

**Recommendations:**
- **Keep Both:** Material escalation detected (rumor → confirmation)
- **Review:** Manual decision needed
- **Remove:** Duplicate or weak event

**Why it matters:** Prevents dataset contamination from duplicate events being counted as independent signals.

---

## 🔄 Complete Workflow

Here's the recommended end-to-end workflow:

```bash
# Step 1: Detect hourly volatility spikes
python3 scripts/mine_events_professional.py

# Step 2: Refine to exact minutes
python3 scripts/validation/refine_spike_timing.py

# Step 3: Generate research guide
python3 scripts/validation/generate_research_guide.py

# Step 4: Manual research (use data/research_guide.md)
# - Click search links
# - Find tier-1 sources
# - Fill in verified_events_batch.json

# Step 5: Import verified events
python3 scripts/import_new_events_json.py

# Step 6: Fetch 1-second price data
python3 scripts/build_verified_dataset.py

# Step 7: VALIDATE CORRELATION (CRITICAL!)
python3 scripts/validation/validate_correlation.py

# Step 8: Check for duplicates
python3 scripts/validation/detect_duplicates.py

# Step 9: If all validation passed, run backtests
python3 src/backtest/test_strategy.py
```

---

## ⚡ Quick Validation Check

Before running a backtest, do a quick quality check:

```bash
# Validate all events
python3 scripts/validation/validate_correlation.py

# Check for duplicates
python3 scripts/validation/detect_duplicates.py

# Query dataset stats
sqlite3 data/hedgemony.db "
SELECT
    COUNT(*) as total_events,
    COUNT(CASE WHEN time_to_impact_seconds IS NOT NULL THEN 1 END) as validated,
    AVG(time_to_impact_seconds) as avg_lag_seconds,
    MIN(time_to_impact_seconds) as min_lag,
    MAX(time_to_impact_seconds) as max_lag
FROM master_events
"
```

**Green flags:**
- ✅ All events have `time_to_impact_seconds` calculated
- ✅ Average lag is 5-30 seconds
- ✅ No events with lag >60s
- ✅ No duplicate pairs flagged

**Red flags:**
- ❌ Events with `time_to_impact_seconds = NULL`
- ❌ Events with lag >60s (wrong news source)
- ❌ Events with lag <0s (price moved before news)
- ❌ Multiple events with identical titles within 24h

---

## 🛠️ Troubleshooting

### "No refined spikes found"
**Cause:** Haven't run `mine_events_professional.py` or spikes already refined
**Fix:** Run spike detection first, or check `status` column in `potential_event_spikes`

### "No price data available"
**Cause:** Event is too old for Binance 1s data (>~6 months)
**Fix:** Use hourly data or skip event (1s data critical for validation)

### "Rate limited by Binance"
**Cause:** Too many API requests in short time
**Fix:** Scripts have built-in rate limiting (0.5s delay), wait a few minutes

### "Event failed validation (lag >60s)"
**Cause:** Wrong news source, or news timestamp is inaccurate
**Fix:** Re-research the spike minute, find the actual tier-1 source

---

## 📊 Understanding Validation Reports

### validate_correlation.py Output:
```
[Event 1] FTX Repayment Announcement
  Timestamp: 2024-08-07T12:15:00+00:00
  ✓ VALID - Valid correlation: 5s lag
    Price at spike: $186.23

[Event 2] SEC Lawsuit News
  Timestamp: 2024-06-05T16:32:00+00:00
  ✗ INVALID - Lag 125s > 60s (news likely wrong source)
    Price at spike: $142.56
```

**Action:** Remove or re-research invalid events.

### detect_duplicates.py Output:
```
⚠ POTENTIAL DUPLICATE FOUND
Event 1 (ID 3): SEC investigating Binance
Event 2 (ID 5): SEC Files Lawsuit vs Binance (3.2h later)

  Title Similarity: 75%
  Spike Analysis: Both caused distinct spikes (Z1=8.2, Z2=12.5)
  Content Overlap: 40%
  New Keywords in Event 2: lawsuit, files, official, charges

  Recommendation:
    ✓ KEEP BOTH - Material Escalation detected
```

**Action:** Keep both (rumor → confirmation escalation).

---

## 🔐 Data Integrity Guarantee

Running these scripts ensures:
1. **No look-ahead bias** - Events can't use future price data
2. **No false correlations** - News must actually precede price moves
3. **No duplicates** - Each event is truly independent
4. **Accurate timestamps** - Precision validated, not assumed

**Bottom line:** Your backtest results will be trustworthy.

---

## 📝 Best Practices

### Daily Workflow
1. Run `mine_events_professional.py` overnight (scans full history)
2. Morning: Refine spikes and generate research guide
3. Afternoon: Manual research (2-3 hours for ~20 events)
4. Evening: Import, validate, check for duplicates

### Before Every Backtest
```bash
# Quick validation check
python3 scripts/validation/validate_correlation.py
python3 scripts/validation/detect_duplicates.py
```

### Monthly Audit
```bash
# Re-validate entire dataset
python3 scripts/validation/validate_correlation.py
python3 scripts/validation/detect_duplicates.py

# Check for data drift
sqlite3 data/hedgemony.db "
SELECT
    strftime('%Y-%m', timestamp) as month,
    COUNT(*) as events,
    AVG(time_to_impact_seconds) as avg_lag
FROM master_events
GROUP BY month
ORDER BY month DESC
LIMIT 12
"
```

---

## 🚀 Future Enhancements

Potential improvements:
- Auto-retry failed validations with alternative sources
- Machine learning to predict event category automatically
- Real-time validation as events are imported
- Web dashboard for validation results
- Integration with Twitter API for auto-sourcing

---

**Last Updated:** 2026-01-31
**Maintainer:** Event Scraping Skill
**Questions?** See [event_scraping SKILL.md](../../.agent/skills/event_scraping/SKILL.md)
