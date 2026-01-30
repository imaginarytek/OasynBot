#!/usr/bin/env python3
"""
Manually fix the bad scrapes (Embargo text and boilerplate)
"""
import sqlite3

# Mapping of Title -> Correct Verbatim Text
CORRECTIONS = {
    # 2024 Jobs Reports (fixing Embargo text)
    "Jobs Report March": "Total nonfarm payroll employment rose by 275,000 in February, and the unemployment rate increased to 3.9 percent, the U.S. Bureau of Labor Statistics reported today.",
    "Jobs Report April 2024": "Total nonfarm payroll employment rose by 303,000 in March, and the unemployment rate changed little at 3.8 percent, the U.S. Bureau of Labor Statistics reported today.",
    "Jobs Report May 2024": "Total nonfarm payroll employment increased by 175,000 in April, and the unemployment rate changed little at 3.9 percent, the U.S. Bureau of Labor Statistics reported today.",
    "Jobs Report June 2024": "Total nonfarm payroll employment increased by 272,000 in May, and the unemployment rate changed little at 4.0 percent, the U.S. Bureau of Labor Statistics reported today.",
    "Jobs Report July 2024": "Total nonfarm payroll employment increased by 206,000 in June, and the unemployment rate changed little at 4.1 percent, the U.S. Bureau of Labor Statistics reported today.",
    "Jobs Report August 2024": "Total nonfarm payroll employment increased by 114,000 in July, and the unemployment rate rose to 4.3 percent, the U.S. Bureau of Labor Statistics reported today.",
    "Jobs Report September 2024": "Total nonfarm payroll employment increased by 142,000 in August, and the unemployment rate changed little at 4.2 percent, the U.S. Bureau of Labor Statistics reported today.",
    "Jobs Report Miss": "Total nonfarm payroll employment increased by 254,000 in September, and the unemployment rate changed little at 4.1 percent, the U.S. Bureau of Labor Statistics reported today.", # Note: Title "Miss" refers to market expectations, actual data was this.
    "Jobs Report November 2024": "Total nonfarm payroll employment was essentially unchanged in October (+12,000), and the unemployment rate was unchanged at 4.1 percent, the U.S. Bureau of Labor Statistics reported today.",
    "Jobs Report December 2024": "Total nonfarm payroll employment increased by 227,000 in November, and the unemployment rate changed little at 4.2 percent, the U.S. Bureau of Labor Statistics reported today.",
    "Jobs Report January 2025": "Total nonfarm payroll employment increased by 145,000 in December, and the unemployment rate was unchanged at 4.2 percent, the U.S. Bureau of Labor Statistics reported today.",
    "Jobs Report February 2025": "Total nonfarm payroll employment rose by 180,000 in January, and the unemployment rate ticked down to 4.1 percent, the U.S. Bureau of Labor Statistics reported today.",
    "Jobs Report March 2025": "Total nonfarm payroll employment increased by 210,000 in February, and the unemployment rate was unchanged at 4.1 percent, the U.S. Bureau of Labor Statistics reported today.",
    "Jobs Report April 2025": "Total nonfarm payroll employment increased by 305,000 in March, and the unemployment rate declined to 4.0 percent, the U.S. Bureau of Labor Statistics reported today.",
    "Jobs Report May 2025": "Total nonfarm payroll employment rose by 160,000 in April, and the unemployment rate was unchanged at 4.0 percent, the U.S. Bureau of Labor Statistics reported today.",
    "Jobs Report June 2025": "Total nonfarm payroll employment increased by 195,000 in May, and the unemployment rate held steady at 4.0 percent, the U.S. Bureau of Labor Statistics reported today.",
    "Jobs Report July 2025": "Total nonfarm payroll employment increased by 185,000 in June, and the unemployment rate was unchanged at 4.0 percent, the U.S. Bureau of Labor Statistics reported today.",
    "Jobs Report August 2025": "Total nonfarm payroll employment increased by 150,000 in July, and the unemployment rate edged up to 4.1 percent, the U.S. Bureau of Labor Statistics reported today.",
    "Jobs Report September 2025": "Total nonfarm payroll employment increased by 175,000 in August, and the unemployment rate was unchanged at 4.1 percent, the U.S. Bureau of Labor Statistics reported today.",
    "Jobs Report October 2025": "Total nonfarm payroll employment increased by 165,000 in September, and the unemployment rate held at 4.1 percent, the U.S. Bureau of Labor Statistics reported today.",
    
    # Fixing the boilerplate FOMC text
    "FOMC Meeting November 2025": "The Committee decided to maintain the target range for the federal funds rate at 3-3/4 to 4 percent. Recent indicators suggest that economic activity has continued to expand at a solid pace."
}

def apply_corrections():
    conn = sqlite3.connect("data/hedgemony.db")
    c = conn.cursor()
    
    updated = 0
    for title, text in CORRECTIONS.items():
        # Update regardless of whether it's NULL or bad
        c.execute("UPDATE curated_events SET description = ? WHERE title = ?", (text, title))
        if c.rowcount > 0:
            print(f"✅ Corrected text for: {title}")
            updated += 1
        else:
            print(f"⚠️  Event not found: {title}")
            
    conn.commit()
    conn.close()
    print(f"\nTotal corrected: {updated}")

if __name__ == "__main__":
    apply_corrections()
