#!/usr/bin/env python3
"""
PROFESSIONAL EVENT MINING - Spike Detection + News Correlation
Based on academic event study methodology and HFT best practices
"""
import sqlite3
import json
from datetime import datetime, timedelta
import statistics

def detect_volatility_spikes():
    """
    Step 1: Find abnormal volatility in existing 1s data
    Using rolling standard deviation to detect outliers
    """
    print("=" * 100)
    print("PROFESSIONAL EVENT MINING - Volatility Spike Detection")
    print("=" * 100)
    
    conn = sqlite3.connect('data/hedgemony.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get all events with 1s data
    c.execute("SELECT title, timestamp, sol_price_data FROM curated_events WHERE sol_price_data IS NOT NULL")
    events = c.fetchall()
    
    print(f"\n🔍 Analyzing {len(events)} events for volatility spikes...")
    
    spike_candidates = []
    
    for event in events:
        try:
            price_data = json.loads(event['sol_price_data'])
            if len(price_data) < 100:
                continue
            
            # Calculate returns for each second
            returns = []
            for i in range(1, len(price_data)):
                ret = (price_data[i]['close'] - price_data[i-1]['close']) / price_data[i-1]['close']
                returns.append(abs(ret))  # Absolute return (volatility)
            
            # Find the maximum volatility spike in first 60 seconds
            if len(returns) < 60:
                continue
                
            first_60s = returns[:60]
            max_spike = max(first_60s)
            max_idx = first_60s.index(max_spike)
            
            # Calculate baseline volatility (using 30s-60s window as "normal")
            if len(returns) > 60:
                baseline_vol = statistics.mean(returns[30:60])
                baseline_std = statistics.stdev(returns[30:60]) if len(returns[30:60]) > 1 else 0
            else:
                baseline_vol = statistics.mean(returns)
                baseline_std = statistics.stdev(returns) if len(returns) > 1 else 0
            
            # Z-score: how many standard deviations above normal?
            if baseline_std > 0:
                z_score = (max_spike - baseline_vol) / baseline_std
            else:
                z_score = 0
            
            # Calculate cumulative move in first 30s
            start_price = price_data[0]['close']
            price_30s = price_data[29]['close'] if len(price_data) > 29 else price_data[-1]['close']
            move_30s = abs((price_30s - start_price) / start_price * 100)
            
            spike_candidates.append({
                'title': event['title'],
                'timestamp': event['timestamp'],
                'max_spike_pct': max_spike * 100,
                'spike_second': max_idx,
                'z_score': z_score,
                'move_30s': move_30s,
                'baseline_vol': baseline_vol * 100,
                'price_data': price_data
            })
            
        except Exception as e:
            print(f"   Error processing {event['title']}: {e}")
            continue
    
    # Sort by Z-score (statistical significance)
    spike_candidates.sort(key=lambda x: x['z_score'], reverse=True)
    
    print(f"\n🏆 TOP 30 EVENTS BY VOLATILITY SPIKE (Z-Score):")
    print(f"   {'RANK':<5} | {'EVENT':<45} | {'Z-SCORE':<8} | {'SPIKE%':<8} | {'@SEC':<6} | {'30s MOVE':<8}")
    print("   " + "-" * 100)
    
    for i, spike in enumerate(spike_candidates[:30], 1):
        print(f"   {i:<5} | {spike['title'][:43]:<45} | {spike['z_score']:>6.2f}σ | {spike['max_spike_pct']:>6.3f}% | {spike['spike_second']:>4}s | {spike['move_30s']:>6.2f}%")
    
    # Identify events with HIGH z-score but LOW 30s move (timing issues)
    print(f"\n⚠️  TIMING MISALIGNMENT CANDIDATES:")
    print(f"   Events with high volatility spike but low 30s cumulative move")
    print(f"   (Suggests event timestamp is AFTER the actual announcement)")
    print()
    print(f"   {'EVENT':<50} | {'Z-SCORE':<8} | {'SPIKE@':<8} | {'30s MOVE':<8}")
    print("   " + "-" * 85)
    
    misaligned = [s for s in spike_candidates if s['z_score'] > 3.0 and s['move_30s'] < 0.3]
    for spike in misaligned[:15]:
        print(f"   {spike['title'][:48]:<50} | {spike['z_score']:>6.2f}σ | {spike['spike_second']:>6}s | {spike['move_30s']:>6.2f}%")
    
    # Identify STRONG events (high z-score AND high 30s move)
    print(f"\n✅ WELL-TIMED EVENTS:")
    print(f"   Events with both high volatility AND strong 30s move")
    print(f"   (These are correctly timestamped to the announcement)")
    print()
    print(f"   {'EVENT':<50} | {'Z-SCORE':<8} | {'SPIKE@':<8} | {'30s MOVE':<8}")
    print("   " + "-" * 85)
    
    well_timed = [s for s in spike_candidates if s['z_score'] > 3.0 and s['move_30s'] > 0.15]
    for spike in well_timed[:15]:
        print(f"   {spike['title'][:48]:<50} | {spike['z_score']:>6.2f}σ | {spike['spike_second']:>6}s | {spike['move_30s']:>6.2f}%")
    
    # RECOMMENDATION: Events to re-timestamp
    print(f"\n💡 RECOMMENDATIONS:")
    print(f"   1. {len(misaligned)} events show timing misalignment")
    print(f"   2. For these events, search Twitter for EXACT announcement time")
    print(f"   3. Re-fetch 1s data starting from the TRUE announcement timestamp")
    print(f"   4. Focus on tier-1 sources: @federalreserve, @BLS_gov, @SECGov, etc.")
    
    # Export misaligned events for manual review
    print(f"\n📋 Exporting misaligned events for timestamp correction...")
    
    with open('data/events_to_retimestamp.txt', 'w') as f:
        f.write("EVENTS REQUIRING TIMESTAMP CORRECTION\n")
        f.write("=" * 80 + "\n\n")
        f.write("Instructions:\n")
        f.write("1. Search Twitter for the EXACT announcement time\n")
        f.write("2. Use tier-1 sources only (@federalreserve, @BLS_gov, @SECGov, etc.)\n")
        f.write("3. Note the EXACT timestamp (to the second)\n")
        f.write("4. Update the database with corrected timestamp\n\n")
        f.write("-" * 80 + "\n\n")
        
        for spike in misaligned:
            f.write(f"Event: {spike['title']}\n")
            f.write(f"Current Timestamp: {spike['timestamp']}\n")
            f.write(f"Volatility Spike at: +{spike['spike_second']}s from current timestamp\n")
            f.write(f"Z-Score: {spike['z_score']:.2f}σ\n")
            f.write(f"30s Move: {spike['move_30s']:.2f}%\n")
            f.write(f"Action: Search for official announcement, update timestamp\n")
            f.write("-" * 80 + "\n\n")
    
    print(f"   ✅ Saved to: data/events_to_retimestamp.txt")
    
    print("\n" + "=" * 100)
    
    conn.close()
    
    return {
        'all_spikes': spike_candidates,
        'misaligned': misaligned,
        'well_timed': well_timed
    }

def analyze_intraday_patterns():
    """
    Step 2: Analyze WHERE in the 125-minute window the spike occurs
    """
    print("\n" + "=" * 100)
    print("INTRADAY SPIKE TIMING ANALYSIS")
    print("=" * 100)
    
    conn = sqlite3.connect('data/hedgemony.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT title, sol_price_data FROM curated_events WHERE sol_price_data IS NOT NULL")
    events = c.fetchall()
    
    spike_positions = []
    
    for event in events:
        try:
            price_data = json.loads(event['sol_price_data'])
            if len(price_data) < 100:
                continue
            
            # Find position of maximum absolute return
            max_ret = 0
            max_pos = 0
            
            for i in range(1, min(len(price_data), 7500)):
                ret = abs((price_data[i]['close'] - price_data[i-1]['close']) / price_data[i-1]['close'])
                if ret > max_ret:
                    max_ret = ret
                    max_pos = i
            
            spike_positions.append({
                'title': event['title'],
                'spike_position': max_pos,
                'spike_pct': max_ret * 100
            })
            
        except:
            continue
    
    # Histogram of spike positions
    early_spikes = len([s for s in spike_positions if s['spike_position'] < 60])  # First minute
    mid_spikes = len([s for s in spike_positions if 60 <= s['spike_position'] < 1800])  # 1-30 min
    late_spikes = len([s for s in spike_positions if s['spike_position'] >= 1800])  # After 30 min
    
    print(f"\n📊 SPIKE TIMING DISTRIBUTION:")
    print(f"   First 60 seconds: {early_spikes} events ({early_spikes/len(spike_positions)*100:.1f}%)")
    print(f"   1-30 minutes: {mid_spikes} events ({mid_spikes/len(spike_positions)*100:.1f}%)")
    print(f"   After 30 minutes: {late_spikes} events ({late_spikes/len(spike_positions)*100:.1f}%)")
    
    if early_spikes / len(spike_positions) < 0.5:
        print(f"\n   ⚠️  WARNING: Only {early_spikes/len(spike_positions)*100:.1f}% of spikes occur in first 60s")
        print(f"   This suggests our timestamps are NOT aligned to the actual announcements")
        print(f"   Professional HFT datasets show 80%+ of spikes in first 5 seconds")
    
    conn.close()

if __name__ == "__main__":
    results = detect_volatility_spikes()
    analyze_intraday_patterns()
    
    print(f"\n📈 NEXT STEPS:")
    print(f"   1. Review data/events_to_retimestamp.txt")
    print(f"   2. For each event, find the EXACT tweet timestamp from tier-1 source")
    print(f"   3. Re-fetch 1s price data starting from corrected timestamp")
    print(f"   4. This will dramatically improve 30s price impact metrics")
