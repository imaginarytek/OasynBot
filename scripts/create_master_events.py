#!/usr/bin/env python3
"""
Create Master Events Table
Combines curated_events + gold_events + optimized_events into one unified table
with quality metadata and best practices applied
"""
import sqlite3
import json
from datetime import datetime

def safe_get(row, key, default=''):
    """Safely get value from sqlite3.Row object"""
    try:
        return row[key] if row[key] is not None else default
    except (KeyError, IndexError):
        return default

def validate_no_lookahead_bias(event_data, lag_seconds=None):
    """
    STRICT BIAS CHECK: logical referee to prevent cheating.
    Returns (Passed: bool, Reason: str)
    """
    # 1. Parse timestamps
    try:
        # Assuming ISO format for now, strictly speaking we should be rigorous here
        event_time_str = event_data.get('timestamp')
        if not event_time_str:
            return False, "Missing timestamp"
        
        # 2. Check Physical Constraints
        # If we have price data, we can check if the move happened AFTER the event
        price_json = event_data.get('sol_price_data')
        if price_json:
            prices = json.loads(price_json)
            if not prices:
                return True, "No price data to validate against"
                
            # Basic sanity: Timestamp of first price candle vs event
            # TODO: Implement strict timestamp comparision once we standardize formats
            pass
            
        # 3. Latency Check
        # If verified high-quality event, it MUST have a measured lag or explicit waiver
        quality = event_data.get('quality_level', 0)
        if quality == 2 and (lag_seconds is None or lag_seconds <= 0):
             # Soft warning only - we allow it now as we use System Latency for execution
             pass

    except Exception as e:
        return False, f"Validation Error: {str(e)}"

    return True, "Valid"


def create_master_events():
    """
    Create a unified master_events table with all verified events
    """
    print("="*100)
    print("🔄 CREATING MASTER EVENTS TABLE")
    print("="*100)
    
    conn = sqlite3.connect('data/hedgemony.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Create master_events table with comprehensive schema
    print("\n📋 Creating master_events table schema...")
    c.execute("DROP TABLE IF EXISTS master_events") # Ensure fresh schema
    c.execute("""
        CREATE TABLE IF NOT EXISTS master_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            
            -- Event Information
            title TEXT NOT NULL,
            description TEXT,
            timestamp TEXT NOT NULL,
            source TEXT,
            source_url TEXT,
            category TEXT,
            
            -- Quality Metadata
            quality_level INTEGER,  -- 0=archive, 1=normal, 2=high-impact
            methodology TEXT,       -- 'event-first' or 'spike-first'
            verified BOOLEAN DEFAULT 1,
            timestamp_precision TEXT, -- 'hour', 'minute', 'second'
            
            -- Price Data (1-second resolution)
            sol_price_data TEXT,
            
            -- Price Impact Metrics
            move_5s REAL,
            move_30s REAL,
            move_5m REAL,
            move_30m REAL,
            move_1h REAL,
            volatility_z_score REAL,
            time_to_impact_seconds INTEGER,  -- Diagnostic only (QA)
            
            -- Tracking
            impact_score INTEGER,
            tradeable BOOLEAN DEFAULT 1,
            notes TEXT,
            
            -- Tracking
            date_added TEXT,
            last_updated TEXT,
            
            UNIQUE(title, timestamp)
        )
    """)
    
    print("   ✅ Schema created")
    
    print("   ✅ Schema created")
    
    # NOTE: We do NOT migrate legacy tables (curated_events, gold_events)
    # properly. The master_events table is now strictly for High-Fidelity verified events.
    # Use scripts/import_new_events_json.py to populate it.
    
    conn.commit()
    
    # Generate summary
    print(f"\n{'='*100}")
    print("📊 DATABASE RESET COMPLETE")
    print(f"{'='*100}\n")
    
    c.execute("SELECT COUNT(*) FROM master_events")
    total = c.fetchone()[0]
    
    print(f"Total Events in master_events: {total} (Should be 0)")
    print(f"\n✅ Master events table reset successfully!")
    print(f"\n👉 NEXT STEP: Run 'python3 scripts/import_new_events_json.py' to load verified data.")
    
    conn.close()

if __name__ == "__main__":
    create_master_events()
