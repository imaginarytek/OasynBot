#!/usr/bin/env python3
"""
Test New Timestamp for Event

Use this to test if a new source timestamp improves the lag calculation.
"""

import sqlite3
import json
import pandas as pd
import sys
from datetime import datetime

DB_PATH = 'data/hedgemony.db'

def test_timestamp(event_id, new_timestamp_str):
    """
    Test how a new timestamp would affect lag calculation.

    Args:
        event_id: Event ID to test
        new_timestamp_str: New timestamp to test (ISO format)
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    event = conn.execute("SELECT * FROM master_events WHERE id = ?", (event_id,)).fetchone()

    if not event:
        print(f"Event {event_id} not found")
        return

    print("=" * 80)
    print(f"TESTING NEW TIMESTAMP FOR EVENT {event_id}")
    print("=" * 80)
    print(f"\nEvent: {event['title']}")
    print(f"\nCurrent Source: {event['source']}")
    print(f"Current Timestamp: {event['timestamp']}")
    print(f"Current Lag: {event['time_to_impact_seconds']}s")

    # Load price data
    if not event['sol_price_data']:
        print("\nNo price data available")
        return

    price_data = json.loads(event['sol_price_data'])
    df = pd.DataFrame(price_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['close'] = pd.to_numeric(df['close'])

    # Normalize timezone
    if df['timestamp'].dt.tz is None:
        df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')

    # Test new timestamp
    new_event_time = pd.to_datetime(new_timestamp_str)
    if new_event_time.tzinfo is None:
        new_event_time = new_event_time.tz_localize('UTC')

    print(f"\n{'-' * 80}")
    print(f"TESTING NEW TIMESTAMP: {new_timestamp_str}")
    print(f"{'-' * 80}")

    # Find new event position in price data
    df['time_diff'] = (df['timestamp'] - new_event_time).abs()
    new_event_idx = df['time_diff'].idxmin()

    new_base_price = df.loc[new_event_idx, 'close']

    # Calculate when price moved >0.1%
    search_window = df[df.index >= new_event_idx].copy()
    search_window['pct_change'] = ((search_window['close'] - new_base_price) / new_base_price).abs()

    moved_indices = search_window[search_window['pct_change'] >= 0.001].index

    if len(moved_indices) == 0:
        print("\n❌ Price never moved >0.1% after this timestamp")
        print("   This timestamp is probably TOO LATE")
        return

    spike_idx = moved_indices[0]
    spike_time = df.loc[spike_idx, 'timestamp']
    spike_price = df.loc[spike_idx, 'close']

    new_lag = (spike_time - new_event_time).total_seconds()

    print(f"\nBase price at new timestamp: ${new_base_price:.2f}")
    print(f"First >0.1% move at: {spike_time}")
    print(f"Price at spike: ${spike_price:.2f}")
    print(f"NEW CALCULATED LAG: {int(new_lag)} seconds")

    # Compare
    print(f"\n{'-' * 80}")
    print("COMPARISON")
    print(f"{'-' * 80}")
    print(f"Old lag: {event['time_to_impact_seconds']}s")
    print(f"New lag: {int(new_lag)}s")

    improvement = event['time_to_impact_seconds'] - new_lag

    if new_lag < 10:
        print(f"\n✅ EXCELLENT! New lag <10s (improvement: {int(improvement)}s)")
        print("   This is likely the correct first source!")
    elif new_lag < 15:
        print(f"\n✅ GOOD! New lag <15s (improvement: {int(improvement)}s)")
        print("   This is better, but keep searching for <10s source")
    elif new_lag < event['time_to_impact_seconds']:
        print(f"\n⚠️ BETTER but still suspicious (improvement: {int(improvement)}s)")
        print("   Keep searching for earlier source")
    else:
        print(f"\n❌ WORSE! This timestamp is later than current source")
        print("   This is not the right source")

    # Show what to update
    if new_lag < event['time_to_impact_seconds']:
        print(f"\n{'-' * 80}")
        print("TO UPDATE EVENT IN DATABASE:")
        print(f"{'-' * 80}")
        print(f"UPDATE master_events SET")
        print(f"  timestamp = '{new_timestamp_str}',")
        print(f"  time_to_impact_seconds = {int(new_lag)},")
        print(f"  source = '[NEW SOURCE NAME]',")
        print(f"  source_url = '[NEW SOURCE URL]'")
        print(f"WHERE id = {event_id};")

    conn.close()

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 test_new_timestamp.py <event_id> <new_timestamp>")
        print("\nExample:")
        print("  python3 test_new_timestamp.py 5 '2023-08-29T14:19:36+00:00'")
        return

    event_id = int(sys.argv[1])
    new_timestamp = sys.argv[2]

    test_timestamp(event_id, new_timestamp)

if __name__ == "__main__":
    main()
