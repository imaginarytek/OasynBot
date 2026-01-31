#!/usr/bin/env python3
"""
Import New Events from JSON
Reads data/new_events.json and adds them to BOTH databases:
- Input data → hedgemony.db (what bot sees)
- Validation metadata → hedgemony_validation.db (QA only)
"""
import sys
import os
import json
import sqlite3
from datetime import datetime
import pandas as pd

# Database paths
INPUT_DB_PATH = 'data/hedgemony.db'
VALIDATION_DB_PATH = 'data/hedgemony_validation.db'
INPUT_FILE = 'data/verified_events_batch.json'

def validate_event(event):
    """
    Validates event against Gold Standard:
    - Measured Lag (Must be > 0)
    - Verbatim Text (Over 50 chars)
    - Timestamp (ISO format)
    """
    issues = []
    
    # Check 1: Time to Impact (Diagnostic)
    # Renamed from measured_execution_lag_seconds
    # We still check for positive integer to ensure decent data quality
    lag = event.get('time_to_impact_seconds')
    # Use get with default none to check existence
    if lag is None:
         # Backward compatibility: check old key
         lag = event.get('measured_execution_lag_seconds')
         
    if lag is None or not isinstance(lag, int) or lag <= 0:
        issues.append(f"❌ Missing positive integer for 'time_to_impact_seconds'")

    # Check 2: Verbatim Text
    text = event.get('verbatim_text', '')
    if not text or len(text) < 10: # Short tweets are valid breaking news
        issues.append(f"❌ Verbatim text too short (<10 chars). Need verified source text.")

    # Check 3: Timestamp
    try:
        # Basic check, ideally use strict parsing
        datetime.fromisoformat(event.get('timestamp', '').replace('Z', '+00:00'))
    except ValueError:
        issues.append(f"❌ Invalid timestamp format (Use ISO8601 e.g. 2023-01-01T12:00:00+00:00)")

    return issues

def main():
    print("="*60)
    print("📥 IMPORTING NEW EVENTS FROM JSON")
    print("="*60)

    if not os.path.exists(INPUT_FILE):
        print(f"❌ Error: {INPUT_FILE} not found.")
        return

    try:
        with open(INPUT_FILE, 'r') as f:
            events = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error decoding JSON: {e}")
        return

    print(f"Found {len(events)} events to process...")

    # Connect to both databases
    input_conn = sqlite3.connect(INPUT_DB_PATH)
    validation_conn = sqlite3.connect(VALIDATION_DB_PATH)

    input_cursor = input_conn.cursor()
    validation_cursor = validation_conn.cursor()

    # Ensure tables exist
    # (Assumes migration has been run - tables should exist)

    success_count = 0
    
    for evt in events:
        print(f"\nProcessing: {evt.get('title', 'Unknown')}")
        
        # 1. Validate
        issues = validate_event(evt)
        if issues:
            for issue in issues:
                print(f"  {issue}")
            print("  ⚠️ Skipped.")
            continue
            
        # 2. Fetch Price Data (Placeholder - In real deployment, call BitQuery/Binance)
        # For now, we assume user might have put file path or we skip
        # TODO: Integrate price fetcher here
        
        # 3. Save to BOTH databases
        try:
            # Insert input data (what bot sees)
            input_cursor.execute("""
                INSERT INTO master_events (
                    title, timestamp, source, source_url, category,
                    description, date_added, last_updated
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                evt['title'],
                evt['timestamp'],
                evt['source'],
                evt.get('source_url'),
                evt.get('category'),
                evt.get('verbatim_text'),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

            # Get the inserted event ID
            event_id = input_cursor.lastrowid

            # Insert validation metadata (bot cannot see this)
            validation_cursor.execute("""
                INSERT INTO event_metrics (
                    event_id, time_to_impact_seconds, verified, quality_level,
                    methodology, date_added, last_updated
                ) VALUES (?, ?, 1, 1, 'spike-first', ?, ?)
            """, (
                event_id,
                evt.get('time_to_impact_seconds', evt.get('measured_execution_lag_seconds')),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

            print(f"  ✅ Added to both databases (ID: {event_id}).")
            success_count += 1

        except sqlite3.IntegrityError:
            print("  ⚠️ Skipped (Duplicate title/timestamp).")
        except Exception as e:
            print(f"  ❌ Database Error: {e}")
            # Rollback both if either fails
            input_conn.rollback()
            validation_conn.rollback()

    # Commit both databases
    input_conn.commit()
    validation_conn.commit()

    # Close connections
    input_conn.close()
    validation_conn.close()

    print("\n" + "="*60)
    print(f"Done. Imported {success_count}/{len(events)} events to both databases.")

if __name__ == "__main__":
    main()
