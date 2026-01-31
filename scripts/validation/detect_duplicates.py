#!/usr/bin/env python3
"""
Detect Duplicate and Related Events (Material Escalation Filter)

Enforces the "Material Escalation" rule from event_scraping skill:
- Rumor: "SEC investigating X" → Keep (causes spike)
- Confirmation: "SEC Files Lawsuit" → Keep (new spike + new info)
- Echo: "Report: SEC lawsuit details" → Reject (no new spike, no new info)

This script:
1. Finds events within 24 hours with similar titles
2. Checks if each caused a distinct price spike (Z > 3.0)
3. Analyzes verbatim text for new information
4. Flags potential duplicates/echoes for manual review
5. Suggests which events to keep vs reject

Run this BEFORE finalizing the dataset to ensure no redundant events.
"""

import sqlite3
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from difflib import SequenceMatcher
import sys
import os

# Constants
INPUT_DB_PATH = 'data/hedgemony.db'
VALIDATION_DB_PATH = 'data/hedgemony_validation.db'
TIME_WINDOW_HOURS = 24  # Consider events within 24h as potentially related
TITLE_SIMILARITY_THRESHOLD = 0.6  # 60% similar = potentially related
MIN_Z_SCORE_FOR_DISTINCT = 3.0  # Each event must cause Z>3 spike to be kept

# Color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def get_db_connections():
    """Create connections to both databases"""
    input_conn = sqlite3.connect(INPUT_DB_PATH)
    input_conn.row_factory = sqlite3.Row

    validation_conn = sqlite3.connect(VALIDATION_DB_PATH)
    validation_conn.row_factory = sqlite3.Row

    return input_conn, validation_conn


def calculate_title_similarity(title1, title2):
    """
    Calculate similarity ratio between two titles (0.0 to 1.0).

    Uses SequenceMatcher for fuzzy string matching.
    """
    if not title1 or not title2:
        return 0.0

    # Normalize: lowercase, remove extra spaces
    t1 = ' '.join(title1.lower().split())
    t2 = ' '.join(title2.lower().split())

    return SequenceMatcher(None, t1, t2).ratio()


def extract_keywords(text):
    """
    Extract key entities/terms from text for content comparison.

    Returns set of important words (excluding common stopwords).
    """
    if not text:
        return set()

    stopwords = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
        'could', 'may', 'might', 'can', 'this', 'that', 'these', 'those'
    }

    words = text.lower().split()
    keywords = {w.strip('.,!?;:') for w in words if len(w) > 3 and w not in stopwords}

    return keywords


def analyze_content_overlap(desc1, desc2):
    """
    Analyze if two event descriptions contain new vs repeated information.

    Returns:
        - overlap_ratio (float): 0.0 to 1.0, how much content is shared
        - new_info_in_2 (set): Keywords in desc2 that aren't in desc1
    """
    keywords1 = extract_keywords(desc1)
    keywords2 = extract_keywords(desc2)

    if not keywords1 or not keywords2:
        return 0.0, keywords2

    overlap = keywords1.intersection(keywords2)
    new_info = keywords2 - keywords1

    if len(keywords2) == 0:
        overlap_ratio = 0.0
    else:
        overlap_ratio = len(overlap) / len(keywords2)

    return overlap_ratio, new_info


def check_distinct_spikes(event1_data, event2_data):
    """
    Check if two events each caused distinct price spikes.

    Returns:
        - both_spiked (bool): True if both events show Z>3 spike
        - reason (str): Explanation
    """
    z1 = event1_data.get('volatility_z_score')
    z2 = event2_data.get('volatility_z_score')

    if z1 is None or z2 is None:
        return False, "Missing volatility_z_score for one or both events"

    if z1 >= MIN_Z_SCORE_FOR_DISTINCT and z2 >= MIN_Z_SCORE_FOR_DISTINCT:
        return True, f"Both caused distinct spikes (Z1={z1:.1f}, Z2={z2:.1f})"

    if z1 < MIN_Z_SCORE_FOR_DISTINCT and z2 >= MIN_Z_SCORE_FOR_DISTINCT:
        return False, f"Event 1 weak (Z={z1:.1f}), Event 2 valid (Z={z2:.1f}) → Keep Event 2"

    if z2 < MIN_Z_SCORE_FOR_DISTINCT and z1 >= MIN_Z_SCORE_FOR_DISTINCT:
        return False, f"Event 2 weak (Z={z2:.1f}), Event 1 valid (Z={z1:.1f}) → Keep Event 1"

    return False, f"Both weak (Z1={z1:.1f}, Z2={z2:.1f})"


