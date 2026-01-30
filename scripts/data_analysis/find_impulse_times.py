
import sqlite3
import json
import pandas as pd
from datetime import datetime, timezone

def find_price_impulse_times():
    """Find the exact second when price started moving for top 10 events"""
    print("🔍 FINDING ACTUAL PRICE IMPULSE TIMES FOR TOP 10 EVENTS...\n")
    conn = sqlite3.connect("data/hedgemony.db")
    c = conn.cursor()
    
    key_events = [
        "President Trump Announces U.S. Crypto Reserve",
        "Jackson Hole Speech: Policy Adjustment", 
        "Spot Bitcoin ETF Anticipation Volatility",
        "Roaring Kitty Returns: 'Lean Forward' Meme",
        "Trump Elected President",
        "Approval of Ether Spot ETFs",
        "Nikkei 225 Plunges 12% in Historic Rout",
        "Binance Lists Book of Meme (BOME)",
        "SEC Closes Investigation into Ethereum 2.0",
        "CPI / FOMC Data Release"
    ]
    
    results = []
    
    for event_title in key_events:
        c.execute("""
            SELECT title, timestamp, sol_price_data 
            FROM gold_events 
            WHERE title LIKE ? 
            AND sol_price_data IS NOT NULL
            LIMIT 1
        """, (f"%{event_title}%",))
        
        row = c.fetchone()
        if not row:
            print(f"❌ No data found for: {event_title}")
            continue
            
        title, ts_str, raw_data = row
        candles = json.loads(raw_data)
        
        if len(candles) < 100:
            continue
        
        df = pd.DataFrame(candles)
        df['ts_obj'] = pd.to_datetime(df['timestamp'])
        df['price_change'] = df['close'].pct_change().abs()
        df['volume'] = pd.to_numeric(df['volume'])
        
        # Calculate rolling averages for baseline
        df['vol_avg'] = df['volume'].rolling(60, min_periods=1).mean()
        df['vol_spike'] = df['volume'] / df['vol_avg']
        
        # Find first major anomaly (volume spike >5x OR price move >0.3%)
        anomalies = df[(df['vol_spike'] > 5) | (df['price_change'] > 0.003)]
        
        if not anomalies.empty:
            first_impulse = anomalies.iloc[0]
            impulse_time = first_impulse['ts_obj']
            
            result = {
                'title': title,
                'current_timestamp': ts_str,
                'actual_impulse': impulse_time.strftime('%Y-%m-%d %H:%M:%S UTC'),
                'impulse_unix': int(impulse_time.timestamp())
            }
            results.append(result)
            
            print(f"📊 {title[:50]}")
            print(f"   Current DB Timestamp: {ts_str}")
            print(f"   Actual Price Impulse: {result['actual_impulse']}")
            print(f"   → Need to find Tier 1 source published BEFORE {result['actual_impulse']}\n")
    
    conn.close()
    return results

if __name__ == "__main__":
    results = find_price_impulse_times()
    
    print("\n" + "="*80)
    print("SUMMARY - Target Times for Tier 1 Source Research:")
    print("="*80)
    for r in results:
        print(f"{r['title'][:45]:<45} | Impulse: {r['actual_impulse']}")
