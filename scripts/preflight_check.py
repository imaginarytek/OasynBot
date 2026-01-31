#!/usr/bin/env python3
"""
Event Discovery Pre-Flight Check

Run this BEFORE starting any event discovery work.
Ensures you're following the documented spike-first workflow.

USAGE:
    python3 scripts/preflight_check.py

This script checks:
    1. Are there unprocessed spikes in the database?
    2. Has spike refinement been run?
    3. Has research guide been generated?
    4. Are validation scripts available?
    5. Is the workflow being followed correctly?

If any check fails, it will tell you exactly what to run next.
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{bcolors.HEADER}{bcolors.BOLD}{text}{bcolors.ENDC}")

def print_success(text):
    print(f"{bcolors.OKGREEN}✅ {text}{bcolors.ENDC}")

def print_warning(text):
    print(f"{bcolors.WARNING}⚠️  {text}{bcolors.ENDC}")

def print_error(text):
    print(f"{bcolors.FAIL}❌ {text}{bcolors.ENDC}")

def check_database_exists(db_path='data/hedgemony.db'):
    """Check if database exists"""
    if not Path(db_path).exists():
        print_error(f"Database not found: {db_path}")
        print("   Run: python3 scripts/create_master_events.py")
        return False

    print_success(f"Database exists: {db_path}")
    return True

def check_spikes_detected(db_path='data/hedgemony.db'):
    """Check if spikes have been detected"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='hourly_volatility_spikes'
    """)

    if not cursor.fetchone():
        conn.close()
        print_error("hourly_volatility_spikes table not found")
        print("   Run: python3 scripts/mine_events_professional.py")
        return False, 0

    # Count spikes
    cursor.execute("SELECT COUNT(*) FROM hourly_volatility_spikes")
    spike_count = cursor.fetchone()[0]
    conn.close()

    if spike_count == 0:
        print_warning("No spikes detected in database")
        print("   Run: python3 scripts/mine_events_professional.py")
        return False, 0

    print_success(f"Found {spike_count} volatility spikes")
    return True, spike_count

def check_spike_refinement(db_path='data/hedgemony.db'):
    """Check if spike timing has been refined"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if refined_timestamp column exists
    cursor.execute("PRAGMA table_info(hourly_volatility_spikes)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'refined_timestamp' not in columns:
        conn.close()
        print_warning("Spike refinement has not been run")
        print("   Run: python3 scripts/validation/refine_spike_timing.py")
        return False

    # Check if any spikes have been refined
    cursor.execute("""
        SELECT COUNT(*) FROM hourly_volatility_spikes
        WHERE refined_timestamp IS NOT NULL
    """)
    refined_count = cursor.fetchone()[0]
    conn.close()

    if refined_count == 0:
        print_warning("No spikes have been refined to minute precision")
        print("   Run: python3 scripts/validation/refine_spike_timing.py")
        return False

    print_success(f"Spike timing refined for {refined_count} spikes")
    return True

def check_research_guide():
    """Check if research guide has been generated"""
    if not Path('data/research_guide.md').exists():
        print_warning("Research guide not found")
        print("   Run: python3 scripts/validation/generate_research_guide.py")
        return False

    # Check if guide is recent (within 7 days)
    mtime = Path('data/research_guide.md').stat().st_mtime
    age_days = (datetime.now().timestamp() - mtime) / 86400

    if age_days > 7:
        print_warning(f"Research guide is {age_days:.1f} days old")
        print("   Consider regenerating: python3 scripts/validation/generate_research_guide.py")
    else:
        print_success(f"Research guide exists (generated {age_days:.1f} days ago)")

    return True

def check_validation_scripts():
    """Check if validation scripts are available"""
    scripts = [
        'scripts/validation/refine_spike_timing.py',
        'scripts/validation/generate_research_guide.py',
        'scripts/validation/validate_correlation.py',
        'scripts/validation/check_source_priority.py',
        'scripts/validation/validate_verbatim_text.py'
    ]

    missing = []
    for script in scripts:
        if not Path(script).exists():
            missing.append(script)

    if missing:
        print_warning(f"Missing {len(missing)} validation scripts:")
        for script in missing:
            print(f"   - {script}")
        return False

    print_success(f"All {len(scripts)} validation scripts available")
    return True

def check_master_events_setup(db_path='data/hedgemony.db'):
    """Check master_events table setup"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if table exists
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='master_events'
    """)

    if not cursor.fetchone():
        conn.close()
        print_error("master_events table not found")
        print("   Run: python3 scripts/create_master_events.py")
        return False

    # Check if spike_id column exists
    cursor.execute("PRAGMA table_info(master_events)")
    columns = [row[1] for row in cursor.fetchall()]

    if 'spike_id' not in columns:
        conn.close()
        print_warning("master_events missing spike_id column")
        print("   Run: python3 scripts/migrations/add_spike_id_constraint.py")
        return False

    # Count existing events
    cursor.execute("SELECT COUNT(*) FROM master_events")
    event_count = cursor.fetchone()[0]
    conn.close()

    print_success(f"master_events table configured ({event_count} events)")
    return True

