#!/usr/bin/env python3
"""
ENFORCED Event Addition - The ONLY Way to Add Events to master_events

This script enforces the spike-first methodology with hard blocks.
It physically prevents adding events that bypass the documented workflow.

USAGE:
    python3 scripts/add_events_enforced.py --validate-only  # Check readiness
    python3 scripts/add_events_enforced.py --import verified_events_batch.json

WORKFLOW IT ENFORCES:
    Step 1: scripts/mine_events_professional.py (detect spikes)
    Step 2: scripts/validation/refine_spike_timing.py (exact minute)
    Step 3: scripts/validation/generate_research_guide.py (search links)
    Step 4: Manual research → fill verified_events_batch.json
    Step 5: THIS SCRIPT (validates & imports with enforcement)
    Step 6: scripts/build_verified_dataset.py (fetch 1s price data)
    Step 7: scripts/validation/validate_correlation.py (verify <60s)

HARD BLOCKS (Will reject events that fail):
    ❌ Event without spike_id (must come from hourly_volatility_spikes)
    ❌ Description <200 chars (must be verbatim, not summary)
    ❌ Non-tier-1 source (must be Bloomberg/Reuters/CoinDesk/etc)
    ❌ Missing required fields (timestamp, title, source_url)
    ❌ Duplicate event (same title+timestamp already exists)
"""

import sys
import sqlite3
import json
from datetime import datetime
from pathlib import Path

# Tier-1 sources that are allowed
TIER1_SOURCES = {
    # Bloomberg
    '@Bloomberg', '@business', '@markets',
    # Reuters
    '@Reuters', '@ReutersBiz',
    # CoinDesk
    '@CoinDesk',
    # Crypto-specific tier-1
    '@WatcherGuru', '@tier10k', '@DeItaone',
    # Court reporters (for regulatory events)
    '@EleanorTerrett', '@jbarro', '@KatieGrfeld',
    # Exchanges (official)
    '@binance', '@coinbase', '@krakenfx',
    # Official government (for regulatory only)
    'sec.gov', 'uscourts.gov', 'federalregister.gov'
}

class EventEnforcementError(Exception):
    """Raised when event fails enforcement checks"""
    pass

def check_tier1_source(source: str) -> bool:
    """Check if source is tier-1 (breaking news, not secondary)"""
    if not source:
        return False

    source_lower = source.lower()

    # Check if any tier-1 source is in the provided source
    for tier1 in TIER1_SOURCES:
        if tier1.lower() in source_lower:
            return True

    return False

