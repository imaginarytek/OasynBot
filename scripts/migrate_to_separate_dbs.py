#!/usr/bin/env python3
"""
Migrate Database to Separate Input/Validation Databases

This script separates the master_events database into two databases:
1. hedgemony.db - Bot input data ONLY (what the AI sees)
2. hedgemony_validation.db - Validation metadata ONLY (for QA/analysis)

WHY: Prevents look-ahead bias. The bot cannot accidentally see future price
movements or post-hoc judgments about tradeability.

WHAT IT DOES:
1. Creates hedgemony_validation.db with event_metrics table
2. Copies validation metadata from master_events
3. Creates new clean master_events with ONLY input fields
4. Backs up original database

RUN THIS ONCE to migrate your existing data.
"""

import sqlite3
import shutil
from datetime import datetime
import os

# Paths
ORIGINAL_DB = 'data/hedgemony.db'
BACKUP_DB = f'data/hedgemony_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
INPUT_DB = 'data/hedgemony.db'
VALIDATION_DB = 'data/hedgemony_validation.db'

# Color codes
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RED = '\033[91m'
RESET = '\033[0m'


def backup_original():
    """Create backup of original database before migration."""
    print(f"{BLUE}Step 1: Creating backup...{RESET}")
    shutil.copy2(ORIGINAL_DB, BACKUP_DB)
    print(f"{GREEN}✓ Backup created: {BACKUP_DB}{RESET}\n")


def create_validation_db():
    """Create new validation database with event_metrics table."""
    print(f"{BLUE}Step 2: Creating validation database...{RESET}")

    conn = sqlite3.connect(VALIDATION_DB)
    c = conn.cursor()

    # Create event_metrics table (validation metadata only)
    c.execute('''
        CREATE TABLE IF NOT EXISTS event_metrics (
            event_id INTEGER PRIMARY KEY,

            -- Validation Metrics (future knowledge - bot must NOT see)
            time_to_impact_seconds INTEGER,
            move_5s REAL,
            move_30s REAL,
            move_5m REAL,
            move_30m REAL,
            move_1h REAL,
            volatility_z_score REAL,

            -- Quality Control Metadata
            quality_level INTEGER,
            methodology TEXT,
            verified BOOLEAN DEFAULT 1,
            timestamp_precision TEXT,

            -- Analysis Metadata
            impact_score INTEGER,
            tradeable BOOLEAN DEFAULT 1,
            notes TEXT,

            -- Tracking
            date_added TEXT,
            last_updated TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print(f"{GREEN}✓ Validation database created: {VALIDATION_DB}{RESET}\n")


def migrate_validation_data():
    """Copy validation metadata from master_events to event_metrics."""
    print(f"{BLUE}Step 3: Migrating validation metadata...{RESET}")

    # Connect to both databases
    input_conn = sqlite3.connect(INPUT_DB)
    validation_conn = sqlite3.connect(VALIDATION_DB)

    input_conn.row_factory = sqlite3.Row

    # Read all events
    events = input_conn.execute('SELECT * FROM master_events').fetchall()

    print(f"  Found {len(events)} events to migrate")

    # Insert validation data into event_metrics
    for event in events:
        validation_conn.execute('''
            INSERT INTO event_metrics (
                event_id,
                time_to_impact_seconds,
                move_5s,
                move_30s,
                move_5m,
                move_30m,
                move_1h,
                volatility_z_score,
                quality_level,
                methodology,
                verified,
                timestamp_precision,
                impact_score,
                tradeable,
                notes,
                date_added,
                last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event['id'],
            event['time_to_impact_seconds'],
            event['move_5s'],
            event['move_30s'],
            event['move_5m'],
            event['move_30m'],
            event['move_1h'],
            event['volatility_z_score'],
            event['quality_level'],
            event['methodology'],
            event['verified'],
            event['timestamp_precision'],
            event['impact_score'],
            event['tradeable'],
            event['notes'],
            event['date_added'],
            event['last_updated']
        ))

    validation_conn.commit()
    validation_conn.close()
    input_conn.close()

    print(f"{GREEN}✓ Migrated validation data for {len(events)} events{RESET}\n")


