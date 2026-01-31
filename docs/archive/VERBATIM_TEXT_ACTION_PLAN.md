# VERBATIM TEXT COLLECTION - ACTION PLAN

**Status:** Ready to execute
**Goal:** Populate all 80 events with exact announcement text for God-tier AI training

---

## WHY THIS MATTERS

For the AI sentiment model to work in production, it needs to be trained on:
- **Exact text** that appears in real announcements
- **Same format** as what it will see live
- **No paraphrasing** or summarization

This ensures the AI learns to recognize:
- Official language patterns
- Key sentiment indicators
- Numerical data formats
- Urgency signals

---

## CURRENT STATUS

✅ **Database Structure:** Ready (description column exists)
✅ **Price Data:** Complete (80 events with 1s data)
✅ **Timing Data:** Verified (median 1s lag)
❌ **Verbatim Text:** Missing (all descriptions are NULL)

---

## WHAT WE HAVE

### Tools Created:
1. ✅ `scripts/scrape_verbatim_text.py` - Automated scraper for BLS/Fed
2. ✅ `scripts/populate_verbatim_text.py` - Manual population script
3. ✅ `VERBATIM_TEXT_TEMPLATE.md` - Research guide

### Event Breakdown:
- **CPI Reports:** 24 events (can automate)
- **Jobs Reports:** 24 events (can automate)
- **FOMC Meetings:** 16 events (can automate)
- **Crypto Events:** 10 events (manual research)
- **Political Events:** 6 events (manual research)

**Total:** 64 can be automated, 16 need manual research

---

## EXECUTION PLAN

### Phase 1: Automated Collection (2-3 hours)
```bash
# Run the automated scraper
python3 scripts/scrape_verbatim_text.py
```

This will:
- Fetch exact text from BLS.gov for all CPI/Jobs reports
- Fetch exact text from FederalReserve.gov for FOMC statements
- Update database with verbatim text
- Generate report of successes/failures

**Expected:** 60-64 events populated automatically

---

### Phase 2: Manual Research (3-4 hours)

For remaining ~16 events, manually research and add:

#### Crypto Events (10 events):
1. **SEC Twitter Hack** - Find archived tweet
2. **Bitcoin ETF Approval** - SEC.gov press release
3. **Bitcoin ETF Trading** - NYSE announcement
4. **Ethereum ETF Approval** - SEC.gov
5. **Ethereum ETF Trading** - NYSE announcement
6. **BOME Whale Accumulation** - On-chain data description
7. **BOME Binance Listing** - Binance announcement
8. **Roaring Kitty Returns** - Twitter post
9. **GameStop Rally** - Market data description
10. **SEC Closes ETH Investigation** - SEC.gov

#### Political Events (6 events):
1. **Trump Election Called** - AP announcement
2. **Trump Inauguration** - Official ceremony
3. **Trump Crypto Reserve** - Truth Social post
4. **Powell Jackson Hole** - Fed speech transcript
5. **Powell Testimony** - Congressional testimony
6. **Bank of Japan Rate Hike** - BoJ statement

---

### Phase 3: Verification (1-2 hours)

For each event, verify:
- [ ] Text is exact verbatim (not paraphrased)
- [ ] Source is Tier 1 official
- [ ] Timestamp matches
- [ ] Text length is appropriate (100-500 chars)
- [ ] No typos or formatting issues

---

## EXAMPLE OUTPUT

### Before:
```
Title: CPI Report July 2024
Description: NULL
```

### After:
```
Title: CPI Report July 2024
Description: "The Consumer Price Index for All Urban Consumers (CPI-U) increased 0.2 percent in July on a seasonally adjusted basis, after being unchanged in June, the U.S. Bureau of Labor Statistics reported today. Over the last 12 months, the all items index increased 2.9 percent before seasonal adjustment."
```

---

## QUALITY STANDARDS

### Good Example (BLS):
```
"Total nonfarm payroll employment rose by 275,000 in February, and the unemployment rate edged up to 3.9 percent, the U.S. Bureau of Labor Statistics reported today."
```
✅ Official language
✅ Specific numbers
✅ Source attribution
✅ Complete sentence

### Bad Example:
```
"Jobs report came in strong, unemployment steady"
```
❌ Paraphrased
❌ No numbers
❌ Informal language
❌ No source

---

## NEXT STEPS

1. **Run automated scraper** (do this first)
   ```bash
   python3 scripts/scrape_verbatim_text.py
   ```

2. **Review results** - Check how many succeeded

3. **Manual research** - Fill in remaining events

4. **Verify quality** - Spot check 10-20 events

5. **Test AI model** - Run sentiment analysis on sample

---

## ESTIMATED TIMELINE

- **Automated scraping:** 2-3 hours (includes troubleshooting)
- **Manual research:** 3-4 hours
- **Verification:** 1-2 hours
- **Testing:** 1 hour

**Total:** 7-10 hours to complete

---

## DELIVERABLE

When complete, we'll have:
- ✅ 80 events with exact verbatim announcement text
- ✅ All text from Tier 1 official sources
- ✅ Perfect format for AI sentiment training
- ✅ Production-ready dataset

This will enable the AI to:
- Recognize official announcement patterns
- Extract sentiment from real-world text
- React to live news with same accuracy as training
- Achieve God-tier performance in production

---

## READY TO START?

Run this command to begin automated collection:
```bash
python3 scripts/scrape_verbatim_text.py
```

This will handle 60-64 events automatically, leaving only ~16 for manual research.
