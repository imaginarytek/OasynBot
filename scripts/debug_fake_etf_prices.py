import sqlite3
import json
import pandas as pd

conn = sqlite3.connect('data/hedgemony.db')
c = conn.cursor()

c.execute("SELECT sol_price_data FROM master_events WHERE title LIKE '%Cointelegraph%'")
row = c.fetchone()

if row:
    data = json.loads(row[0])
    df = pd.DataFrame(data)
    
    # Locate T=0 (Target Timestamp)
    # The JSON usually contains pre-buffer.
    # Our script logic: T0 is usually index 300 (5 mins * 60s).
    
    t0_idx = 300
    if len(df) > t0_idx + 300: # Ensure we have 5 mins post
        t0 = df.iloc[t0_idx]
        t5m = df.iloc[t0_idx + 300]
        
        print(f"T=0 ({t0['timestamp']}): Open={t0['open']}, High={t0['high']}, Low={t0['low']}, Close={t0['close']}")
        print(f"T+5m ({t5m['timestamp']}): Open={t5m['open']}, Close={t5m['close']}")
        
        move = (t5m['close'] - t0['open']) / t0['open']
        print(f"Calculated 5m Move: {move * 100:.2f}%")
        
    else:
        print("Data too short")
else:
    print("Event not found")
