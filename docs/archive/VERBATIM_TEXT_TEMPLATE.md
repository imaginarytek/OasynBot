# VERBATIM TEXT COLLECTION TEMPLATE
**Purpose:** Collect exact announcement text for all 80 curated events
**Goal:** Enable God-tier AI sentiment analysis by training on real-world text

---

## INSTRUCTIONS

For each event, we need to find and record:
1. **Exact headline** from the official source
2. **First 1-2 sentences** of the announcement (verbatim)
3. **Source URL** for verification

This text will be fed to the AI sentiment model EXACTLY as it appeared in real-time.

---

## TEMPLATE FOR EACH EVENT

```
Event: [Title]
Date: [YYYY-MM-DD HH:MM:SS UTC]
Source: [Official Source Name]
URL: [Direct link to announcement]

Headline: "[Exact headline text]"

Body Text (first 1-2 sentences):
"[Exact verbatim text from announcement]"

Keywords: [key, terms, for, search]
```

---

## PRIORITY EVENTS (Top 20 by 5s price impact)

### 1. Jobs Report April 2025 (+1.08% in 5s)
**Source:** Bureau of Labor Statistics (BLS.gov)
**URL:** https://www.bls.gov/news.release/empsit.nr0.htm
**Date:** 2025-04-04 12:30:00 UTC

**Headline:** "The Employment Situation - April 2025"

**Body Text:**
"Total nonfarm payroll employment [ROSE/FELL] by [XXX,000] in April, and the unemployment rate [INCREASED/DECREASED] to [X.X] percent, the U.S. Bureau of Labor Statistics reported today."

**Research Needed:** Find exact April 2025 BLS release

---

### 2. CPI Report July 2024 (+0.96% in 5s)
**Source:** Bureau of Labor Statistics
**URL:** https://www.bls.gov/news.release/cpi.nr0.htm
**Date:** 2024-07-11 12:30:00 UTC

**Headline:** "Consumer Price Index - July 2024"

**Body Text:**
"The Consumer Price Index for All Urban Consumers (CPI-U) [INCREASED/DECREASED] [X.X] percent in July on a seasonally adjusted basis, after [rising/falling] [X.X] percent in June, the U.S. Bureau of Labor Statistics reported today."

**Research Needed:** Find exact July 2024 CPI release

---

### 3. FOMC Meeting June 2024 (-0.88% in 5s)
**Source:** Federal Reserve
**URL:** https://www.federalreserve.gov/newsevents/pressreleases.htm
**Date:** 2024-06-12 18:00:00 UTC

**Headline:** "Federal Reserve issues FOMC statement"

**Body Text:**
"Recent indicators suggest that economic activity has been expanding at a [solid/moderate] pace. The Committee decided to [maintain/raise/lower] the target range for the federal funds rate at [X-X/X to X-X/X] percent."

**Research Needed:** Find exact June 2024 FOMC statement

---

## RESEARCH STRATEGY

### For Economic Data (CPI, Jobs, FOMC):
1. Go to official source (BLS.gov, FederalReserve.gov)
2. Find "News Releases" or "Press Releases"
3. Navigate to specific date
4. Copy EXACT headline and first paragraph
5. Note the exact release time (usually 8:30 AM or 2:00 PM ET)

### For Crypto Events (ETF, Hacks, Announcements):
1. Check SEC.gov for regulatory announcements
2. Check exchange official Twitter/blog for listings
3. Check blockchain explorers for on-chain events
4. Use archive.org if original source is gone
5. Cross-reference with Bloomberg Terminal screenshots if available

### For Political Events:
1. Check official government websites
2. Check Associated Press for election calls
3. Check Truth Social / Twitter for Trump announcements
4. Verify with multiple sources

---

## AUTOMATION OPPORTUNITIES

### BLS Reports (CPI & Jobs):
- **Pattern:** Very consistent format
- **Automation:** Can scrape from BLS.gov archives
- **URL Format:** `https://www.bls.gov/news.release/archives/[cpi/empsit]_[MMDDYYYY].htm`

### FOMC Statements:
- **Pattern:** Consistent format
- **Automation:** Can scrape from FederalReserve.gov
- **URL Format:** `https://www.federalreserve.gov/newsevents/pressreleases/monetary[YYYYMMDD]a.htm`

### SEC Announcements:
- **Pattern:** Press releases
- **Automation:** Can scrape from SEC.gov
- **URL Format:** `https://www.sec.gov/news/press-release/[YYYY-XXX]`

---

## NEXT STEPS

1. **Create automated scraper** for BLS/Fed/SEC (covers ~60 events)
2. **Manual research** for crypto-specific events (~10 events)
3. **Manual research** for political events (~10 events)
4. **Verify all text** is exact verbatim
5. **Update database** with collected text
6. **Test AI model** on sample events

---

## QUALITY CHECKLIST

For each event, verify:
- [ ] Text is EXACT verbatim (not paraphrased)
- [ ] Source is Tier 1 (official, not news article)
- [ ] Timestamp matches announcement time
- [ ] URL is direct link to original source
- [ ] Text is what a real-time trader would see first

---

## EXAMPLE: PERFECT ENTRY

```
Event: Bitcoin Spot ETF Approved by SEC
Date: 2024-01-10 21:30:00 UTC
Source: U.S. Securities and Exchange Commission
URL: https://www.sec.gov/news/statement/gensler-statement-spot-bitcoin-011023

Headline: "Statement on the Approval of Spot Bitcoin Exchange-Traded Products"

Body Text:
"Today the Commission approved the listing and trading of shares of spot bitcoin exchange-traded products (ETPs). While we approved the listing and trading of certain spot bitcoin ETP shares today, we did not approve or endorse bitcoin. Investors should remain cautious about the myriad risks associated with bitcoin and products whose value is tied to crypto."

Keywords: SEC, Bitcoin, ETF, approved, Gensler, spot, exchange-traded
```

**This is the GOLD STANDARD** - exact text from official source, with URL for verification.

---

## ESTIMATED EFFORT

- **Automated (BLS/Fed/SEC):** 60 events × 5 min = 5 hours
- **Manual (Crypto):** 10 events × 15 min = 2.5 hours  
- **Manual (Political):** 10 events × 15 min = 2.5 hours
- **Verification:** 80 events × 2 min = 2.5 hours

**Total:** ~12-15 hours of research work

**Deliverable:** Database with exact verbatim text for all 80 events, ready for AI training
