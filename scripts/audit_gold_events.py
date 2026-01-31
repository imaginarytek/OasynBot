#!/usr/bin/env python3
"""
AUDIT: Master Events Data Quality (Final Check)
"""
import sqlite3
import json
from datetime import datetime

def audit_master_events():
    print("="*80)
    print("🔍 MASTER EVENTS DATA QUALITY AUDIT")
    print("="*80)
    
    conn = sqlite3.connect('data/hedgemony.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Check Count
    c.execute("SELECT count(*) as count FROM master_events")
    count = c.fetchone()['count']
    print(f"\n1. Total Events: {count} (Target: 5)")
    
    if count == 0:
        print("   ❌ CRITICAL: Database is empty!")
        return

    # Check Data Integrity
    c.execute("""
        SELECT title, timestamp, move_5m, verified, description, sol_price_data 
        FROM master_events
    """)
    events = c.fetchall()
    
    print(f"\n2. Event Integrity Check:")
    print(f"{'Title':<60} | {'TimeStamp':<20} | {'5m Move':<10} | {'Data Pts'}")
    print("-" * 110)
    
    for evt in events:
        try:
            price_data = json.loads(evt['sol_price_data'])
            pts = len(price_data)
        except:
            pts = 0
            
        title = evt['title'][:58]
        ts = evt['timestamp']
        move = evt['move_5m']
        
        # Check for ZERO move anomaly
        alert = "⚠️ 0.00%" if (move == 0.0 and pts > 0) else f"{move:.2f}%"
        
        print(f"{title:<60} | {ts:<20} | {alert:<10} | {pts}")
        
        # Deep Dive on Zero check
        if move == 0.0 and pts > 300:
            p0 = price_data[300]['close']
            p300 = price_data[600]['close'] # 5m later (approx)
            print(f"   -> DEBUG: T0({p0}) vs T+5m({p300}). Net: {p300-p0}")
            if p300 == p0:
                print("   -> FACT: Price reverted exactly to start price.")
                
    # Check Text Quality
    print(f"\n3. Verbatim Text Check:")
    for evt in events:
        text = evt['description']
        length = len(text) if text else 0
        status = "✅" if length > 10 else "❌ TOO SHORT"
        print(f"   - {evt['title'][:40]}... : {length} chars {status}")

    conn.close()

if __name__ == "__main__":
    audit_master_events()
