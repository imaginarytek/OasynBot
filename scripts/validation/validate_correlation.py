#!/usr/bin/env python3
"""
Validate Correlation Between News Timestamp and Price Spike

This script enforces the 60-second rule:
- Measures when price actually started moving (>0.1% threshold)
- Compares to news publication timestamp
- Flags events where correlation is invalid (lag > 60s or negative)
- Calculates and stores time_to_impact_seconds for each event

Run this BEFORE backtesting to ensure data quality.
"""

import sqlite3
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Constants
INPUT_DB_PATH = 'data/hedgemony.db'  # Bot input data (what AI sees)
VALIDATION_DB_PATH = 'data/hedgemony_validation.db'  # QA metadata (bot cannot see)
PRICE_MOVE_THRESHOLD = 0.001  # 0.1% move to detect impact start
MAX_VALID_LAG_SECONDS = 60    # Reject if news->price lag > 60s
MIN_VALID_LAG_SECONDS = -10   # Allow 10s pre-movement (news leaked early)
SUSPICIOUS_LAG_THRESHOLD = 15 # Warn if lag >15s (likely wrong source)

# Color codes for terminal output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def get_db_connections():
    """Create connections to both input and validation databases"""
    input_conn = sqlite3.connect(INPUT_DB_PATH)
    input_conn.row_factory = sqlite3.Row

    validation_conn = sqlite3.connect(VALIDATION_DB_PATH)
    validation_conn.row_factory = sqlite3.Row

    return input_conn, validation_conn


def parse_timestamp(ts_str):
    """Parse timestamp from various formats to datetime"""
    if not ts_str:
        return None

    try:
        # Handle ISO8601 with Z suffix
        ts_str = ts_str.replace('Z', '+00:00')
        return pd.to_datetime(ts_str)
    except Exception as e:
        print(f"    {RED}Error parsing timestamp '{ts_str}': {e}{RESET}")
        return None


def measure_time_to_impact(price_data_json, event_timestamp_str):
    """
    Measure time from news publication to when price actually moved.

    Returns:
        - time_to_impact_seconds (int): Measured lag, or None if cannot calculate
        - spike_start_price (float): Price when movement started
        - validation_status (str): 'valid', 'invalid', or 'unknown'
        - reason (str): Explanation
    """
    if not price_data_json:
        return None, None, 'unknown', 'No price data available'

    try:
        price_data = json.loads(price_data_json)
    except json.JSONDecodeError:
        return None, None, 'unknown', 'Price data is not valid JSON'

    if not price_data or len(price_data) < 10:
        return None, None, 'unknown', 'Insufficient price data (<10 candles)'

    # Convert to DataFrame
    df = pd.DataFrame(price_data)
    if 'timestamp' not in df.columns or 'close' not in df.columns:
        return None, None, 'unknown', 'Price data missing timestamp or close columns'

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['close'] = pd.to_numeric(df['close'], errors='coerce')
    df = df.sort_values('timestamp').reset_index(drop=True)

    # Parse event timestamp
    event_time = parse_timestamp(event_timestamp_str)
    if event_time is None:
        return None, None, 'unknown', 'Invalid event timestamp format'

    # Normalize timezone awareness - convert both to UTC
    if df['timestamp'].dt.tz is None:
        df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
    else:
        df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')

    if event_time.tzinfo is None:
        event_time = event_time.tz_localize('UTC')
    else:
        event_time = event_time.tz_convert('UTC')

    # Find the candle closest to event time (this should be index 0 or near it)
    # We expect price_data to start ~5min before event
    df['time_diff'] = (df['timestamp'] - event_time).abs()
    event_idx = df['time_diff'].idxmin()

    # Sanity check: event should be near the beginning of the data
    if event_idx > 600:  # More than 10 minutes into the data
        return None, None, 'unknown', f'Event timestamp is {event_idx}s into price data (expected near start)'

    # Get base price at event time
    base_price = df.loc[event_idx, 'close']
    if pd.isna(base_price) or base_price <= 0:
        return None, None, 'unknown', 'Invalid base price at event time'

    # Search forward from event time to find when price moved >threshold
    search_window = df[df.index >= event_idx].copy()
    search_window['pct_change'] = ((search_window['close'] - base_price) / base_price).abs()

    # Find first candle where movement exceeds threshold
    moved_indices = search_window[search_window['pct_change'] >= PRICE_MOVE_THRESHOLD].index

    if len(moved_indices) == 0:
        return None, None, 'invalid', f'Price never moved >{PRICE_MOVE_THRESHOLD*100:.1f}% (weak event)'

    spike_start_idx = moved_indices[0]
    spike_start_time = df.loc[spike_start_idx, 'timestamp']
    spike_start_price = df.loc[spike_start_idx, 'close']

    # Calculate lag
    time_to_impact = (spike_start_time - event_time).total_seconds()

    # Validate lag is within acceptable range
    if time_to_impact > MAX_VALID_LAG_SECONDS:
        return int(time_to_impact), spike_start_price, 'invalid', \
               f'Lag {int(time_to_impact)}s > {MAX_VALID_LAG_SECONDS}s (news likely wrong source)'

    if time_to_impact < MIN_VALID_LAG_SECONDS:
        return int(time_to_impact), spike_start_price, 'invalid', \
               f'Lag {int(time_to_impact)}s < {MIN_VALID_LAG_SECONDS}s (price moved before news)'

    # Check for suspicious lag (likely secondary source, not first breaking news)
    if time_to_impact > SUSPICIOUS_LAG_THRESHOLD:
        return int(time_to_impact), spike_start_price, 'suspicious', \
               f'SUSPICIOUS: {int(time_to_impact)}s lag (likely NOT first source - check for earlier tweets/alerts)'

    # Valid correlation
    return int(time_to_impact), spike_start_price, 'valid', \
           f'Valid correlation: {int(time_to_impact)}s lag'


