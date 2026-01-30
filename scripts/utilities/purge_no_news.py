
import sqlite3
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.db import Database

def purge_no_news():
    print("🚀 Purging 'No News' Events from Database...")
    db = Database()
    conn = db.get_connection()
    c = conn.cursor()
    
    # 1. Select Count before
    c.execute("SELECT COUNT(*) FROM gold_events")
    total_before = c.fetchone()[0]
    
    # 2. Delete Unmapped
    # Criteria: Title starts with "Unmapped" OR "Unspecified"
    # AND Description matches the generic placeholder
    
    c.execute("""
        DELETE FROM gold_events 
        WHERE title LIKE 'Unmapped%' 
        OR title LIKE 'Unspecified%'
        OR source = 'Unknown Tier 1 Source'
    """)
    deleted = c.rowcount
    conn.commit()
    
    # 3. Select Count after
    c.execute("SELECT COUNT(*) FROM gold_events")
    total_after = c.fetchone()[0]
    
    print(f"📉 Deleted {deleted} events with no confirmed news.")
    print(f"✅ Remaining High-Quality Training Events: {total_after}")
    
    conn.close()

if __name__ == "__main__":
    purge_no_news()
