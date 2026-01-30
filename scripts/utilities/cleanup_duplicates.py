#!/usr/bin/env python3
"""
Clean up duplicate entries in curated_events table
Keep only the most recent fetch for each unique event
"""
import sqlite3

def cleanup_duplicates():
    print("🧹 CLEANING UP DUPLICATE EVENTS\n")
    
    conn = sqlite3.connect("data/hedgemony.db")
    c = conn.cursor()
    
    # Count before
    c.execute("SELECT COUNT(*) FROM curated_events")
    before_count = c.fetchone()[0]
    print(f"Before cleanup: {before_count} total entries")
    
    # Find duplicates
    c.execute("""
        SELECT title, timestamp, COUNT(*) as count
        FROM curated_events
        GROUP BY title, timestamp
        HAVING count > 1
    """)
    duplicates = c.fetchall()
    print(f"Found {len(duplicates)} events with duplicates")
    
    # Delete duplicates, keep the latest (highest rowid)
    c.execute("""
        DELETE FROM curated_events 
        WHERE rowid NOT IN (
            SELECT MAX(rowid) 
            FROM curated_events 
            GROUP BY title, timestamp
        )
    """)
    
    deleted = c.rowcount
    conn.commit()
    
    # Count after
    c.execute("SELECT COUNT(*) FROM curated_events")
    after_count = c.fetchone()[0]
    
    # Count with data
    c.execute("SELECT COUNT(*) FROM curated_events WHERE sol_price_data IS NOT NULL")
    with_data = c.fetchone()[0]
    
    conn.close()
    
    print(f"\n✅ Cleanup complete!")
    print(f"   Deleted: {deleted} duplicate entries")
    print(f"   Remaining: {after_count} unique events")
    print(f"   With price data: {with_data}")
    print(f"   Without data: {after_count - with_data}")

if __name__ == "__main__":
    cleanup_duplicates()
