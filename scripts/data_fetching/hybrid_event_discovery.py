#!/usr/bin/env python3
"""
HYBRID EVENT DISCOVERY - Option 3
Phase 1: Manual verification template for top 20 spikes
Phase 2: Automated correlation for remaining spikes
"""
import sqlite3
from datetime import datetime, timedelta
import json

def generate_top20_research_guide():
    """
    Create a focused research guide for the top 20 most significant spikes
    """
    print("=" * 100)
    print("PHASE 1: TOP 20 SPIKE MANUAL VERIFICATION")
    print("=" * 100)
    
    conn = sqlite3.connect('data/hedgemony.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get top 20 unmatched spikes
    c.execute("""
        SELECT * FROM hourly_volatility_spikes 
        WHERE news_event IS NULL 
        ORDER BY z_score DESC 
        LIMIT 20
    """)
    spikes = c.fetchall()
    
    # Generate focused research document
    with open('data/TOP20_MANUAL_RESEARCH.md', 'w') as f:
        f.write("# TOP 20 VOLATILITY SPIKES - MANUAL VERIFICATION GUIDE\n\n")
        f.write("## Quick Reference\n\n")
        f.write("**Goal**: Find the exact news event that caused each spike\n\n")
        f.write("**Time Estimate**: 5-10 minutes per spike = 2-3 hours total\n\n")
        f.write("**Tier-1 Sources to Check**:\n")
        f.write("- Economic: @BLS_gov, @federalreserve, @USTreasury\n")
        f.write("- Crypto: @binance, @coinbase, @cz_binance, @SECGov\n")
        f.write("- News: @AP, @Reuters, @Bloomberg, @CNBC\n\n")
        f.write("**How to Research**:\n")
        f.write("1. Click the Twitter search link\n")
        f.write("2. Look for tweets from tier-1 sources within ±30 min of spike\n")
        f.write("3. If found, note the EXACT timestamp\n")
        f.write("4. If not found, try the Google search\n")
        f.write("5. Fill in the findings section\n\n")
        f.write("---\n\n")
        
        for i, spike in enumerate(spikes, 1):
            spike_dt = datetime.fromisoformat(spike['datetime'])
            
            f.write(f"## Spike #{i}: {spike_dt.strftime('%Y-%m-%d %H:%M UTC')}\n\n")
            
            # Visual indicator of importance
            stars = "⭐" * min(int(spike['z_score'] / 3), 5)
            f.write(f"**Significance**: {stars} ({spike['z_score']:.1f}σ)\n\n")
            
            f.write(f"**Metrics**:\n")
            f.write(f"- Move: {spike['move_pct']:+.2f}%\n")
            f.write(f"- Price: ${spike['open_price']:.2f} → ${spike['close_price']:.2f}\n")
            f.write(f"- Range: {spike['intra_range']*100:.2f}%\n\n")
            
            # Time context
            day_of_week = spike_dt.strftime('%A')
            hour_et = (spike_dt.hour - 5) % 24  # Convert UTC to ET
            
            f.write(f"**Time Context**:\n")
            f.write(f"- Day: {day_of_week}\n")
            f.write(f"- Hour (ET): {hour_et:02d}:00\n")
            
            # Suggest likely event types based on time
            likely_events = []
            if hour_et in [8, 9]:  # 8:30 AM ET = common economic release time
                likely_events.append("📊 Economic Data (CPI, Jobs, GDP)")
            if hour_et in [14, 15]:  # 2:00 PM ET = FOMC announcements
                likely_events.append("🏦 Fed/FOMC Announcement")
            if spike_dt.hour in [0, 1, 23]:  # Late night UTC = Asia session
                likely_events.append("🌏 Asia Market Event (BOJ, China)")
            if abs(spike['move_pct']) > 8:
                likely_events.append("⚡ Black Swan / Major Shock")
            
            if likely_events:
                f.write(f"- Likely Type: {', '.join(likely_events)}\n")
            f.write("\n")
            
            # Search links
            since = (spike_dt - timedelta(hours=1)).strftime('%Y-%m-%d_%H:%M:%S_UTC')
            until = (spike_dt + timedelta(hours=1)).strftime('%Y-%m-%d_%H:%M:%S_UTC')
            
            # Twitter searches
            f.write(f"**🔍 SEARCH LINKS**:\n\n")
            
            # Economic sources
            econ_sources = "from:BLS_gov OR from:federalreserve OR from:USTreasury"
            twitter_econ = f"https://twitter.com/search?q=({econ_sources}) since:{since} until:{until}&f=live"
            f.write(f"1. [Twitter: Economic Sources]({twitter_econ})\n")
            
            # Crypto sources
            crypto_sources = "from:binance OR from:coinbase OR from:SECGov OR from:cz_binance"
            twitter_crypto = f"https://twitter.com/search?q=({crypto_sources}) since:{since} until:{until}&f=live"
            f.write(f"2. [Twitter: Crypto Sources]({twitter_crypto})\n")
            
            # News sources
            news_sources = "from:AP OR from:Reuters OR from:Bloomberg"
            twitter_news = f"https://twitter.com/search?q=({news_sources}) since:{since} until:{until}&f=live"
            f.write(f"3. [Twitter: Breaking News]({twitter_news})\n")
            
            # Google search
            date_str = spike_dt.strftime('%B %d %Y')
            google_search = f"https://www.google.com/search?q=crypto+market+{date_str}+news&tbs=cdr:1,cd_min:{spike_dt.strftime('%m/%d/%Y')},cd_max:{spike_dt.strftime('%m/%d/%Y')}"
            f.write(f"4. [Google: News Search]({google_search})\n\n")
            
            # Findings template
            f.write(f"**📝 FINDINGS**:\n")
            f.write(f"```\n")
            f.write(f"[ ] Event Found\n")
            f.write(f"Event Title: _________________________________________________\n")
            f.write(f"Source: ______________________________________________________\n")
            f.write(f"Exact Timestamp (UTC): _______________________________________\n")
            f.write(f"URL: _________________________________________________________\n")
            f.write(f"Category: [ ] Economic [ ] Crypto [ ] Regulatory [ ] Other\n")
            f.write(f"Notes: _______________________________________________________\n")
            f.write(f"_____________________________________________________________\n")
            f.write(f"```\n\n")
            f.write("---\n\n")
    
    print(f"\n✅ Created: data/TOP20_MANUAL_RESEARCH.md")
    print(f"\n📋 INSTRUCTIONS:")
    print(f"   1. Open data/TOP20_MANUAL_RESEARCH.md")
    print(f"   2. Work through each spike (5-10 min each)")
    print(f"   3. Fill in the findings sections")
    print(f"   4. When done, run: python3 scripts/import_manual_findings.py")
    
    conn.close()

def create_import_script():
    """
    Create a script to import manual research findings back into the database
    """
    script_content = '''#!/usr/bin/env python3
"""
Import manually researched findings into the database
"""
import sqlite3
from datetime import datetime

def import_findings():
    """
    After completing manual research in TOP20_MANUAL_RESEARCH.md,
    run this script to update the database
    """
    print("=" * 100)
    print("IMPORTING MANUAL RESEARCH FINDINGS")
    print("=" * 100)
    
    # This will be filled in after manual research
    # Format: (spike_datetime, event_title, source, exact_timestamp, url, category, notes)
    findings = [
        # Example:
        # ("2025-04-10 03:00:00", "FTX Estate Repayments Announcement", "@FTX_Official", "2025-04-10 02:45:00", "https://twitter.com/...", "Crypto", "Major selling pressure expected"),
    ]
    
    if not findings:
        print("\\n⚠️  No findings to import yet.")
        print("   Please edit this script and add your findings from TOP20_MANUAL_RESEARCH.md")
        print("   Follow the example format shown in the 'findings' list")
        return
    
    conn = sqlite3.connect('data/hedgemony.db')
    c = conn.cursor()
    
    updated = 0
    for finding in findings:
        spike_dt, title, source, exact_ts, url, category, notes = finding
        
        # Update the spike record
        c.execute("""
            UPDATE hourly_volatility_spikes 
            SET news_event = ?, verified = 1
            WHERE datetime = ?
        """, (title, spike_dt))
        
        if c.rowcount > 0:
            updated += 1
            print(f"   ✓ Updated: {spike_dt} -> {title}")
    
    conn.commit()
    conn.close()
    
    print(f"\\n✅ Imported {updated} findings")
    print(f"\\n📊 Next Steps:")
    print(f"   1. Run: python3 scripts/build_verified_dataset.py")
    print(f"   2. This will fetch 1s data for verified events")
    print(f"   3. Then run backtest with new dataset")

if __name__ == "__main__":
    import_findings()
'''
    
    with open('scripts/import_manual_findings.py', 'w') as f:
        f.write(script_content)
    
    print(f"✅ Created: scripts/import_manual_findings.py")

def create_automated_correlation():
    """
    Create automated correlation script for remaining spikes
    """
    script_content = '''#!/usr/bin/env python3
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
    
    print(f"\\n🤖 Processing {len(spikes)} spikes with automated correlation...")
    print(f"   This will use heuristics and pattern matching\\n")
    
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
    
    print(f"\\n✅ Auto-correlated {auto_correlated} events")
    print(f"   Note: These are heuristic matches and should be manually verified")
    print(f"   before using in production trading")

if __name__ == "__main__":
    auto_correlate_remaining()
'''
    
    with open('scripts/auto_correlate_spikes.py', 'w') as f:
        f.write(script_content)
    
    print(f"✅ Created: scripts/auto_correlate_spikes.py")

if __name__ == "__main__":
    print("🚀 HYBRID EVENT DISCOVERY - OPTION 3")
    print("   Phase 1: Manual verification (Top 20)")
    print("   Phase 2: Automated correlation (Remaining)\n")
    
    # Phase 1: Generate manual research guide
    generate_top20_research_guide()
    
    # Create helper scripts
    create_import_script()
    create_automated_correlation()
    
    print(f"\n{'='*100}")
    print("📋 WORKFLOW")
    print(f"{'='*100}")
    print(f"\n**PHASE 1 (Manual - 2-3 hours)**:")
    print(f"   1. Open: data/TOP20_MANUAL_RESEARCH.md")
    print(f"   2. Research each spike using provided links")
    print(f"   3. Fill in findings sections")
    print(f"   4. Edit: scripts/import_manual_findings.py (add your findings)")
    print(f"   5. Run: python3 scripts/import_manual_findings.py")
    
    print(f"\n**PHASE 2 (Automated - 5 minutes)**:")
    print(f"   6. Run: python3 scripts/auto_correlate_spikes.py")
    print(f"   7. Review auto-correlated events")
    
    print(f"\n**PHASE 3 (Build Dataset - 10 minutes)**:")
    print(f"   8. Run: python3 scripts/build_verified_dataset.py")
    print(f"   9. This fetches 1s data for all verified events")
    print(f"   10. Run backtest with new optimized dataset")
    
    print(f"\n{'='*100}")
    print("✅ Setup complete! Start with data/TOP20_MANUAL_RESEARCH.md")
    print(f"{'='*100}\n")
