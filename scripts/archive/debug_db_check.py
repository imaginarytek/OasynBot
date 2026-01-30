
import sqlite3
import os
import sys

# Check standard path
db_path = "data/hedgemony.db"
print(f"Checking DB at: {os.path.abspath(db_path)}")

conn = sqlite3.connect(db_path)
c = conn.cursor()

try:
    c.execute("SELECT id, title, sol_price_data FROM gold_events LIMIT 1")
    row = c.fetchone()
    if row:
        eid, title, data = row
        if data:
            print(f"✅ Data Found! Event ID: {eid}")
            print(f"   Title: {title}")
            print(f"   Data Length: {len(data)} characters")
        else:
            print(f"❌ Data is NULL/Empty for Event ID: {eid} - {title}")
    else:
        print("❌ no rows found in gold_events table")

except Exception as e:
    print(f"Error: {e}")

conn.close()