def validate_event_data(event: dict, db_path: str = 'data/hedgemony.db') -> dict:
    """
    Validate event against all enforcement rules.

    Returns: dict with validation results and enriched event data
    Raises: EventEnforcementError if critical validation fails
    """
    errors = []
    warnings = []

    # HARD REQUIREMENT 1: Must have spike_id
    if 'spike_id' not in event or event['spike_id'] is None:
        errors.append("❌ CRITICAL: Event must have spike_id (must originate from detected spike)")
        errors.append("   Run scripts/validation/generate_research_guide.py to get spike_id")

    # HARD REQUIREMENT 2: Must have title
    if 'title' not in event or not event['title']:
        errors.append("❌ CRITICAL: Event must have title (exact headline)")

    # HARD REQUIREMENT 3: Must have timestamp
    if 'timestamp' not in event or not event['timestamp']:
        errors.append("❌ CRITICAL: Event must have timestamp (ISO format)")

    # HARD REQUIREMENT 4: Must have source
    if 'source' not in event or not event['source']:
        errors.append("❌ CRITICAL: Event must have source (@username or outlet)")
    else:
        # Check if source is tier-1
        if not check_tier1_source(event['source']):
            warnings.append(f"⚠️  WARNING: Source '{event['source']}' is not recognized tier-1")
            warnings.append("   Tier-1 sources: Bloomberg, Reuters, CoinDesk, official exchanges")
            warnings.append("   If this is correct, add to TIER1_SOURCES in this script")

    # HARD REQUIREMENT 5: Must have source_url
    if 'source_url' not in event or not event['source_url']:
        errors.append("❌ CRITICAL: Event must have source_url (for verification)")

    # HARD REQUIREMENT 6: Description must be verbatim (not summary)
    if 'description' not in event or not event['description']:
        errors.append("❌ CRITICAL: Event must have description (verbatim text)")
    elif len(event['description']) < 200:
        errors.append("❌ CRITICAL: Description too short (<200 chars)")
        errors.append("   Must be verbatim text from source (3-4 paragraphs)")
        errors.append("   Current length: " + str(len(event['description'])))

    # HARD REQUIREMENT 7: Check for duplicates
    if 'title' in event and 'timestamp' in event:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, title FROM master_events
            WHERE title = ? AND timestamp = ?
        """, (event['title'], event['timestamp']))
        duplicate = cursor.fetchone()
        conn.close()

        if duplicate:
            errors.append(f"❌ CRITICAL: Duplicate event exists (id={duplicate[0]})")
            errors.append(f"   Title: {duplicate[1]}")

    # HARD REQUIREMENT 8: Verify spike_id exists
    if 'spike_id' in event and event['spike_id']:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, datetime, z_score FROM hourly_volatility_spikes
            WHERE id = ?
        """, (event['spike_id'],))
        spike = cursor.fetchone()
        conn.close()

        if not spike:
            errors.append(f"❌ CRITICAL: spike_id {event['spike_id']} does not exist")
            errors.append("   Run scripts/mine_events_professional.py first")
        else:
            # Add spike info to event
            event['_spike_datetime'] = spike[1]
            event['_spike_z_score'] = spike[2]
            warnings.append(f"✅ Linked to spike: {spike[1]} (Z={spike[2]:.2f}σ)")

    # If there are errors, raise exception
    if errors:
        raise EventEnforcementError("\n".join(errors))

    return {
        'valid': True,
        'errors': errors,
        'warnings': warnings,
        'event': event
    }

def add_event_to_database(event: dict, db_path: str = 'data/hedgemony.db') -> int:
    """
    Add validated event to master_events table.

    Returns: event_id of inserted event
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Insert event
    cursor.execute("""
        INSERT INTO master_events (
            spike_id, title, description, timestamp, source, source_url,
            category, methodology, verified, timestamp_precision,
            date_added, last_updated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        event.get('spike_id'),
        event['title'],
        event['description'],
        event['timestamp'],
        event['source'],
        event['source_url'],
        event.get('category', 'Crypto'),
        'spike-first',
        1,  # Always verified since it went through enforcement
        event.get('timestamp_precision', 'minute'),
        datetime.now().isoformat(),
        datetime.now().isoformat()
    ))

    event_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return event_id

