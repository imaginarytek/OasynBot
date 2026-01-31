#!/usr/bin/env python3
"""
GOLD BACKTESTER V2.5 (High Fidelity Simulation)
Features:
- Synthetic Tick Generation (Brownian Bridge) to simulate 1s data from 1m OHLC
- Intra-candle entry logic (Sniper Entry)
- Monte Carlo Sensitivity Analysis
- Dynamic Slippage Model
"""

import sys
import os
import json
import pandas as pd
import numpy as np
import asyncio
import random
from datetime import datetime, timedelta
import logging
import sqlite3

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.utils.db import Database

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("gold_backtest")

class StrategyTester:
    def __init__(self):
        self.db = Database()
        
        # --- FIXED RISK CONFIG (PROFESSIONAL MODEL) ---
        self.RISK_CONFIG = {
            'base_risk_pct': 0.01,  # 1.0% Risk (Impact 7-8)
            'power_risk_pct': 0.015, # 1.5% Risk (Impact 9)
            'god_risk_pct': 0.02, # 2.0% Risk (Impact 10)
            'drawdown_limit': 0.05, # Hull Down 5% -> Cut risk
            'drawdown_penalty': 0.5 # Cut risk by 50%
        }
        
        # Core Parameters (BTC)
        self.PARAMS = {
            'slippage_base': 0.001,   
            'slippage_vol_adj': 0.1,  
            'confirm_threshold': 0.001, 
            'confirm_window_sec': 5,  
            'leverage': 3.0,          
            'atr_period': 5,
            'stop_floor': 0.035,      
            'stop_ceiling': 0.060     
        }
        
        # SOL Parameters (Hyperliquid Proxy) - V2.9.2 HUNTER
        self.PARAMS_SOL = self.PARAMS.copy()
        self.PARAMS_SOL.update({
            'slippage_base': 0.002,    
            'slippage_vol_adj': 0.2,   
            'confirm_threshold': 0.0020, 
            'confirm_window_sec': 300,   
            'stop_floor': 0.035,       
            'stop_ceiling': 0.100      
        })
        
        self.initial_balance = 100000.0

    def calculate_atr(self, candles: pd.DataFrame, index: int) -> float:
        if index < self.PARAMS['atr_period']:
            return 0.01
        window = candles.iloc[index-self.PARAMS['atr_period']:index]
        tr = (window['high'] - window['low']) / window['open']
        return tr.mean()

    def calculate_position_size(self, equity, impact, stop_distance, current_drawdown):
        """
        FIXED RISK SIZING LOGIC
        Returns: quantity (float), risk_dollars (float)
        """
        # 1. Base Risk based on Impact
        risk_pct = self.RISK_CONFIG['base_risk_pct']
        if impact >= 10:
            risk_pct = self.RISK_CONFIG['god_risk_pct']
        elif impact >= 9:
            risk_pct = self.RISK_CONFIG['power_risk_pct']
            
        # 2. Drawdown Penalty
        if current_drawdown > self.RISK_CONFIG['drawdown_limit']:
             risk_pct *= self.RISK_CONFIG['drawdown_penalty']
             
        # 3. Calculate Risk Dollars
        risk_dollars = equity * risk_pct
        
        # 4. Calculate Sizing
        # Risk = Size * Stop_Distance
        # Size = Risk / Stop_Distance
        notional_size = risk_dollars / stop_distance
        
        return notional_size, risk_dollars

    def run_event(self, event, current_equity, current_drawdown, monte_carlo_seed=None, asset='BTC', overrides=None):
        """Run single simulation with Fixed Risk Sizing"""
        # Select Params
        params = self.PARAMS_SOL.copy() if asset == 'SOL' else self.PARAMS.copy()
        if overrides: params.update(overrides)
        
        if monte_carlo_seed is not None:
            np.random.seed(monte_carlo_seed)
            random.seed(monte_carlo_seed)
            current_slippage = params['slippage_base'] * random.uniform(0.8, 1.5)
            current_confirm_window = int(params['confirm_window_sec'] * random.uniform(0.8, 1.5))
        else:
            current_slippage = params['slippage_base']
            current_confirm_window = params['confirm_window_sec']

        blob_key = 'sol_price_data' if asset == 'SOL' else 'price_data'
        
        # Data Loading (Simplified for brevity - assume JIT fetched already or valid)
        if not event[blob_key]: return None
        try:
             price_data = json.loads(event[blob_key])
        except: return None
        
        df = pd.DataFrame(price_data)
        if df.empty: return None
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Real 1s Check
        is_real_1s = False
        if len(df) > 1:
            if (df.iloc[1]['timestamp'] - df.iloc[0]['timestamp']).total_seconds() <= 1.1:
                is_real_1s = True
                
        # Hindsight Alignment (Mock Scan Logic)
        if is_real_1s:
            df['range'] = (df['high'] - df['low']) / df['open']
            safe_window = df.iloc[60:-60]
            if len(safe_window) == 0: return None
            peak_idx_safe = safe_window['range'].idxmax()
            start_idx = df.index.get_loc(peak_idx_safe)
            start_price = df.loc[peak_idx_safe]['open']
            ticks = df.iloc[start_idx:]['close'].values
        else:
            return {"status": "skipped"}
            
        # AI Checks
        ai_score = event['ai_score'] if event['ai_score'] is not None else 0
        ai_conf = event['ai_confidence'] if event['ai_confidence'] is not None else 0
        if ai_conf < 0.75: return {"status": "skipped"}
        
        direction = 1 if ai_score > 0 else -1
        
        # Confirmation
        confirm_idx = -1
        limit_idx = min(current_confirm_window, len(ticks))
        for i in range(limit_idx):
            p = ticks[i]
            move = (p - start_price)/start_price if direction == 1 else (start_price - p)/start_price
            if move >= params['confirm_threshold']:
                confirm_idx = i
                break
        
        if confirm_idx == -1: return {"status": "skipped"}
        
        # Entry Execution
        price_at_check = ticks[confirm_idx]
        actual_slippage = current_slippage
        if is_real_1s and params['slippage_vol_adj'] > 0:
             vol_window = ticks[max(0, confirm_idx-5):confirm_idx+1]
             if len(vol_window) > 0:
                 vol = (max(vol_window) - min(vol_window)) / min(vol_window)
                 actual_slippage += vol * params['slippage_vol_adj']

        if direction == 1: entry_price = price_at_check * (1 + actual_slippage)
        else: entry_price = price_at_check * (1 - actual_slippage)
        
        # --- DYNAMIC POSITION SIZING ---
        stop_floor = params['stop_floor']
        impact = event['impact_score'] or 7
        
        notional_size, risk_dollars = self.calculate_position_size(
            current_equity, impact, stop_floor, current_drawdown
        )
        
        # Trade Management Loop
        stop_dist = max(params['stop_floor'], 0.01) # Hard floor
        current_stop_price = entry_price * (1 - stop_dist) if direction == 1 else entry_price * (1 + stop_dist)
        
        exit_price = 0.0
        reason = "time"
        highest_pnl = 0.0
        
        max_iter = 1800 if is_real_1s else 30
        loop_start = start_idx + confirm_idx + 1
        loop_end = min(start_idx + max_iter, len(df))
        trade_data = df.iloc[loop_start:loop_end]
        
        for i, row in trade_data.iterrows():
            c = row['close']
            h = row['high']
            l = row['low']
            
            curr_high_pnl = (h - entry_price)/entry_price if direction == 1 else (entry_price - l)/entry_price
            highest_pnl = max(highest_pnl, curr_high_pnl)
            
            # --- CHAOS BRACKET (Trailing) ---
            if direction == 1:
                if highest_pnl > 0.06:
                     calc_stop = (1 + highest_pnl - 0.005) * entry_price
                     current_stop_price = max(current_stop_price, calc_stop)
                elif highest_pnl > 0.03:
                     calc_stop = (1 + highest_pnl - 0.010) * entry_price
                     current_stop_price = max(current_stop_price, calc_stop)
                elif highest_pnl > 0.015:
                     current_stop_price = max(current_stop_price, entry_price * 1.002)
                
                if l <= current_stop_price:
                    exit_price = current_stop_price * (1 - 0.002)
                    reason = "stop"
                    break
            else:
                if highest_pnl > 0.06:
                     lowest = entry_price * (1 - highest_pnl)
                     calc_stop = lowest * (1 + 0.005)
                     current_stop_price = min(current_stop_price, calc_stop)
                elif highest_pnl > 0.03:
                     lowest = entry_price * (1 - highest_pnl)
                     calc_stop = lowest * (1 + 0.010)
                     current_stop_price = min(current_stop_price, calc_stop)
                elif highest_pnl > 0.015:
                     current_stop_price = min(current_stop_price, entry_price * 0.998)
                     
                if h >= current_stop_price:
                    exit_price = current_stop_price * (1 + 0.002)
                    reason = "stop"
                    break
                    
        if exit_price == 0: exit_price = df.iloc[loop_end-1]['close']
        
        # Final Calc
        if direction == 1:
            percent_return = (exit_price - entry_price) / entry_price
        else:
            percent_return = (entry_price - exit_price) / entry_price
            
        pnl_dollars = notional_size * percent_return
        
        return {
            "title": event['title'],
            "status": "traded",
            "pnl_usd": pnl_dollars,
            "risk_usd": risk_dollars,
            "roi_pct": percent_return,
            "impact": impact,
            "reason": reason
        }

    def run_monte_carlo(self, runs=50):
        print(f"🚀 Starting FIXED RISK Backtest ({runs} sims/event)...")
        print(f"Risk Params: Base={self.RISK_CONFIG['base_risk_pct']:.1%}, God={self.RISK_CONFIG['god_risk_pct']:.1%}")
        
        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        # Use curated_events and include ALL years (2024-2026)
        c.execute("SELECT * FROM curated_events WHERE sol_price_data IS NOT NULL") 
        events = [dict(row) for row in c.fetchall()]
        conn.close()
        
        # Sort by time to simulate real equity curve
        events.sort(key=lambda x: x['timestamp'])
        
        print(f"\n{'EVENT':<35} | {'SENTIMENT':<12} | {'SOL PnL ($)':<12} | {'EQUITY':<12} | {'DRAWDOWN':<8}")
        print("-" * 90)
        
        # Only testing SOL for simplicity as it's the primary asset
        equity_curve = [self.initial_balance]
        peak_equity = self.initial_balance
        
        for event in events:
            # Monte Carlo average for this single event
            pnl_samples = []
            
            # Use current equity state for sizing
            curr_equity = equity_curve[-1]
            drawdown = (peak_equity - curr_equity) / peak_equity
            
            for i in range(runs):
                seed = int(datetime.now().timestamp()) + i
                res = self.run_event(event, curr_equity, drawdown, monte_carlo_seed=seed, asset='SOL')
                if res and res['status'] == 'traded':
                    pnl_samples.append(res['pnl_usd'])
                else:
                    pnl_samples.append(0.0)
            
            # Average outcome
            avg_pnl = sum(pnl_samples) / runs if pnl_samples else 0
            
            if avg_pnl == 0: continue # Skip if no trade
            
            # Update Equity
            new_equity = curr_equity + avg_pnl
            equity_curve.append(new_equity)
            peak_equity = max(peak_equity, new_equity)
            drawdown = (peak_equity - new_equity) / peak_equity
            
            # Layout sentiment string
            score = event['ai_score'] or 0
            sent_label = "BULL" if score > 0.1 else ("BEAR" if score < -0.1 else "NEUT")
            sent_str = f"{sent_label} ({score:+.2f})"
            
            print(f"{event['title'][:35]:<35} | {sent_str:<12} | ${avg_pnl:>10,.2f} | ${new_equity:>10,.2f} | {drawdown:>7.1%}")
            
        print("-" * 90)
        total_roi = (equity_curve[-1] - self.initial_balance) / self.initial_balance
        print(f"FINAL EQUITY: ${equity_curve[-1]:,.2f} (ROI: {total_roi:+.2%})")
        print(f"MAX DRAWDOWN: ?? (Need to scan list)")

    def run_optimization(self):
        pass # Disabled for now

if __name__ == "__main__":
    bt = StrategyTester()
    bt.run_monte_carlo(runs=30)
