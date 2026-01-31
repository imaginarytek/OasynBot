---
name: Event Scraping & Backtesting Data Management
description: Professional methodology for scraping, validating, and managing historical market event data for backtesting trading strategies. Focuses on data quality and realistic lag measurement.
---

# Event Scraping & Backtesting Skill

## Purpose
This skill documents the **professional methodology** for scraping and managing historical market event data for **backtesting purposes only**. It captures hard-won lessons from building high-quality event datasets for strategy validation and testing. 

in theNever edit this file without my script permission.

---

## Core Principles

### 1. **Spike-First Methodology (PROVEN SUPERIOR)**
✅ **DO THIS:**
- Start with abnormal 1hr volatility detection on SOL/USDT (Z-score > 3.0σ)
- Then find the very first tier 1 news source that caused the spike and make sure the time stamp correlates with the spike on the 1 second SOL/USDT chart
- Verify with tier-1 sources
- **KILL SWITCH:** If exact source timestamp is not found or is > 60s after spike, REJECT THE EVENT.
- Use exact timestamps from official announcements

❌ **DON'T DO THIS:**
- Pick "important sounding" events (CPI, FOMC, Jobs)
- Hope they moved the market
- Use approximate timestamps

**Why:** Spike-first found events with 10x better price impact and 98% better coverage of major market moves.

### 1.1 **HOW TO NEVER DO IT BACKWARDS (CRITICAL)**

**🚫 THE #1 MISTAKE - News-First Workflow:**
```
❌ WRONG ORDER:
1. Search for "important news" (SEC lawsuit, etc.)
2. Try to find if it moved the price
3. Hope timestamps match

Problem: You'll pick biased events and miss real market movers
```

**✅ THE ONLY CORRECT WAY - Spike-First Workflow:**
```
✅ CORRECT ORDER:
1. Scan price data → Find Z > 3.0σ spikes
2. Search news at EXACT spike timestamp
3. Add event ONLY if timestamps match (<60s)

Benefit: You find what ACTUALLY moved the market
```

**ENFORCEMENT:**
Use `scripts/spike_first_workflow.py` - this script **PREVENTS** adding events without spikes:
- Step 1: Find spikes (REQUIRED FIRST)
- Step 2: Search news (GUIDED - only for detected spikes)
- Step 3: Add event (VALIDATED - rejects if timestamp >60s from spike)

**Red Flags You're Doing It Wrong:**
- ❌ Starting with Google search for "SOL news 2023"
- ❌ Picking events that "should be important"
- ❌ Adding events without checking price data first
- ❌ Using news timestamps without spike verification

**Why This Matters:**
- News-first = Selection bias (you pick what YOU think is important)
- Spike-first = Market-driven (you pick what MARKET thought was important)
- Backtest needs to prove it can find signals, not that it can memorize your biases

### 2. **Unified Gold Standard (No Hierarchy)**
We do not separate events into "High Impact" vs "Normal" because that creates selection bias. Instead, ALL events in `master_events` must meet the **Unified Gold Standard**: All events must meet the highest data fidelity.
- Time stamps correlate with the spike on the 1 second chart
- 1-second price data (Verified)
- Verbatim Source headline and body text (Immutable)
- **Zero-Sum Validation**: The backtest result is binary.
- **Source of Truth**: The `title` (Headline) and `description` (Body) fields are SACRED.
    - ❌ No internal tags like "(Chart-Verified)".
    - ❌ No summarization.
    - ✅ Exact copy of the News Headline and Tweet/Article text.
- ✅ **Timestamp precision: ±60 seconds**

