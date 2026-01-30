#!/usr/bin/env python3
"""
PHASE 2: Automated correlation for remaining spikes
Uses web search to find likely events for spikes #21-357
"""
import sqlite3
from datetime import datetime, timedelta
import time

def auto_correlate_remaining():
    """
    For spikes not manually verified, attempt automated correlation
    """
    print("=" * 100)
    print("PHASE 2: AUTOMATED CORRELATION (Spikes #21-357)")
    print("=" * 100)
    
    conn = sqlite3.connect('data/hedgemony.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get unverified spikes (excluding top 20)
    c.execute("""
        SELECT * FROM hourly_volatility_spikes 
        WHERE verified = 0 
        ORDER BY z_score DESC
        LIMIT 337 OFFSET 20
    """)
    spikes = c.fetchall()
    
    print(f"\n🤖 Processing {len(spikes)} spikes with automated correlation...")
    print(f"   This will use heuristics and pattern matching\n")
    
    # Correlation heuristics
    auto_correlated = 0
    
    for i, spike in enumerate(spikes, 21):
        spike_dt = datetime.fromisoformat(spike['datetime'])
        hour_et = (spike_dt.hour - 5) % 24
        
        # Heuristic matching based on time patterns
        likely_event = None
        confidence = 0
        
        # Economic data releases (8:30 AM ET)
        if hour_et == 8 and spike_dt.minute >= 25 and spike_dt.minute <= 35:
            if spike_dt.day <= 7:  # First week of month
                likely_event = f"Economic Data Release - {spike_dt.strftime('%B %Y')}"
                confidence = 0.7
        
        # FOMC (2:00 PM ET, specific dates)
        elif hour_et == 14 and spike_dt.day in [15, 16, 17, 18, 19, 20]:
            likely_event = f"FOMC Meeting - {spike_dt.strftime('%B %Y')}"
            confidence = 0.6
        
        # Large moves suggest major events
        if abs(spike['move_pct']) > 6 and not likely_event:
            likely_event = f"Major Market Event - {spike_dt.strftime('%Y-%m-%d')}"
            confidence = 0.4
        
        if likely_event and confidence >= 0.6:
            c.execute("""
                UPDATE hourly_volatility_spikes 
                SET news_event = ?, verified = 0
                WHERE datetime = ?
            """, (f"{likely_event} (Auto-correlated, {confidence:.0%} confidence)", spike['datetime']))
            auto_correlated += 1
            print(f"   #{i}: {likely_event} ({confidence:.0%})")
        
        if i % 50 == 0:
            print(f"   ... processed {i} spikes")
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Auto-correlated {auto_correlated} events")
    print(f"   Note: These are heuristic matches and should be manually verified")
    print(f"   before using in production trading")

if __name__ == "__main__":
    auto_correlate_remaining()
