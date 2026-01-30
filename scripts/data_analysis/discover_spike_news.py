#!/usr/bin/env python3
"""
STEP 3: Automated News Discovery for Top Volatility Spikes
Search for tier-1 news announcements that caused the biggest price moves
"""
import sqlite3
from datetime import datetime, timedelta
import time

def investigate_top_spikes():
    """
    For each major spike, search for news events
    """
    print("=" * 100)
    print("STEP 3: NEWS DISCOVERY FOR TOP VOLATILITY SPIKES")
    print("=" * 100)
    
    conn = sqlite3.connect('data/hedgemony.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get top unmatched spikes
    c.execute("""
        SELECT * FROM hourly_volatility_spikes 
        WHERE news_event IS NULL 
        ORDER BY z_score DESC 
        LIMIT 20
    """)
    spikes = c.fetchall()
    
    print(f"\n🔍 Investigating top {len(spikes)} unmatched spikes...")
    print(f"   Will search web for news events around each spike time\n")
    
    discoveries = []
    
    for i, spike in enumerate(spikes, 1):
        spike_dt = datetime.fromisoformat(spike['datetime'])
        
        print(f"\n{'='*90}")
        print(f"Spike #{i}: {spike_dt.strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"Z-Score: {spike['z_score']:.2f}σ | Move: {spike['move_pct']:+.2f}% | Price: ${spike['close_price']:.2f}")
        print(f"{'='*90}")
        
        # Search parameters
        search_start = spike_dt - timedelta(minutes=30)
        search_end = spike_dt + timedelta(minutes=30)
        
        # Format for search
        date_str = spike_dt.strftime('%Y-%m-%d')
        time_str = spike_dt.strftime('%H:%M')
        
        print(f"\n📰 Searching for news events...")
        print(f"   Time window: {search_start.strftime('%H:%M')} - {search_end.strftime('%H:%M')} UTC")
        
        # We'll search for common event types based on the time and magnitude
        search_queries = []
        
        # Economic data releases (typically 8:30 AM ET = 13:30 UTC or 12:30 UTC)
        hour_utc = spike_dt.hour
        if hour_utc in [12, 13, 14]:  # US economic data release times
            search_queries.append(f"BLS jobs report {date_str}")
            search_queries.append(f"CPI inflation {date_str}")
            search_queries.append(f"Federal Reserve {date_str}")
            search_queries.append(f"FOMC {date_str}")
        
        # Crypto-specific events (can happen any time)
        search_queries.append(f"Solana SOL {date_str}")
        search_queries.append(f"crypto market crash {date_str}")
        search_queries.append(f"Bitcoin {date_str}")
        
        # Major news events
        if abs(spike['move_pct']) > 8:  # Very large moves
            search_queries.append(f"breaking news {date_str}")
            search_queries.append(f"market crash {date_str}")
        
        discoveries.append({
            'spike': spike,
            'search_queries': search_queries,
            'spike_time': spike_dt
        })
        
        print(f"\n   Suggested searches:")
        for q in search_queries:
            print(f"      - {q}")
        
        time.sleep(0.5)  # Rate limit
    
    conn.close()
    
    # Generate research template
    print(f"\n{'='*100}")
    print("📋 GENERATING RESEARCH TEMPLATE")
    print(f"{'='*100}\n")
    
    with open('data/spike_investigation_template.md', 'w') as f:
        f.write("# Volatility Spike Investigation Template\n\n")
        f.write("## Instructions\n")
        f.write("For each spike below, search Twitter/news to find the tier-1 announcement.\n\n")
        f.write("### Tier-1 Sources\n")
        f.write("- **Economic Data**: @BLS_gov, @federalreserve, @USTreasury\n")
        f.write("- **Crypto**: @binance, @coinbase, @SECGov\n")
        f.write("- **Breaking News**: @AP, @Reuters, @Bloomberg\n\n")
        f.write("---\n\n")
        
        for i, disc in enumerate(discoveries, 1):
            spike = disc['spike']
            spike_dt = disc['spike_time']
            
            f.write(f"## Spike #{i}: {spike_dt.strftime('%Y-%m-%d %H:%M UTC')}\n\n")
            f.write(f"**Metrics:**\n")
            f.write(f"- Z-Score: {spike['z_score']:.2f}σ\n")
            f.write(f"- Move: {spike['move_pct']:+.2f}%\n")
            f.write(f"- Price: ${spike['open_price']:.2f} → ${spike['close_price']:.2f}\n\n")
            
            f.write(f"**Search Window:** {(spike_dt - timedelta(minutes=30)).strftime('%H:%M')} - {(spike_dt + timedelta(minutes=30)).strftime('%H:%M')} UTC\n\n")
            
            f.write(f"**Suggested Searches:**\n")
            for q in disc['search_queries']:
                f.write(f"- `{q}`\n")
            
            f.write(f"\n**Twitter Search Links:**\n")
            
            # Generate Twitter search URLs
            sources = "from:BLS_gov OR from:federalreserve OR from:SECGov OR from:binance"
            since = (spike_dt - timedelta(hours=1)).strftime('%Y-%m-%d_%H:%M:%S_UTC')
            until = (spike_dt + timedelta(hours=1)).strftime('%Y-%m-%d_%H:%M:%S_UTC')
            
            twitter_url = f"https://twitter.com/search?q=({sources}) since:{since} until:{until}"
            f.write(f"- [Search Tier-1 Sources]({twitter_url})\n\n")
            
            f.write(f"**FINDINGS:**\n")
            f.write(f"```\n")
            f.write(f"Event Title: _______________________________________\n")
            f.write(f"Source: ____________________________________________\n")
            f.write(f"Exact Timestamp: ___________________________________\n")
            f.write(f"Tweet/Announcement URL: ____________________________\n")
            f.write(f"```\n\n")
            f.write("---\n\n")
    
    print(f"✅ Research template saved to: data/spike_investigation_template.md")
    print(f"\n💡 Next: Open the template and manually research each spike")
    
    return discoveries

if __name__ == "__main__":
    discoveries = investigate_top_spikes()
    
    print(f"\n{'='*100}")
    print("📊 SUMMARY")
    print(f"{'='*100}")
    print(f"   Spikes to investigate: {len(discoveries)}")
    print(f"   Research template: data/spike_investigation_template.md")
    print(f"\n   After completing research:")
    print(f"   1. Update database with found events")
    print(f"   2. Fetch 1-second price data for verified events")
    print(f"   3. Build new optimized dataset")
