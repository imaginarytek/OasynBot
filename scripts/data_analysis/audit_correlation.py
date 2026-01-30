
import sqlite3
import json
import numpy as np
import pandas as pd
from datetime import datetime, timezone

def audit_correlation():
    print("🚀 AUDITING NEWS-TO-PRICE CORRELATION LATENCY...")
    conn = sqlite3.connect("data/hedgemony.db") # Using confirmed path
    c = conn.cursor()
    
    c.execute("SELECT title, timestamp, sol_price_data FROM gold_events WHERE sol_price_data IS NOT NULL")
    rows = c.fetchall()
    
    results = []
    
    print(f"{'LAG (s)':<10} | {'EVENT TITLE':<50} | {'IMPULSE TIME'}")
    print("-" * 80)
    
    for row in rows:
        title, ts_str, raw_data = row
        
        # Parse News Time
        try:
            news_time = datetime.fromisoformat(ts_str.replace("Z", "")).replace(tzinfo=timezone.utc)
        except:
            continue # Skip bad formats
            
        candles = json.loads(raw_data)
        if len(candles) < 100: continue
        
        df = pd.DataFrame(candles)
        df['ts_obj'] = pd.to_datetime(df['timestamp'])
        
        # Identify Baseline Volume (first 2 mins or pre-news)
        # We assume data starts -2 mins before news.
        # Find index of News Time
        
        # Closest candle to News Time
        # Using searchsorted requires sorted index
        
        # Simple method: Iterate
        impulse_time = None
        
        # Look for the first candle AFTER news_time that has abnormally high volume/move
        # Threshold: 3x mean volume of previous 60s?
        # Or just biggest move?
        
        # Let's find the First Explosion.
        # Calc relative volume
        df['vol_rolling'] = df['volume'].rolling(60).mean().shift(1) # 1m avg
        df['vol_mult'] = df['volume'] / df['vol_rolling']
        
        df['price_change'] = df['close'].pct_change().abs()
        
        # Filter for time > news_time - 30s (Catch slightly early) and < news_time + 10m
        mask = (df['ts_obj'] >= (news_time - timedelta(seconds=30))) & \
               (df['ts_obj'] <= (news_time + timedelta(minutes=10)))
               
        window = df[mask]
        
        # Panic Trigger: Vol > 5x OR Price Change > 0.1% in 1s
        triggers = window[ (window['vol_mult'] > 5) | (window['price_change'] > 0.001) ]
        
        if not triggers.empty:
            first_trigger = triggers.iloc[0]
            impulse_time = first_trigger['ts_obj']
            lag = (impulse_time - news_time).total_seconds()
            
            results.append({
                "title": title,
                "lag": lag,
                "news": news_time,
                "impulse": impulse_time
            })
            
            # Color code output
            status = "✅"
            if lag < -5: status = "⚠️ EARLY"
            elif lag > 300: status = "⚠️ LATE"
            
            print(f"{status} {lag:>6.1f}s | {title[:48]:<50} | {impulse_time.time()}")
            
        else:
            # No explosion found?
            # print(f"❓ No Impulse | {title[:48]}")
            pass

    # Summary Stats
    lags = [r['lag'] for r in results]
    if lags:
        avg_lag = np.mean(lags)
        med_lag = np.median(lags)
        print("-" * 80)
        print(f"📊 SUMMARY: Analyzed {len(results)} Events")
        print(f"   Median Latency: {med_lag:.1f} seconds")
        print(f"   Average Latency: {avg_lag:.1f} seconds")
        print(f"   Ideally, median should be 0s - 60s.")

from datetime import timedelta
if __name__ == "__main__":
    audit_correlation()
