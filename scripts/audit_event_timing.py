#!/usr/bin/env python3
"""
GOLD STANDARD: TIMING AUDIT
Correlates "News Timestamp" vs "Market Reaction Time" (SOL 1s).
Generates rank of biggest moves.
"""

import sys
import os
import json
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.db import Database

class TimingAuditor:
    def __init__(self):
        self.db = Database()

    def run(self):
        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM gold_events WHERE sol_price_data IS NOT NULL AND timestamp NOT LIKE '2025%'")
        events = [dict(row) for row in c.fetchall()]
        conn.close()
        
        results = []
        
        for e in events:
            # Parse Data
            try:
                data = json.loads(e['sol_price_data'])
                if not data: continue
                df = pd.DataFrame(data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp').reset_index(drop=True)
            except: continue
            
            # News Time
            try:
                news_time = pd.to_datetime(e['timestamp'].replace("Z", "+00:00"))
            except:
                continue
                
            # Find Market Reaction (Peak Volatility in first 10 mins)
            # We look 2 mins before news (leak) to 10 mins after
            start_search = news_time - timedelta(minutes=2)
            end_search = news_time + timedelta(minutes=10)
            
            mask = (df['timestamp'] >= start_search) & (df['timestamp'] <= end_search)
            window = df.loc[mask].copy()
            
            if len(window) < 10:
                results.append({
                    "title": e['title'],
                    "news_time": news_time,
                    "market_time": news_time,
                    "lag": 0,
                    "impulse_5s": 0.0,
                    "max_move": 0.0,
                    "note": "No Data Window"
                })
                continue
            
            # Metric: High-Low Range relative to Open (Volatility Candle)
            window['vol'] = (window['high'] - window['low']) / window['open']
            
            # Find Max Vol Second
            peak_idx = window['vol'].idxmax()
            peak_row = window.loc[peak_idx]
            market_time = peak_row['timestamp']
            
            # Lag
            lag_seconds = (market_time - news_time).total_seconds()
            
            # 5s Impulse (From Market Time)
            start_price = peak_row['open']
            # Get next 5 ticks
            future_mask = (df['timestamp'] >= market_time) & (df['timestamp'] <= market_time + timedelta(seconds=5))
            future_window = df.loc[future_mask]
            
            if len(future_window) > 0:
                end_price = future_window.iloc[-1]['close']
                impulse_5s = abs(end_price - start_price) / start_price
            else:
                impulse_5s = 0.0
                
            # Max 30m Move (Range)
            # Full window
            range_30m = (df['high'].max() - df['low'].min()) / df.iloc[0]['open']
            
            results.append({
                "title": e['title'],
                "news_time": news_time,
                "market_time": market_time,
                "lag": lag_seconds,
                "impulse_5s": impulse_5s,
                "max_move": range_30m,
                "note": ""
            })
            
        # Sort by Max Move
        results.sort(key=lambda x: x['max_move'], reverse=True)
        
        # Generate Markdown
        md = "# Gold Standard: Event Timing & Correlation Audit\n\n"
        md += "| Event | News Time (UTC) | Market Time (Peak Vol) | Lag (s) | 5s Impulse | 30m Max Move |\n"
        md += "|---|---|---|---|---|---|\n"
        
        for r in results:
            title = r['title'].replace("|", "-")
            md += f"| {title} | {r['news_time'].strftime('%H:%M:%S')} | {r['market_time'].strftime('%H:%M:%S')} | {r['lag']:+.0f}s | {r['impulse_5s']:.2%} | **{r['max_move']:.2%}** |\n"
            
        # Save to File
        with open("docs/event_correlation_audit.md", "w") as f:
            f.write(md)
            
        print("✅ Report generated: docs/event_correlation_audit.md")
        
        # Print Top 20 for Console
        print(f"\n{'EVENT':<40} | {'LAG':<6} | {'5s Impulse':<10} | {'30m RANGE'}")
        print("-" * 80)
        for r in results[:20]:
            print(f"{r['title'][:38]:<40} | {r['lag']:+4.0f}s | {r['impulse_5s']:>8.2%} | {r['max_move']:>8.2%}")

if __name__ == "__main__":
    auditor = TimingAuditor()
    auditor.run()