def detect_duplicates():
    """
    Detect and report duplicate/related events in master_events.

    Groups events by:
    1. Time proximity (within 24 hours)
    2. Title similarity (>60%)

    For each group:
    - Check if both caused distinct spikes
    - Analyze content overlap
    - Apply Material Escalation logic
    - Suggest which to keep vs remove
    """
    print("=" * 80)
    print(f"{BLUE}DUPLICATE EVENT DETECTOR{RESET}")
    print("=" * 80)
    print(f"\nDetection Rules:")
    print(f"  - Events within {TIME_WINDOW_HOURS}h with >{TITLE_SIMILARITY_THRESHOLD*100:.0f}% title similarity")
    print(f"  - Each event must cause distinct Z>{MIN_Z_SCORE_FOR_DISTINCT} spike")
    print(f"  - Later event must contain NEW information (not just echo)\n")

    input_conn, validation_conn = get_db_connections()

    # Get events from input DB
    input_events = input_conn.execute("""
        SELECT id, title, timestamp, description, source, category
        FROM master_events
        ORDER BY timestamp ASC
    """).fetchall()

    # Get metrics from validation DB
    metrics = {}
    for row in validation_conn.execute("SELECT event_id, volatility_z_score, time_to_impact_seconds FROM event_metrics"):
        metrics[row['event_id']] = {
            'volatility_z_score': row['volatility_z_score'],
            'time_to_impact_seconds': row['time_to_impact_seconds']
        }

    # Combine data
    events = []
    for event in input_events:
        event_dict = dict(event)
        event_metrics = metrics.get(event['id'], {})
        event_dict['volatility_z_score'] = event_metrics.get('volatility_z_score')
        event_dict['time_to_impact_seconds'] = event_metrics.get('time_to_impact_seconds')
        events.append(event_dict)

    if len(events) == 0:
        print(f"{YELLOW}No events found in master_events.{RESET}")
        input_conn.close()
        validation_conn.close()
        return

    print(f"Analyzing {len(events)} events for duplicates...\n")
    print("=" * 80)

    # Convert to list of dicts for easier processing
    events_list = [dict(row) for row in events]

    # Track duplicate groups
    duplicate_groups = []
    checked_pairs = set()

    # Compare each event with subsequent events
    for i, event1 in enumerate(events_list):
        for j in range(i + 1, len(events_list)):
            event2 = events_list[j]

            # Skip if already checked
            pair_key = (event1['id'], event2['id'])
            if pair_key in checked_pairs:
                continue
            checked_pairs.add(pair_key)

            # Parse timestamps
            try:
                ts1 = pd.to_datetime(event1['timestamp'])
                ts2 = pd.to_datetime(event2['timestamp'])
            except Exception:
                continue

            # Check time proximity
            time_diff_hours = abs((ts2 - ts1).total_seconds() / 3600)
            if time_diff_hours > TIME_WINDOW_HOURS:
                continue  # Too far apart in time

            # Check title similarity
            similarity = calculate_title_similarity(event1['title'], event2['title'])
            if similarity < TITLE_SIMILARITY_THRESHOLD:
                continue  # Titles not similar enough

            # Found a potential duplicate pair!
            print(f"\n{YELLOW}⚠ POTENTIAL DUPLICATE FOUND{RESET}")
            print(f"{BLUE}Event 1 (ID {event1['id']}):{RESET}")
            print(f"  Title: {event1['title'][:70]}")
            print(f"  Time:  {ts1}")
            print(f"  Source: {event1['source']}")
            print(f"{BLUE}Event 2 (ID {event2['id']}):{RESET}")
            print(f"  Title: {event2['title'][:70]}")
            print(f"  Time:  {ts2} ({time_diff_hours:.1f}h later)")
            print(f"  Source: {event2['source']}")
            print(f"\n  Title Similarity: {similarity*100:.1f}%")

            # Check if both caused distinct spikes
            both_spiked, spike_reason = check_distinct_spikes(event1, event2)
            print(f"  Spike Analysis: {spike_reason}")

            # Analyze content overlap
            desc1 = event1.get('description', '')
            desc2 = event2.get('description', '')
            overlap_ratio, new_keywords = analyze_content_overlap(desc1, desc2)

            print(f"  Content Overlap: {overlap_ratio*100:.1f}%")
            if new_keywords and len(new_keywords) > 0:
                print(f"  New Keywords in Event 2: {', '.join(list(new_keywords)[:10])}")

            # Apply Material Escalation Logic
            print(f"\n  {BLUE}Recommendation:{RESET}")

            if both_spiked and overlap_ratio < 0.7:
                # Both caused spikes AND Event 2 has new info → KEEP BOTH
                print(f"    {GREEN}✓ KEEP BOTH{RESET} - Material Escalation detected")
                print(f"      Each event caused distinct market reaction with new information")
                recommendation = "keep_both"
            elif both_spiked and overlap_ratio >= 0.7:
                # Both spiked but content is mostly duplicate → REVIEW
                print(f"    {YELLOW}? REVIEW{RESET} - Both valid but similar content")
                print(f"      Manual review needed to determine if truly distinct")
                recommendation = "review"
            elif not both_spiked:
                # One or both didn't cause valid spike → REMOVE WEAK ONE
                z1 = event1.get('volatility_z_score', 0)
                z2 = event2.get('volatility_z_score', 0)

                if z1 < MIN_Z_SCORE_FOR_DISTINCT and z2 >= MIN_Z_SCORE_FOR_DISTINCT:
                    print(f"    {RED}✗ REMOVE Event 1 (ID {event1['id']}){RESET} - Weak spike")
                    recommendation = "remove_event1"
                elif z2 < MIN_Z_SCORE_FOR_DISTINCT and z1 >= MIN_Z_SCORE_FOR_DISTINCT:
                    print(f"    {RED}✗ REMOVE Event 2 (ID {event2['id']}){RESET} - Weak spike")
                    recommendation = "remove_event2"
                else:
                    print(f"    {RED}✗ REMOVE BOTH{RESET} - Neither caused valid spike")
                    recommendation = "remove_both"
            else:
                recommendation = "review"

            # Store duplicate group
            duplicate_groups.append({
                'event1_id': event1['id'],
                'event2_id': event2['id'],
                'similarity': similarity,
                'time_diff_hours': time_diff_hours,
                'both_spiked': both_spiked,
                'content_overlap': overlap_ratio,
                'recommendation': recommendation
            })

    input_conn.close()
    validation_conn.close()

    # Summary
    print("\n" + "=" * 80)
    print(f"{BLUE}DETECTION SUMMARY{RESET}")
    print("=" * 80)

    if len(duplicate_groups) == 0:
        print(f"\n{GREEN}✓ No duplicates detected! Dataset is clean.{RESET}")
    else:
        print(f"\n{YELLOW}Found {len(duplicate_groups)} potential duplicate pairs:{RESET}")

        keep_both = sum(1 for g in duplicate_groups if g['recommendation'] == 'keep_both')
        review = sum(1 for g in duplicate_groups if g['recommendation'] == 'review')
        remove = sum(1 for g in duplicate_groups if 'remove' in g['recommendation'])

        print(f"  {GREEN}✓ Keep Both:{RESET}  {keep_both} (Material Escalation)")
        print(f"  {YELLOW}? Review:{RESET}     {review} (Manual decision needed)")
        print(f"  {RED}✗ Remove:{RESET}     {remove} (Duplicates/Weak events)")

        if review > 0 or remove > 0:
            print(f"\n{YELLOW}⚠ Manual review recommended before running backtests.{RESET}")

    print("\n" + "=" * 80)


def main():
    if not os.path.exists(INPUT_DB_PATH):
        print(f"{RED}Error: Input database not found at {INPUT_DB_PATH}{RESET}")
        sys.exit(1)

    if not os.path.exists(VALIDATION_DB_PATH):
        print(f"{RED}Error: Validation database not found at {VALIDATION_DB_PATH}{RESET}")
        sys.exit(1)

    detect_duplicates()


if __name__ == "__main__":
    main()
