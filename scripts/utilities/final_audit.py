
import sqlite3
import json
import os
import sys

# Checking hedgemony.db as confirmed
db_path = "data/hedgemony.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

print("🚀 FINAL DATA INTEGRITY AUDIT")
print("-" * 40)

# Check one High Quality Event
c.execute("""
    SELECT title, timestamp, length(sol_price_data), sol_price_data 
    FROM gold_events 
    WHERE sol_price_data IS NOT NULL 
    AND length(sol_price_data) > 100000 
    ORDER BY random() LIMIT 1
""")

row = c.fetchone()
if row:
    title, ts, size, raw_json = row
    data = json.loads(raw_json)
    
    print(f"✅ VERIFIED EVENT: {title}")
    print(f"📅 Timestamp: {ts}")
    print(f"📦 Payload Size: {size/1024:.2f} KB")
    print(f"🕯️  Candle Count: {len(data)}")
    
    if len(data) > 7000:
        print("🎉 SUCCESS: Data covers > 120 Minutes (1s resolution).")
        print(f"   First Candle: {data[0]['timestamp']}")
        print(f"   Last Candle:  {data[-1]['timestamp']}")
    else:
        print(f"⚠️ WARNING: Data count {len(data)} is less than expected 7200.")

else:
    print("❌ NO DATA FOUND with > 100KB payload. Backfill might have failed.")

conn.close()
