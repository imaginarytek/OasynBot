#!/usr/bin/env python3
"""
Refine Spike Timing: From Hourly Windows to Exact Minute

Problem: mine_events_professional.py detects spikes on hourly candles,
but we need the exact MINUTE to search for news sources.

This script:
1. Loads hourly spikes from potential_event_spikes
2. Fetches 1-minute candles for each spike hour
3. Identifies the exact minute with highest volatility
4. Updates the spike record with refined timestamp
5. Generates research guide for manual news verification

Run this AFTER mine_events_professional.py and BEFORE manual research.
"""

import sqlite3
import requests
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Constants
DB_PATH = 'data/hedgemony.db'
SYMBOL = 'SOLUSDT'
BINANCE_API = 'https://api.binance.com/api/v3/klines'

# Color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_binance_klines(symbol, interval, start_time, end_time, max_retries=3):
    """
    Fetch klines from Binance with retry logic.

    Args:
        symbol: Trading pair (e.g., 'SOLUSDT')
        interval: Candle interval ('1m', '5m', '1h')
        start_time: Start timestamp (datetime)
        end_time: End timestamp (datetime)
        max_retries: Number of retry attempts

    Returns:
        List of klines or None if failed
    """
    start_ms = int(start_time.timestamp() * 1000)
    end_ms = int(end_time.timestamp() * 1000)

    params = {
        'symbol': symbol,
        'interval': interval,
        'startTime': start_ms,
        'endTime': end_ms,
        'limit': 1000
    }

    for attempt in range(max_retries):
        try:
            response = requests.get(BINANCE_API, params=params, timeout=10)

            if response.status_code == 429:  # Rate limit
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"    {YELLOW}Rate limited. Waiting {wait_time}s...{RESET}")
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            data = response.json()

            if not isinstance(data, list):
                print(f"    {RED}Unexpected API response: {data}{RESET}")
                return None

            return data

        except requests.RequestException as e:
            if attempt < max_retries - 1:
                print(f"    {YELLOW}Request failed (attempt {attempt+1}/{max_retries}): {e}{RESET}")
                time.sleep(1)
            else:
                print(f"    {RED}Failed after {max_retries} attempts: {e}{RESET}")
                return None

    return None


def find_exact_spike_minute(hourly_timestamp_str):
    """
    Given an hourly timestamp, find the exact minute with highest volatility.

    Args:
        hourly_timestamp_str: ISO timestamp of hourly candle (e.g., '2023-06-05T16:00:00')

    Returns:
        dict with:
            - exact_timestamp: ISO timestamp of spike minute
            - volatility: Volatility measure
            - price_range_pct: Price range % for that minute
            - volume: Trading volume
            - reason: Explanation or error message
    """
    try:
        hourly_time = pd.to_datetime(hourly_timestamp_str)
    except Exception as e:
        return {'exact_timestamp': None, 'reason': f'Invalid timestamp: {e}'}

    # Fetch 1-minute candles for the hour
    hour_start = hourly_time
    hour_end = hourly_time + timedelta(hours=1)

    print(f"    Fetching 1-minute data: {hour_start} to {hour_end}")

    klines = fetch_binance_klines(SYMBOL, '1m', hour_start, hour_end)

    if not klines or len(klines) == 0:
        return {'exact_timestamp': None, 'reason': 'No 1-minute data available (event too old?)'}

    # Convert to DataFrame
    df = pd.DataFrame(klines, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_vol', 'trades', 'tb_base', 'tb_quote', 'ignore'
    ])

    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    # Calculate volatility metrics for each minute
    df['price_range'] = df['high'] - df['low']
    df['price_range_pct'] = (df['price_range'] / df['open']) * 100
    df['abs_return'] = abs((df['close'] - df['open']) / df['open']) * 100

    # Combined volatility score: range + absolute return
    df['volatility_score'] = df['price_range_pct'] + (df['abs_return'] * 2)

    # Find minute with highest volatility
    max_idx = df['volatility_score'].idxmax()
    spike_row = df.loc[max_idx]

    result = {
        'exact_timestamp': spike_row['timestamp'].isoformat(),
        'volatility': float(spike_row['volatility_score']),
        'price_range_pct': float(spike_row['price_range_pct']),
        'volume': float(spike_row['volume']),
        'open': float(spike_row['open']),
        'high': float(spike_row['high']),
        'low': float(spike_row['low']),
        'close': float(spike_row['close']),
        'reason': 'Successfully refined to exact minute'
    }

    return result


