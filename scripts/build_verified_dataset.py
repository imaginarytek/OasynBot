#!/usr/bin/env python3
"""
Build Verified Dataset
Fetches 1-second resolution price data from Binance for every verified event.
Writes:
- Price data (sol_price_data) → hedgemony.db (input DB)
- Impact metrics (move_5s, move_30s, etc.) → hedgemony_validation.db (validation DB)
"""
import sqlite3
import requests
import json
import time
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Database paths
INPUT_DB_PATH = 'data/hedgemony.db'
VALIDATION_DB_PATH = 'data/hedgemony_validation.db'
TABLE_NAME = 'master_events'
SYMBOL = 'SOLUSDT'
INTERVAL = '1s'

# Fetch Window
PRE_EVENT_SECONDS = 300   # 5 minutes before
POST_EVENT_SECONDS = 7200 # 2 hours after

def get_db_connections():
    """Create connections to both databases"""
    input_conn = sqlite3.connect(INPUT_DB_PATH)
    input_conn.row_factory = sqlite3.Row

    validation_conn = sqlite3.connect(VALIDATION_DB_PATH)
    validation_conn.row_factory = sqlite3.Row

    return input_conn, validation_conn

def fetch_binance_klines(symbol, interval, start_ms, end_ms):
    """Fetch all klines in range, handling pagination limits"""
    url = "https://api.binance.com/api/v3/klines"
    all_data = []
    current_start = start_ms
    
    while current_start < end_ms:
        params = {
            'symbol': symbol,
            'interval': interval,
            'startTime': current_start,
            'endTime': end_ms,
            'limit': 1000
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            if not isinstance(data, list):
                print(f"    ❌ API Error: {data}")
                break
            
            if len(data) == 0:
                break
                
            all_data.extend(data)
            
            # Update start to last candle + 1ms
            last_timestamp = data[-1][0]
            current_start = last_timestamp + 1
            
            # Respect rate limits
            time.sleep(0.1)
            
        except Exception as e:
            print(f"    ❌ Connection Error: {e}")
            time.sleep(1) # Backoff
            
    return all_data

def process_price_data(klines):
    """Convert raw klines to DataFrame and calculate moves"""
    if not klines:
        return None, {}
        
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume', 
        'close_time', 'quote_vol', 'trades', 'tb_base', 'tb_quote', 'ignore'
    ])
    
    # Clean types
    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    
    # Keep only essential columns for storage
    storage_df = df[['timestamp', 'open', 'high', 'low', 'close', 'volume']].copy()
    
    # Calculate Impact Metrics (relative to start)
    # We assume index 0 IS near T-300s. We need T=0.
    # Actually, simpler: We calculate moves relative to the OPEN of the window vs CLOSE at logic steps
    # But better: Calculate relative to the price AT THE EVENT TIME.
    
    # For storage simplicity, we return the list of dicts stringified
    json_data = storage_df.to_json(orient='records', date_format='iso')
    
    return json_data, df

