#!/usr/bin/env python3
"""
REVERSE CORRELATION ANALYSIS
Check if our curated events actually captured the biggest SOL moves
"""
import sqlite3
import json
from datetime import datetime
import ccxt

def analyze_event_quality():
    print("=" * 100)
    print("EVENT QUALITY ANALYSIS - Are we capturing the REAL movers?")
    print("=" * 100)
    
    # Get hourly candles for comparison
    print("\n📊 Fetching hourly SOL candles for context...")
    exchange = ccxt.binance({'enableRateLimit': True})
    
    since = exchange.parse8601('2024-01-01T00:00:00Z')
    hourly_candles = []
    current = since
    
    for _ in range(24):  # Get ~24k hours (2 years)
        try:
            candles = exchange.fetch_ohlcv('SOL/USDT', '1h', since=current, limit=1000)
            if not candles:
                break
            hourly_candles.extend(candles)
            current = candles[-1][0] + 3600000
        except:
            break
    
    print(f"   ✅ Loaded {len(hourly_candles)} hourly candles")
    
    # Load our curated events
    conn = sqlite3.connect('data/hedgemony.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT title, timestamp, sol_price_data FROM curated_events WHERE sol_price_data IS NOT NULL")
    events = c.fetchall()
    conn.close()
    
    print(f"\n🔍 Analyzing {len(events)} curated events...")
    
    results = []
    
    for event in events:
        try:
            event_time = datetime.fromisoformat(event['timestamp'])
            price_data = json.loads(event['sol_price_data'])
            
            if len(price_data) < 30:
                continue
            
            # Calculate actual moves from our 1s data
            start_price = price_data[0]['close']
            
            # 5-second move
            move_5s = abs((price_data[4]['close'] - start_price) / start_price * 100) if len(price_data) > 4 else 0
            
            # 30-second move
            move_30s = abs((price_data[29]['close'] - start_price) / start_price * 100) if len(price_data) > 29 else 0
            
            # 5-minute move
            move_5m = abs((price_data[299]['close'] - start_price) / start_price * 100) if len(price_data) > 299 else 0
            
            # 30-minute move
            move_30m = abs((price_data[1799]['close'] - start_price) / start_price * 100) if len(price_data) > 1799 else 0
            
            # Find corresponding hourly candle
            event_ts = int(event_time.timestamp() * 1000)
            hourly_move = 0
            
            for candle in hourly_candles:
                if abs(candle[0] - event_ts) < 3600000:  # Within same hour
                    hourly_move = abs((candle[4] - candle[1]) / candle[1] * 100)
                    break
            
            results.append({
                'title': event['title'],
                'datetime': event_time,
                'move_5s': move_5s,
                'move_30s': move_30s,
                'move_5m': move_5m,
                'move_30m': move_30m,
                'hourly_move': hourly_move,
                'start_price': start_price
            })
            
        except Exception as e:
            print(f"   Error processing {event['title']}: {e}")
            continue
    
    # Sort by 30-second move (most important for initial reaction)
    results.sort(key=lambda x: x['move_30s'], reverse=True)
    
    print(f"\n🏆 TOP 30 EVENTS BY 30-SECOND PRICE IMPACT:")
    print(f"   {'RANK':<5} | {'EVENT':<45} | {'5s':<7} | {'30s':<7} | {'5m':<7} | {'30m':<7} | {'HOURLY':<7}")
    print("   " + "-" * 100)
    
    for i, r in enumerate(results[:30], 1):
        print(f"   {i:<5} | {r['title'][:43]:<45} | {r['move_5s']:>5.2f}% | {r['move_30s']:>5.2f}% | {r['move_5m']:>5.2f}% | {r['move_30m']:>5.2f}% | {r['hourly_move']:>5.2f}%")
    
    # Identify weak events (low 30s move)
    weak_events = [r for r in results if r['move_30s'] < 0.1]
    
    print(f"\n⚠️  WEAK EVENTS (< 0.1% move in 30 seconds):")
    print(f"   Found {len(weak_events)} events with minimal immediate price impact")
    
    if weak_events:
        print(f"\n   {'EVENT':<50} | {'30s MOVE':<10} | {'30m MOVE':<10}")
        print("   " + "-" * 75)
        for r in weak_events[:10]:
            print(f"   {r['title'][:48]:<50} | {r['move_30s']:>8.3f}% | {r['move_30m']:>8.2f}%")
    
    # Statistics
    print(f"\n📊 OVERALL STATISTICS:")
    
    moves_30s = [r['move_30s'] for r in results]
    moves_5m = [r['move_5m'] for r in results]
    moves_30m = [r['move_30m'] for r in results]
    
    import statistics
    
    print(f"   30-Second Moves:")
    print(f"      Mean: {statistics.mean(moves_30s):.3f}%")
    print(f"      Median: {statistics.median(moves_30s):.3f}%")
    print(f"      Max: {max(moves_30s):.3f}%")
    print(f"      Events >0.5%: {len([m for m in moves_30s if m > 0.5])}")
    print(f"      Events >1.0%: {len([m for m in moves_30s if m > 1.0])}")
    
    print(f"\n   5-Minute Moves:")
    print(f"      Mean: {statistics.mean(moves_5m):.3f}%")
    print(f"      Median: {statistics.median(moves_5m):.3f}%")
    print(f"      Max: {max(moves_5m):.3f}%")
    
    print(f"\n   30-Minute Moves:")
    print(f"      Mean: {statistics.mean(moves_30m):.3f}%")
    print(f"      Median: {statistics.median(moves_30m):.3f}%")
    print(f"      Max: {max(moves_30m):.3f}%")
    
    # Compare to hourly spike threshold
    big_hourly_moves = [r for r in results if r['hourly_move'] > 3.0]
    
    print(f"\n🎯 EVENTS DURING BIG HOURLY MOVES (>3%):")
    print(f"   {len(big_hourly_moves)} events occurred during major hourly spikes")
    
    if big_hourly_moves:
        print(f"\n   {'EVENT':<50} | {'30s':<7} | {'HOURLY':<7}")
        print("   " + "-" * 70)
        for r in sorted(big_hourly_moves, key=lambda x: x['hourly_move'], reverse=True)[:15]:
            print(f"   {r['title'][:48]:<50} | {r['move_30s']:>5.2f}% | {r['hourly_move']:>5.2f}%")
    
    print("\n" + "=" * 100)
    
    return results

if __name__ == "__main__":
    results = analyze_event_quality()
    
    # Final assessment
    strong_30s = len([r for r in results if r['move_30s'] > 0.5])
    total = len(results)
    
    print(f"\n💡 ASSESSMENT:")
    print(f"   {strong_30s}/{total} events ({strong_30s/total*100:.1f}%) have >0.5% move in 30 seconds")
    
    if strong_30s / total < 0.3:
        print(f"\n   ⚠️  WARNING: Most events show weak immediate price reaction")
        print(f"   This suggests:")
        print(f"      1. Event timing may not be precise to the second")
        print(f"      2. Some events may not be tier-1 market movers")
        print(f"      3. We may be missing the actual spike moments")
