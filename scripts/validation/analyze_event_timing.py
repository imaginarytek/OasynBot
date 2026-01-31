#!/usr/bin/env python3
"""
Analyze Event Timing - Deep Dive into Price Movement

Shows second-by-second price action to verify correlation quality.
"""
import sqlite3
import json
import pandas as pd
import sys

INPUT_DB_PATH = 'data/hedgemony.db'
VALIDATION_DB_PATH = 'data/hedgemony_validation.db'

def analyze_event(event_id):
    """Analyze second-by-second price movement for an event"""
    input_conn = sqlite3.connect(INPUT_DB_PATH)
    input_conn.row_factory = sqlite3.Row

    validation_conn = sqlite3.connect(VALIDATION_DB_PATH)
    validation_conn.row_factory = sqlite3.Row

    # Get event data
    event = input_conn.execute("SELECT * FROM master_events WHERE id = ?", (event_id,)).fetchone()

    if not event:
        print(f"Event {event_id} not found")
        input_conn.close()
        validation_conn.close()
        return

    # Get validation metrics
    metrics = validation_conn.execute("SELECT * FROM event_metrics WHERE event_id = ?", (event_id,)).fetchone()
    time_to_impact = metrics['time_to_impact_seconds'] if metrics else None

    print("=" * 80)
    print(f"EVENT {event_id}: {event['title']}")
    print("=" * 80)
    print(f"Timestamp: {event['timestamp']}")
    print(f"Source: {event['source']}")
    print(f"Stored time_to_impact: {time_to_impact}s")
    print()

    if not event['sol_price_data']:
        print("No price data available")
        return

    # Load price data
    price_data = json.loads(event['sol_price_data'])
    df = pd.DataFrame(price_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['close'] = pd.to_numeric(df['close'])
    df['open'] = pd.to_numeric(df['open'])
    df['high'] = pd.to_numeric(df['high'])
    df['low'] = pd.to_numeric(df['low'])

    # Normalize timezone
    if df['timestamp'].dt.tz is None:
        df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')

    # Event time
    event_time = pd.to_datetime(event['timestamp'])
    if event_time.tzinfo is None:
        event_time = event_time.tz_localize('UTC')

    # Calculate time from event and price changes
    df['seconds_from_event'] = (df['timestamp'] - event_time).dt.total_seconds()
    base_price = df.iloc[0]['close']
    df['pct_change_from_start'] = ((df['close'] - base_price) / base_price * 100)
    df['abs_pct_change'] = df['pct_change_from_start'].abs()

    # Show first 60 seconds
    print("SECOND-BY-SECOND PRICE ACTION (First 60 seconds):")
    print("=" * 80)
    print(f"{'Sec':<5} {'Time (UTC)':<12} {'Open':<8} {'High':<8} {'Low':<8} {'Close':<8} {'Change %':<10}")
    print("=" * 80)

    first_move_idx = None
    first_move_time = None

    for idx, row in df.head(65).iterrows():
        sec = int(row['seconds_from_event'])
        time_str = str(row['timestamp'])[11:19]

        # Mark first significant move
        marker = ""
        if row['abs_pct_change'] >= 0.1 and first_move_idx is None:
            first_move_idx = idx
            first_move_time = sec
            marker = " ← FIRST >0.1% MOVE"

        print(f"{sec:<5} {time_str:<12} {row['open']:<8.2f} {row['high']:<8.2f} "
              f"{row['low']:<8.2f} {row['close']:<8.2f} {row['pct_change_from_start']:<+10.3f}{marker}")

    print("=" * 80)

    if first_move_idx is not None:
        print(f"\nFIRST >0.1% MOVE: {first_move_time} seconds after news")
        print(f"Price at move: ${df.iloc[first_move_idx]['close']:.2f}")
        print(f"Move size: {df.iloc[first_move_idx]['pct_change_from_start']:+.3f}%")
    else:
        print(f"\nNO >0.1% MOVE in first 60 seconds")
        max_move = df.head(60)['abs_pct_change'].max()
        print(f"Maximum absolute move: {max_move:.3f}%")

    # Check for earlier smaller moves
    print("\n" + "=" * 80)
    print("SENSITIVITY ANALYSIS: When did price start moving?")
    print("=" * 80)

    thresholds = [0.01, 0.02, 0.05, 0.1, 0.2, 0.5]
    for thresh in thresholds:
        first_cross = df[df['abs_pct_change'] >= thresh].head(1)
        if len(first_cross) > 0:
            sec = int(first_cross.iloc[0]['seconds_from_event'])
            pct = first_cross.iloc[0]['pct_change_from_start']
            print(f"  >{thresh:4.2f}% threshold crossed at: {sec:3d}s ({pct:+.3f}%)")
        else:
            print(f"  >{thresh:4.2f}% threshold: NEVER CROSSED")

    input_conn.close()
    validation_conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        event_id = int(sys.argv[1])
    else:
        # Default to event 5
        event_id = 5

    analyze_event(event_id)
