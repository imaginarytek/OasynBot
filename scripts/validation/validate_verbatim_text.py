#!/usr/bin/env python3
"""
Validate Verbatim Text - Ensure Event Descriptions Are Not Summaries

This script validates that event descriptions contain verbatim text from the original
source, not paraphrased summaries or AI-generated content.

Problem: The bot's "brain" needs the EXACT raw input traders saw to make accurate
decisions. Summaries lose crucial sentiment, tone, and emotional vocabulary that
markets react to.

This script identifies events where descriptions appear to be:
- Paraphrased summaries instead of verbatim text
- Too short to contain full source content
- Written in journalism style (not source language)
- Mixed quotes with narration/connecting text

Run this BEFORE backtesting to ensure data quality.
"""

import sqlite3
import re
from datetime import datetime

DB_PATH = 'data/hedgemony.db'

# Color codes for terminal output
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

# Minimum description lengths by source type
MIN_LENGTH_PRESS_RELEASE = 400  # SEC/official press releases should be substantial
MIN_LENGTH_COURT_DOC = 500      # Court rulings have formal language
MIN_LENGTH_ARTICLE = 300        # News articles
MIN_LENGTH_TWEET = 30           # Tweets are short but should be complete

# Red flag phrases that indicate journalism/summary, not verbatim source
JOURNALISM_RED_FLAGS = [
    'according to',
    'reported that',
    'according to documents',
    'providing a rare look',
    'the disclosure',
    'comes as',
    'marking a',
    'the report',
    'sources say',
    'people familiar with',
    'wrote in a statement',
    'said in a statement',
    'announced that',
    'revealed that',
]

# Green flag patterns that indicate verbatim official sources
OFFICIAL_LANGUAGE_PATTERNS = [
    r'^Washington D\.C\.,',                    # SEC press releases
    r'^Plaintiff, the Securities',             # Court documents
    r'^The .*Court of',                        # Court rulings
    r'^BREAKING:',                             # Breaking news tweets
    r'^The Securities and Exchange Commission', # SEC official
    r'^The U\.S\. Court',                      # Federal court docs
]

# Transitional phrases that connect quotes (indicates summary, not verbatim)
TRANSITIONAL_PHRASES = [
    'the ruling went on to say',
    'in addition',
    'furthermore',
    'the court also noted',
    'the commission explained',
    'as the ruling stated',
]


def detect_journalism_language(text):
    """
    Detect phrases that indicate journalism/summary style rather than verbatim source.

    Returns:
        - List of red flag phrases found
    """
    text_lower = text.lower()
    found_flags = []

    for flag in JOURNALISM_RED_FLAGS:
        if flag in text_lower:
            found_flags.append(flag)

    return found_flags


def detect_transitional_phrases(text):
    """
    Detect transitional phrases that connect quotes (indicates paraphrasing).

    Returns:
        - List of transitional phrases found
    """
    text_lower = text.lower()
    found_phrases = []

    for phrase in TRANSITIONAL_PHRASES:
        if phrase in text_lower:
            found_phrases.append(phrase)

    return found_phrases


def check_official_opening(text):
    """
    Check if text starts with official language patterns.

    Returns:
        - True if starts with official pattern
        - False otherwise
    """
    for pattern in OFFICIAL_LANGUAGE_PATTERNS:
        if re.match(pattern, text, re.IGNORECASE):
            return True
    return False


def classify_source_type(source_str, source_url):
    """
    Classify source type to determine expected description length.

    Returns:
        - 'press_release', 'court_doc', 'article', 'tweet', or 'unknown'
    """
    if not source_str and not source_url:
        return 'unknown'

    combined = (source_str or '').lower() + ' ' + (source_url or '').lower()

    if 'sec.gov' in combined or 'press release' in combined:
        return 'press_release'
    elif 'court' in combined or 'uscourts.gov' in combined or 'courtlistener.com' in combined:
        return 'court_doc'
    elif 'twitter' in combined or '@' in source_str:
        return 'tweet'
    elif 'wsj' in combined or 'bloomberg' in combined or 'reuters' in combined:
        return 'article'
    else:
        return 'unknown'


