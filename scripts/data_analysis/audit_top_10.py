
import sqlite3
import json
import pandas as pd
from datetime import datetime, timezone, timedelta

def audit_top_10_correlation():
    print("🚀 AUDITING TOP 10 EVENTS - NEWS-TO-PRICE CORRELATION...")
    conn = sqlite3.connect("data/hedgemony.db")
    c = conn.cursor()
    
    # Target the 10 key events we just updated
    key_events = [
        "President Trump Announces U.S. Crypto Reserve",
        "Jackson Hole Speech: Policy Adjustment",
        "Spot Bitcoin ETF Anticipation Volatility",
        "Roaring Kitty Returns: 'Lean Forward' Meme",
        "Trump Elected President",
        "Approval of Ether Spot ETFs",
        "Nikkei 225 Plunges 12% in Historic Rout",
        "Binance Lists Book of Meme (BOME)"
    ]
    
    print(f"\n{'EVENT':<50} | {'NEWS TIME (UTC)':<20} | {'IMPULSE TIME':<20} | {'LAG (s)'}")
    print("-" * 120)
    
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
            continue
            
        title, ts_str, raw_data = row
        
        # Parse News Time
        try:
            news_time = datetime.fromisoformat(ts_str.replace("Z", "")).replace(tzinfo=timezone.utc)
        except:
            continue
            
        candles = json.loads(raw_data)
        if len(candles) < 100:
            continue
        
        df = pd.DataFrame(candles)
        df['ts_obj'] = pd.to_datetime(df['timestamp'])
        df['price_change'] = df['close'].pct_change().abs()
        
        # Find first major move within +/- 2 minutes of news time
        window_start = news_time - timedelta(seconds=120)
        window_end = news_time + timedelta(minutes=5)
        
        mask = (df['ts_obj'] >= window_start) & (df['ts_obj'] <= window_end)
        window = df[mask]
        
        # Find biggest move
        if not window.empty:
            max_move_idx = window['price_change'].idxmax()
            impulse_row = window.loc[max_move_idx]
            impulse_time = impulse_row['ts_obj']
            lag = (impulse_time - news_time).total_seconds()
            
            status = "✅" if -5 <= lag <= 60 else "⚠️"
            
            print(f"{status} {title[:48]:<50} | {news_time.strftime('%Y-%m-%d %H:%M:%S'):<20} | {impulse_time.strftime('%H:%M:%S'):<20} | {lag:>6.0f}s")
    
    conn.close()

if __name__ == "__main__":
    audit_top_10_correlation()
