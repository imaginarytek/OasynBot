#!/usr/bin/env python3
"""
Source Priority Checker

Identifies events where the source might be SECONDARY (official publication)
instead of PRIMARY (first breaking news).

Problem: Markets react to BREAKING NEWS (tweets, terminal alerts), not official
publications. If your source is sec.gov but lag is 25s, traders likely learned
from a Bloomberg tweet 20s earlier.

This script helps identify which events need re-research to find the TRUE first source.
"""

import sqlite3
import json
import re
from datetime import datetime, timedelta

INPUT_DB_PATH = 'data/hedgemony.db'
VALIDATION_DB_PATH = 'data/hedgemony_validation.db'

# Source priority classification
SECONDARY_SOURCES = [
    'sec.gov',
    'uscourts.gov',
    'courtlistener.com',
    'federalregister.gov',
    '.gov',  # Any government website
]

BREAKING_NEWS_SOURCES = [
    'bloomberg',
    'reuters',
    'twitter',
    '@',  # Twitter handles
    'terminal',
    'alert',
]

# Color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def classify_source(source_str, source_url):
    """
    Classify if source is PRIMARY (breaking news) or SECONDARY (official).

    Returns:
        - 'primary': Breaking news source (tweets, Bloomberg Terminal, etc.)
        - 'secondary': Official publication (government websites, court filings)
        - 'unknown': Cannot determine
    """
    if not source_str and not source_url:
        return 'unknown'

    combined = (source_str or '').lower() + ' ' + (source_url or '').lower()

    # Check for breaking news indicators
    for indicator in BREAKING_NEWS_SOURCES:
        if indicator in combined:
            return 'primary'

    # Check for secondary source indicators
    for indicator in SECONDARY_SOURCES:
        if indicator in combined:
            return 'secondary'

    return 'unknown'


def check_all_sources():
    """
    Check all events for source priority issues.

    Flags events where:
    1. Source is SECONDARY (official website)
    2. Lag is >10s (suggests traders learned earlier from breaking news)
    """
    print("=" * 80)
    print(f"{BLUE}SOURCE PRIORITY CHECKER{RESET}")
    print("=" * 80)
    print(f"\nThis script identifies events using SECONDARY sources (official publications)")
    print(f"instead of PRIMARY sources (first breaking news).\n")
    print(f"Why this matters: Markets react to tweets/terminal alerts, not gov websites.")
    print(f"If you use sec.gov as source but lag is 20s, traders likely learned from a")
    print(f"Bloomberg tweet 15 seconds earlier!\n")

    # Connect to both databases
    input_conn = sqlite3.connect(INPUT_DB_PATH)
    input_conn.row_factory = sqlite3.Row

    validation_conn = sqlite3.connect(VALIDATION_DB_PATH)
    validation_conn.row_factory = sqlite3.Row

    # Get events from input DB
    input_events = input_conn.execute("""
        SELECT id, title, timestamp, source, source_url
        FROM master_events
        ORDER BY id
    """).fetchall()

    # Get metrics from validation DB
    metrics = {}
    for row in validation_conn.execute("SELECT event_id, time_to_impact_seconds FROM event_metrics"):
        metrics[row['event_id']] = row['time_to_impact_seconds']

    # Combine data
    events = []
    for event in input_events:
        event_dict = dict(event)
        event_dict['time_to_impact_seconds'] = metrics.get(event['id'])
        events.append(event_dict)

    # Sort by lag (highest first)
    events.sort(key=lambda x: x['time_to_impact_seconds'] if x['time_to_impact_seconds'] is not None else 0, reverse=True)

    if len(events) == 0:
        print(f"{YELLOW}No events found in master_events.{RESET}")
        input_conn.close()
        validation_conn.close()
        return

    print(f"Analyzing {len(events)} events...\n")
    print("=" * 80)

    issues = []

    for row in events:
        event_id = row['id']
        title = row['title']
        source = row['source']
        source_url = row['source_url']
        lag = row['time_to_impact_seconds']

        # Classify source
        source_type = classify_source(source, source_url)

        # Flag issues
        has_issue = False
        issue_reasons = []

        if source_type == 'secondary' and lag and lag > 10:
            has_issue = True
            issue_reasons.append(f"Secondary source with {lag}s lag")

        if source_type == 'secondary' and lag and lag > 20:
            has_issue = True
            issue_reasons.append(f"CRITICAL: Secondary source with {lag}s lag (very likely wrong)")

        if has_issue:
            print(f"\n{YELLOW}⚠ Event {event_id}: {title[:55]}{RESET}")
            print(f"  Source: {source}")
            print(f"  URL: {source_url}")
            print(f"  Lag: {lag}s")
            print(f"  Type: {source_type.upper()}")
            print(f"  Issues:")
            for reason in issue_reasons:
                print(f"    - {reason}")
            print(f"\n  {BLUE}Recommended Action:{RESET}")
            print(f"    1. Calculate when spike actually happened: T - {lag}s")
            print(f"    2. Search Twitter for that exact time:")

            # Calculate what time to search
            if lag:
                event_time = datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00'))
                actual_spike_time = event_time + timedelta(seconds=lag)
                search_start = actual_spike_time - timedelta(seconds=30)
                search_end = actual_spike_time + timedelta(seconds=10)

                print(f"       site:twitter.com since:{search_start.strftime('%Y-%m-%d_%H:%M:%S')}")
                print(f"                        until:{search_end.strftime('%Y-%m-%d_%H:%M:%S')}")

            print(f"    3. Look for:")
            print(f"       - Bloomberg Terminal screenshots")
            print(f"       - Court reporters: @jbarro, @KatieGrfeld, @EleanorTerrett")
            print(f"       - Breaking news: @tier10k, @unusual_whales, @DeItaone")
            print(f"    4. Update event with the FIRST breaking source")

            issues.append({
                'event_id': event_id,
                'title': title,
                'source_type': source_type,
                'lag': lag,
                'reasons': issue_reasons
            })

    input_conn.close()
    validation_conn.close()

    # Summary
    print("\n" + "=" * 80)
    print(f"{BLUE}SUMMARY{RESET}")
    print("=" * 80)

    if len(issues) == 0:
        print(f"\n{GREEN}✓ No source priority issues found!{RESET}")
        print(f"All events appear to use primary/breaking sources with tight timing.")
    else:
        print(f"\n{YELLOW}Found {len(issues)} events with potential source priority issues:{RESET}\n")

        for issue in issues:
            print(f"  Event {issue['event_id']}: {issue['title'][:50]}... ")
            print(f"    → {issue['source_type'].upper()} source, {issue['lag']}s lag")

        print(f"\n{YELLOW}⚠ These events should be re-researched to find the TRUE first source.{RESET}")
        print(f"\nSource Priority Hierarchy:")
        print(f"  {GREEN}1. PRIMARY (Use this!):{RESET}")
        print(f"     - Bloomberg Terminal alerts")
        print(f"     - Breaking news tweets (@Bloomberg, @Reuters)")
        print(f"     - Court reporter tweets (if in courtroom)")
        print(f"     - News wire flashes")
        print(f"  {YELLOW}2. SECONDARY (Avoid if lag >10s):{RESET}")
        print(f"     - Official government websites (sec.gov, uscourts.gov)")
        print(f"     - Press release pages")
        print(f"     - Court docket websites")
        print(f"\n{BLUE}Why?{RESET} Traders don't read .gov websites. They see tweets and terminal alerts first!")

    print("\n" + "=" * 80)


def main():
    check_all_sources()


if __name__ == "__main__":
    main()
