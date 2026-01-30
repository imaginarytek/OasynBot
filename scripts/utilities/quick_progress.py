#!/usr/bin/env python3
"""
Quick progress checker for curated events fetching
"""
import sqlite3

def check():
    conn = sqlite3.connect("data/hedgemony.db")
    c = conn.cursor()
    
    # Count fetched events
    c.execute("SELECT COUNT(*) FROM curated_events WHERE sol_price_data IS NOT NULL")
    fetched = c.fetchone()[0]
    
    # Get latest
    c.execute("""
        SELECT title, timestamp, LENGTH(sol_price_data) as data_size
        FROM curated_events 
        WHERE sol_price_data IS NOT NULL 
        ORDER BY rowid DESC 
        LIMIT 1
    """)
    latest = c.fetchone()
    
    conn.close()
    
    progress_pct = (fetched / 100) * 100
    
    print(f"\n{'='*70}")
    print(f"📊 CURATED EVENTS FETCH PROGRESS")
    print(f"{'='*70}")
    print(f"✅ Fetched: {fetched}/100 ({progress_pct:.1f}%)")
    print(f"⏳ Remaining: {100 - fetched}")
    
    if latest:
        title, ts, size = latest
        candles_approx = size // 200  # Rough estimate
        print(f"\n📍 Latest Event:")
        print(f"   {title}")
        print(f"   {ts}")
        print(f"   ~{candles_approx:,} candles")
    
    print(f"{'='*70}\n")
    
    if fetched == 100:
        print("🎉 COMPLETE! All 100 events fetched successfully!")
    else:
        est_remaining_min = (100 - fetched) * 0.3  # ~20s per event
        print(f"⏱️  Estimated time remaining: ~{est_remaining_min:.0f} minutes")

if __name__ == "__main__":
    check()