def recreate_clean_input_db():
    """Recreate master_events with ONLY input fields (no validation metadata)."""
    print(f"{BLUE}Step 4: Creating clean input database...{RESET}")

    # Connect to original DB to read data
    original_conn = sqlite3.connect(BACKUP_DB)
    original_conn.row_factory = sqlite3.Row
    events = original_conn.execute('SELECT * FROM master_events').fetchall()
    original_conn.close()

    # Connect to input DB
    input_conn = sqlite3.connect(INPUT_DB)
    c = input_conn.cursor()

    # Drop old table
    c.execute('DROP TABLE IF EXISTS master_events')

    # Create new clean table (AI INPUT ONLY)
    c.execute('''
        CREATE TABLE master_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            -- AI INPUT (what traders actually saw - NO FUTURE KNOWLEDGE)
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            source TEXT,
            source_url TEXT,
            category TEXT,

            -- Price Data (will be filtered to only show past prices)
            sol_price_data TEXT,

            -- Tracking (for dataset management, not decision-making)
            date_added TEXT,
            last_updated TEXT,

            UNIQUE(title, timestamp)
        )
    ''')

    # Insert clean data (only input fields)
    for event in events:
        c.execute('''
            INSERT INTO master_events (
                id,
                title,
                description,
                timestamp,
                source,
                source_url,
                category,
                sol_price_data,
                date_added,
                last_updated
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            event['id'],
            event['title'],
            event['description'],
            event['timestamp'],
            event['source'],
            event['source_url'],
            event['category'],
            event['sol_price_data'],
            event['date_added'],
            datetime.now().isoformat()  # Update last_updated
        ))

    input_conn.commit()
    input_conn.close()

    print(f"{GREEN}✓ Recreated clean input database with {len(events)} events{RESET}\n")


def verify_migration():
    """Verify migration was successful."""
    print(f"{BLUE}Step 5: Verifying migration...{RESET}")

    # Check input DB
    input_conn = sqlite3.connect(INPUT_DB)
    input_count = input_conn.execute('SELECT COUNT(*) FROM master_events').fetchone()[0]
    input_cols = [col[1] for col in input_conn.execute('PRAGMA table_info(master_events)').fetchall()]
    input_conn.close()

    # Check validation DB
    validation_conn = sqlite3.connect(VALIDATION_DB)
    validation_count = validation_conn.execute('SELECT COUNT(*) FROM event_metrics').fetchone()[0]
    validation_cols = [col[1] for col in validation_conn.execute('PRAGMA table_info(event_metrics)').fetchall()]
    validation_conn.close()

    print(f"  Input DB: {input_count} events")
    print(f"  Validation DB: {validation_count} events")

    # Verify no validation columns in input DB
    forbidden_cols = ['time_to_impact_seconds', 'move_5s', 'move_30s', 'move_5m',
                      'move_30m', 'move_1h', 'tradeable', 'impact_score']
    found_forbidden = [col for col in forbidden_cols if col in input_cols]

    if found_forbidden:
        print(f"{RED}✗ ERROR: Input DB still contains validation columns: {found_forbidden}{RESET}")
        return False

    if input_count != validation_count:
        print(f"{RED}✗ ERROR: Event count mismatch!{RESET}")
        return False

    print(f"{GREEN}✓ Migration verified successfully!{RESET}\n")
    return True


def print_summary():
    """Print migration summary and next steps."""
    print("=" * 80)
    print(f"{GREEN}MIGRATION COMPLETE{RESET}")
    print("=" * 80)
    print(f"\n{BLUE}Database Structure:{RESET}")
    print(f"\n📁 {INPUT_DB} (Bot Input - Clean)")
    print(f"   └─ master_events table")
    print(f"      ├─ title, description, timestamp (WHAT TRADERS SAW)")
    print(f"      ├─ source, source_url, category")
    print(f"      └─ sol_price_data (will be filtered to past data)")

    print(f"\n📁 {VALIDATION_DB} (QA Metadata - Bot CANNOT Access)")
    print(f"   └─ event_metrics table")
    print(f"      ├─ time_to_impact_seconds (FUTURE KNOWLEDGE)")
    print(f"      ├─ move_5s, move_30s, move_5m, move_30m, move_1h (FUTURE DATA)")
    print(f"      ├─ quality_level, verified, methodology")
    print(f"      └─ impact_score, tradeable, notes")

    print(f"\n📁 {BACKUP_DB}")
    print(f"   └─ Original database backup (in case you need to rollback)")

    print(f"\n{BLUE}Next Steps:{RESET}")
    print(f"1. Validation scripts now use BOTH databases")
    print(f"2. Bot/backtest code ONLY accesses {INPUT_DB}")
    print(f"3. Keep backup safe in case you need to rollback")
    print(f"4. Run validation scripts to confirm everything works")

    print(f"\n{YELLOW}Important:{RESET}")
    print(f"  - Bot config should ONLY point to: {INPUT_DB}")
    print(f"  - Never give bot access to: {VALIDATION_DB}")
    print(f"  - This ensures ZERO risk of look-ahead bias")

    print("\n" + "=" * 80)


def main():
    """Run migration."""
    print("\n" + "=" * 80)
    print(f"{BLUE}DATABASE MIGRATION - Separate Input/Validation{RESET}")
    print("=" * 80)
    print(f"\nThis will create two separate databases:")
    print(f"  1. {INPUT_DB} (bot reads)")
    print(f"  2. {VALIDATION_DB} (validation only)")
    print(f"\nOriginal will be backed up to: {BACKUP_DB}")
    print("\n" + "=" * 80 + "\n")

    # Confirm
    response = input(f"{YELLOW}Proceed with migration? (yes/no): {RESET}")
    if response.lower() not in ['yes', 'y']:
        print(f"{RED}Migration cancelled.{RESET}")
        return

    print()

    try:
        # Run migration steps
        backup_original()
        create_validation_db()
        migrate_validation_data()
        recreate_clean_input_db()

        # Verify
        if verify_migration():
            print_summary()
        else:
            print(f"\n{RED}Migration verification failed. Check errors above.{RESET}")
            print(f"Original database backed up to: {BACKUP_DB}")

    except Exception as e:
        print(f"\n{RED}ERROR during migration: {e}{RESET}")
        print(f"Original database backed up to: {BACKUP_DB}")
        print(f"You can restore from backup if needed.")
        raise


if __name__ == "__main__":
    main()
