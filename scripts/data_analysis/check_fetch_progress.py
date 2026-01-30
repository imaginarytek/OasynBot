
import sqlite3
import json
from datetime import datetime

def check_progress():
    """Check how many events have been fetched"""
    conn = sqlite3.connect("data/hedgemony.db")
    c = conn.cursor()
    
    # Count total events in curated_events table
    c.execute("SELECT COUNT(*) FROM curated_events WHERE sol_price_data IS NOT NULL")
    fetched_count = c.fetchone()[0]
    
    # Get latest event
    c.execute("""
        SELECT title, timestamp 
        FROM curated_events 
        WHERE sol_price_data IS NOT NULL 
        ORDER BY rowid DESC 
        LIMIT 1
    """)
    latest = c.fetchone()
    
    conn.close()
    
    print(f"📊 FETCH PROGRESS REPORT")
    print(f"{'='*60}")
    print(f"Events fetched: {fetched_count}/100")
    print(f"Progress: {fetched_count/100*100:.1f}%")
    
    if latest:
        print(f"\nLatest event:")
        print(f"  {latest[0]}")
        print(f"  {latest[1]}")
    
    print(f"\nRemaining: {100 - fetched_count} events")
    print(f"{'='*60}")

if __name__ == "__main__":
    check_progress()