def validate_verbatim_text(event_id, title, description, source, source_url):
    """
    Validate if description appears to be verbatim text.

    Returns:
        - status: 'valid', 'suspicious', or 'invalid'
        - issues: List of issues found
    """
    if not description:
        return 'invalid', ['No description provided']

    issues = []
    source_type = classify_source_type(source, source_url)

    # Check 1: Length validation
    desc_len = len(description)

    if source_type == 'press_release' and desc_len < MIN_LENGTH_PRESS_RELEASE:
        issues.append(f"Too short for press release ({desc_len} chars, expected >{MIN_LENGTH_PRESS_RELEASE})")
    elif source_type == 'court_doc' and desc_len < MIN_LENGTH_COURT_DOC:
        issues.append(f"Too short for court document ({desc_len} chars, expected >{MIN_LENGTH_COURT_DOC})")
    elif source_type == 'article' and desc_len < MIN_LENGTH_ARTICLE:
        issues.append(f"Too short for article ({desc_len} chars, expected >{MIN_LENGTH_ARTICLE})")
    elif source_type == 'tweet' and desc_len < MIN_LENGTH_TWEET:
        issues.append(f"Too short for tweet ({desc_len} chars, expected >{MIN_LENGTH_TWEET})")

    # Check 2: Journalism language red flags
    journalism_flags = detect_journalism_language(description)
    if journalism_flags:
        issues.append(f"Contains journalism language: {', '.join(journalism_flags)}")

    # Check 3: Transitional phrases (indicates summary with quotes)
    transitional = detect_transitional_phrases(description)
    if transitional:
        issues.append(f"Contains transitional phrases: {', '.join(transitional)}")

    # Check 4: Official opening (for non-tweets)
    if source_type in ['press_release', 'court_doc'] and not check_official_opening(description):
        issues.append("Doesn't start with official language pattern")

    # Determine status
    if len(issues) == 0:
        return 'valid', []
    elif len(issues) >= 3 or any('journalism language' in i for i in issues):
        return 'invalid', issues  # Definitely not verbatim
    else:
        return 'suspicious', issues  # Might be verbatim, needs review