def update_event_metrics(input_conn, validation_conn, event_id, df, target_timestamp_iso):
    """
    Calculate moves relative to the exact event timestamp.
    Writes:
    - Price data → hedgemony.db (input DB)
    - Impact metrics → hedgemony_validation.db (validation DB)
    """
    # Find the row closest to target_timestamp
    target_dt = pd.to_datetime(target_timestamp_iso)

    # Ensure timezone awareness match (UTC)
    if target_dt.tzinfo is None:
        target_dt = target_dt.replace(tzinfo=pd.Timestamp.min.tzinfo) # fallback

    # Find index of candle closest to event time
    # Note: df['timestamp'] might be naive or tz-aware. Binance is UTC.
    try:
        # Convert to UTC if needed
        df['timestamp'] = df['timestamp'].dt.tz_localize(None)
        target_dt_naive = target_dt.replace(tzinfo=None)

        # Get index
        event_idx = df.index[df['timestamp'] >= target_dt_naive].min()

        if pd.isna(event_idx):
            print("    ⚠️ Event time is outside fetched window?")
            return

        # Base price is the OPEN of the event second
        base_price = df.loc[event_idx, 'open']

        # Helper to get move %
        def get_move(seconds_fwd):
            future_idx = event_idx + seconds_fwd
            if future_idx in df.index:
                price = df.loc[future_idx, 'close']
                return ((price - base_price) / base_price) * 100
            return None

        move_5s = get_move(5)
        move_30s = get_move(30)
        move_5m = get_move(300)
        move_30m = get_move(1800)
        move_1h = get_move(3600)

        # Update INPUT DB (price data only - bot can see this)
        input_conn.execute("""
            UPDATE master_events
            SET sol_price_data = ?,
                last_updated = ?
            WHERE id = ?
        """, (
            df.to_json(orient='records', date_format='iso'),
            datetime.now().isoformat(),
            event_id
        ))

        # Update VALIDATION DB (impact metrics - bot CANNOT see this)
        validation_conn.execute("""
            UPDATE event_metrics
            SET move_5s = ?,
                move_30s = ?,
                move_5m = ?,
                move_30m = ?,
                move_1h = ?,
                last_updated = ?
            WHERE event_id = ?
        """, (
            move_5s,
            move_30s,
            move_5m,
            move_30m,
            move_1h,
            datetime.now().isoformat(),
            event_id
        ))

        input_conn.commit()
        validation_conn.commit()
        print(f"    ✅ Updated both DBs: 5m Move = {move_5m:.2f}%")

    except Exception as e:
        print(f"    ❌ Calc Error: {e}")


def main():
    print("="*60)
    print("🏗️  BUILDING VERIFIED DATASET (1-Second Resolution)")
    print("="*60)

    # Connect to both databases
    input_conn, validation_conn = get_db_connections()

    # Get all events from input DB
    events = input_conn.execute("""
        SELECT id, title, timestamp
        FROM master_events
        ORDER BY timestamp DESC
    """).fetchall()

    # Get verified status from validation DB
    verified_ids = set()
    for row in validation_conn.execute("SELECT event_id FROM event_metrics WHERE verified = 1"):
        verified_ids.add(row['event_id'])

    # Filter to verified events only
    verified_events = [e for e in events if e['id'] in verified_ids]

    print(f"Found {len(verified_events)} verified events to hydrate.")
    
    for row in verified_events:
        eid = row['id']
        title = row['title']
        ts_str = row['timestamp']

        print(f"\nProcessing ID {eid}: {title}")
        print(f"  Time: {ts_str}")

        # Parse Time
        try:
            event_dt = pd.to_datetime(ts_str)
            start_dt = event_dt - timedelta(seconds=PRE_EVENT_SECONDS)
            end_dt = event_dt + timedelta(seconds=POST_EVENT_SECONDS)

            start_ms = int(start_dt.timestamp() * 1000)
            end_ms = int(end_dt.timestamp() * 1000)

            # Fetch
            print(f"  ⬇️  Fetching 1s candles ({PRE_EVENT_SECONDS}s pre, {POST_EVENT_SECONDS}s post)...")
            klines = fetch_binance_klines(SYMBOL, INTERVAL, start_ms, end_ms)

            if not klines or len(klines) < 100:
                print("    ⚠️ No data found (Event might be too old for 1s data or API issue)")
                continue

            print(f"    Got {len(klines)} candles.")

            # Process & Save to both databases
            _, df = process_price_data(klines)
            update_event_metrics(input_conn, validation_conn, eid, df, ts_str)

        except Exception as e:
            print(f"  ❌ Error: {e}")

    # Close both connections
    input_conn.close()
    validation_conn.close()

    print("\n" + "="*60)
    print("Done. Price data → hedgemony.db, Metrics → hedgemony_validation.db")

if __name__ == "__main__":
    main()
