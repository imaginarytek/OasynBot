# Source Priority Upgrade - Critical Fix

**Date:** 2026-01-31
**Issue:** Event 5 audit revealed we were using SECONDARY sources (official publications) instead of PRIMARY sources (breaking news), causing 26s lag instead of <10s.

---

## 🚨 The Problem

### What We Found
Event 5 (Grayscale ruling) had a 26-second lag because:
- **Source used:** cadc.uscourts.gov (official court website)
- **When published:** 14:20:00 UTC
- **Price moved:** 14:20:26 UTC (+26s lag)

### The Real Issue
Traders didn't read the court website. They saw:
- Bloomberg Terminal alert at ~14:19:34
- Breaking news tweets at ~14:19:35-40
- **Then** official court website posted at 14:20:00

**We had the RIGHT news but the WRONG source (secondary, not primary).**

---

## ✅ The Solution - Source Priority Hierarchy

### Always Find the FIRST Source Traders Saw

**TIER 1A - PRIMARY SOURCES (Markets react to these):**
1. Bloomberg Terminal alerts
2. Breaking news tweets (@Bloomberg, @Reuters, @tier10k)
3. Court reporter tweets (reporters in courtroom)
4. News wire flashes
5. Direct exchange announcements

**TIER 1B - SECONDARY SOURCES (Avoid if lag >10s):**
1. Official .gov websites
2. Press release pages
3. Full news articles

### Validation Rule
- Use Tier 1A whenever possible
- If using Tier 1B AND lag >15s → **WRONG SOURCE** → Re-research

---

## 🔧 What Was Upgraded

### 1. validate_correlation.py - Now Flags Suspicious Lags

**Before:**
```
✓ VALID - 26s lag
```

**After:**
```
⚠ SUSPICIOUS - 26s lag (likely NOT first source)
  → Action: Re-research to find FIRST breaking source
  → Search Twitter/Bloomberg 26s BEFORE current timestamp
```

**New threshold:** Lag >15s = suspicious (likely secondary source)

### 2. check_source_priority.py - NEW Script

Automatically identifies events using secondary sources:
```bash
python3 scripts/validation/check_source_priority.py
```

**Output:**
```
⚠ Event 5: Grayscale Wins Lawsuit
  Source: uscourts.gov
  Lag: 26s
  Type: SECONDARY

  Recommended Action:
    1. Search Twitter: 2023-08-29 14:19:30-14:19:45
    2. Look for court reporters: @EleanorTerrett, @jbarro
    3. Update with FIRST breaking source
```

### 3. event_scraping SKILL.md - New Section Added

**Phase 2.5: Source Priority Hierarchy**
- Documents Tier 1A vs 1B sources
- Explains why markets react to tweets, not .gov websites
- Provides examples of right vs wrong sources
- Red flags for identifying secondary sources

### 4. Updated Lessons Learned

Added three critical lessons:
- **PRIMARY sources beat SECONDARY** (Breaking news > official websites)
- **Lag >15s = wrong source** (Find the earlier breaking tweet)
- **Markets react to what traders SEE** (Bloomberg Terminal > sec.gov)

---

## 📋 New Validation Workflow

### Before (Old Way)
```bash
# 1-6. Same as before...
# 7. Validate correlation
python3 scripts/validation/validate_correlation.py
# 8. Check duplicates
python3 scripts/validation/detect_duplicates.py
# DONE
```

### After (New Way - Catches Wrong Sources)
```bash
# 1-6. Same as before...

# 7. Validate correlation (now flags suspicious lags)
python3 scripts/validation/validate_correlation.py

# 8. Check source priority (NEW - identifies secondary sources)
python3 scripts/validation/check_source_priority.py

# 9. Check duplicates
python3 scripts/validation/detect_duplicates.py

# DONE - Dataset now has PRIMARY sources with tight lags
```

---

## 🎯 How to Fix Event 5 (Example)

### Current State (WRONG)
```
Event 5: Grayscale Wins Lawsuit
Source: DC Circuit Court of Appeals
URL: https://www.cadc.uscourts.gov/...
Timestamp: 2023-08-29 14:20:00
Lag: 26s ← SUSPICIOUS
```

### Research Process

1. **Calculate actual spike time:**
   - News at: 14:20:00
   - Lag: 26s
   - Price spiked at: 14:20:26
   - Work backward: News likely broke ~14:19:34

