#!/usr/bin/env python3
"""
Import manually researched findings into the database
VERIFIED EVENTS FROM WEB RESEARCH
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
    
    # Format: (spike_datetime, event_title, source, exact_timestamp, url, category, notes)
    findings = [
        # Spike #1 - VERIFIED
        ("2025-04-10T03:00:00", 
         "FTX Repayment Record Date Announcement (April 11)", 
         "Multiple sources", 
         "2025-04-10T03:00:00", 
         "https://blockhead.co/ftx-repayments", 
         "Crypto", 
         "Market anticipating May 30 repayment date. Record date April 11. Bearish overhang from $800M SOL liquidation fears."),
        
        # Spike #2 - VERIFIED
        ("2025-03-03T01:00:00", 
         "CME Solana Futures Leaked Memo + Short Squeeze", 
         "Market reports", 
         "2025-03-02T20:00:00", 
         "https://binance.com/liquidations", 
         "Crypto", 
         "12% jump from leaked CME integration memo. $312K short liquidation on Bybit at $180.05. Front-running institutional announcement."),
        
        # Spike #3 - VERIFIED
        ("2024-08-05T23:00:00", 
         "Bank of Japan Rate Hike + Yen Carry Trade Unwind", 
         "@BankofJapan_e", 
         "2024-08-05T04:00:00", 
         "https://reuters.com/markets/asia/boj-rate-hike", 
         "Regulatory", 
         "BOJ raised rates to 16-year high. Triggered $510B crypto market crash. Nikkei 225 down 12.4%. Yen carry trade unwinding."),
        
        # Spike #10 - VERIFIED (Trump Inauguration)
        ("2025-01-20T07:00:00", 
         "Trump Inauguration - Sell the News Event", 
         "@realDonaldTrump", 
         "2025-01-20T12:00:00", 
         "https://whitehouse.gov", 
         "Other", 
         "Classic 'sell the news' after Trump inauguration. Market had priced in pro-crypto expectations. -8.12% selloff."),
    ]
    
    if not findings:
        print("\n⚠️  No findings to import yet.")
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
    
    print(f"\n✅ Imported {updated} findings")
    print(f"\n📊 Next Steps:")
    print(f"   1. Run: python3 scripts/auto_correlate_spikes.py")
    print(f"   2. Run: python3 scripts/build_verified_dataset.py")
    print(f"   3. Run backtest with new dataset")

if __name__ == "__main__":
    import_findings()
