#!/usr/bin/env python3
"""
ANALYSIS: WHY DID WE SKIP?
categorizes every event into:
- TRADED
- SKIP (AI Low Conf)
- SKIP (No Price Confirmation)
"""

import sys
import os
import json
import sqlite3
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.db import Database

class SkipAnalyzer:
    def __init__(self):
        self.db = Database()
        self.AI_THRESH = 0.75
        self.CONF_THRESH = 0.0010 # 0.10% (Winning setting)

    def run(self):
        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM gold_events WHERE sol_price_data IS NOT NULL AND timestamp NOT LIKE '2025%'")
        events = [dict(row) for row in c.fetchall()]
        conn.close()
        
        print(f"{'EVENT':<40} | {'STATUS':<10} | {'AI CONF':<7} | {'5s MOVE':<8} | {'REASON'}")
        print("-" * 90)
        
        counts = {"TRADED": 0, "SKIP_AI": 0, "SKIP_CONF": 0}
        
        for e in events:
            # 1. AI Check
            ai_conf = e['ai_confidence'] or 0
            if ai_conf < self.AI_THRESH:
                status = "SKIP_AI"
                reason = f"Conf {ai_conf:.2f} < 0.75"
                counts["SKIP_AI"] += 1
                move_str = "N/A"
            else:
                # 2. Conf Check
                try:
                    data = json.loads(e['sol_price_data'])
                    ticks = [c['close'] for c in data] # Simple close
                    start_idx = 300 # Approx match to opt script
                    if start_idx >= len(ticks):
                        status = "ERR_DATA"
                        reason = "No Data"
                    else:
                        start_price = ticks[start_idx]
                        max_move = 0
                        direction = 1 if (e['ai_score'] or 0) > 0 else -1
                        
                        for i in range(5):
                            idx = start_idx + i
                            if idx >= len(ticks): break
                            p = ticks[idx]
                            m = (p - start_price)/start_price if direction == 1 else (start_price - p)/start_price
                            max_move = max(max_move, m)
                            
                        move_str = f"{max_move:.2%}"
                        
                        if max_move >= self.CONF_THRESH:
                            status = "TRADED"
                            reason = "Confirmed"
                            counts["TRADED"] += 1
                        else:
                            status = "SKIP_CONF"
                            reason = f"Move {max_move:.2%} < 0.10%"
                            counts["SKIP_CONF"] += 1
                except:
                    status = "ERR"
                    reason = "Json Error"
                    move_str = "?"
            
            # Print row
            color = ""
            if status == "TRADED": color = "⭐"
            print(f"{e['title'][:38]:<40} | {status:<10} | {ai_conf:>7.2f} | {move_str:>8} | {reason} {color}")
            
        print("-" * 90)
        print(f"SUMMARY: AI Skips: {counts['SKIP_AI']} | Market Veto: {counts['SKIP_CONF']} | Traded: {counts['TRADED']}")

if __name__ == "__main__":
    app = SkipAnalyzer()
    app.run()
