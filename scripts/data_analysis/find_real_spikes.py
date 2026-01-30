#!/usr/bin/env python3
"""
SPIKE DETECTION & EVENT CORRELATION
Find the biggest SOL price movements and correlate with news events
"""
import sqlite3
import json
from datetime import datetime, timedelta
import ccxt

def find_major_spikes():
    """
    Strategy:
    1. Scan 1-hour candles for major moves (>3% in 1 hour)
    2. For each spike, drill down to 1-second data to find exact moment
    3. Search for news events within ±5 minutes of spike
    4. Verify uniqueness (no duplicate events for same price action)
    """
    
    print("=" * 100)
    print("SOL PRICE SPIKE DETECTION & NEWS CORRELATION ANALYSIS")
    print("=" * 100)
    
    # Initialize exchange
    exchange = ccxt.binance({
        'enableRateLimit': True,
        'options': {'defaultType': 'future'}
    })
    
    # Fetch 1-hour candles for last 2 years
    print("\n📊 Step 1: Fetching 1-hour SOL/USDT candles (2024-2026)...")
    
    since = exchange.parse8601('2024-01-01T00:00:00Z')
    now = exchange.milliseconds()
    
    all_candles = []
    current = since
    
    while current < now:
        try:
            candles = exchange.fetch_ohlcv('SOL/USDT', '1h', since=current, limit=1000)
            if not candles:
                break
            all_candles.extend(candles)
            current = candles[-1][0] + 3600000  # Next hour
            print(f"   Fetched {len(all_candles)} candles...", end='\r')
        except Exception as e:
            print(f"\n   Error: {e}")
            break
    
    print(f"\n   ✅ Loaded {len(all_candles)} hourly candles")
    
    # Find major spikes (>3% move in 1 hour)
    print("\n🔍 Step 2: Detecting major price spikes (>3% hourly move)...")
    
    spikes = []
    for i, candle in enumerate(all_candles):
        timestamp, open_p, high, low, close, volume = candle
        
        # Calculate hourly move
        move_pct = abs((close - open_p) / open_p * 100)
        
        if move_pct >= 3.0:
            dt = datetime.fromtimestamp(timestamp / 1000)
            spikes.append({
                'timestamp': timestamp,
                'datetime': dt,
                'open': open_p,
                'close': close,
                'high': high,
                'low': low,
                'move_pct': move_pct,
                'direction': 'UP' if close > open_p else 'DOWN'
            })
    
    print(f"   ✅ Found {len(spikes)} major spikes (>3% hourly move)")
    
    # Sort by magnitude
    spikes.sort(key=lambda x: x['move_pct'], reverse=True)
    
    print(f"\n📈 Top 20 Biggest Hourly Moves:")
    print(f"   {'DATE':<20} | {'MOVE':<8} | {'DIR':<4} | {'OPEN':<8} | {'CLOSE':<8}")
    print("   " + "-" * 70)
    
    for i, spike in enumerate(spikes[:20]):
        print(f"   {spike['datetime'].strftime('%Y-%m-%d %H:%M'):<20} | {spike['move_pct']:>6.2f}% | {spike['direction']:<4} | ${spike['open']:>7.2f} | ${spike['close']:>7.2f}")
    
    # Now drill down to 1-second data for each spike
    print(f"\n🔬 Step 3: Drilling down to 1-second data for top spikes...")
    
    detailed_spikes = []
    
    for spike in spikes[:30]:  # Analyze top 30
        spike_time = spike['timestamp']
        
        # Fetch 1-second data around this spike (±30 minutes)
        start_time = spike_time - (30 * 60 * 1000)
        end_time = spike_time + (30 * 60 * 1000)
        
        try:
            # Fetch in chunks (Binance limits)
            second_candles = []
            current = start_time
            
            while current < end_time:
                chunk = exchange.fetch_ohlcv('SOL/USDT', '1s', since=current, limit=1000)
                if not chunk:
                    break
                second_candles.extend(chunk)
                current = chunk[-1][0] + 1000
            
            if len(second_candles) < 100:
                continue
            
            # Find the exact second of maximum move
            max_move = 0
            max_idx = 0
            base_price = second_candles[0][1]  # Open of first candle
            
            for i, candle in enumerate(second_candles):
                move = abs((candle[4] - base_price) / base_price * 100)
                if move > max_move:
                    max_move = move
                    max_idx = i
            
            exact_time = datetime.fromtimestamp(second_candles[max_idx][0] / 1000)
            
            detailed_spikes.append({
                'hourly_move': spike['move_pct'],
                'exact_time': exact_time,
                'exact_timestamp': second_candles[max_idx][0],
                'max_30s_move': max_move,
                'direction': spike['direction'],
                'price_data': second_candles
            })
            
            print(f"   ✓ {exact_time.strftime('%Y-%m-%d %H:%M:%S')} - {spike['move_pct']:.2f}% hourly, {max_move:.2f}% max intraday")
            
        except Exception as e:
            print(f"   ✗ Failed to fetch 1s data for {spike['datetime']}: {e}")
            continue
    
    # Correlate with curated events
    print(f"\n🔗 Step 4: Correlating spikes with curated events...")
    
    conn = sqlite3.connect('data/hedgemony.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT title, timestamp FROM curated_events")
    events = c.fetchall()
    conn.close()
    
    correlated = []
    uncorrelated = []
    
    for spike in detailed_spikes:
        spike_dt = spike['exact_time']
        
        # Search for events within ±5 minutes
        matched = False
        for event in events:
            event_dt = datetime.fromisoformat(event['timestamp'])
            time_diff = abs((spike_dt - event_dt).total_seconds())
            
            if time_diff <= 300:  # 5 minutes
                correlated.append({
                    'spike': spike,
                    'event': event['title'],
                    'time_diff': time_diff
                })
                matched = True
                break
        
        if not matched:
            uncorrelated.append(spike)
    
    print(f"\n   ✅ Correlated: {len(correlated)} spikes matched to events")
    print(f"   ❌ Uncorrelated: {len(uncorrelated)} spikes with NO event match")
    
    # Show uncorrelated spikes (potential missing events)
    if uncorrelated:
        print(f"\n⚠️  MISSING EVENTS - Major price spikes with NO news correlation:")
        print(f"   {'DATETIME':<20} | {'HOURLY MOVE':<12} | {'MAX MOVE':<10} | {'DIR':<4}")
        print("   " + "-" * 60)
        
        for spike in uncorrelated[:10]:
            print(f"   {spike['exact_time'].strftime('%Y-%m-%d %H:%M:%S'):<20} | {spike['hourly_move']:>10.2f}% | {spike['max_30s_move']:>8.2f}% | {spike['direction']:<4}")
    
    # Show correlated spikes
    if correlated:
        print(f"\n✅ CORRELATED EVENTS - Spikes matched to news:")
        print(f"   {'DATETIME':<20} | {'EVENT':<50} | {'MOVE':<8} | {'LAG':<6}")
        print("   " + "-" * 95)
        
        for item in correlated[:15]:
            print(f"   {item['spike']['exact_time'].strftime('%Y-%m-%d %H:%M:%S'):<20} | {item['event'][:48]:<50} | {item['spike']['hourly_move']:>6.2f}% | {item['time_diff']:>4.0f}s")
    
    print("\n" + "=" * 100)
    
    return {
        'total_spikes': len(spikes),
        'detailed_spikes': detailed_spikes,
        'correlated': correlated,
        'uncorrelated': uncorrelated
    }

if __name__ == "__main__":
    results = find_major_spikes()
    
    print(f"\n📋 SUMMARY:")
    print(f"   Total Major Spikes (>3% hourly): {results['total_spikes']}")
    print(f"   Analyzed with 1s data: {len(results['detailed_spikes'])}")
    print(f"   Matched to events: {len(results['correlated'])}")
    print(f"   Missing events: {len(results['uncorrelated'])}")
    
    if results['uncorrelated']:
        print(f"\n💡 RECOMMENDATION:")
        print(f"   Investigate the {len(results['uncorrelated'])} uncorrelated spikes")
        print(f"   These may represent missing tier-1 events or false signals")