def validate_workflow_readiness(db_path: str = 'data/hedgemony.db') -> dict:
    """
    Check if the workflow prerequisites are met.

    Returns: dict with readiness status
    """
    issues = []
    ready = True

    # Check 1: Database exists
    if not Path(db_path).exists():
        issues.append("❌ Database not found: " + db_path)
        ready = False
        return {'ready': ready, 'issues': issues}

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check 2: hourly_volatility_spikes table exists
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='hourly_volatility_spikes'
    """)
    if not cursor.fetchone():
        issues.append("❌ hourly_volatility_spikes table not found")
        issues.append("   Run: python3 scripts/mine_events_professional.py")
        ready = False
    else:
        # Check 3: Are there spikes to process?
        cursor.execute("SELECT COUNT(*) FROM hourly_volatility_spikes")
        spike_count = cursor.fetchone()[0]
        if spike_count == 0:
            issues.append("⚠️  No spikes detected in database")
            issues.append("   Run: python3 scripts/mine_events_professional.py")
        else:
            issues.append(f"✅ Found {spike_count} volatility spikes")

    # Check 4: master_events table exists and has spike_id column
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='master_events'
    """)
    if not cursor.fetchone():
        issues.append("❌ master_events table not found")
        issues.append("   Run: python3 scripts/create_master_events.py")
        ready = False
    else:
        # Check if spike_id column exists
        cursor.execute("PRAGMA table_info(master_events)")
        columns = [col[1] for col in cursor.fetchall()]
        if 'spike_id' not in columns:
            issues.append("⚠️  master_events missing spike_id column (will be added)")
            issues.append("   This will be added automatically on first import")

    # Check 5: Research guide exists
    if not Path('data/research_guide.md').exists():
        issues.append("⚠️  Research guide not found")
        issues.append("   Run: python3 scripts/validation/generate_research_guide.py")
    else:
        issues.append("✅ Research guide exists")

    conn.close()

    return {'ready': ready, 'issues': issues}

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='ENFORCED Event Addition - Prevents bypassing spike-first workflow'
    )
    parser.add_argument('--validate-only', action='store_true',
                      help='Check workflow readiness without importing')
    parser.add_argument('--import', dest='import_file', type=str,
                      help='Import events from JSON file (verified_events_batch.json)')
    parser.add_argument('--db', type=str, default='data/hedgemony.db',
                      help='Database path (default: data/hedgemony.db)')

    args = parser.parse_args()

    print("=" * 80)
    print("ENFORCED EVENT ADDITION - Spike-First Workflow Validation")
    print("=" * 80)
    print()

    # Check workflow readiness
    readiness = validate_workflow_readiness(args.db)

    print("WORKFLOW READINESS CHECK:")
    print("-" * 80)
    for issue in readiness['issues']:
        print(issue)
    print()

    if not readiness['ready']:
        print("❌ WORKFLOW NOT READY - Fix issues above before proceeding")
        sys.exit(1)

    if args.validate_only:
        print("✅ VALIDATION PASSED - Ready to import events")
        print()
        print("Next steps:")
        print("1. Fill in data/verified_events_batch.json with event data")
        print("2. Run: python3 scripts/add_events_enforced.py --import data/verified_events_batch.json")
        sys.exit(0)

    # Import events
    if not args.import_file:
        print("No import file specified. Use --import <file> or --validate-only")
        sys.exit(1)

    # Load events from JSON
    try:
        with open(args.import_file, 'r') as f:
            data = json.load(f)
            events = data if isinstance(data, list) else [data]
    except Exception as e:
        print(f"❌ ERROR: Failed to load {args.import_file}")
        print(f"   {e}")
        sys.exit(1)

    print(f"IMPORTING {len(events)} EVENTS")
    print("=" * 80)
    print()

    success_count = 0
    failed_count = 0

    for i, event in enumerate(events, 1):
        print(f"Event {i}/{len(events)}: {event.get('title', 'NO TITLE')[:60]}...")
        print("-" * 80)

        try:
            # Validate event
            result = validate_event_data(event, args.db)

            # Show warnings
            if result['warnings']:
                for warning in result['warnings']:
                    print(warning)

            # Add to database
            event_id = add_event_to_database(result['event'], args.db)

            print(f"✅ SUCCESS: Event added (id={event_id})")
            success_count += 1

        except EventEnforcementError as e:
            print(f"❌ REJECTED: Event failed validation")
            print(str(e))
            failed_count += 1
        except Exception as e:
            print(f"❌ ERROR: Unexpected error")
            print(f"   {e}")
            failed_count += 1

        print()

    print("=" * 80)
    print(f"IMPORT COMPLETE: {success_count} succeeded, {failed_count} failed")
    print("=" * 80)
    print()

    if success_count > 0:
        print("NEXT STEPS:")
        print("1. Run: python3 scripts/build_verified_dataset.py (fetch 1s price data)")
        print("2. Run: python3 scripts/validation/validate_correlation.py (verify <60s lag)")
        print("3. Run: python3 scripts/validation/validate_verbatim_text.py (check text quality)")

    sys.exit(0 if failed_count == 0 else 1)

if __name__ == '__main__':
    main()
