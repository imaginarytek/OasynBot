#!/usr/bin/env python3
"""
Find Exact Spike Minute
Fetches 1-minute resolution data for target dates to pinpoint the EXACT moment of impact.
"""
import requests
import pandas as pd
from datetime import datetime, timedelta, timezone

SYMBOL = 'SOLUSDT'
INTERVAL = '1m'

TARGET_Dates = [
    "2023-06-15", # BlackRock Filing
    "2023-10-16", # Fake ETF News
    "2023-10-23", # DTCC Rumors
    "2023-10-24"  # DTCC Blowoff
]

def fetch_day_klines(symbol, date_str):
    """Fetch 1m klines for a full 24h day (UTC)"""
    # Force UTC
    start_dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    end_dt = start_dt + timedelta(days=1)
    
    start_ms = int(start_dt.timestamp() * 1000)
    end_ms = int(end_dt.timestamp() * 1000)
    
    url = "https://api.binance.com/api/v3/klines"
    all_data = []
    current_start = start_ms
    
    print(f"  ⬇️  Fetching {date_str}...")
    
    while current_start < end_ms:
        params = {
            'symbol': symbol,
            'interval': '1m',
            'startTime': current_start,
            'endTime': end_ms,
            'limit': 1000
        }
        res = requests.get(url, params=params).json()
        if not res or isinstance(res, dict): break
        all_data.extend(res)
        current_start = res[-1][0] + 1
        
    return all_data

def analyze_day(date_str):
    klines = fetch_day_klines(SYMBOL, date_str)
    if not klines: return
    
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume', 
        'close_time', 'quote_vol', 'trades', 'tb_base', 'tb_quote', 'ignore'
    ])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['close'] = pd.to_numeric(df['close'])
    df['open'] = pd.to_numeric(df['open'])
    
    # Calculate 1m return
    df['return'] = (df['close'] - df['open']) / df['open']
    df['volatility'] = df['return'].abs()
    
    # Sort by biggest candles
    print(f"\n📊 Top 10 Impact Minutes for {date_str}:")
    top = df.nlargest(10, 'volatility')
    
    for _, row in top.iterrows():
        ts = row['timestamp']
        pct = row['return'] * 100
        print(f"   🕒 {ts} UTC  | Move: {pct:+.2f}%")

if __name__ == "__main__":
    print("🔎 Pinpointing Exact Impact Minutes...")
    for d in TARGET_Dates:
        analyze_day(d)