def refine_all_spikes():
    """
    Refine all spikes in potential_event_spikes table.

    Updates each record with:
    - refined_timestamp: Exact minute of spike
    - volatility_1m: 1-minute volatility score
    - status: Updated to 'refined'
    """
    print("=" * 80)
    print(f"{BLUE}SPIKE TIMING REFINER{RESET}")
    print("=" * 80)
    print(f"\nThis script narrows hourly spikes down to the exact minute.\n")

    conn = get_db_connection()
    c = conn.cursor()

    # Check if refined_timestamp column exists, create if not
    try:
        c.execute("ALTER TABLE potential_event_spikes ADD COLUMN refined_timestamp TEXT")
        c.execute("ALTER TABLE potential_event_spikes ADD COLUMN volatility_1m REAL")
        c.execute("ALTER TABLE potential_event_spikes ADD COLUMN price_range_pct REAL")
        conn.commit()
        print(f"{GREEN}✓ Added refined_timestamp columns to database{RESET}\n")
    except sqlite3.OperationalError:
        # Columns already exist
        pass

    # Get spikes that haven't been refined yet
    spikes = c.execute("""
        SELECT timestamp, symbol, return_pct, z_score, status
        FROM potential_event_spikes
        WHERE (status = 'new' OR status IS NULL OR refined_timestamp IS NULL)
        ORDER BY z_score DESC
        LIMIT 20
    """).fetchall()

    if len(spikes) == 0:
        print(f"{YELLOW}No unrefined spikes found.{RESET}")
        print(f"Run mine_events_professional.py first to detect spikes.")
        conn.close()
        return

    print(f"Found {len(spikes)} spikes to refine.\n")
    print("=" * 80)

    refined_count = 0
    failed_count = 0

    for row in spikes:
        hourly_ts = row['timestamp']
        z_score = row['z_score']
        hourly_return = row['return_pct']

        print(f"\n{BLUE}Spike: {hourly_ts}{RESET}")
        print(f"  Hourly Z-Score: {z_score:.2f}")
        print(f"  Hourly Return: {hourly_return*100:.2f}%")

        # Find exact minute
        result = find_exact_spike_minute(hourly_ts)

        if result['exact_timestamp'] is None:
            print(f"  {RED}✗ Failed:{RESET} {result['reason']}")
            failed_count += 1
            continue

        # Display result
        exact_ts = result['exact_timestamp']
        print(f"  {GREEN}✓ Refined to:{RESET} {exact_ts}")
        print(f"    1-min Volatility: {result['volatility']:.2f}")
        print(f"    Price Range: {result['price_range_pct']:.2f}%")
        print(f"    OHLC: O=${result['open']:.2f} H=${result['high']:.2f} "
              f"L=${result['low']:.2f} C=${result['close']:.2f}")

        # Update database
        try:
            c.execute("""
                UPDATE potential_event_spikes
                SET refined_timestamp = ?,
                    volatility_1m = ?,
                    price_range_pct = ?,
                    status = 'refined'
                WHERE timestamp = ?
            """, (exact_ts, result['volatility'], result['price_range_pct'], hourly_ts))
            conn.commit()
            refined_count += 1
        except Exception as e:
            print(f"  {RED}✗ Database update failed: {e}{RESET}")
            failed_count += 1

        # Rate limiting - be nice to Binance
        time.sleep(0.5)

    conn.close()

    # Summary
    print("\n" + "=" * 80)
    print(f"{BLUE}REFINEMENT SUMMARY{RESET}")
    print("=" * 80)
    print(f"\nTotal Processed: {len(spikes)}")
    print(f"  {GREEN}✓ Refined:{RESET}  {refined_count}")
    print(f"  {RED}✗ Failed:{RESET}   {failed_count}")

    if refined_count > 0:
        print(f"\n{GREEN}✓ {refined_count} spikes refined successfully!{RESET}")
        print(f"\n{BLUE}NEXT STEP:{RESET} Generate research guide:")
        print(f"  python3 scripts/validation/generate_research_guide.py")

    print("\n" + "=" * 80)


def main():
    if not os.path.exists(DB_PATH):
        print(f"{RED}Error: Database not found at {DB_PATH}{RESET}")
        sys.exit(1)

    refine_all_spikes()


if __name__ == "__main__":
    main()
