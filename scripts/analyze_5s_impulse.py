#!/usr/bin/env python3
"""
GOLD STANDARD: 5-SECOND IMPULSE ANALYZER
Quantifies the "Speed of the Move" for events with Real 1s Data.
Answers: How much of the 1-minute move happens in the first 5 seconds?
"""

import sys
import os
import json
import sqlite3
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.db import Database

class ImpulseAnalyzer:
    def __init__(self):
        self.db = Database()

    def run(self):
        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT * FROM gold_events")
        events = [dict(row) for row in c.fetchall()]
        conn.close()
        
        print(f"{'EVENT':<35} | {'5s MOVE':<8} | {'MAX 30m':<10} | {'END 30m':<10} | {'TYPE'}")
        print("-" * 90)
        
        total_impulse_ratio = []
        
        for event in events:
            if not event['price_data']: continue
            price_data = json.loads(event['price_data'])
            if not price_data: continue
            
            df = pd.DataFrame(price_data)
            
            # Check for Real 1s Data
            is_real = False
            if len(df) > 0:
                time_diff = (pd.to_datetime(df.iloc[1]['timestamp']) - pd.to_datetime(df.iloc[0]['timestamp'])).total_seconds()
                if time_diff <= 1.1:
                    is_real = True
            
            if not is_real: continue
            
            # Hindsight Alignment (Peak Volatility)
            df['range'] = (df['high'] - df['low']) / df['open']
            safe_window = df.iloc[60:-60]
            if len(safe_window) == 0: continue
            
            peak_idx = safe_window['range'].idxmax()
            start_row = df.loc[peak_idx]
            start_price = start_row['open']
            
            # Get Price at T+5s and T+60s, and Max Excursion in 30m
            # Note: We assume T+0 is the Open of the impulse candle for calculation base
            
            # Slice forward
            idx = df.index.get_loc(peak_idx)
            max_idx = min(idx + 1800, len(df)) # 30 mins * 60s
            
            p5 = df.iloc[idx + 5]['close'] if idx + 5 < len(df) else df.iloc[-1]['close']
            p60 = df.iloc[idx + 60]['close'] if idx + 60 < len(df) else df.iloc[-1]['close']
            
            # 30m Window
            window_30m = df.iloc[idx:max_idx]
            p_close_30m = window_30m.iloc[-1]['close']
            
            # Max Excursion (High or Low depending on direction)
            # Find max deviation from start
            high_dev = (window_30m['high'].max() - start_price) / start_price
            low_dev = (window_30m['low'].min() - start_price) / start_price
            
            # Use the larger magnitude
            max_move_30m = max(abs(high_dev), abs(low_dev))
            final_move_30m = (p_close_30m - start_price) / start_price
            
            # Calculate Absolute Moves
            move_5s = abs(p5 - start_price) / start_price
            move_60s = abs(p60 - start_price) / start_price
            
            # Ratio
            ratio = move_5s / move_60s if move_60s > 0.0001 else 0
            if ratio > 5: ratio = 5 # Cap crazy ratios (wicks)
            
            total_impulse_ratio.append(ratio)
            
            type_label = "⚡ SNIPER" if ratio > 0.5 else "🌊 DRIFT"
            
            print(f"{event['title'][:35]:<35} | {move_5s*100:.2f}%   | {max_move_30m*100:.2f}%      | {abs(final_move_30m)*100:.2f}%      | {type_label}")
            
        print("-" * 90)
        if total_impulse_ratio:
            avg_ratio = np.mean(total_impulse_ratio)
            print(f"AVERAGE IMPULSE SPEED: {avg_ratio*100:.1f}% of the 1-minute move happens in FIRST 5 SECONDS.")
            if avg_ratio > 0.4:
                print("CONCLUSION: Market is FAST. 15s Confirmation Window is too slow.")
            else:
                print("CONCLUSION: Market DRIFTS. 15s Confirmation Window is safe.")

if __name__ == "__main__":
    analyzer = ImpulseAnalyzer()
    analyzer.run()
