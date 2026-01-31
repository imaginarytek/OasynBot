#!/usr/bin/env python3
"""
Audit Event Alignment
Forensic tool to find the TRUE market impact time vs the CLAIMED event time.
"""
import sqlite3
import pandas as pd
import json
import numpy as np

DB_PATH = 'data/hedgemony.db'

def audit_event(event_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM master_events WHERE id=?", (event_id,)).fetchone()
    conn.close()
    
    if not row:
        print(f"Event {event_id} not found.")
        return

    print(f"\n🕵️‍♂️ AUDITING EVENT: {row['title']}")
    print(f"📅 Claimed Timestamp: {row['timestamp']}")
    
    if not row['sol_price_data']:
        print("❌ No price data found.")
        return

    # Load Data
    data = json.loads(row['sol_price_data'])
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Calculate 1-second returns
    df['return'] = df['close'].pct_change()
    df['volatility'] = df['return'].abs()
    
    # Find the SINGLE BIGGEST 1-SECOND MOVE
    max_idx = df['volatility'].idxmax()
    max_row = df.iloc[max_idx]
    
    max_time = max_row['timestamp']
    max_vol = max_row['volatility'] * 100
    
    # Find the BIGGEST 5-MINUTE CRASH
    # Rolling 300s return
    df['rolling_5m'] = df['close'].pct_change(periods=300)
    min_5m_idx = df['rolling_5m'].idxmin() # Biggest drop
    max_5m_idx = df['rolling_5m'].idxmax() # Biggest pump
    
    drop_row = df.iloc[min_5m_idx]
    pump_row = df.iloc[max_5m_idx]
    
    print(f"\n💥 IMPACT ANALYSIS:")
    print(f"   Max 1s Volatility: {max_vol:.2f}% at {max_time}")
    print(f"   Max 5m Drop:       {drop_row['rolling_5m']*100:.2f}% at {drop_row['timestamp']}")
    print(f"   Max 5m Pump:       {pump_row['rolling_5m']*100:.2f}% at {pump_row['timestamp']}")
    
    # Calculate Misalignment
    claimed_dt = pd.to_datetime(row['timestamp']).replace(tzinfo=None)
    impact_dt = max_time.replace(tzinfo=None)
    
    diff_seconds = (impact_dt - claimed_dt).total_seconds()
    
    print(f"\n⏱️  ALIGNMENT CHECK:")
    print(f"   Gap: {diff_seconds:.0f} seconds")
    
    if abs(diff_seconds) > 300:
        print("   ❌ MAJOR MISALIGNMENT DETECTED (> 5 mins)")
        print(f"   Recommendation: Update timestamp to {max_time}")
    else:
        print("   ✅ Alignment looks reasonable.")

if __name__ == "__main__":
    # Audit Scimitar (ID 1) and Binance (ID 2)
    audit_event(1)
    audit_event(2)
