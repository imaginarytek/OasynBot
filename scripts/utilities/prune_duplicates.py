
import sqlite3
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.db import Database

def prune_duplicates():
    print("🚀 Pruning Database: Keeping only FIRST MOVER per 48h Cluster...")
    db = Database()
    conn = db.get_connection()
    c = conn.cursor()
    
    # Get all events sorted by time
    c.execute("SELECT id, timestamp, title FROM gold_events ORDER BY timestamp ASC")
    events = c.fetchall()
    
    if not events:
        print("No events found.")
        return

    keep_ids = []
    dropped_count = 0
    
    # Logic:
    # Iterate through sorted events.
    # Keep the first one.
    # Skip any subsequent event that is within X hours of the last KEPT event.
    
    last_kept_time = None
    COOLDOWN_HOURS = 48 
    
    for eid, ts_str, title in events:
        # Parse TS (Handle potential Z or no Z)
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", ""))
        except:
            # Fallback format if needed
            ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
            
        if last_kept_time is None:
            # First event ever -> Keep
            keep_ids.append(eid)
            last_kept_time = ts
            continue

        # TZ Normalization for comparison
        if ts.tzinfo is None and last_kept_time.tzinfo is not None:
             ts = ts.replace(tzinfo=last_kept_time.tzinfo)
        elif ts.tzinfo is not None and last_kept_time.tzinfo is None:
             last_kept_time = last_kept_time.replace(tzinfo=ts.tzinfo)
            # print(f"✅ Keeper: {ts} - {title}")
        else:
            diff = (ts - last_kept_time).total_seconds() / 3600
            if diff < COOLDOWN_HOURS:
                # Inside cooldown -> Drop (It's an aftershock)
                dropped_count += 1
                # print(f"❌ Dropping Duplicate: {ts} (+{diff:.1f}h) - {title}")
            else:
                # New Cluster Found -> Keep
                keep_ids.append(eid)
                last_kept_time = ts
                # print(f"✅ Keeper: {ts} - {title}")
                
    # Execute Purge
    all_ids = [e[0] for e in events]
    drop_ids = set(all_ids) - set(keep_ids)
    
    if drop_ids:
        # Convert list to tuple for SQL IN clause
        # If tuple has 1 item, python needs trailing comma, sqlite handles list better
        drop_list = list(drop_ids)
        placeholders = ','.join('?' for _ in drop_list)
        c.execute(f"DELETE FROM gold_events WHERE id IN ({placeholders})", drop_list)
        conn.commit()
    
    print(f"📉 Pruned {dropped_count} Duplicate Follow-up Events.")
    print(f"✅ Remaining Unique Alpha Events: {len(keep_ids)}")
    
    conn.close()

if __name__ == "__main__":
    prune_duplicates()
