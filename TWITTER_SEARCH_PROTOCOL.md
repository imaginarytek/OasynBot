# Twitter/X Search Protocol for Spike-First Event Validation

## Purpose
This protocol guides you through finding the EXACT news source (with timestamp) that caused each price spike.

## Why Twitter/X?
- ✅ **Precise timestamps** (down to the second)
- ✅ **Breaking news first** (faster than official press releases)
- ✅ **Tier-1 sources** verified accounts (@Bloomberg, @Reuters, @SEC_News)
- ✅ **Verbatim text** (original headlines/announcements)

---

## Step-by-Step Process

### Step 1: Get Spike Timestamp from Price Data
**Already done:** Run `scripts/find_2023_spikes.py`

Example output:
```
1. 2023-07-14 10:00 UTC | Z=15.64σ | +12.84% UP
2. 2023-06-10 14:00 UTC | Z=12.71σ | -10.56% DOWN
3. 2023-06-06 01:00 UTC | Z=8.58σ  | -7.35% DOWN
```

### Step 2: Convert to Twitter Search Window
**Critical:** Search ±5 minutes from spike time

Example for Spike #1 (July 14, 2023 10:00 UTC):
- Start: 2023-07-14 09:55:00 UTC
- End: 2023-07-14 10:05:00 UTC

### Step 3: Build Twitter Advanced Search Query

**Template:**
```
(Solana OR SOL OR crypto OR Bitcoin OR BTC OR ETH OR Ethereum OR XRP OR Ripple)
since:YYYY-MM-DD_HH:MM:SS_UTC
until:YYYY-MM-DD_HH:MM:SS_UTC
```

**For Spike #1:**
```
(Solana OR SOL OR crypto OR Bitcoin OR BTC OR ETH OR Ethereum)
since:2023-07-14_09:55:00_UTC
until:2023-07-14_10:05:00_UTC
```

**Access Twitter Advanced Search:**
1. Go to: https://twitter.com/search-advanced
2. OR build URL manually:
   ```
   https://twitter.com/search?q=YOUR_QUERY&src=typed_query&f=live
   ```

### Step 4: Filter by Tier-1 Sources

**Add to query to filter by source:**
```
from:Bloomberg OR from:Reuters OR from:WSJ OR from:CoinDesk OR from:SEC_News OR from:SECGov
```

**Full query example:**
```
(Solana OR SOL OR crypto OR XRP OR Ripple)
(from:Bloomberg OR from:Reuters OR from:CoinDesk)
since:2023-07-14_09:55:00_UTC
until:2023-07-14_10:05:00_UTC
```

### Step 5: Identify THE FIRST Breaking Tweet

**Look for:**
- ✅ Earliest timestamp in the window
- ✅ Tier-1 verified source
- ✅ Breaking news language ("BREAKING:", "JUST IN:")
- ✅ Contains actual news (not commentary)

**Example of GOOD source:**
```
@Bloomberg - Jul 14, 2023 · 9:58 AM UTC
BREAKING: Judge rules Ripple's XRP token sales on exchanges
do not constitute investment contracts - court document
```

**Example of BAD source:**
```
@RandomCryptoGuy - Jul 14, 2023 · 10:02 AM
Wow SOL pumping hard! Must be the XRP news 🚀
```
(This is commentary, not the source)

### Step 6: Verify Timestamp Correlation

**CRITICAL RULE: News timestamp MUST be ≤60 seconds from spike**

Example verification:
- Spike time: 2023-07-14 10:00:00 UTC
- Tweet time: 2023-07-14 09:58:14 UTC
- Difference: 106 seconds **❌ REJECT** (>60s)

VS

- Spike time: 2023-07-14 10:00:00 UTC
- Tweet time: 2023-07-14 09:59:45 UTC
- Difference: 15 seconds **✅ VALID** (<60s)

### Step 7: Extract Verbatim Text

**Get the EXACT tweet text:**
1. Open tweet in browser
2. Copy full text (no paraphrasing!)
3. Note: Title = first line/headline
4. Description = full tweet text

**Example:**
```json
{
  "title": "Judge rules Ripple's XRP token sales on exchanges do not constitute investment contracts",
  "description": "BREAKING: Judge rules Ripple's XRP token sales on exchanges do not constitute investment contracts - court document. The decision is a partial victory for Ripple in its case against the SEC.",
  "source": "Bloomberg",
  "source_url": "https://twitter.com/Bloomberg/status/1234567890",
  "timestamp": "2023-07-14T09:59:45Z"
}
```

### Step 8: Cross-Reference with Original Source (If Needed)

**If tweet links to article:**
1. Check article timestamp
2. Use WHICHEVER came first:
   - Bloomberg tweet @ 9:59 AM
   - Bloomberg article @ 10:02 AM
   → Use tweet (earlier = closer to spike)

---

## Complete Search Queries for Top 5 Spikes

### Spike #1: July 14, 2023 10:00 UTC (+12.84%)

**Twitter Search:**
```
(Solana OR SOL OR crypto OR XRP OR Ripple OR SEC OR court OR ruling)
(from:Bloomberg OR from:Reuters OR from:CoinDesk OR from:WSJ)
since:2023-07-14_09:55:00_UTC
until:2023-07-14_10:05:00_UTC
```

