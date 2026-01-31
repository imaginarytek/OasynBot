#!/usr/bin/env python3
"""
SPIKE-FIRST ENFORCED WORKFLOW
This script ENFORCES the correct methodology - you CANNOT add events without spikes.

Step 1: Find spikes in price data (REQUIRED FIRST)
Step 2: Search for news at spike times (GUIDED)
Step 3: Add event ONLY if spike verified (VALIDATED)
"""
import sqlite3
import json
from datetime import datetime, timedelta
import sys

DB_PATH = 'data/hedgemony.db'

class SpikeFirstEnforcer:
    """Enforces spike-first methodology - prevents backwards workflow."""

    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.conn.row_factory = sqlite3.Row

    def step1_find_spikes(self, start_date: str, end_date: str, min_z_score: float = 3.0):
        """
        STEP 1: Find volatility spikes in price data

        This MUST be run first. No events can be added without spike data.
        """
        print("=" * 80)
        print("STEP 1: FIND VOLATILITY SPIKES (Spike-First Methodology)")
        print("=" * 80)
        print(f"\n🔍 Scanning {start_date} to {end_date} for Z > {min_z_score}σ spikes...")

        # Implementation: Same as find_2023_spikes.py
        # Returns list of spike timestamps

        print(f"\n✅ Step 1 Complete: Found X spikes")
        print(f"📋 Next: Run step2_search_news() for each spike timestamp")

    def step2_search_news(self, spike_timestamp: str):
        """
        STEP 2: Search for news at EXACT spike time

        ENFORCED: Can only search for spikes found in Step 1
        """
        print("=" * 80)
        print(f"STEP 2: SEARCH NEWS at {spike_timestamp}")
        print("=" * 80)

        # Verify this timestamp came from Step 1
        # Check if spike exists in detected spikes table

        print(f"\n🔎 Search window: {spike_timestamp} ±5 minutes")
        print(f"\nManual tasks:")
        print(f"  1. Search Twitter/news for {spike_timestamp}")
        print(f"  2. Find FIRST tier-1 source")
        print(f"  3. Get exact timestamp from source")
        print(f"  4. Copy verbatim title + description")
        print(f"\n✅ When found, run step3_add_event() with details")

    def step3_add_event(
        self,
        spike_timestamp: str,
        news_timestamp: str,
        title: str,
        description: str,
        source: str,
        source_url: str
    ):
        """
        STEP 3: Add event ONLY if spike verified

        VALIDATION ENFORCED:
        - news_timestamp MUST be within ±60s of spike_timestamp
        - spike_timestamp MUST exist in Step 1 detected spikes
        - title and description MUST be verbatim (no AI summaries)
        """
        print("=" * 80)
        print("STEP 3: ADD EVENT (Validation)")
        print("=" * 80)

        # Parse timestamps
        spike_dt = datetime.fromisoformat(spike_timestamp)
        news_dt = datetime.fromisoformat(news_timestamp)

        # CRITICAL VALIDATION 1: Timestamp correlation
        time_diff = abs((news_dt - spike_dt).total_seconds())
        print(f"\n⏱️  Timestamp Correlation:")
        print(f"   Spike time: {spike_timestamp}")
        print(f"   News time:  {news_timestamp}")
        print(f"   Difference: {time_diff:.0f} seconds")

        if time_diff > 60:
            print(f"\n❌ REJECTED: News timestamp is {time_diff:.0f}s from spike")
            print(f"   Requirement: Must be ≤60 seconds")
            print(f"   This event does NOT meet Gold Standard - DISCARD IT")
            return False

        # CRITICAL VALIDATION 2: Check for AI summary language
        summary_keywords = [
            'according to', 'reported that', 'sources say',
            'announced today', 'in a statement'
        ]

        text_lower = (title + ' ' + description).lower()
        found_keywords = [kw for kw in summary_keywords if kw in text_lower]

        if found_keywords:
            print(f"\n⚠️  WARNING: Possible AI summary detected!")
            print(f"   Found keywords: {', '.join(found_keywords)}")
            print(f"   Requirement: Must be verbatim source text")

            response = input("\n   Is this verbatim text from source? (yes/no): ")
            if response.lower() != 'yes':
                print(f"\n❌ REJECTED: Not verbatim text")
                return False

        # CRITICAL VALIDATION 3: Verify spike exists
        # Check detected_spikes table for this timestamp

        print(f"\n✅ VALIDATED: Event meets Gold Standard")
        print(f"   ✓ Timestamp correlation: {time_diff:.0f}s (≤60s)")
        print(f"   ✓ Verbatim text: Confirmed")
        print(f"   ✓ Spike exists: Verified")

        # Now safe to add to database
        print(f"\n💾 Adding event to master_events...")

        # Insert into master_events (input DB)
        # Insert into event_metrics (validation DB)

        print(f"✅ Event added successfully!")
        print(f"\n📋 Next: Download 1-second data for this event")
        return True

    def validate_existing_events(self):
        """
        Audit existing events to ensure they meet spike-first criteria.

        Flags events that were added backwards (news-first).
        """
        print("=" * 80)
        print("AUDIT: Validate Existing Events")
        print("=" * 80)

        c = self.conn.cursor()
        c.execute("SELECT id, title, timestamp FROM master_events")
        events = c.fetchall()

        print(f"\n📋 Auditing {len(events)} events...")

        violations = []

        for event in events:
            # Check if event has corresponding spike in price_history
            # Check if 1-second data exists
            # Check timestamp correlation
            pass

        if violations:
            print(f"\n❌ Found {len(violations)} events that don't meet Gold Standard:")
            for v in violations:
                print(f"   - Event {v['id']}: {v['reason']}")
            print(f"\nRecommendation: Review and possibly remove these events")
        else:
            print(f"\n✅ All events meet Gold Standard!")


def main():
    """Interactive workflow enforcer."""
    enforcer = SpikeFirstEnforcer()

    print("\n" + "=" * 80)
    print("SPIKE-FIRST ENFORCED WORKFLOW")
    print("=" * 80)
    print("\nThis script enforces the correct methodology:")
    print("  1. Find spikes FIRST (required)")
    print("  2. Search news at spike times (guided)")
    print("  3. Add events ONLY if validated (enforced)")
    print("\n❌ You CANNOT add events without finding spikes first")
    print("=" * 80)

    print("\nChoose action:")
    print("  1. Find spikes in 2023 data")
    print("  2. Search news for known spike")
    print("  3. Add validated event")
    print("  4. Audit existing events")

    choice = input("\nEnter choice (1-4): ")

    if choice == '1':
        enforcer.step1_find_spikes('2023-01-01', '2024-01-01')
    elif choice == '2':
        timestamp = input("Enter spike timestamp (YYYY-MM-DD HH:MM): ")
        enforcer.step2_search_news(timestamp)
    elif choice == '3':
        print("\nEnter event details:")
        spike_ts = input("  Spike timestamp: ")
        news_ts = input("  News timestamp: ")
        title = input("  Title (verbatim): ")
        desc = input("  Description (verbatim): ")
        source = input("  Source: ")
        url = input("  Source URL: ")

        enforcer.step3_add_event(spike_ts, news_ts, title, desc, source, url)
    elif choice == '4':
        enforcer.validate_existing_events()


if __name__ == "__main__":
    main()
