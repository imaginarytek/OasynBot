# Event Research Guide - Updated for 2024-2026 Database

**Generated:** 2026-01-31
**Total Spikes to Research:** 20 (Top Z-scores from 2024-2026 only)
**Database Date Range:** January 2024 - January 2026

---

## Progress Summary

**Events Found with Tier-1 Sources: 7/20 (35%)**
**Events Pending Research: 13/20 (65%)**

---

## Events FOUND ✅

### 1. FTX Solana Token Unlock (March 1-3, 2025)
- **Spike #2:** 2025-03-03 01:00 UTC | Z=13.70σ | +11.83% UP
- **Spike #9:** 2025-03-03 02:00 UTC | Z=9.38σ | +9.30% UP
- **Tier-1 Source:** CoinDesk (Feb 24, 2025)
- **Details:** 11.2M SOL unlocked ($2.07B), 2.29% of total supply

### 2. OSL Hong Kong SFC Approval (August 11-23, 2025)
- **Spike #6:** 2025-08-23 00:00 UTC | Z=11.31σ | +6.39% UP
- **Tier-1 Source:** Motley Fool, CoinDesk
- **Details:** First licensed HK exchange to offer SOL to retail investors

### 3. Black Monday Crypto Crash (August 5, 2024)
- **Spike #3:** 2024-08-05 23:00 UTC | Z=12.75σ | +9.55% UP (recovery bounce)
- **Tier-1 Source:** Fortune, CNBC
- **Details:** Bank of Japan rate hike, $367B selloff, Bitcoin <$50K, Solana -30% weekly

### 4. Solana ATH $294.85 (January 19, 2025)
- **Spike #15:** 2025-01-19 14:00 UTC | Z=8.46σ | +7.08% UP
- **Tier-1 Source:** CoinMarketCap, Coinbase, TradingView
- **Details:** All-time high driven by institutional interest, meme coin frenzy

### 5. Solana Bottom & Recovery (April 2025)
- **Spike #1:** 2025-04-10 03:00 UTC | Z=13.80σ | +10.24% UP
- **Tier-1 Source:** Yahoo Finance, Tickeron
- **Details:** SOL bottomed at $100 in April after falling from $260 peak

### 6. Trump Inauguration Peak & Crash (January 20, 2025)
- **Spike #10:** 2025-01-20 07:00 UTC | Z=9.35σ | -8.12% DOWN
- **Tier-1 Source:** Yahoo Finance, NPR, CoinMarketCap
- **Details:** Peaked Jan 19 at $294, crashed after inauguration, TRUMP/MELANIA meme coins

### 7. Mt. Gox + Germany Bitcoin Sales (July 8, 2024)
- **Spike #20:** 2024-07-08 18:00 UTC | Z=8.16σ | +5.96% UP
- **Tier-1 Source:** StatMuse, Grayscale Research
- **Details:** Germany sold 50K BTC, Mt. Gox repaid 60K BTC, market weakness then bounce

---

## Events PENDING Research ⏳

### 8. Unknown Event - 2024-03-06 05:00 UTC
- **Spike #4:** Z=12.30σ | -9.04% DOWN
- **Search Needed:** March 6, 2024 crypto crash morning

### 9. Unknown Event - 2024-06-18 11:00 UTC
- **Spike #5:** Z=11.85σ | -6.31% DOWN
- **Search Needed:** June 18, 2024 crypto crash midday

### 10. Unknown Event - 2024-06-27 23:00 UTC
- **Spike #7:** Z=10.42σ | +6.02% UP
- **Search Needed:** June 27, 2024 crypto rally late evening

### 11. Possible Solana ETF Filing - 2024-11-17 14:00 UTC
- **Spike #8:** Z=9.65σ | +6.24% UP
- **Search Needed:** November 17, 2024 - Bitwise filed in Nov, check exact date

### 12. Unknown Event - 2024-03-01 10:00 UTC
- **Spike #11:** Z=8.62σ | +5.87% UP
- **Search Needed:** March 1, 2024 crypto rally

### 13. Unknown Event - 2024-06-12 22:00 UTC
- **Spike #12:** Z=8.58σ | +4.68% UP
- **Search Needed:** June 12, 2024 crypto rally late evening

### 14. RECENT! - 2026-01-19 09:00 UTC
- **Spike #13:** Z=8.56σ | -3.50% DOWN
- **Search Needed:** January 19, 2026 crypto news (just 12 days ago!)

### 15. Unknown Event - 2025-01-16 21:00 UTC
- **Spike #14:** Z=8.49σ | +6.15% UP
- **Search Needed:** January 16, 2025 crypto rally

### 16. Unknown Event - 2024-04-13 04:00 UTC
- **Spike #16:** Z=8.31σ | -7.64% DOWN
- **Search Needed:** April 13, 2024 crypto crash early morning

### 17. Unknown Event - 2024-11-02 01:00 UTC
- **Spike #17:** Z=8.29σ | -4.32% DOWN
- **Search Needed:** November 2, 2024 crypto news early morning

### 18. RECENT! - 2026-01-22 02:00 UTC
- **Spike #18:** Z=8.28σ | -3.72% DOWN
- **Search Needed:** January 22, 2026 crypto news (just 9 days ago!)

### 19. Unknown Event - 2025-10-11 01:00 UTC
- **Spike #19:** Z=8.27σ | -4.15% DOWN
- **Search Needed:** October 11, 2025 crypto crash

---

## Instructions

For each pending spike:
1. Search for news at the exact timestamp (±2 minutes)
2. Find tier-1 sources (Bloomberg, Reuters, CoinDesk, SEC.gov, official announcements)
3. Extract **verbatim headline and first 3-4 paragraphs**
4. Verify timestamp is within 60 seconds of spike
5. Add to `verified_events_batch.json`

## Tier-1 Sources Priority

1. **Official Announcements:** SEC.gov, exchange official accounts
2. **Financial Wire Services:** Bloomberg Terminal, Reuters, Dow Jones
3. **Crypto Tier-1:** CoinDesk, The Block, Decrypt
4. **Traditional Finance:** CNBC, Yahoo Finance, Fortune (for crypto coverage)

## Gold Standard Checklist

Before adding an event:
- ✅ Source timestamp within ±60s of price spike
- ✅ Verbatim text >200 characters (real content, not just headline)
- ✅ Source is tier-1 (not Reddit, blogs, unverified accounts)
- ✅ Timestamp in ISO8601 format with timezone
- ✅ Event is not a duplicate

**REJECT if:**
- ❌ Source timestamp >60s after spike (wrong source)
- ❌ Can't find any news at spike time (market noise, not event-driven)
- ❌ Source is tier-2/3 (Reddit, blog, unverified account)
- ❌ Text is summarized or paraphrased

---

**Next Steps:**
1. Continue researching pending spikes
2. Extract verbatim text from tier-1 sources
3. Compile into `verified_events_batch.json`
4. Import using `scripts/add_events_enforced.py --import`
5. Run validation scripts

---

**Database:** data/hedgemony.db
**Date Range:** 2024-01-03 to 2026-01-30
**Total Spikes:** 357
**Top 20 Being Researched:** Sorted by Z-score (highest volatility)