**Direct URL:**
```
https://twitter.com/search?q=(Solana%20OR%20SOL%20OR%20crypto%20OR%20XRP)%20(from%3ABloomberg%20OR%20from%3AReuters)%20since%3A2023-07-14_09%3A55%3A00_UTC%20until%3A2023-07-14_10%3A05%3A00_UTC&f=live
```

### Spike #2: June 10, 2023 14:00 UTC (-10.56%)

**Twitter Search:**
```
(Solana OR SOL OR crypto OR SEC OR Coinbase OR Binance)
(from:Bloomberg OR from:Reuters OR from:CoinDesk OR from:WSJ)
since:2023-06-10_13:55:00_UTC
until:2023-06-10_14:05:00_UTC
```

### Spike #3: June 6, 2023 01:00 UTC (-7.35%)

**Note:** 01:00 UTC = June 5 21:00 EDT (9 PM Eastern)

**Twitter Search:**
```
(Solana OR SOL OR crypto OR SEC OR Binance OR lawsuit)
(from:Bloomberg OR from:Reuters OR from:CoinDesk OR from:SEC_News)
since:2023-06-06_00:55:00_UTC
until:2023-06-06_01:05:00_UTC
```

**Alternative (June 5 evening EDT):**
```
(Solana OR SOL OR crypto OR SEC OR Binance)
(from:Bloomberg OR from:Reuters OR from:CoinDesk)
since:2023-06-05_20:55:00_UTC
until:2023-06-05_21:05:00_UTC
```

### Spike #4: October 24, 2023 08:00 UTC (+8.00%)

**Twitter Search:**
```
(Solana OR SOL OR crypto OR Bitcoin OR BTC)
(from:Bloomberg OR from:Reuters OR from:CoinDesk OR from:WSJ)
since:2023-10-24_07:55:00_UTC
until:2023-10-24_08:05:00_UTC
```

### Spike #5: November 2, 2023 03:00 UTC (+7.81%)

**Twitter Search:**
```
(Solana OR SOL OR crypto OR Bitcoin OR BTC)
(from:Bloomberg OR from:Reuters OR from:CoinDesk OR from:WSJ)
since:2023-11-02_02:55:00_UTC
until:2023-11-02_03:05:00_UTC
```

---

## Tier-1 Source Priority (Use This Order)

**PRIMARY SOURCES (BEST - Breaking News First):**
1. @Bloomberg
2. @Reuters
3. @WSJ
4. @CoinDesk
5. @SEC_News / @SECGov (official)

**SECONDARY SOURCES (If primary not found):**
6. @CNBC
7. @FT (Financial Times)
8. @TheBlock__
9. @Cointelegraph

**DO NOT USE:**
- ❌ Random crypto influencers
- ❌ Aggregator bots
- ❌ Commentary accounts
- ❌ Price alert bots

---

## Validation Checklist

Before adding ANY event, verify:

- [ ] Spike detected in price data FIRST (Z > 3.0σ)
- [ ] Twitter search performed at EXACT spike time (±5 min)
- [ ] Tier-1 source found (Bloomberg, Reuters, etc.)
- [ ] Tweet timestamp ≤60s from spike timestamp
- [ ] Verbatim text extracted (no AI summary)
- [ ] Source URL recorded (tweet link)

If ANY checkbox unchecked → REJECT THE EVENT

---

## Pro Tips

**Tip 1: Check Multiple Accounts**
Bloomberg may tweet before Bloomberg Crypto - check both

**Tip 2: Look for Retweets**
If Bloomberg retweeted @SEC_News, the SEC tweet is the PRIMARY source

**Tip 3: Time Zone Awareness**
Twitter shows local time by default - always convert to UTC

**Tip 4: Use Twitter Bookmarks**
Bookmark valid tweets for easy reference later

**Tip 5: Archive Tweets**
Use archive.org or screenshot in case tweet is deleted

---

## After Finding Valid Tweet

**Next steps:**
1. Record in `data/spike_news_matches.json`
2. Download 1-second price data for event window
3. Run `scripts/spike_first_workflow.py` to add event
4. Validate with `scripts/validation/validate_correlation.py`

---

## Example: Complete Workflow

**Spike Found:**
```
2023-07-14 10:00 UTC | +12.84% | Z=15.64σ
```

**Twitter Search:**
- Window: 09:55 - 10:05 UTC
- Found: @Bloomberg tweet at 09:59:45 UTC
- Content: "BREAKING: Ripple wins partial victory vs SEC"
- Correlation: 15 seconds ✅

**Validation:**
```python
spike_time = datetime(2023, 7, 14, 10, 0, 0, tzinfo=timezone.utc)
tweet_time = datetime(2023, 7, 14, 9, 59, 45, tzinfo=timezone.utc)
diff = (spike_time - tweet_time).total_seconds()
# diff = 15 seconds ✅ VALID (<60s)
```

**Add Event:**
```bash
python3 scripts/spike_first_workflow.py
# Step 3: Add validated event
# Provide spike timestamp, tweet timestamp, verbatim text
```

---

## Troubleshooting

**Problem:** No tweets found in window
**Solution:** Expand search window to ±10 minutes, then verify timestamp carefully

**Problem:** Multiple tweets at same time
**Solution:** Use earliest tier-1 source

**Problem:** Tweet is deleted
**Solution:** Search news archives, check archive.org

**Problem:** Timestamp exactly 60 seconds
**Solution:** REJECT (must be <60s, not ≤60s)

---

**Last Updated:** 2026-01-31
**Status:** Mandatory protocol for all spike-first event validation