def validate_all_events():
    """
    Validate all events in master_events table for verbatim text.
    """
    print("=" * 80)
    print(f"{BLUE}VERBATIM TEXT VALIDATOR{RESET}")
    print("=" * 80)
    print(f"\nValidation Rules:")
    print(f"  - Event descriptions must be verbatim from original source")
    print(f"  - No paraphrasing, summarization, or AI rewriting")
    print(f"  - Preserves exact emotional tone and vocabulary")
    print(f"  - This is CRITICAL for AI analysis accuracy\n")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    events = conn.execute("""
        SELECT id, title, description, source, source_url
        FROM master_events
        ORDER BY id
    """).fetchall()

    if len(events) == 0:
        print(f"{YELLOW}No events found in master_events table.{RESET}")
        conn.close()
        return

    print(f"Analyzing {len(events)} events...\n")
    print("=" * 80)

    # Track results
    results = {
        'valid': [],
        'suspicious': [],
        'invalid': []
    }

    for row in events:
        event_id = row['id']
        title = row['title'][:60]
        description = row['description']
        source = row['source']
        source_url = row['source_url']

        print(f"\n{BLUE}[Event {event_id}]{RESET} {title}")
        print(f"  Source: {source}")
        print(f"  Length: {len(description) if description else 0} characters")

        # Validate
        status, issues = validate_verbatim_text(event_id, title, description, source, source_url)

        # Display result
        if status == 'valid':
            print(f"  {GREEN}✓ VALID{RESET} - Appears to be verbatim text")
            results['valid'].append(event_id)
        elif status == 'suspicious':
            print(f"  {YELLOW}⚠ SUSPICIOUS{RESET} - May not be fully verbatim")
            for issue in issues:
                print(f"    - {issue}")
            print(f"    {YELLOW}→ Action: Verify this is exact copy-paste from source{RESET}")
            results['suspicious'].append(event_id)
        else:  # invalid
            print(f"  {RED}✗ INVALID{RESET} - Likely paraphrased/summarized")
            for issue in issues:
                print(f"    - {issue}")
            print(f"    {RED}→ Action: Replace with verbatim text from source URL{RESET}")
            results['invalid'].append(event_id)

    conn.close()

    # Summary
    print("\n" + "=" * 80)
    print(f"{BLUE}VALIDATION SUMMARY{RESET}")
    print("=" * 80)

    total = len(events)
    valid_count = len(results['valid'])
    suspicious_count = len(results['suspicious'])
    invalid_count = len(results['invalid'])

    print(f"\nTotal Events: {total}")
    print(f"  {GREEN}✓ Valid:{RESET}       {valid_count:2d} ({valid_count/total*100:.1f}%)")
    print(f"  {YELLOW}⚠ Suspicious:{RESET}  {suspicious_count:2d} ({suspicious_count/total*100:.1f}%)")
    print(f"  {RED}✗ Invalid:{RESET}     {invalid_count:2d} ({invalid_count/total*100:.1f}%)")

    if invalid_count > 0:
        print(f"\n{RED}⚠ CRITICAL: {invalid_count} events contain non-verbatim text!{RESET}")
        print(f"These descriptions appear to be paraphrased summaries, not exact source text.")
        print(f"\n{RED}Why this matters:{RESET}")
        print(f"  - AI models need exact emotional vocabulary from original source")
        print(f"  - Summaries lose subtle sentiment signals markets react to")
        print(f"  - Paraphrasing introduces hindsight bias")
        print(f"  - Your bot's 'brain' gets inferior input data")
        print(f"\nInvalid events:")
        for event_id in results['invalid']:
            event = [e for e in events if e['id'] == event_id][0]
            print(f"  - Event {event_id}: {event['title'][:50]}...")
            print(f"    URL: {event['source_url']}")
        print(f"\n{RED}Action Required:{RESET}")
        print(f"  1. Visit the source URL")
        print(f"  2. Copy-paste the FIRST 3-4 paragraphs EXACTLY (verbatim)")
        print(f"  3. Include ALL original text (including typos, formatting)")
        print(f"  4. Do NOT summarize, paraphrase, or clean up")
        print(f"  5. Update database with true verbatim text")

    if suspicious_count > 0:
        print(f"\n{YELLOW}⚠ WARNING: {suspicious_count} events need verification{RESET}")
        print(f"These may be verbatim but show some warning signs.")
        print(f"\nSuspicious events:")
        for event_id in results['suspicious']:
            event = [e for e in events if e['id'] == event_id][0]
            print(f"  - Event {event_id}: {event['title'][:50]}...")

    if valid_count == total:
        print(f"\n{GREEN}✓ All events contain verbatim text! Dataset is clean.{RESET}")

    print("\n" + "=" * 80)
    print(f"\n{BLUE}RED FLAGS - How to Spot Non-Verbatim Text:{RESET}")
    print(f"\n❌ RED FLAGS (Not Verbatim):")
    print(f"  - Contains 'according to', 'reported that', 'sources say'")
    print(f"  - Has transitional sentences: 'The disclosure comes as...'")
    print(f"  - Mixes quotes with narration")
    print(f"  - Too short for source type (press release <400 chars)")
    print(f"  - Reads like journalism, not official source")
    print(f"\n✅ GREEN FLAGS (Verbatim):")
    print(f"  - Starts with: 'Washington D.C., [Date] —' (SEC)")
    print(f"  - Starts with: 'Plaintiff, the Securities...' (Court)")
    print(f"  - Pure official language throughout")
    print(f"  - 800-2000+ characters for official sources")
    print(f"  - Reads like bureaucratic/legal document")
    print(f"  - Preserves original emotional vocabulary")
    print("\n" + "=" * 80)


def main():
    validate_all_events()


if __name__ == "__main__":
    main()
