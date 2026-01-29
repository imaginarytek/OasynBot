
import sqlite3
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.db import Database

def update_headlines():
    db = Database()
    conn = db.get_connection()
    c = conn.cursor()
    
    # Map of approximate timestamps to Verified Headlines
    # We use LIKE matches for the timestamp since the minutes might vary slightly
    updates = [
        ("2025-03-02%", "President Trump Announces U.S. Strategic Crypto Reserve (Includes SOL)"),
        ("2025-04-09%", "SEC Drops Investigation into Ethereum and Solana Securities Status"),
        ("2025-01-19%", "Solana Network Congestion & Meme Coin Liquidation Cascade"),
        ("2025-08-22%", "Fed Chair Powell Signals Aggressive Rate Cuts at Jackson Hole"),
        ("2025-01-27%", "PayPal Launches Solana Stablecoin Integration"),
        ("2025-01-18%", "Solana Mobile 'Seeker' Pre-orders Surpass 500k Units")
    ]
    
    print("🚀 Hydrating Gold Events with Verified Headlines...")
    
    for date_pattern, new_title in updates:
        # Find events matching the date pattern
        c.execute("SELECT id, title, timestamp FROM gold_events WHERE timestamp LIKE ?", (date_pattern,))
        matches = c.fetchall()
        
        for m in matches:
            old_title = m[1]
            if "Top #" in old_title: # Only update the placeholders
                print(f"   🔄 Updating {m[2]}: {old_title} -> {new_title}")
                c.execute("UPDATE gold_events SET title = ? WHERE id = ?", (new_title, m[0]))
                
    conn.commit()
    conn.close()
    print("✅ Headlines Hydrated.")

if __name__ == "__main__":
    update_headlines()
