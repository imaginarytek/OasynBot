#!/usr/bin/env python3
"""
Fetch Hourly History
Downloads 1 year of SOL/USDT hourly candles from Binance to populate price_history.
"""
import requests
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import time

DB_PATH = 'data/hedgemony.db'
SYMBOL = 'SOLUSDT'
INTERVAL = '1h'
DAYS = 365

def create_table(conn):
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS price_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            symbol TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            UNIQUE(timestamp, symbol)
        )
    """)
    conn.commit()

def fetch_binance_klines(symbol, interval, start_time_ms, end_time_ms):
    url = "https://api.binance.com/api/v3/klines"
    all_data = []
    current_start = start_time_ms
    
    print(f"🌍 Fetching data for {symbol} ({interval})...")
    
    while current_start < end_time_ms:
        params = {
            'symbol': symbol,
            'interval': interval,
            'startTime': current_start,
            'endTime': end_time_ms,
            'limit': 1000
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            if not isinstance(data, list):
                print(f"❌ Error: {data}")
                break
                
            if len(data) == 0:
                break
                
            all_data.extend(data)
            
            # Update start time to timestamp of last candle + 1ms
            last_timestamp = data[-1][0]
            current_start = last_timestamp + 1
            
            # Progress indicator
            dt = datetime.fromtimestamp(last_timestamp / 1000)
            print(f"   Fetched up to {dt.strftime('%Y-%m-%d %H:%M')}")
            
            time.sleep(0.1) # Be nice to API
            
        except Exception as e:
            print(f"❌ Connection Error: {e}")
            break
            
    return all_data

def save_to_db(data):
    conn = sqlite3.connect(DB_PATH)
    create_table(conn)
    c = conn.cursor()
    
    parsed_data = []
    symbol = 'SOL/USDT' # Standardized format for DB
    
    print("💾 Saving to database...")
    for dl in data:
        # Binance: [Open Time, Open, High, Low, Close, Volume, ...]
        ts = datetime.fromtimestamp(dl[0] / 1000).isoformat()
        
        try:
            c.execute("""
                INSERT OR IGNORE INTO price_history 
                (timestamp, symbol, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                ts, symbol, 
                float(dl[1]), float(dl[2]), float(dl[3]), float(dl[4]), float(dl[5])
            ))
        except Exception as e:
            pass
            
    conn.commit()
    print(f"✅ Successfully saved {len(data)} hourly candles.")
    conn.close()

def main():
    # Fetch verified history (2023-2024) ensuring we have researchable events
    start_time = datetime(2023, 1, 1)
    end_time = datetime(2024, 1, 1)
    
    print(f"📅 Fetching history from {start_time} to {end_time}")
    
    start_ms = int(start_time.timestamp() * 1000)
    end_ms = int(end_time.timestamp() * 1000)
    
    klines = fetch_binance_klines(SYMBOL, INTERVAL, start_ms, end_ms)
    
    if klines:
        save_to_db(klines)
    else:
        print("❌ No data fetched.")

if __name__ == "__main__":
    main()
