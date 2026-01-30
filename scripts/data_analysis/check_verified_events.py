
import sqlite3
import json
from datetime import datetime, timezone

# VERIFIED TIER 1 EVENTS - Hand-curated list with exact timestamps
VERIFIED_EVENTS = [
    {
        'title': 'SEC Twitter Hack: Fake Bitcoin ETF Approval',
        'timestamp': '2024-01-09 21:11:00+00:00',
        'source': '@SECGov (Twitter - Compromised)',
        'description': 'Unauthorized tweet from hacked SEC account falsely claiming Bitcoin ETF approval',
        'sentiment': 'bullish',
        'keywords': ['Bitcoin', 'ETF', 'SEC', 'approval', 'hack']
    },
    {
        'title': 'Trump Election Called by Associated Press',
        'timestamp': '2024-11-06 10:34:00+00:00',
        'source': 'Associated Press',
        'description': 'AP officially calls 2024 presidential election for Donald Trump',
        'sentiment': 'bullish',
        'keywords': ['Trump', 'election', 'president', 'win']
    },
    {
        'title': 'Roaring Kitty Returns to Twitter',
        'timestamp': '2024-05-13 00:00:00+00:00',  # May 12, 8pm EST = May 13 00:00 UTC
        'source': '@TheRoaringKitty (Twitter)',
        'description': 'Keith Gill posts first tweet in 3 years - lean forward meme',
        'sentiment': 'bullish',
        'keywords': ['Roaring Kitty', 'GameStop', 'GME', 'meme stock']
    },
    {
        'title': 'Powell Jackson Hole Speech',
        'timestamp': '2024-08-23 14:00:00+00:00',
        'source': 'Federal Reserve',
        'description': 'Jerome Powell delivers Jackson Hole Economic Symposium speech',
        'sentiment': 'neutral',  # Depends on content
        'keywords': ['Powell', 'Fed', 'Jackson Hole', 'policy', 'rates']
    },
    {
        'title': 'Nikkei 225 Opens Down 12%',
        'timestamp': '2024-08-05 00:00:00+00:00',  # 9am JST
        'source': 'Tokyo Stock Exchange',
        'description': 'Nikkei 225 crashes 12% at market open - worst day since 1987',
        'sentiment': 'bearish',
        'keywords': ['Nikkei', 'Japan', 'crash', 'market', 'risk-off']
    },
    # Add more as we verify them
]

def check_price_correlation():
    """
    For each verified event, check if we have price data and measure the lag
    """
    print("🔍 CHECKING PRICE CORRELATION FOR VERIFIED EVENTS\n")
    print("="*100)
    
    conn = sqlite3.connect("data/hedgemony.db")
    c = conn.cursor()
    
    results = []
    
    for event in VERIFIED_EVENTS:
        print(f"\n📰 {event['title']}")
        print(f"   News Time: {event['timestamp']}")
        print(f"   Source: {event['source']}")
        
        # Parse news time
        news_time = datetime.fromisoformat(event['timestamp'])
        
        # Check if we have ANY event within +/- 30 minutes
        search_start = (news_time - timedelta(minutes=30)).isoformat()
        search_end = (news_time + timedelta(minutes=30)).isoformat()
        
        c.execute("""
            SELECT rowid, title, timestamp, sol_price_data
            FROM gold_events
            WHERE timestamp BETWEEN ? AND ?
            AND sol_price_data IS NOT NULL
        """, (search_start, search_end))
        
        matches = c.fetchall()
        
        if matches:
            print(f"   ✅ Found {len(matches)} existing event(s) in database near this time:")
            for match in matches:
                rowid, title, ts, _ = match
                print(f"      - {title} ({ts})")
        else:
            print(f"   ❌ NO existing event in database - need to add this")
        
        # Now check the actual price data for this time
        # We need to load SOL/USDT 1s data for this specific timestamp
        # and measure lag from news to first spike
        
        print(f"   🔍 Checking price action...")
        
        # For now, just note if we need to fetch data
        results.append({
            'event': event,
            'in_database': len(matches) > 0,
            'needs_price_data': len(matches) == 0
        })
    
    conn.close()
    
    print(f"\n\n{'='*100}")
    print("SUMMARY:")
    print(f"{'='*100}")
    
    in_db = sum(1 for r in results if r['in_database'])
    missing = sum(1 for r in results if not r['in_database'])
    
    print(f"✅ Already in database: {in_db}")
    print(f"❌ Missing from database: {missing}")
    print(f"\nNext step: Fetch 1s price data for missing events and measure exact lag")

from datetime import timedelta

if __name__ == "__main__":
    check_price_correlation()
