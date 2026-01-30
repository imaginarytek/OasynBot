
import sqlite3
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.db import Database

def migrate_schema():
    print("🚀 Upgrading Database Schema for High-Fidelity News...")
    db = Database()
    conn = db.get_connection()
    c = conn.cursor()
    
    # Check if columns exist
    c.execute("PRAGMA table_info(gold_events)")
    columns = [row[1] for row in c.fetchall()]
    
    if 'source' not in columns:
        print("   + Adding 'source' column")
        c.execute("ALTER TABLE gold_events ADD COLUMN source TEXT")
        
    if 'description' not in columns:
        print("   + Adding 'description' column (Full Report Text)")
        c.execute("ALTER TABLE gold_events ADD COLUMN description TEXT")

    # Clean up generic titles if needed? No, let's keep them until we fill them.
    
    conn.commit()
    conn.close()
    print("✅ Schema Upgrade Complete.")

if __name__ == "__main__":
    migrate_schema()