**Outcome Independence:**
The dataset contains **both** massive market-moving events (5σ spikes) and "avarage movers" (events that didn't move much). This allows the backtester to prove it can ignore noise.

**Junk Filter:**
- If an event does not meet the Gold Standard (e.g., missing 1s data, vague timestamp), it is **rejected entirely**. We do not keep "Archive" or "Level 0" data.

### 3. **Always Use 1-Second Data (SOL/USDT Only)**
✅ **Efficiency Rule:**
- **Step 1:** Use **Hourly** `SOL/USDT` candles to find the spike (very fast to scan 3 years).
- **Step 2:** Only download **1-Second** `SOL/USDT` candles for the specific event window (-5m to +120m).
- **Reason:** Downloading 3 years of 1s data is terabytes. Downloading 300 event windows is megabytes.

✅ **Asset:**
- **SOL/USDT (Binance Spot)** is our primary index.
- Do not mix assets. All backtests run on SOL to ensure comparable volatility baselines. 

### 4. **Material Escalation (Smart De-Clustering)**
Markets often react in stages (Rumor -> Confirmation -> Action). We MUST trade significant escalations, even if related to a previous event.

✅ **The "New Information" Test:**
If a subsequent spike occurs for the *same narrative*, **KEEP IT IF:**
1.  **Fresh Volatility:** It causes a *new, distinct* Z > 3.0 spike (proving the market was surprised again).
2.  **Material Escalation:** The news contains **new facts** or **official confirmation** not present before.
    - *Rumor:* "SEC investigating X" (Tradeable)
    - *Confirmation:* "SEC Officially Files Lawsuit vs X" (**Tradeable Escalation**)
    - *Echo:* "Report: SEC lawsuit details" (Noise -> Discard)

❌ **Discard Stale Echoes:**
- If the headline merely repeats known facts without new action, discard it regardless of price movement (it's likely just liquidity/panic, not a valid signal trigger).

---

## ⛔ CRITICAL: What NOT to Do (BLOCKING REQUIREMENTS)

**BEFORE doing ANY event discovery work, read this section!**

### ❌ DON'T Do Manual Web Searches

**NEVER do these without running the automated workflow first:**

```
❌ DON'T: WebSearch for "Solana news 2024"
   - This is event-first (backwards/wrong)
   - Creates selection bias
   - You'll miss what actually moved the market

✅ DO: Run scripts/preflight_check.py
   - Checks if automation is ready
   - Tells you exactly what to run next
```

### ❌ DON'T Bypass Automation

**These scripts exist for a reason - USE THEM:**

```
❌ DON'T: Manually search for news and create event records
❌ DON'T: Use ChatGPT/web search to find "important events"
❌ DON'T: Add events based on "I remember this happened"
❌ DON'T: Copy summaries from news articles

✅ DO: Follow the enforced workflow:
   1. python3 scripts/preflight_check.py (checks readiness)
   2. python3 scripts/mine_events_professional.py (detects spikes)
   3. python3 scripts/validation/refine_spike_timing.py (exact minute)
   4. python3 scripts/validation/generate_research_guide.py (search links)
   5. Manual research using the guide → fill verified_events_batch.json
   6. python3 scripts/add_events_enforced.py --import (validates & imports)
```

### ❌ DON'T Write Event Descriptions

**Event descriptions must be VERBATIM, not written by you:**

```
❌ DON'T: "The SEC sued Binance for securities violations"
   - This is a summary you wrote
   - Loses emotional tone and exact language
   - Creates hindsight bias

✅ DO: Copy exact text from source (3-4 paragraphs)
   - "The Securities and Exchange Commission today charged..."
   - Word-for-word from Bloomberg/Reuters/CoinDesk
   - Preserves original sentiment for AI analysis
```

### ❌ DON'T Add Events Without spike_id

**The database will REJECT events without spike_id:**

```
❌ DON'T: Manually INSERT INTO master_events
   - Will fail due to database constraint
   - Events must come from hourly_volatility_spikes

✅ DO: Use scripts/add_events_enforced.py
   - Enforces spike_id requirement
   - Validates tier-1 source
   - Checks verbatim text length
   - Prevents duplicates
```

### 🚨 RED FLAG TRIGGERS

**If you find yourself doing ANY of these, STOP immediately:**

1. **About to call WebSearch for historical news?**
   → STOP - Run scripts/preflight_check.py instead

2. **About to create event records manually?**
   → STOP - Use scripts/add_events_enforced.py instead

3. **About to write an event description?**
   → STOP - Copy verbatim text from tier-1 source instead

4. **About to add event "because it's important"?**
   → STOP - Must come from detected spike first

5. **User asks to "find events"?**
   → STOP - Ask: "Should I run the automated spike-first workflow?"

### ✅ CORRECT WORKFLOW CHECKLIST

**Before adding ANY event, ALL must be checked:**

- [ ] Event came from detected spike (has spike_id)
- [ ] Spike timing refined to minute precision
- [ ] Research guide generated and used
- [ ] Tier-1 source found (Bloomberg/Reuters/CoinDesk)
- [ ] Timestamp within ±60 seconds of spike
- [ ] Verbatim text copied (3-4 paragraphs, >200 chars)
- [ ] Used scripts/add_events_enforced.py (NOT manual INSERT)
- [ ] Ran scripts/validation/validate_correlation.py after import

**If ANY checkbox is unchecked → DO NOT ADD THE EVENT**

---

## Event Collection Workflow

**⚠️ MANDATORY PRE-FLIGHT CHECKLIST**
**Before adding ANY event, verify ALL items are ✅:**

```
SPIKE-FIRST VERIFICATION CHECKLIST:

□ Step 1: Price spike detected FIRST (Z > 3.0σ)
  - Tool: scripts/find_2023_spikes.py or scripts/fetch_hourly_history.py
  - Evidence: Spike timestamp recorded from price data

□ Step 2: News found AT spike time (±5 minutes)
  - Search performed at EXACT spike timestamp
  - NOT searched by "important keywords" or "known events"

□ Step 3: Timestamp correlation verified (<60 seconds)
  - News timestamp ≤ 60s from spike timestamp
  - If >60s: EVENT REJECTED (no exceptions)

□ Step 4: Verbatim text obtained
  - Title = Exact headline from source
  - Description = First 3-4 paragraphs, word-for-word
  - No AI summaries, no paraphrasing

□ Step 5: Source priority verified
  - PRIMARY source (breaking tweet/headline) found
  - NOT secondary source (official press release hours later)

If ANY checkbox is unchecked → DO NOT ADD THE EVENT
Use scripts/spike_first_workflow.py to enforce this automatically
```

### Phase 1: Volatility Detection
```python
# Detect hourly spikes
1. Fetch hourly OHLCV data
2. Calculate returns: (close - open) / open
3. Calculate volatility Z-scores
4. Flag spikes where Z > 3.0σ
5. Store in hourly_volatility_spikes table
```

### Phase 2: Chart-Guided Sourcing (The Valid Way)
**❌ OLD WAY (Wrong):** Find an article -> Use its timestamp -> Hope it matches.
**✅ NEW WAY (Chart-First):** Find the Crash Time -> Find the Tweet at that exact minute.

**CRITICAL RULE: Zero-Trust Provenance**
If you cannot find a URL with a timestamp $\le$ Spike Time:
*   **REJECT THE EVENT.**
*   Do not guess. Do not assume "it must be this."
*   Better to have 10 perfect events than 50 verified + 1 fake.

**Step-by-Step:**
1.  **Pinpoint the Crash:** Look at the 1-minute chart.
    *   *Example:* "The candle opened at 16:02 and dropped 4%."
    *   *Target Time:* **16:01:00 - 16:03:00 UTC**.
2.  **The Dragnet:** Search Twitter/X and Terminals for *that specific minute*.
    *   `verify "binance" since:2023-06-05_16:01:00 until:2023-06-05_16:03:00`
3.  **The Match:** matching source MUST be within **60 seconds** of the candle start.
    *   *Found:* "@SEC_News: We charged Binance" at **16:02:14**.
    *   *Verdict:* **PERFECT MATCH.** Update Master Record.

**Note:** If your "Source" is at 15:00 but the market moved at 16:02, **YOU FOUND THE WRONG SOURCE.** Keep looking (it might be the *tweet* of the article, not the article itself).

### Phase 2.5: Source Priority Hierarchy (CRITICAL)

**Problem:** Markets don't react to official publications. They react to BREAKING NEWS.

If you use "sec.gov press release published 16:02:00" as your source but price moved at 16:01:58, traders didn't read the SEC website - they saw a Bloomberg tweet at 16:01:56!

**The "First Source" Rule:**
Find the VERY FIRST place the market learned about the news, not the "official" source.

**Source Priority Hierarchy (Use in this order):**

✅ **TIER 1A - PRIMARY SOURCES (Markets react to these):**
1.  **Bloomberg Terminal Alerts** - Professional traders see these FIRST
2.  **Breaking News Tweets** - @Bloomberg, @Reuters, @DeItaone, @tier10k
3.  **Court Reporter Tweets** - Reporters IN the courtroom: @jbarro, @EleanorTerrett, @KatieGrfeld
4.  **News Wire Flashes** - Reuters/Bloomberg News (before article)
5.  **Exchange Announcements** - Direct from Binance, Coinbase, etc.

⚠️ **TIER 1B - SECONDARY SOURCES (Use only if lag <10s):**
1.  **Official Websites** - sec.gov, uscourts.gov, federalregister.gov
2.  **Press Release Pages** - Company websites, court dockets
3.  **News Articles** - Full articles published after headlines

**Validation Rule:**
-   If you use a Tier 1B source AND lag >15s → **WRONG SOURCE**
-   Re-research to find the Tier 1A source (likely a tweet 15-30s earlier)

**Example - Right vs Wrong:**

❌ **WRONG (Secondary Source):**
```
Event: SEC sues Binance
Source: https://www.sec.gov/news/press-release/2023-101
Timestamp: 2023-06-05 16:02:00
Lag: 25 seconds (price moved at 16:02:25)
Problem: Traders didn't wait for sec.gov to update!
```

✅ **RIGHT (Primary Source):**
```
Event: SEC sues Binance
Source: @tier10k (Breaking news tweet)
Timestamp: 2023-06-05 16:01:58
Lag: 2 seconds (price moved at 16:02:00)
Why: This is what traders actually saw first!
```

**How to Find the Primary Source:**
1.  Look at your spike time: `16:02:00`
2.  Search Twitter 2 minutes BEFORE: `16:00:00 - 16:02:00`
3.  Find the FIRST tier-1A account to tweet it
4.  That's your source (lag should be <10s)
5.  Official publication comes later (don't use it!)

**Red Flags You Have the Wrong Source:**
-   ❌ Lag >15 seconds
-   ❌ Source is a .gov website
-   ❌ Source is "official court filing"
-   ❌ Source is a full news article (vs headline/alert)

### Phase 3: Automated Correlation (Remaining)
```python
# For medium-impact spikes
1. Use heuristics (FOMC dates, CPI schedule, etc.)
2. Assign confidence scores
3. Flag for manual verification if high-value
```

### Phase 4: Dataset Building
```python
# Fetch 1-second price data
1. For each verified event
2. Fetch 1s data: event_time - 5min → event_time + 120min
3. Calculate moves: 5s, 30s, 5m, 30m, 1hr, 3hr
4. Store in master_events table
```

---

## Automated Validation Workflow (NEW)

**Problem:** The original workflow relied on manual diligence with no automated safeguards. This created risks of bad data contaminating the backtest dataset.

**Solution:** A suite of validation scripts that enforce the gold standard automatically.

### Improved Workflow with Validation Scripts

```
Phase 1: Volatility Detection
├─ Script: mine_events_professional.py
├─ Detects hourly spikes (Z > 3.0σ)
└─ Output: potential_event_spikes table

Phase 1.5: Spike Refinement (NEW)
├─ Script: scripts/validation/refine_spike_timing.py
├─ Fetches 1-minute candles for each spike hour
├─ Identifies exact minute with highest volatility
├─ Updates potential_event_spikes with refined_timestamp
└─ Output: Exact spike times (not just hourly windows)

Phase 2: Research Guide Generation (NEW)
├─ Script: scripts/validation/generate_research_guide.py
├─ Creates markdown guide with pre-filled search links
├─ Generates Twitter/Google News URLs for exact spike minute
├─ Provides JSON template for verified events
└─ Output: data/research_guide.md + data/verified_events_template.json

Phase 3: Manual Research (Guided)
├─ Use research_guide.md to find tier-1 sources
├─ Verify timestamp within ±60s of spike
├─ Copy verbatim headline and body text
├─ Measure time_to_impact from chart
└─ Fill in verified_events_batch.json

Phase 4: Event Import
├─ Script: scripts/import_new_events_json.py
├─ Validates basic requirements
├─ Adds events to master_events (without price data yet)
└─ Output: Events in database, ready for price data fetch

Phase 5: Price Data Collection
├─ Script: scripts/build_verified_dataset.py
├─ Fetches 1s data from Binance (-5m to +120m window)
├─ Calculates impact metrics (5s, 30s, 5m, 30m, 1h)
└─ Output: master_events with sol_price_data populated

Phase 6: Correlation Validation (NEW - CRITICAL)
├─ Script: scripts/validation/validate_correlation.py
├─ Measures time from news to actual price movement
├─ Validates lag is within -10s to +60s
├─ Flags invalid events (correlation failures)
├─ Updates time_to_impact_seconds field
└─ Output: Validation report + updated database

Phase 7: Source Priority Check (NEW - CRITICAL)
├─ Script: scripts/validation/check_source_priority.py
├─ Identifies events using SECONDARY sources (official .gov sites)
├─ Flags events where lag >15s (likely wrong source)
├─ Recommends finding PRIMARY sources (breaking tweets/alerts)
└─ Output: Source priority analysis report

Phase 8: Duplicate Detection (NEW)
├─ Script: scripts/validation/detect_duplicates.py
├─ Finds events within 24h with similar titles
├─ Applies Material Escalation logic
├─ Checks if both events caused distinct spikes
├─ Recommends which to keep vs remove
└─ Output: Duplicate analysis report

Phase 9: Verbatim Text Validation (NEW - CRITICAL FOR AI)
├─ Script: scripts/validation/validate_verbatim_text.py
├─ Ensures descriptions are verbatim from source (not summaries)
├─ Detects journalism language red flags
├─ Validates proper length for source type
├─ Flags paraphrased or AI-generated content
└─ Output: Verbatim text validation report
```

### Quick Reference: Validation Commands

```bash
# Complete workflow from spike detection to validated dataset:

# 1. Detect hourly spikes
python3 scripts/mine_events_professional.py

# 2. Refine to exact minutes (NEW)
python3 scripts/validation/refine_spike_timing.py

# 3. Generate research guide (NEW)
python3 scripts/validation/generate_research_guide.py

# 4. Manual research (use data/research_guide.md)
# ... fill in verified_events_batch.json ...

# 5. Import verified events
python3 scripts/import_new_events_json.py

# 6. Fetch price data
python3 scripts/build_verified_dataset.py

# 7. Validate correlation (NEW - RUN BEFORE BACKTESTING)
python3 scripts/validation/validate_correlation.py

# 8. Check source priority (NEW - Finds secondary sources)
python3 scripts/validation/check_source_priority.py

# 9. Check for duplicates (NEW)
python3 scripts/validation/detect_duplicates.py

# 10. Validate verbatim text (NEW - CRITICAL FOR AI)
python3 scripts/validation/validate_verbatim_text.py
```

### Validation Standards (Automated Enforcement)

**validate_correlation.py enforces:**
- ✅ Price must move >0.1% to count as impact
- ✅ News->Price lag must be -10s to +60s
- ✅ Events outside this range are flagged INVALID
- ✅ time_to_impact_seconds is calculated and stored
- ✅ Report shows which events passed/failed

**check_source_priority.py enforces:**
- ✅ Source must be PRIMARY (breaking news) not SECONDARY (official .gov)
- ✅ Lag >15s triggers source review
- ✅ Identifies events using wrong source type
- ✅ Recommends Twitter/Bloomberg search for first source

**detect_duplicates.py enforces:**
- ✅ Material Escalation: Each event must cause distinct Z>3 spike
- ✅ Content Analysis: Later event must contain NEW information
- ✅ De-duplication: Similar titles within 24h are flagged
- ✅ Recommendations: Keep both / Review / Remove weak

**validate_verbatim_text.py enforces:**
- ✅ Description must be verbatim from source (no summaries)
- ✅ No journalism language ("according to", "reported that")
- ✅ Proper length for source type (press releases >400 chars)
- ✅ Preserves exact emotional tone and vocabulary
- ✅ CRITICAL: AI "brain" needs exact raw input traders saw

**Benefits:**
1. **Prevents bad data** - Invalid events are caught before backtesting
2. **Saves time** - Research guide makes manual work 10x faster
3. **Enforces standards** - No reliance on human memory
4. **Reproducible** - Same validation logic every time
5. **Audit trail** - Validation reports document quality

---

## Database Schema

### master_events (Backtesting Dataset)
```sql
CREATE TABLE master_events (
    -- Event Information
    title TEXT NOT NULL,
    description TEXT,
    timestamp TEXT NOT NULL,  -- ISO format with timezone
    source TEXT,              -- @username or news outlet
    source_url TEXT,
    category TEXT,            -- Crypto/Regulatory/Political/Other
    
    -- Quality Metadata
    -- unified_gold_standard (Implicit: all events here are verified standard)
    quality_level INTEGER,    -- DEPRECATED: Retained for compatibility (set to 1 for all)
    methodology TEXT,         -- 'event-first' or 'spike-first'
    verified BOOLEAN,
    timestamp_precision TEXT, -- 'hour', 'minute', 'second'
    
    -- Price Data (1-second resolution)
    sol_price_data TEXT,      -- JSON array of OHLCV
    
    -- Price Impact Metrics
    move_5s REAL,
    move_30s REAL,
    move_5m REAL,
    move_30m REAL,
    move_4hr REAL,
    volatility_z_score REAL,
    time_to_impact_seconds INTEGER,  -- Measured lag from news to >0.1% price move (validation only, NOT used for execution)
    
    -- Tracking
    impact_score INTEGER,
    tradeable BOOLEAN DEFAULT 1,
    date_added TEXT,
    last_updated TEXT,
    
    UNIQUE(title, timestamp)
);
```

---

### Phase 2: Manual Verification & Source Capture (Top 20)
```python
# For highest-impact spikes
1. Generate research guide with search links
2. Search Twitter, Google News for tier-1 sources
3. Find exact announcement timestamp
4. Verify event category (Crypto/Regulatory/Political/Other)
5. **Capture verbatim headline (exact text from source)**
6. **Capture BODY TEXT exactly as written.**
   - ❌ NO Summarization.
   - ❌ NO "Cleaning" or Grammar Fixing.
   - ✅ Copy/Paste exact characters (including typos).
   - This is the "Raw Input" for the AI Brain.
7. **Save source URL for verification**
8. Document all findings in import_manual_findings.py
```
*Note: We accept events regardless of their price impact (High or Low) as long as the data fidelity is perfect.*

---

## Source Content Capture Standards

### Why Detailed Verbatim Text is Critical
To validly backtest AI strategies, we must feed the "brain" the **exact raw input** the market first reacted to, not a human summary written after the fact.
- **LLM Context:** 3-4 paragraphs allow models to detect crucial nuance (e.g., "aggressive rate hike" vs "gradual adjustment").
- **Avoid Hindsight Bias:** Summaries written later often unknowingly include market outcomes. We need the text *as it appeared* at the moment of impact.
- **Sentiment Accuracy:** AI models need the original emotional vocabulary (e.g., "grave concern," "unprecedented," "robust") to score sentiment correctly.

### Capture Requirements
1.  **Headline:** Copy the **exact** title from the press release or tweet.
    *   ❌ *Bad:* "Fed raises rates by 25bps" (Summary)
    *   ✅ *Good:* "Federal Reserve issues FOMC statement: Committee decides to raise the target range for the federal funds rate to 5-1/4 to 5-1/2 percent" (Verbatim)
2.  **Body Text:** Copy-paste the first **3-4 paragraphs verbatim**.
    *   **Do NOT** summarize.
    *   **Do NOT** rewrite.
    *   Include "Key Takeaways" bullet points if present in the source.

---

### Timestamp Precision Best Practices
**Rule:** The Timestamp in `master_events` is the **News Source Time** (T=0), not the Market Move Time.
*   However, T=0 and Price Move MUST be < 60s apart.
*   If they are > 60s apart, you likely have the wrong T=0.

**Finding Exact Announcement Times:**
1.  **Twitter (The Standard):** News breaks on X first. Search simple keywords during the *exact spike minute*.
2.  **Press Releases:** Often published *after* the headlines hit the terminal. Be careful.
3.  **Terminal Headlines:** If you can find a screenshot of a Bloomberg Terminal headline, use THAT timestamp.

**Refinement Protocol:**
1.  See Price Spike at `HH:MM`.
2.  Search `since:HH:MM-2m until:HH:MM+2m`.
3.  Lock in the *first* Tier 1 account to tweet it. That is T=0.

---

## Dataset Integrity & Bias Prevention

To strictly prevent "cheating" where backtests use future data, we enforce a **Bias Prevention Protocol** during dataset creation.

### 1. `validate_no_lookahead_bias()` Verification
Every event added to `master_events` must pass these logical checks:
- **Causality Check:** `entry_time > signal_time`. You cannot buy before the signal exists.
- **Data Availability Check:** Signal generation must only use data from `timestamp < signal_time`. (e.g., cannot use the "close" of the current unfinished candle).

### 2. Physical Impossibility Filters
We flag and reject events that violate physical constraints:
- **Pre-Event Execution:** Any trade where `execution_time < event_timestamp` is flagged as an error.
- **Zero-Latency Trades:** Any trade assuming 0ms lag is rejected. We enforce `execution_time >= event_timestamp + measured_execution_lag_seconds`.

### 3. Bias Reporting
The dataset generation process produces a bias report. **WARNING: BIAS DETECTED** alerts will trigger if:
- Trades execute before signal generation.
- Latency assumptions violate the measured lag.

**Why This Matters:**
In high-frequency news trading, a 15-second difference between "actual news time" and "bot entry time" is the difference between profit and loss. We validate this during *dataset creation* so the backtester never even sees "impossible" profitable trades.

---

## Price Impact Calculation

### Standard Metrics
```python
# From 1-second data
start_price = price_data[0]['close']

# 5-second move
move_5s = abs((price_data[4]['close'] - start_price) / start_price * 100)

# 30-second move  
move_30s = abs((price_data[29]['close'] - start_price) / start_price * 100)

# 5-minute move (300 seconds)
move_5m = abs((price_data[299]['close'] - start_price) / start_price * 100)

# 30-minute move (1800 seconds)
move_30m = abs((price_data[1799]['close'] - start_price) / start_price * 100)
```

### Diagnostic Metric: Time-To-Impact (QA Only)
We calculate this **ONLY** to verify the event is valid (causal). We **DO NOT** use it to delay execution.

```python
def check_causality(price_data, event_timestamp):
    # If price didn't move within 60s, this event is a dud/mis-timed.
    time_to_impact = measure_move_start(price_data)
    if time_to_impact > 60:
         return "REJECT: Market too slow (Non-causal)"
    return f"VALID: Impact at T+{time_to_impact}s"
```

✅ **Execution Standard: Fixed System Latency**
For backtesting, we assume a **Fixed System Latency** (e.g. 1000ms).
- **News Time:** T=0
- **Execution:** T+1s (regardless of when the market moved).
- **Reason:** Testing "Can I react fast enough?" is better than testing "Did I wait long enough?"

---

## Event Categories & Examples

### Crypto-Specific Events (Highest Impact)
- Exchange announcements (FTX repayments, Binance listings)
- Protocol updates (network upgrades, hard forks)
- Institutional news (CME futures, ETF filings)
- Liquidation cascades
- **Example:** FTX Repayment Announcement (13.80σ, +10.24% hourly)

### Regulatory Events (High Impact)
- Central bank decisions (BOJ rate hikes, Fed pivots)
- SEC announcements (ETF approvals, enforcement actions)
- Government policy (crypto reserves, bans)
- **Example:** BOJ Rate Hike + Carry Trade Unwind (12.75σ, +9.55% hourly)

### Political Events (Medium Impact)
- Elections (Trump inauguration)
- Executive orders
- Congressional hearings
- **Example:** Trump Inauguration Selloff (9.35σ, -8.12% hourly)

### Scheduled Data Releases (Low Impact)
- CPI reports
- Jobs reports
- FOMC meetings (unless surprise)
- **Note:** Often already priced in, weak immediate impact

---

## Common Pitfalls & Solutions

### Pitfall 1: Trusting Article Timestamps
**Problem:** "Article published at 15:00" -> Market crashed at 16:02. Why? 
**Reality:** The article was a summary published *an hour before* the actual filing, OR the article was back-dated/updated.
**Solution:** IGNORE article times. Trust the **Minute of Impact** and find the source that matches it (usually a Tweet or Wire Flash).
**Impact:** Eliminates "Phantom Lag" of 60 minutes.

### Pitfall 2: Event-First Selection Bias
**Problem:** Picking events that "sound important" misses actual market movers  
**Solution:** Start with volatility spikes, then find the cause  
**Impact:** 98% better coverage of major moves

### Pitfall 3: Settling for 1-Minute Data
**Problem:** Can't measure true immediate impact  
**Solution:** Always use Binance Spot API with 1-second resolution  
**Impact:** 60x better time precision

### Pitfall 4: Ignoring Duplicates Across Datasets
**Problem:** Same event in multiple tables with different quality  
**Solution:** Use master_events with quality_level priority  
**Impact:** Clean, deduplicated dataset

### Pitfall 5: Assuming Execution Lag Instead of Measuring It
**Problem:** Backtests assume arbitrary lag (e.g., 15 seconds) without measuring actual price movement
**Solution:** Measure when price actually started moving (0.1% threshold detection)
**Impact:** Honest, data-driven performance expectations (measured lag varies: 2-45 seconds per event)

### Pitfall 6: Using Summarized Text Instead of Verbatim Source
**Problem:** Event descriptions contain paraphrased summaries or AI-generated content instead of exact source text
**Reality:** AI models need the EXACT emotional vocabulary, tone, and phrasing from the original source to make accurate trading decisions. Summaries lose subtle sentiment signals and introduce hindsight bias.
**Solution:** Always copy-paste first 3-4 paragraphs VERBATIM from the source. Use `validate_verbatim_text.py` to catch paraphrasing.
**Impact:** Your bot's "brain" gets the same raw input traders actually saw, not a sanitized summary written after the fact.

---

## Scripts & Tools

### Core Scripts (Data Collection)
- `scripts/mine_events_professional.py` - Detect hourly volatility spikes (Z > 3.0σ)
- `scripts/import_new_events_json.py` - Import verified events from JSON
- `scripts/build_verified_dataset.py` - Fetch 1s price data from Binance
- `scripts/create_master_events.py` - Initialize master_events table

### Validation Scripts (NEW - Quality Enforcement)
- `scripts/validation/refine_spike_timing.py` - Narrow hourly spikes to exact minute
- `scripts/validation/generate_research_guide.py` - Create research guide with search links
- `scripts/validation/validate_correlation.py` - **CRITICAL** - Verify news timestamp correlates with price spike (flags lag >15s as suspicious)
- `scripts/validation/check_source_priority.py` - **CRITICAL** - Identify secondary sources that should be replaced with primary breaking news
- `scripts/validation/validate_verbatim_text.py` - **CRITICAL FOR AI** - Ensure descriptions are verbatim from source (no summaries/paraphrasing)
- `scripts/validation/detect_duplicates.py` - Find related events and apply Material Escalation logic
- `scripts/validation/analyze_event_timing.py` - Deep dive second-by-second price analysis for debugging
- `scripts/validation/test_new_timestamp.py` - Test how different timestamps affect lag calculation

### Research Tools
- `data/research_guide.md` - Auto-generated research guide with pre-filled search links
- `data/verified_events_template.json` - Template for manual event entry
- Twitter Advanced Search (links generated automatically)
- Google News date filters (links generated automatically)
- Binance charts for visual verification

---

## Future Enhancements

### Short-term
1. ~~Timestamp refinement automation~~ ✅ **COMPLETED** (refine_spike_timing.py)
2. ~~Automated correlation validation~~ ✅ **COMPLETED** (validate_correlation.py)
3. ~~Duplicate detection~~ ✅ **COMPLETED** (detect_duplicates.py)
4. Real-time spike detection
5. Quarterly dataset audits

### Long-term
1. Bloomberg Terminal integration for tier-1 sources
2. Twitter API real-time monitoring (auto-capture breaking news)
3. Machine learning event classification (auto-categorize Crypto/Regulatory/Political)
4. Sub-second WebSocket data for ultra-precise timing
5. Automated news correlation using NLP similarity matching

---

## Success Metrics

### Dataset Quality
- ✅ 80%+ events with >2% 5-minute move
- ✅ 100% with 1-second price data
- ✅ Timestamp precision ±60 seconds

### Coverage
- ✅ 100% of Z>5.0σ spikes verified
- ✅ 50-100 backtest-ready events
- ✅ Monthly updates with new historical events

---

## Quick Reference Commands

```bash
# COMPLETE WORKFLOW (Recommended Order):

# 1. Detect hourly spikes
python3 scripts/mine_events_professional.py

# 2. Refine to exact minutes
python3 scripts/validation/refine_spike_timing.py

# 3. Generate research guide
python3 scripts/validation/generate_research_guide.py
# (Then manually research events using data/research_guide.md)

# 4. Import verified events
python3 scripts/import_new_events_json.py

# 5. Fetch 1s price data
python3 scripts/build_verified_dataset.py

# 6. Validate correlation (CRITICAL - run before backtesting!)
python3 scripts/validation/validate_correlation.py

# 7. Check source priority (CRITICAL - identifies secondary sources)
python3 scripts/validation/check_source_priority.py

# 8. Validate verbatim text (CRITICAL FOR AI - ensures exact source text)
python3 scripts/validation/validate_verbatim_text.py

# 9. Check for duplicates
python3 scripts/validation/detect_duplicates.py

# Query validated events
sqlite3 data/hedgemony.db "SELECT id, title, timestamp, time_to_impact_seconds FROM master_events"
```

---

## Lessons Learned Summary

1. **Spike-first beats event-first** (10x better impact, 98% better coverage)
2. **1-second data is accessible** (Binance Spot API, free tier sufficient)
3. **Timestamp precision matters** (±60s vs ±60min = 5-10x better moves)
4. **Not all "important" events move markets** (CPI often weak, exchange news strong)
5. **Measure lag, don't assume it** (Actual lag varies 2-45s per event, measured from price data)
6. **Quality over quantity** (10 perfect events > 100 mixed-quality events)
7. **Automation prevents errors** (Validation scripts catch bad data before backtesting)
8. **Hourly → Minute refinement is essential** (Can't find news without exact spike minute)
9. **Manual research needs tooling** (Research guide makes workflow 10x faster)
10. **Continuous validation** (Run validate_correlation.py before every backtest)
11. **PRIMARY sources beat SECONDARY** (Breaking news tweets/terminal alerts, NOT official .gov websites)
12. **Lag >15s = wrong source** (If official source has long lag, find the earlier breaking tweet)
13. **Markets react to what traders SEE** (Bloomberg Terminal > sec.gov, always find the first public source)
14. **VERBATIM text is critical for AI analysis** (Exact emotional vocabulary matters - summaries lose sentiment signals)
15. **Paraphrasing introduces hindsight bias** (Summaries written after the fact unknowingly include outcomes)
16. **Always validate verbatim text** (Use validate_verbatim_text.py to catch journalism language red flags)

---

**Last Updated:** 2026-01-31
**Status:** Production-ready methodology with automated validation
**Next Review:** 2026-04-30
