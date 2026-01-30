#!/usr/bin/env python3
"""
Helper script to manually input verbatim text for specific events
"""
import sqlite3

def input_manual_text():
    conn = sqlite3.connect("data/hedgemony.db")
    c = conn.cursor()
    
    # Get events needing manual input
    c.execute("""
        SELECT rowid, title, timestamp 
        FROM curated_events 
        WHERE description IS NULL 
        ORDER BY timestamp
    """)
    events = c.fetchall()
    
    print(f"Found {len(events)} events needing manual text.\n")
    
    for rowid, title, ts in events:
        print("="*60)
        print(f"Event: {title}")
        print(f"Date:  {ts}")
        print("="*60)
        print("Enter verbatim text (or SKIP/EXIT):")
        
        text = input("> ")
        
        if text.upper() == 'EXIT':
            break
        if text.upper() == 'SKIP':
            continue
            
        if text:
            c.execute("UPDATE curated_events SET description = ? WHERE rowid = ?", (text, rowid))
            conn.commit()
            print("✅ Saved.")
    
    conn.close()

if __name__ == "__main__":
    input_manual_text()
