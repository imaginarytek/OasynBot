#!/usr/bin/env python3
"""
GOLD STANDARD: SENTIMENT AUDIT
Why are we skipping everything? Let's look at the raw AI scores.
"""

import sys
import os
import sqlite3
import pandas as pd

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.db import Database

class SentimentAuditor:
    def __init__(self):
        self.db = Database()

    def run(self):
        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT title, ai_score, ai_label, ai_confidence, price_data FROM gold_events")
        events = [dict(row) for row in c.fetchall()]
        
        print(f"{'EVENT':<40} | {'SCORE':<6} | {'CONF':<5} | {'LABEL':<8} | {'REASON'}")
        print("-" * 90)
        
        low_conf_count = 0
        total_events = 0
        
        for e in events:
            # Check price data existence for context
            has_data = len(e['price_data']) > 10 if e['price_data'] else False
            
            score = e['ai_score'] if e['ai_score'] is not None else 0
            conf = e['ai_confidence'] if e['ai_confidence'] is not None else 0
            label = e['ai_label'] if e['ai_label'] else "none"
            
            total_events += 1
            reason = "OK"
            if conf < 0.85:
                reason = "LOW CONF (<0.85)"
                low_conf_count += 1
            if score == 0:
                reason = "NEUTRAL (0.0)"
            
            print(f"{e['title'][:38]:<40} | {score:+.2f}  | {conf:.2f}  | {label:<8} | {reason}")
            
        print("-" * 90)
        print(f"TOTAL EVENTS: {total_events}")
        print(f"LOW CONFIDENCE REJECTS: {low_conf_count} ({low_conf_count/total_events*100:.1f}%)")

if __name__ == "__main__":
    auditor = SentimentAuditor()
    auditor.run()
