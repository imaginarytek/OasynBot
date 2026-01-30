#!/usr/bin/env python3
"""
GOLD STANDARD: DATA QUALITY AUDIT
Identify which events have High Fidelity (1s) vs Low Fidelity (1m) vs Missing data.
"""

import sys
import os
import json
import sqlite3
import pandas as pd
import statistics

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.db import Database

class DataAuditor:
    def __init__(self):
        self.db = Database()

    def run(self):
        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT title, timestamp, price_data FROM gold_events ORDER BY timestamp DESC")
        events = [dict(row) for row in c.fetchall()]
        
        print(f"{'DATE':<12} | {'EVENT':<40} | {'QUALITY':<8} | {'NOTES'}")
        print("-" * 90)
        
        counts = {"1s": 0, "1m": 0, "Missing": 0}
        
        for e in events:
            # Skip future mocks (purged, but just in case)
            if '2025-' in e['timestamp']: continue
            
            quality = "Missing"
            notes = "No data blob"
            
            if e['price_data']:
                try:
                    data = json.loads(e['price_data'])
                    if len(data) > 2:
                        # Check resolution
                        t1 = pd.to_datetime(data[0]['timestamp'])
                        t2 = pd.to_datetime(data[1]['timestamp'])
                        diff = (t2 - t1).total_seconds()
                        
                        if diff <= 1.1:
                            quality = "🌟 1s"
                            notes = f"{len(data)} ticks"
                            counts["1s"] += 1
                        elif diff <= 65:
                            quality = "⚠️ 1m"
                            notes = "Low Res (Binance 1m)"
                            counts["1m"] += 1
                        else:
                            quality = "❓ Gap"
                            notes = f"Avg diff {diff}s"
                    else:
                        quality = "Missing"
                        notes = "Empty list"
                        counts["Missing"] += 1
                except:
                    quality = "Error"
                    notes = "JSON Parse Fail"
            
            # Print only missing/low res to answer user question?
            # Or all? User asked "what events... do we NOT have".
            # So I highlight the non-1s.
            
            if quality != "🌟 1s":
                print(f"{e['timestamp'][:10]:<12} | {e['title'][:38]:<40} | {quality:<8} | {notes}")
            
        print("-" * 90)
        print(f"SUMMARY: 1s (High Res): {counts['1s']}, 1m (Low Res): {counts['1m']}, Missing: {counts['Missing']}")

if __name__ == "__main__":
    auditor = DataAuditor()
    auditor.run()
