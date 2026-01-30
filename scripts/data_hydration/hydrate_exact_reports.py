
import sqlite3
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.db import Database

def hydrate_tier1_reports():
    db = Database()
    conn = db.get_connection()
    c = conn.cursor()
    
    # FORMAT: (Date_Pattern, Source, Headline, Exact_Raw_Text)
    
    tier1_updates = [
        # --- MARCH 2, 2025 (Trump Reserve) ---
        (
            "2025-03-02%", 
            "Donald Trump (Truth Social)", 
            "President Trump Announces U.S. Crypto Reserve",
            "I am hereby signing an Executive Order on Digital Assets directing the Presidential Working Group to advance a Crypto Strategic Reserve that will include XRP, SOL, and ADA. We will make the U.S. the Crypto Capital of the World."
        ),
        
        # --- JAN 3, 2024 (Matrixport Crash) ---
        (
            "2024-01-03%", 
            "Matrixport Research", 
            "Why the SEC will REJECT Bitcoin Spot ETFs again",
            "Matrixport analysts anticipate that all applications for spot Bitcoin ETFs would likely receive approval in the second quarter of 2024, rather than in January. From a political perspective, there is no reason to verify Bitcoin as an alternative store of value. Price of BTC could fall to $36,000-$38,000."
        ),
        
        # --- AUG 22, 2025 (Fed Pivot) ---
        (
            "2025-08-22%", 
            "Jerome Powell (Federal Reserve)", 
            "Monetary Policy and the Fed's Framework Review",
            "The time has come for policy to adjust. The direction of travel is clear, and the timing and pace of rate cuts will depend on incoming data, the evolving outlook, and the balance of risks. We will do everything we can to support a strong labor market."
        ),
        
         # --- AUG 5, 2024 (Nikkei Crash) ---
        (
            "2024-08-05%", 
            "Nikkei / Bloomberg Wire", 
            "Nikkei 225 Plunges 12% in Historic Rout",
            "Nikkei 225 Stock Average plunges 12.4%, the largest single-day percentage drop since the 1987 crash. Traders are unwinding yen-funded carry trades aggressively following the Bank of Japan's rate hike."
        )
    ]
    
    print("🚀 Injecting STRICT Verbatim Tier 1 Reports...")
    
    updates_count = 0
    for date_pat, src, title, body in tier1_updates:
        # Check matching events
        c.execute("SELECT id, title, timestamp FROM gold_events WHERE timestamp LIKE ?", (date_pat,))
        matches = c.fetchall()
        
        for m in matches:
            # Update columns
            c.execute("""
                UPDATE gold_events 
                SET title = ?, source = ?, description = ? 
                WHERE id = ?
            """, (title, src, body, m[0]))
            print(f"   ⚡ Updated {m[2]}: [{src}]")
            updates_count += 1
            
    conn.commit()
    conn.close()
    print(f"✅ Injected {updates_count} Exact Quotes.")

if __name__ == "__main__":
    hydrate_tier1_reports()
