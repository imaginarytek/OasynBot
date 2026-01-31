#!/usr/bin/env python3
"""
Mine Events Professional
Detects high-volatility spikes (>3.0 sigma) in historical hourly data.
This is Step 1 of the Event Collection Workflow.
"""
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Constants
DB_PATH = 'data/hedgemony.db'
Z_SCORE_THRESHOLD = 3.0  # Detect anything above 3 sigma
MIN_HOURLY_MOVE = 0.02   # Ignore spikes smaller than 2% move

def fetch_hourly_data():
    """Fetch hourly OHLCV data for SOL/USDT from database or API simulation"""
    conn = sqlite3.connect(DB_PATH)
    
    # Check if price_history exists
    try:
        df = pd.read_sql("SELECT * FROM price_history ORDER BY timestamp ASC", conn)
        # Use ISO8601 parsing or mixed to handle the DB format
        df['timestamp'] = pd.to_datetime(df['timestamp'], format='ISO8601') 
        df.set_index('timestamp', inplace=True)
    except Exception as e:
        print(f"⚠️ Could not load from DB: {e}")
        print("Using synthetic data for demonstration (You need to populate price_history first!)")
        
        # Create synthetic data if DB is empty (for testing flow)
        dates = pd.date_range(start='2023-01-01', end='2024-01-01', freq='h')
        df = pd.DataFrame(index=dates)
        df['open'] = 100 + np.random.randn(len(df)).cumsum()
        df['close'] = df['open'] * (1 + np.random.randn(len(df)) * 0.01)
        # Inject a massive spike
        df.iloc[500]['close'] = df.iloc[500]['open'] * 1.15 # +15% spike
        
    conn.close()
    return df

def detect_spikes(df):
    """Calculate Z-scores and identify spikes"""
    print(f"📉 Analyzing {len(df)} hourly candles...")
    
    # Calculate returns
    df['return'] = (df['close'] - df['open']) / df['open']
    
    # Calculate rolling volatility (30-day window)
    window_size = 24 * 30 
    df['rolling_std'] = df['return'].rolling(window=window_size).std()
    
    # Calculate Z-Score
    df['z_score'] = df['return'].abs() / df['rolling_std']
    
    # Filter for spikes
    spikes = df[
        (df['z_score'] > Z_SCORE_THRESHOLD) & 
        (df['return'].abs() > MIN_HOURLY_MOVE)
    ].copy()
    
    return spikes.sort_values(by='z_score', ascending=False)

def save_spikes(spikes):
    """Save detected spikes to DB for manual research"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Create extraction table if not exists
    c.execute("""
        CREATE TABLE IF NOT EXISTS potential_event_spikes (
            timestamp TEXT PRIMARY KEY,
            symbol TEXT DEFAULT 'SOL/USDT',
            return_pct REAL,
            z_score REAL,
            status TEXT DEFAULT 'new' -- new, researching, verified, rejected
        )
    """)
    
    count = 0
    for ts, row in spikes.iterrows():
        try:
            c.execute("""
                INSERT OR IGNORE INTO potential_event_spikes (timestamp, return_pct, z_score)
                VALUES (?, ?, ?)
            """, (ts.isoformat(), row['return'], row['z_score']))
            if c.rowcount > 0:
                count += 1
        except Exception as e:
            print(f"Error saving {ts}: {e}")
            
    conn.commit()
    conn.close()
    return count

def main():
    print("="*60)
    print("💎 MINE EVENTS PROFESSIONAL: Volatility Detection")
    print("="*60)
    
    df = fetch_hourly_data()
    spikes = detect_spikes(df)
    
    print(f"\n📊 Found {len(spikes)} significant volatility spikes (Z > {Z_SCORE_THRESHOLD})")
    
    if len(spikes) > 0:
        print("\nTop 20 Spikes:")
        print(spikes[['return', 'z_score']].head(20))
        
        saved = save_spikes(spikes)
        print(f"\n✅ Saved {saved} new spikes to 'potential_event_spikes' table.")
        print("👉 Next Step: Use 'search_web' to research these timestamps and identify the news.")
    else:
        print("No spikes found. Try lowering threshold or fetching more data.")

if __name__ == "__main__":
    main()