def suggest_next_steps(checks):
    """Suggest what to do next based on check results"""
    print_header("NEXT STEPS")

    if not checks['database']:
        print("1. Create database structure:")
        print("   python3 scripts/create_master_events.py")
        return

    if not checks['spikes_detected']:
        print("1. Detect volatility spikes:")
        print("   python3 scripts/mine_events_professional.py")
        return

    if not checks['spike_refinement']:
        print("1. Refine spike timing to minute precision:")
        print("   python3 scripts/validation/refine_spike_timing.py")
        print()
        print("2. Then generate research guide:")
        print("   python3 scripts/validation/generate_research_guide.py")
        return

    if not checks['research_guide']:
        print("1. Generate research guide with search links:")
        print("   python3 scripts/validation/generate_research_guide.py")
        print()
        print("2. Then use the guide to find tier-1 sources:")
        print("   open data/research_guide.md")
        return

    # All checks passed - ready for manual research
    print("✅ All automated checks passed!")
    print()
    print("Ready for manual event research:")
    print("1. Open research guide: data/research_guide.md")
    print("2. For each spike, find tier-1 source with exact timestamp")
    print("3. Copy verbatim text (3-4 paragraphs)")
    print("4. Fill in: data/verified_events_batch.json")
    print()
    print("After manual research:")
    print("5. Import events: python3 scripts/add_events_enforced.py --import data/verified_events_batch.json")
    print("6. Fetch price data: python3 scripts/build_verified_dataset.py")
    print("7. Validate correlation: python3 scripts/validation/validate_correlation.py")

def main():
    print("=" * 80)
    print("EVENT DISCOVERY PRE-FLIGHT CHECK")
    print("=" * 80)

    checks = {}

    # Run all checks
    print_header("1. DATABASE CHECKS")
    checks['database'] = check_database_exists()

    if checks['database']:
        checks['master_events'] = check_master_events_setup()

    print_header("2. SPIKE DETECTION CHECKS")
    if checks['database']:
        checks['spikes_detected'], spike_count = check_spikes_detected()

        if checks['spikes_detected']:
            checks['spike_refinement'] = check_spike_refinement()

    print_header("3. WORKFLOW TOOL CHECKS")
    checks['validation_scripts'] = check_validation_scripts()
    checks['research_guide'] = check_research_guide()

    # Summary
    print_header("SUMMARY")
    passed = sum(1 for v in checks.values() if v)
    total = len(checks)

    print(f"Passed: {passed}/{total} checks")
    print()

    # Determine readiness
    if all([
        checks.get('database'),
        checks.get('spikes_detected'),
        checks.get('spike_refinement'),
        checks.get('research_guide')
    ]):
        print_success("🚀 READY FOR EVENT DISCOVERY")
        print()
        suggest_next_steps(checks)
        sys.exit(0)
    else:
        print_warning("⏸️  NOT READY - Complete steps below first")
        print()
        suggest_next_steps(checks)
        sys.exit(1)

if __name__ == '__main__':
    main()
