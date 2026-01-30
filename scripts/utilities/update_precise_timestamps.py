
import sqlite3
from datetime import datetime, timezone

def update_precise_timestamps():
    print("🚀 Updating Top 10 Events with Precise Timestamps...")
    conn = sqlite3.connect("data/hedgemony.db")
    c = conn.cursor()
    
    # Mapping of event titles to precise UTC timestamps
    precise_timestamps = {
        "President Trump Announces U.S. Crypto Reserve": "2025-03-02 12:24:00+00:00",
        "Jackson Hole Speech: Policy Adjustment": "2024-08-23 14:00:00+00:00",
        "Spot Bitcoin ETF Anticipation Volatility": "2024-01-10 21:30:00+00:00",  # Approximate
        "Roaring Kitty Returns: 'Lean Forward' Meme": "2024-05-13 00:00:00+00:00",  # 8pm EDT May 12 = midnight UTC May 13
        "Trump Elected President": "2024-11-06 10:34:00+00:00",
        "Approval of Ether Spot ETFs": "2024-05-23 22:00:00+00:00",  # Evening estimate
        "Nikkei 225 Plunges 12% in Historic Rout": "2024-08-05 00:00:00+00:00",  # 9am JST = midnight UTC
        "Binance Lists Book of Meme (BOME)": "2024-03-16 12:30:00+00:00",  # Trading start time
    }
    
    updated = 0
    for title_pattern, new_timestamp in precise_timestamps.items():
        # Update all events matching this title
        c.execute("""
            UPDATE gold_events 
            SET timestamp = ? 
            WHERE title LIKE ?
        """, (new_timestamp, f"%{title_pattern}%"))
        
        if c.rowcount > 0:
            print(f"   ✅ Updated {c.rowcount} events: {title_pattern}")
            print(f"      New timestamp: {new_timestamp}")
            updated += c.rowcount
    
    conn.commit()
    conn.close()
    print(f"\n🎉 Total events updated: {updated}")

if __name__ == "__main__":
    update_precise_timestamps()
