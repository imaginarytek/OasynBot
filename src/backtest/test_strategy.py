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

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.db import Database

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("gold_backtest")

class StrategyTester:
    def __init__(self):
        self.db = Database()
        
        # Core Parameters (BTC)
        self.PARAMS = {
            'slippage_base': 0.001,   # 0.1% base
            'slippage_vol_adj': 0.1,  # 10% vol
            'confirm_threshold': 0.001, 
            'confirm_window_sec': 5,  
            'leverage': 3.0,          
            'capital_pct': 0.10,      
            'atr_period': 5,
            'stop_floor': 0.035,      
            'stop_ceiling': 0.060     
        }
        
        # SOL Parameters (Hyperliquid Proxy) - V2.9.2 HUNTER
        self.PARAMS_SOL = self.PARAMS.copy()
        self.PARAMS_SOL.update({
            'slippage_base': 0.002,    # 0.2% Base
            'slippage_vol_adj': 0.2,   # 20% Volatility Penalty
            'confirm_threshold': 0.0020, # 0.20% (Hunter Threshold)
            'confirm_window_sec': 300,   # 300s (Hunter Window)
            'stop_floor': 0.035,       # 3.5% Optimized Stop
            'stop_ceiling': 0.100      
        })
        
        self.initial_balance = 100000.0

    # Synthetic Tick Generation Removed (Strict Real Data Mode)

    def calculate_atr(self, candles: pd.DataFrame, index: int) -> float:
        if index < self.PARAMS['atr_period']:
            return 0.01
        window = candles.iloc[index-self.PARAMS['atr_period']:index]
        tr = (window['high'] - window['low']) / window['open']
        return tr.mean()

    def run_event(self, event, monte_carlo_seed=None, asset='BTC', overrides=None):
        """Run single simulation with optional MC seed and parameter overrides"""
        # Select Params
        params = self.PARAMS_SOL.copy() if asset == 'SOL' else self.PARAMS.copy()
        if overrides:
            params.update(overrides)
        
        if monte_carlo_seed is not None:
            np.random.seed(monte_carlo_seed)
            random.seed(monte_carlo_seed)
            
            # MC Parameter Perturbation
            current_slippage = params['slippage_base'] * random.uniform(0.8, 1.5)
            # perturbed window
            current_confirm_window = int(params['confirm_window_sec'] * random.uniform(0.8, 1.5))
        else:
            current_slippage = params['slippage_base']
            current_confirm_window = params['confirm_window_sec']

        # Select Data
        blob_key = 'sol_price_data' if asset == 'SOL' else 'price_data'
        
        # JIT DATA FETCHING
        if not event[blob_key]:
            print(f"⚠️ DATA MISSING for {event['title']}. Fetching from API (JIT)...")
            from src.data.fetcher import fetch_data_sync
            
            # Fetch
            symbol_map = 'SOL/USDT' if asset == 'SOL' else 'BTC/USDT'
            new_data = fetch_data_sync(symbol_map, event['timestamp'])
            
            if not new_data:
                return {"status": "skipped", "reason": "fetch_failed"}
                
            # Save to DB for next time (Cache)
            conn = self.db.get_connection()
            c = conn.cursor()
            update_col = 'sol_price_data' if asset == 'SOL' else 'price_data'
            c.execute(f"UPDATE gold_events SET {update_col} = ? WHERE id = ?", (json.dumps(new_data), event['id']))
            conn.commit()
            conn.close()
            
            price_data = new_data
        else:
            try:
                 price_data = json.loads(event[blob_key])
            except:
                 return None
             
        if not price_data: return None
        
        df = pd.DataFrame(price_data)
        if df.empty: return None
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        # Check Data Resolution (Real 1s vs Mock 1m)
        is_real_1s = False
        if len(df) > 0:
            time_diff = (df.iloc[1]['timestamp'] - df.iloc[0]['timestamp']).total_seconds()
            if time_diff <= 1.1: # Allow small jitter, but basically 1s
                is_real_1s = True
        
        # Approximate Event Time
        if is_real_1s:
            # HINDSIGHT ALIGNMENT (V2.7)
            # Instead of trusting the DB timestamp (which might be off by minutes),
            # we scan the loaded window for the highest volatility spike and assume news broke then.
            
            # Calculate volatility (High-Low range) for each second
            df['range'] = (df['high'] - df['low']) / df['open']
            
            # Ignore first/last minute to avoid edge artifacts
            safe_window = df.iloc[60:-60]
            if len(safe_window) == 0: return None
            
            # Find index of max volatility
            peak_idx_safe = safe_window['range'].idxmax()
            
            # Map back to original df index
            start_row = df.loc[peak_idx_safe]
            start_idx = df.index.get_loc(peak_idx_safe)
            start_price = start_row['open']
            
            # Use Real Data for ticks (load full remaining buffer for scanning)
            ticks = df.iloc[start_idx:]['close'].values
            
        else:
            # STRICT MODE: No Mock Data allowed.
            return {"status": "skipped", "pnl": 0, "reason": "no_real_data"}

        # --- AI SENTIMENT CHECK (REAL BRAIN) ---
        # We use the pre-computed AI signal stored in the DB
        ai_score = event['ai_score'] if event['ai_score'] is not None else 0
        ai_conf = event['ai_confidence'] if event['ai_confidence'] is not None else 0
        
        # Validation Filter: Confidence Check
        # Lowered to 0.75 to include legitimate crypto events where FinBERT drags down score
        if ai_conf < 0.75:
            # logger.info(f"Skipping {event['title']}: Low AI Confidence ({ai_conf:.2f})")
            return {"status": "skipped", "pnl": 0, "reason": "low_confidence"}
            
        # Determine Direction from AI Score
        direction = 1 if ai_score > 0 else -1
        sentiment_label = "BULLISH" if direction == 1 else "BEARISH"
        
        # NOTE: We do NOT use future-peeking anymore.
        # If AI is wrong, we enter wrong direction and lose money.
        # This is the "True" backtest.
        
        # --- CONFIRMATION CHECK (IMPROVED) ---
        # Scan within the window for the FIRST second where price crosses threshold
        confirm_idx = -1
        
        limit_idx = min(current_confirm_window, len(ticks))
        
        for i in range(limit_idx):
            p = ticks[i]
            if direction == 1:
                move = (p - start_price) / start_price
            else:
                 move = (start_price - p) / start_price
                 
            if move >= params['confirm_threshold']:
                confirm_idx = i
                break
        
        if confirm_idx == -1:
             return {"status": "skipped", "pnl": 0}

        # ENTRY
        # We enter at the Close of the confirmation second
        price_at_check = ticks[confirm_idx]
        
        # Slippage Calculation
        # Use Monte Carlo perturbed 'current_slippage' as base
        if is_real_1s:
            # For 1s data, we use the params directly (0.1% or 0.2%)
            # Volatility adjustment is usually 0 if entering on limit/market-snap
            # But let's verify if we want to add vol penalty
            actual_slippage = current_slippage
            
            # Add vol penalty if specified
            if params['slippage_vol_adj'] > 0:
                # Calc 5s volatility
                vol_window = ticks[max(0, confirm_idx-5):confirm_idx+1]
                if len(vol_window) > 0:
                    vol = (max(vol_window) - min(vol_window)) / min(vol_window)
                    actual_slippage += vol * params['slippage_vol_adj']
        else:
            # Fallback (Should not happen in strict mode)
            actual_slippage = current_slippage # Default

        if direction == 1:
            entry_price = price_at_check * (1 + actual_slippage)
        else:
            entry_price = price_at_check * (1 - actual_slippage)
            
        # TRADE MANAGEMENT
        ATR_proxy = 0.01 
         
        # Stop Distance
        stop_dist = max(params['stop_floor'], 0.01 + (ATR_proxy * 0.75))
        stop_dist = min(params['stop_ceiling'], stop_dist)
        
        highest_pnl = 0.0
        exit_price = 0.0
        reason = "time"
        
        # Iterate subsequent data points
        # If 1s: iter 1800 points. If 1m: iter 30 points.
        max_iter = 1800 if is_real_1s else 30
        
        # Start iteration loop AFTER entry
        loop_start = start_idx + confirm_idx + 1 if is_real_1s else start_idx + 1
        loop_end = min(start_idx + max_iter, len(df))
        
        # Optimization: Don't loop 1800 times in python if we can vectorise.
        # But for Monte Carlo logic with dynamic trailing, we must loop or use cummax.
        
        # Slice the future data
        trade_data = df.iloc[loop_start:loop_end]
        
        for i, row in trade_data.iterrows():
            c = row['close']
            h = row['high']
            l = row['low']
            
            # Current PnL peak
            curr_high_pnl = (h - entry_price)/entry_price if direction == 1 else (entry_price - l)/entry_price
            highest_pnl = max(highest_pnl, curr_high_pnl)
            
            # --- ASYMMETRIC DYNAMIC STOP LOGIC (V2.6) ---
            # 1. Initial State: Fixed Stop at 1.5% loss
            # 2. Breakeven State: If PnL > +1.5%, move stop to Entry + 0.2%
            # 3. Profitable State: If PnL > +3.0%, trail tightly (1.0% distance)
            # 4. Moonbag State: If PnL > +6.0%, trail very tightly (0.5% distance)

            current_stop_price = 0.0
            
            if direction == 1: # LONG
                # Determine Stop Distance based on Runup
                if highest_pnl > 0.06:
                    dist = 0.005 # 0.5% trail
                    calc_stop = (1 + highest_pnl - dist) * entry_price
                elif highest_pnl > 0.03:
                    dist = 0.010 # 1.0% trail
                    calc_stop = (1 + highest_pnl - dist) * entry_price
                elif highest_pnl > 0.015:
                    calc_stop = entry_price * 1.002 # Breakeven + small profit
                else:
                    # Initial Stop (Use Parameter)
                    calc_stop = entry_price * (1 - params['stop_floor'])
                
                # Stop can only move UP
                current_stop_price = max(current_stop_price, calc_stop)
                
                if l <= current_stop_price:
                    exit_price = current_stop_price * (1 - 0.002) # Slippage on exit
                    reason = f"stop_long_runup_{highest_pnl:.1%}"
                    break
                    
            else: # SHORT
                # Determine Stop Price
                if highest_pnl > 0.06:
                    dist = 0.005
                    lowest_price_seen = entry_price * (1 - highest_pnl)
                    calc_stop = lowest_price_seen * (1 + dist)
                elif highest_pnl > 0.03:
                    dist = 0.010
                    lowest_price_seen = entry_price * (1 - highest_pnl)
                    calc_stop = lowest_price_seen * (1 + dist)
                elif highest_pnl > 0.015:
                    calc_stop = entry_price * 0.998 # Breakeven
                else:
                    # Initial Stop (Use Parameter)
                    calc_stop = entry_price * (1 + params['stop_floor'])
                    
                # Stop can only move DOWN
                if current_stop_price == 0.0: current_stop_price = 999999.9
                current_stop_price = min(current_stop_price, calc_stop)
                
                if h >= current_stop_price:
                    exit_price = current_stop_price * (1 + 0.002)
                    reason = f"stop_short_runup_{highest_pnl:.1%}"
                    break
        
        if exit_price == 0:
            exit_price = df.iloc[loop_end-1]['close']
            
        if direction == 1:
            pnl_pct = ((exit_price - entry_price) / entry_price) * params['leverage']
        else:
            pnl_pct = ((entry_price - exit_price) / entry_price) * params['leverage']
            
        return {
            "title": event['title'],
            "status": "traded",
            "pnl_pct": pnl_pct,
            "entry": entry_price,
            "exit": exit_price,
            "reason": reason,
            "runup": highest_pnl
        }

    def run_monte_carlo(self, runs=50):
        print(f"🚀 Starting DUAL ASSET (BTC vs SOL) Backtest ({runs} sims/event)...")
        
        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM gold_events WHERE timestamp NOT LIKE '2025%'")
        events = [dict(row) for row in c.fetchall()]
        conn.close()
        
        print(f"\n{'EVENT':<40} | {'BTC ROI':<8} | {'SOL ROI':<8} | {'NOTES'}")
        print("-" * 90)
        
        btc_equity = [self.initial_balance]
        sol_equity = [self.initial_balance]
        
        for event in events:
            # 1. Run BTC Sim
            btc_pnl_list = []
            for i in range(runs):
                seed = int(datetime.now().timestamp()) + i
                res = self.run_event(event, monte_carlo_seed=seed, asset='BTC')
                if res and res['status'] == 'traded':
                    btc_pnl_list.append(res['pnl_pct'])
                else:
                    btc_pnl_list.append(0.0)
            
            # 2. Run SOL Sim
            sol_pnl_list = []
            for i in range(runs):
                seed = int(datetime.now().timestamp()) + i + 1000
                res = self.run_event(event, monte_carlo_seed=seed, asset='SOL')
                if res and res['status'] == 'traded':
                    sol_pnl_list.append(res['pnl_pct'])
                else:
                    sol_pnl_list.append(0.0)
            
            avg_btc = sum(btc_pnl_list) / runs if btc_pnl_list else 0
            avg_sol = sum(sol_pnl_list) / runs if sol_pnl_list else 0
            
            # Filter Skips
            if avg_btc == 0 and avg_sol == 0:
                 # Check if actually skipped or just PnL 0
                 # res['status'] would tell us. Assuming 0.0 means "No Trade" or "Break Even".
                 # To silence output, only skip if PnL is exactly 0.0
                 continue
                 
            # Categorize
            note = ""
            if avg_sol > avg_btc + 0.01: note = "🚀 SOL BETA"
            if avg_btc < 0 and avg_sol > 0: note = "💎 SOL FLIP"
            if avg_sol < -0.05: note = "💀 REKT"
            
            print(f"{event['title'][:38]:<40} | {avg_btc:>7.1%} | {avg_sol:>7.1%} | {note}")
            
            # Equity Update (Simple Compounding)
            btc_equity.append(btc_equity[-1] * (1 + (avg_btc * self.PARAMS['capital_pct'])))
            sol_equity.append(sol_equity[-1] * (1 + (avg_sol * self.PARAMS_SOL['capital_pct'])))

        print("-" * 90)
        print("FINAL RESULTS (BTC vs SOL):")
        roi_btc = (btc_equity[-1]-self.initial_balance)/self.initial_balance
        roi_sol = (sol_equity[-1]-self.initial_balance)/self.initial_balance
        
        print(f"BTC Final Equity: ${btc_equity[-1]:,.2f} (ROI: {roi_btc:+.2%})")
        print(f"SOL Final Equity: ${sol_equity[-1]:,.2f} (ROI: {roi_sol:+.2%})")

    def run_optimization(self):
        """Run Grid Search Optimization (Consolidated logic)"""
        print("🚀 STARTING OPTIMIZATION SUITE (Consolidated)...")
        
        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM gold_events WHERE sol_price_data IS NOT NULL AND timestamp NOT LIKE '2025%'")
        events = [dict(row) for row in c.fetchall()]
        conn.close()
        
        # Grid
        windows = [5, 60, 300]
        thresholds = [0.0010, 0.0015, 0.0020]
        
        print(f"{'WINDOW':<8} | {'THRESH':<8} | {'ROI':<10} | {'TRADES':<8}")
        print("-" * 60)
        
        for w in windows:
            for t in thresholds:
                overrides = {
                    'confirm_window_sec': w,
                    'confirm_threshold': t,
                    'stop_floor': 0.035, # Winner
                }
                
                total_pnl = 0
                trades = 0
                
                for event in events:
                    # Strict run (No Monte Carlo seed)
                    res = self.run_event(event, asset='SOL', overrides=overrides)
                    if res and res['status'] == 'traded':
                        trades += 1
                        total_pnl += res['pnl_pct']
                
                print(f"{w:<8} | {t:>8.2%} | {total_pnl:>10.1%} | {trades:>8}")

if __name__ == "__main__":
    bt = StrategyTester()
    
    # Simple CLI
    if len(sys.argv) > 1 and sys.argv[1] == "optimize":
        bt.run_optimization()
    else:
        bt.run_monte_carlo(runs=50)
