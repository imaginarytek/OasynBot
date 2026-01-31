#!/usr/bin/env python3
"""
Generate Research Guide for Manual Event Verification

After refine_spike_timing.py identifies exact spike minutes, this script:
1. Loads refined spikes from database
2. Generates pre-filled search links for Twitter, Google News
3. Creates markdown research checklist
4. Provides template for verified_events_batch.json

Makes manual research 10x faster by automating the busywork.
"""

import sqlite3
import json
from datetime import datetime, timedelta
import urllib.parse
import sys
import os

# Constants
DB_PATH = 'data/hedgemony.db'
OUTPUT_FILE = 'data/research_guide.md'
TEMPLATE_FILE = 'data/verified_events_template.json'

# Color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def format_datetime_for_twitter(dt):
    """Format datetime for Twitter advanced search"""
    return dt.strftime('%Y-%m-%d_%H:%M:%S')


def generate_search_links(spike_time, symbol='SOL'):
    """
    Generate pre-filled search URLs for news research.

    Args:
        spike_time: datetime of exact spike minute
        symbol: Asset symbol (default: SOL)

    Returns:
        dict of search URLs
    """
    # Search window: 2 minutes before to 2 minutes after spike
    start_time = spike_time - timedelta(minutes=2)
    end_time = spike_time + timedelta(minutes=2)

    # Twitter advanced search
    twitter_keywords = f"{symbol} OR Solana OR crypto OR binance OR SEC"
    twitter_url = (
        f"https://twitter.com/search?q={urllib.parse.quote(twitter_keywords)}"
        f"&src=typed_query&f=live"
    )

    # Google News search (approximate time filter)
    google_keywords = f"{symbol} Solana cryptocurrency"
    google_date = spike_time.strftime('%Y-%m-%d')
    google_url = (
        f"https://www.google.com/search?q={urllib.parse.quote(google_keywords)}"
        f"&tbm=nws&tbs=cdr:1,cd_min:{google_date},cd_max:{google_date}"
    )

    # CoinDesk archive
    coindesk_date = spike_time.strftime('%Y/%m/%d')
    coindesk_url = f"https://www.coindesk.com/arc/outboundfeeds/news-sitemap-index/?outputType=xml"

    return {
        'twitter': twitter_url,
        'google_news': google_url,
        'coindesk': coindesk_url,
        'search_window': f"{start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%H:%M')} UTC"
    }