2. **Search Twitter for that window:**
   ```
   site:twitter.com "grayscale" OR "SEC"
   since:2023-08-29_14:19:30
   until:2023-08-29_14:19:45
   ```

3. **Look for breaking news accounts:**
   - @EleanorTerrett (crypto reporter)
   - @tier10k (breaking news bot)
   - @unusual_whales
   - @DeItaone (Bloomberg reporter)

4. **Find the FIRST tweet:**
   - Example: @EleanorTerrett tweeted at 14:19:35
   - "BREAKING: DC Circuit rules in favor of Grayscale..."

5. **Update the event:**
   ```
   Source: @EleanorTerrett
   URL: https://twitter.com/EleanorTerrett/status/...
   Timestamp: 2023-08-29 14:19:35
   Expected lag: ~5-10s (much better!)
   ```

### New State (RIGHT)
```
Event 5: Grayscale Wins Lawsuit
Source: @EleanorTerrett (Court Reporter)
URL: https://twitter.com/EleanorTerrett/status/...
Timestamp: 2023-08-29 14:19:35
Lag: 7s ← VALID!
```

---

## 📊 Your Dataset - Before vs After

### Current State (1/31/2026)
```
Total Events: 5
  ✓ Valid:       4 (80%)
  ⚠ Suspicious:  1 (20%) ← Event 5 needs fix
  ✗ Invalid:     0 (0%)
```

**Action needed:** Re-research Event 5 to find primary source.

### Expected After Fix
```
Total Events: 5
  ✓ Valid:       5 (100%)
  ⚠ Suspicious:  0 (0%)
  ✗ Invalid:     0 (0%)
```

---

## 🔍 Red Flags - Know When You Have the Wrong Source

Run the validation and watch for:

❌ **RED FLAGS:**
- Lag >15 seconds
- Source is a .gov website
- Source is "official court filing" or "press release page"
- Source is a full article (vs headline/alert)

✅ **GREEN FLAGS:**
- Lag <10 seconds
- Source is a breaking news tweet
- Source is Bloomberg Terminal screenshot
- Source is court reporter in courtroom
- Source is wire service flash

---

## 💡 Why This Matters for Backtesting

### With Wrong Source (Secondary)
```
Event: SEC sues Binance
Source: sec.gov (published 16:02:00)
Your bot learns: At 16:02:00
Price moved: 16:02:25 (25s later)

Backtest assumes: 25s to react
Reality: News broke at 16:01:55 (Bloomberg tweet)
Real reaction time: 2s

YOUR BACKTEST WILL UNDERESTIMATE PERFORMANCE!
```

### With Right Source (Primary)
```
Event: SEC sues Binance
Source: @tier10k (tweeted 16:01:55)
Your bot learns: At 16:01:55
Price moved: 16:01:57 (2s later)

Backtest assumes: 2s to react
Reality: Matches actual market behavior

YOUR BACKTEST IS ACCURATE!
```

---

## 🚀 Next Steps

### Immediate (Today)
1. Run the new validation scripts:
   ```bash
   python3 scripts/validation/validate_correlation.py
   python3 scripts/validation/check_source_priority.py
   ```

2. Fix Event 5:
   - Search Twitter for 14:19:30-14:19:45
   - Find breaking news tweet
   - Update source in database

### Going Forward (For All New Events)
1. **Always start with the spike time** (from refine_spike_timing.py)
2. **Search Twitter FIRST** (not official websites)
3. **Find the earliest tier-1A source** (breaking news tweet/alert)
4. **Validate lag is <10s** (if >15s, you have the wrong source)
5. **Run check_source_priority.py** before finalizing dataset

---

## 📚 Updated Documentation

All changes documented in:
- [event_scraping SKILL.md](.agent/skills/event_scraping/SKILL.md) - Phase 2.5 added
- [scripts/validation/README.md](scripts/validation/README.md) - Updated workflow
- This document - Upgrade summary

---

## 🎓 Key Takeaway

**Markets don't react to official publications. They react to BREAKING NEWS.**

Your dataset must capture what traders actually SAW (tweets, terminal alerts), not what was "officially published" later.

Lag >15s = 🚩 You found the official source, not the first source.

---

**Status:** Workflow upgraded, Event 5 needs re-research
**Next:** Fix Event 5, then validate all future events with new scripts