def validate_all_events():
    """
    Validate all events in master_events table.

    For each event:
    1. Load price data
    2. Measure time_to_impact
    3. Validate correlation
    4. Update database with results
    5. Generate report
    """
    print("=" * 80)
    print(f"{BLUE}EVENT CORRELATION VALIDATOR{RESET}")
    print("=" * 80)
    print(f"\nValidation Rules:")
    print(f"  - Price must move >{PRICE_MOVE_THRESHOLD*100:.1f}% to count as impact")
    print(f"  - News->Price lag must be {MIN_VALID_LAG_SECONDS}s to {MAX_VALID_LAG_SECONDS}s")
    print(f"  - Events outside this range are flagged as INVALID\n")

    input_conn, validation_conn = get_db_connections()

    # Get all events from input DB
    events = input_conn.execute("""
        SELECT id, title, timestamp, sol_price_data
        FROM master_events
        ORDER BY timestamp DESC
    """).fetchall()

    # Get existing validation metrics
    existing_metrics = {}
    for row in validation_conn.execute("SELECT event_id, time_to_impact_seconds FROM event_metrics"):
        existing_metrics[row['event_id']] = row['time_to_impact_seconds']

    if len(events) == 0:
        print(f"{YELLOW}No events found in master_events table.{RESET}")
        input_conn.close()
        validation_conn.close()
        return

    print(f"Found {len(events)} events to validate.\n")
    print("=" * 80)

    # Track results
    results = {
        'valid': [],
        'invalid': [],
        'suspicious': [],
        'unknown': []
    }

    for row in events:
        event_id = row['id']
        title = row['title'][:60]  # Truncate for display
        timestamp = row['timestamp']
        price_data = row['sol_price_data']
        existing_lag = existing_metrics.get(event_id)

        print(f"\n{BLUE}[Event {event_id}]{RESET} {title}")
        print(f"  Timestamp: {timestamp}")

        # Measure correlation
        measured_lag, spike_price, status, reason = measure_time_to_impact(price_data, timestamp)

        # Display result
        if status == 'valid':
            print(f"  {GREEN}✓ VALID{RESET} - {reason}")
            if spike_price:
                print(f"    Price at spike: ${spike_price:.2f}")
            results['valid'].append(event_id)
        elif status == 'suspicious':
            print(f"  {YELLOW}⚠ SUSPICIOUS{RESET} - {reason}")
            if spike_price:
                print(f"    Price at spike: ${spike_price:.2f}")
            print(f"    {YELLOW}→ Action: Re-research this event to find the FIRST breaking source{RESET}")
            print(f"    {YELLOW}→ Search Twitter/Bloomberg {int(measured_lag)}s BEFORE current timestamp{RESET}")
            results['suspicious'].append(event_id)
        elif status == 'invalid':
            print(f"  {RED}✗ INVALID{RESET} - {reason}")
            if spike_price:
                print(f"    Price at spike: ${spike_price:.2f}")
            results['invalid'].append(event_id)
        else:  # unknown
            print(f"  {YELLOW}? UNKNOWN{RESET} - {reason}")
            results['unknown'].append(event_id)

        # Compare to existing value
        if measured_lag is not None and existing_lag is not None:
            if measured_lag != existing_lag:
                print(f"  {YELLOW}⚠ Stored lag ({existing_lag}s) differs from measured ({measured_lag}s){RESET}")

        # Update validation database with measured value
        if measured_lag is not None:
            try:
                validation_conn.execute("""
                    UPDATE event_metrics
                    SET time_to_impact_seconds = ?,
                        last_updated = ?
                    WHERE event_id = ?
                """, (measured_lag, datetime.now().isoformat(), event_id))
                validation_conn.commit()

                if existing_lag is None:
                    print(f"  {GREEN}✓ Updated time_to_impact_seconds = {measured_lag}s{RESET}")
            except Exception as e:
                print(f"  {RED}✗ Database update failed: {e}{RESET}")

    input_conn.close()
    validation_conn.close()

    # Print summary report
    print("\n" + "=" * 80)
    print(f"{BLUE}VALIDATION SUMMARY{RESET}")
    print("=" * 80)

    total = len(events)
    valid_count = len(results['valid'])
    suspicious_count = len(results['suspicious'])
    invalid_count = len(results['invalid'])
    unknown_count = len(results['unknown'])

    print(f"\nTotal Events: {total}")
    print(f"  {GREEN}✓ Valid:{RESET}      {valid_count:2d} ({valid_count/total*100:.1f}%)")
    print(f"  {YELLOW}⚠ Suspicious:{RESET} {suspicious_count:2d} ({suspicious_count/total*100:.1f}%)")
    print(f"  {RED}✗ Invalid:{RESET}    {invalid_count:2d} ({invalid_count/total*100:.1f}%)")
    print(f"  {YELLOW}? Unknown:{RESET}    {unknown_count:2d} ({unknown_count/total*100:.1f}%)")

    if suspicious_count > 0:
        print(f"\n{YELLOW}⚠ WARNING: {suspicious_count} events have suspicious timing (lag >15s){RESET}")
        print(f"These events likely use SECONDARY sources (official publications) instead of PRIMARY (breaking news).")
        print(f"\nSuspicious events (need re-research):")
        for event_id in results['suspicious']:
            event = [e for e in events if e['id'] == event_id][0]
            lag = event['time_to_impact_seconds']
            print(f"  - Event {event_id}: {event['title'][:50]}... ({lag}s lag)")
        print(f"\n{YELLOW}Action Required:{RESET}")
        print(f"  1. For each event, search Twitter/Bloomberg {SUSPICIOUS_LAG_THRESHOLD}+ seconds BEFORE the current timestamp")
        print(f"  2. Look for breaking news tweets, terminal alerts, reporter posts")
        print(f"  3. Update the event with the TRUE first source (should have <10s lag)")

    if invalid_count > 0:
        print(f"\n{RED}⚠ CRITICAL: {invalid_count} events FAILED validation!{RESET}")
        print(f"These events should be reviewed and possibly removed from the dataset.")
        print(f"\nTo see invalid events (requires joining both databases):")
        print(f"  # Check event details:")
        print(f"  sqlite3 {INPUT_DB_PATH} \"SELECT id, title FROM master_events WHERE id IN ({','.join(map(str, results['invalid']))})\"")
        print(f"  # Check validation metrics:")
        print(f"  sqlite3 {VALIDATION_DB_PATH} \"SELECT event_id, time_to_impact_seconds FROM event_metrics WHERE event_id IN ({','.join(map(str, results['invalid']))})\"")

    if valid_count == total:
        print(f"\n{GREEN}✓ All events passed validation! Dataset is clean.{RESET}")
    elif suspicious_count > 0 and invalid_count == 0:
        print(f"\n{YELLOW}⚠ Dataset needs re-research for {suspicious_count} events, but no critical failures.{RESET}")

    print("\n" + "=" * 80)


def main():
    if not os.path.exists(INPUT_DB_PATH):
        print(f"{RED}Error: Input database not found at {INPUT_DB_PATH}{RESET}")
        sys.exit(1)

    if not os.path.exists(VALIDATION_DB_PATH):
        print(f"{RED}Error: Validation database not found at {VALIDATION_DB_PATH}{RESET}")
        sys.exit(1)

    validate_all_events()


if __name__ == "__main__":
    main()