def generate_research_guide():
    """
    Generate markdown research guide with pre-filled search links.
    """
    print("=" * 80)
    print(f"{BLUE}RESEARCH GUIDE GENERATOR{RESET}")
    print("=" * 80)

    conn = get_db_connection()
    c = conn.cursor()

    # Get refined spikes that need research
    spikes = c.execute("""
        SELECT timestamp, refined_timestamp, z_score, return_pct,
               volatility_1m, price_range_pct
        FROM potential_event_spikes
        WHERE status = 'refined'
        ORDER BY z_score DESC
        LIMIT 20
    """).fetchall()

    if len(spikes) == 0:
        print(f"{YELLOW}No refined spikes found.{RESET}")
        print(f"Run refine_spike_timing.py first.")
        conn.close()
        return

    print(f"Generating research guide for {len(spikes)} spikes...\n")

    # Generate markdown guide
    md_content = f"""# Event Research Guide

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Spikes to Research:** {len(spikes)}

---

## Instructions

For each spike below:
1. Click the search links to find news sources
2. Look for tier-1 sources (Bloomberg Terminal, @SEC_News, official announcements)
3. Find the **exact timestamp** of the news (must be within 60s of spike)
4. Copy the **verbatim headline and body text** (first 3-4 paragraphs)
5. Fill in the template at the bottom of this file
6. Add to `verified_events_batch.json`

---

## Spikes to Research

"""

    template_events = []

    for i, row in enumerate(spikes, 1):
        hourly_ts = row['timestamp']
        refined_ts = row['refined_timestamp']
        z_score = row['z_score']
        hourly_return = row['return_pct']
        vol_1m = row['volatility_1m'] if 'volatility_1m' in row.keys() else 0
        price_range = row['price_range_pct'] if 'price_range_pct' in row.keys() else 0

        spike_time = datetime.fromisoformat(refined_ts.replace('Z', '+00:00'))

        # Generate search links
        links = generate_search_links(spike_time)

        # Add to markdown
        md_content += f"""### {i}. Spike on {spike_time.strftime('%Y-%m-%d %H:%M UTC')}

**Metrics:**
- **Z-Score:** {z_score:.2f}σ (Hourly)
- **Hourly Return:** {hourly_return*100:.2f}%
- **1-min Volatility:** {vol_1m:.2f}
- **1-min Price Range:** {price_range:.2f}%

**Exact Spike Time:** `{refined_ts}`

**Search Links:**
- [Twitter Search (±2min)]({links['twitter']})
- [Google News]({links['google_news']})
- Search Window: {links['search_window']}

**Research Checklist:**
- [ ] Found tier-1 source (official announcement, Bloomberg, Reuters, @SEC_News, etc.)
- [ ] Verified timestamp is within 60s of spike
- [ ] Copied verbatim headline
- [ ] Copied verbatim body text (3-4 paragraphs)
- [ ] Saved source URL
- [ ] Categorized event (Crypto/Regulatory/Political/Other)
- [ ] Measured time_to_impact manually (seconds from news to spike)

**Findings:**
```
Source:
Title:
Timestamp:
Category:
Time to Impact:
```

---

"""

        # Create template entry
        template_events.append({
            "title": "FILL IN: Exact headline from tier-1 source",
            "timestamp": refined_ts,
            "source": "FILL IN: @username or outlet name",
            "source_url": "FILL IN: URL to original tweet/article",
            "category": "FILL IN: Crypto/Regulatory/Political/Other",
            "verbatim_text": "FILL IN: Copy-paste exact text from source (3-4 paragraphs, include typos)",
            "time_to_impact_seconds": 0,  # FILL IN: Measured from chart
            "notes": f"Auto-detected spike: Z={z_score:.1f}σ, 1m_range={price_range:.2f}%"
        })

    # Add template section
    md_content += """
---

## Event Template

Copy this to `verified_events_batch.json` for each event you verify:

```json
{
  "title": "EXACT HEADLINE FROM SOURCE",
  "timestamp": "2023-XX-XXTXX:XX:XX+00:00",
  "source": "@username or outlet",
  "source_url": "https://...",
  "category": "Crypto/Regulatory/Political/Other",
  "verbatim_text": "Copy-paste exact text...",
  "time_to_impact_seconds": 5,
  "notes": "Any observations"
}
```

---

## Gold Standard Checklist

Before adding an event to the dataset, verify:
- ✅ Source timestamp is within ±60s of price spike
- ✅ Verbatim text is >50 characters (real content, not just headline)
- ✅ Source is tier-1 (official, Bloomberg, Reuters, major exchange)
- ✅ Timestamp is in ISO8601 format with timezone
- ✅ time_to_impact_seconds is manually measured from chart
- ✅ Event is not a duplicate of existing event

**REJECT if:**
- ❌ Source timestamp is >60s after spike (wrong source)
- ❌ Can't find any news at spike time (market noise, not event-driven)
- ❌ Source is tier-2/3 (Reddit, blog, unverified account)
- ❌ Text is summarized or paraphrased

---

**Next Steps:**
1. Complete research for each spike above
2. Add verified events to `verified_events_batch.json`
3. Run `python3 scripts/import_new_events_json.py`
4. Run `python3 scripts/build_verified_dataset.py` to fetch 1s price data
5. Run `python3 scripts/validation/validate_correlation.py` to verify quality

"""

    # Write markdown file
    with open(OUTPUT_FILE, 'w') as f:
        f.write(md_content)

    print(f"{GREEN}✓ Research guide written to:{RESET} {OUTPUT_FILE}")

    # Write template JSON
    with open(TEMPLATE_FILE, 'w') as f:
        json.dump(template_events, f, indent=2)

    print(f"{GREEN}✓ Template JSON written to:{RESET} {TEMPLATE_FILE}")

    print(f"\n{BLUE}Next Steps:{RESET}")
    print(f"  1. Open {OUTPUT_FILE}")
    print(f"  2. Click search links and find news sources")
    print(f"  3. Fill in verified_events_batch.json")
    print(f"  4. Run: python3 scripts/import_new_events_json.py")

    print("\n" + "=" * 80)

    conn.close()


def main():
    if not os.path.exists(DB_PATH):
        print(f"{RED}Error: Database not found at {DB_PATH}{RESET}")
        sys.exit(1)

    generate_research_guide()


if __name__ == "__main__":
    main()
