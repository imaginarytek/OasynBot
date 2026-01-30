#!/usr/bin/env python3
"""
Measure lag from news timestamp to first significant price impulse
For all 80 curated events with 1s data
"""
import sqlite3
import json
import pandas as pd
from datetime import datetime, timezone, timedelta
import numpy as np

def measure_lag_all():
    print("📊 MEASURING NEWS-TO-PRICE LAG FOR ALL EVENTS\n")
    print("="*80)
    
    conn = sqlite3.connect("data/hedgemony.db")
    c = conn.cursor()
    
    # Get all events with price data
    c.execute("""
        SELECT rowid, title, timestamp, sentiment, sol_price_data
        FROM curated_events
        WHERE sol_price_data IS NOT NULL
        ORDER BY timestamp
    """)
    
    events = c.fetchall()
    print(f"Analyzing {len(events)} events...\n")
    
    results = []
    
    for idx, (rowid, title, ts_str, sentiment, raw_data) in enumerate(events, 1):
        try:
            # Parse news time
            news_time = datetime.fromisoformat(ts_str)
            
            # Load candles
            candles = json.loads(raw_data)
            if len(candles) < 100:
                continue
            
            df = pd.DataFrame(candles)
            df['ts_obj'] = pd.to_datetime(df['timestamp'])
            df['price_change'] = df['close'].pct_change().abs()
            df['volume'] = pd.to_numeric(df['volume'])
            
            # Calculate rolling volume average
            df['vol_avg'] = df['volume'].rolling(60, min_periods=1).mean()
            df['vol_spike'] = df['volume'] / df['vol_avg']
            
            # Find first significant impulse after news time
            # Criteria: Volume spike >3x OR price change >0.2% in 1 second
            mask = (df['ts_obj'] >= news_time) & (df['ts_obj'] <= news_time + timedelta(minutes=10))
            window = df[mask]
            
            if window.empty:
                continue
            
            # Find anomalies
            anomalies = window[(window['vol_spike'] > 3) | (window['price_change'] > 0.002)]
            
            if not anomalies.empty:
                first_impulse = anomalies.iloc[0]
                impulse_time = first_impulse['ts_obj']
                lag = (impulse_time - news_time).total_seconds()
                
                # Calculate price impact
                price_before = window.iloc[0]['close']
                price_after_1min = window[window['ts_obj'] <= news_time + timedelta(minutes=1)].iloc[-1]['close'] if len(window) > 60 else price_before
                impact_1min = ((price_after_1min - price_before) / price_before) * 100
                
                result = {
                    'rowid': rowid,
                    'title': title[:50],
                    'news_time': ts_str,
                    'impulse_time': impulse_time.isoformat(),
                    'lag_seconds': lag,
                    'sentiment': sentiment,
                    'impact_1min': impact_1min,
                    'vol_spike': first_impulse['vol_spike'],
                    'price_change': first_impulse['price_change'] * 100
                }
                
                results.append(result)
                
                # Print progress
                if lag < 60:
                    status = "✅"
                elif lag < 300:
                    status = "⚠️"
                else:
                    status = "❌"
                
                print(f"[{idx}/{len(events)}] {status} {title[:40]:40} | Lag: {lag:6.1f}s | Impact: {impact_1min:+6.2f}%")
            else:
                print(f"[{idx}/{len(events)}] ⚪ {title[:40]:40} | No clear impulse detected")
                
        except Exception as e:
            print(f"[{idx}/{len(events)}] ❌ Error: {title[:40]} - {e}")
            continue
    
    conn.close()
    
    # Statistics
    if results:
        df_results = pd.DataFrame(results)
        
        print(f"\n{'='*80}")
        print("SUMMARY STATISTICS")
        print(f"{'='*80}")
        print(f"Total events analyzed: {len(events)}")
        print(f"Events with clear impulse: {len(results)}")
        print(f"Detection rate: {len(results)/len(events)*100:.1f}%")
        
        print(f"\nLAG DISTRIBUTION:")
        print(f"  Mean: {df_results['lag_seconds'].mean():.1f}s")
        print(f"  Median: {df_results['lag_seconds'].median():.1f}s")
        print(f"  Std Dev: {df_results['lag_seconds'].std():.1f}s")
        print(f"  Min: {df_results['lag_seconds'].min():.1f}s")
        print(f"  Max: {df_results['lag_seconds'].max():.1f}s")
        
        print(f"\nLAG CATEGORIES:")
        fast = len(df_results[df_results['lag_seconds'] < 10])
        good = len(df_results[(df_results['lag_seconds'] >= 10) & (df_results['lag_seconds'] < 60)])
        slow = len(df_results[(df_results['lag_seconds'] >= 60) & (df_results['lag_seconds'] < 300)])
        very_slow = len(df_results[df_results['lag_seconds'] >= 300])
        
        print(f"  ⚡ Ultra-fast (<10s): {fast} ({fast/len(results)*100:.1f}%)")
        print(f"  ✅ Fast (10-60s): {good} ({good/len(results)*100:.1f}%)")
        print(f"  ⚠️  Slow (60-300s): {slow} ({slow/len(results)*100:.1f}%)")
        print(f"  ❌ Very slow (>300s): {very_slow} ({very_slow/len(results)*100:.1f}%)")
        
        print(f"\nPRICE IMPACT (1 minute):")
        print(f"  Mean: {df_results['impact_1min'].mean():+.2f}%")
        print(f"  Median: {df_results['impact_1min'].median():+.2f}%")
        print(f"  Positive moves: {len(df_results[df_results['impact_1min'] > 0])}")
        print(f"  Negative moves: {len(df_results[df_results['impact_1min'] < 0])}")
        
        # Save results
        df_results.to_csv('data/lag_analysis_results.csv', index=False)
        print(f"\n💾 Saved detailed results to: data/lag_analysis_results.csv")
        
        # Update database with lag values
        conn = sqlite3.connect("data/hedgemony.db")
        c = conn.cursor()
        for result in results:
            c.execute("""
                UPDATE curated_events 
                SET lag_seconds = ?, verified = 1
                WHERE rowid = ?
            """, (result['lag_seconds'], result['rowid']))
        conn.commit()
        conn.close()
        print(f"✅ Updated database with lag measurements")
        
    print(f"\n{'='*80}")

if __name__ == "__main__":
    measure_lag_all()
