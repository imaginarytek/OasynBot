#!/usr/bin/env python3
"""
PROFESSIONAL EVENT MINING PIPELINE
Step 1: Find abnormal volatility in 1-hour SOL data
Step 2: Search for news announcements around those spikes
Step 3: Drill down to 1-second data to verify exact timestamp
Step 4: Build optimized event dataset
"""
import ccxt
import sqlite3
from datetime import datetime, timedelta
import statistics
import time

def step1_find_hourly_spikes():
    """
    Find abnormal volatility spikes in 1-hour SOL/USDT data
    Using statistical outlier detection (Z-score method)
    """
    print("=" * 100)
    print("STEP 1: HOURLY VOLATILITY SPIKE DETECTION")
    print("=" * 100)
    
    exchange = ccxt.binance({
        'enableRateLimit': True,
        'options': {'defaultType': 'future'}
    })
    
    # Fetch 2 years of hourly data
    print("\n📊 Fetching 1-hour SOL/USDT candles (2024-2026)...")
    
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
            current = candles[-1][0] + 3600000
            print(f"   Loaded {len(all_candles)} candles...", end='\r')
            time.sleep(0.1)  # Rate limit
        except Exception as e:
            print(f"\n   Error: {e}")
            break
    
    print(f"\n   ✅ Loaded {len(all_candles)} hourly candles")
    
    # Calculate returns and volatility
    print("\n🔍 Calculating volatility metrics...")
    
    volatility_data = []
    
    for i, candle in enumerate(all_candles):
        timestamp, open_p, high, low, close, volume = candle
        
        # Hourly return (absolute)
        hourly_return = abs((close - open_p) / open_p)
        
        # Intra-hour range (high-low volatility)
        intra_range = (high - low) / open_p
        
        dt = datetime.fromtimestamp(timestamp / 1000)
        
        volatility_data.append({
            'timestamp': timestamp,
            'datetime': dt,
            'open': open_p,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume,
            'hourly_return': hourly_return,
            'intra_range': intra_range,
            'move_pct': (close - open_p) / open_p * 100
        })
    
    # Calculate baseline statistics (rolling 30-day window)
    print("   Calculating baseline volatility (30-day rolling window)...")
    
    window_size = 24 * 30  # 30 days of hourly data
    
    for i in range(len(volatility_data)):
        if i < window_size:
            # Use all available data for early periods
            window = volatility_data[:i+1]
        else:
            # Use 30-day lookback
            window = volatility_data[i-window_size:i]
        
        if len(window) > 1:
            returns = [d['hourly_return'] for d in window]
            mean_vol = statistics.mean(returns)
            std_vol = statistics.stdev(returns)
            
            # Z-score: how many std deviations above normal?
            if std_vol > 0:
                z_score = (volatility_data[i]['hourly_return'] - mean_vol) / std_vol
            else:
                z_score = 0
            
            volatility_data[i]['z_score'] = z_score
            volatility_data[i]['baseline_vol'] = mean_vol
        else:
            volatility_data[i]['z_score'] = 0
            volatility_data[i]['baseline_vol'] = 0
    
    # Find significant spikes (Z-score > 3.0 = 99.7th percentile)
    significant_spikes = [d for d in volatility_data if d.get('z_score', 0) > 3.0]
    
    print(f"\n🎯 Found {len(significant_spikes)} significant volatility spikes (Z-score > 3.0)")
    
    # Sort by Z-score
    significant_spikes.sort(key=lambda x: x['z_score'], reverse=True)
    
    print(f"\n🏆 TOP 50 HOURLY VOLATILITY SPIKES:")
    print(f"   {'RANK':<5} | {'DATETIME':<20} | {'Z-SCORE':<9} | {'MOVE%':<9} | {'RANGE%':<9} | {'PRICE':<10}")
    print("   " + "-" * 90)
    
    for i, spike in enumerate(significant_spikes[:50], 1):
        direction = "↑" if spike['move_pct'] > 0 else "↓"
        print(f"   {i:<5} | {spike['datetime'].strftime('%Y-%m-%d %H:%M'):<20} | {spike['z_score']:>7.2f}σ | {direction}{abs(spike['move_pct']):>6.2f}% | {spike['intra_range']*100:>7.2f}% | ${spike['close']:>8.2f}")
    
    # Save to database for next step
    print(f"\n💾 Saving spike data to database...")
    
    conn = sqlite3.connect('data/hedgemony.db')
    c = conn.cursor()
    
    # Create table for hourly spikes
    c.execute("""
        CREATE TABLE IF NOT EXISTS hourly_volatility_spikes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER,
            datetime TEXT,
            z_score REAL,
            move_pct REAL,
            intra_range REAL,
            open_price REAL,
            close_price REAL,
            high_price REAL,
            low_price REAL,
            volume REAL,
            news_event TEXT,
            verified BOOLEAN DEFAULT 0
        )
    """)
    
    # Clear existing data
    c.execute("DELETE FROM hourly_volatility_spikes")
    
    # Insert spikes
    for spike in significant_spikes:
        c.execute("""
            INSERT INTO hourly_volatility_spikes 
            (timestamp, datetime, z_score, move_pct, intra_range, open_price, close_price, high_price, low_price, volume)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            spike['timestamp'],
            spike['datetime'].isoformat(),
            spike['z_score'],
            spike['move_pct'],
            spike['intra_range'],
            spike['open'],
            spike['close'],
            spike['high'],
            spike['low'],
            spike['volume']
        ))
    
    conn.commit()
    conn.close()
    
    print(f"   ✅ Saved {len(significant_spikes)} spikes to database")
    
    # Export for manual news search
    print(f"\n📋 Exporting spike list for news correlation...")
    
    with open('data/hourly_spikes_for_news_search.txt', 'w') as f:
        f.write("HOURLY VOLATILITY SPIKES - NEWS CORRELATION TASK\n")
        f.write("=" * 100 + "\n\n")
        f.write("Instructions:\n")
        f.write("1. For each spike, search Twitter/news for tier-1 announcements\n")
        f.write("2. Search window: ±30 minutes from spike time\n")
        f.write("3. Tier-1 sources: @federalreserve, @BLS_gov, @SECGov, @binance, etc.\n")
        f.write("4. Record EXACT tweet timestamp if found\n\n")
        f.write("-" * 100 + "\n\n")
        
        for i, spike in enumerate(significant_spikes[:50], 1):
            f.write(f"Spike #{i}\n")
            f.write(f"Date/Time: {spike['datetime'].strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
            f.write(f"Z-Score: {spike['z_score']:.2f}σ\n")
            f.write(f"Move: {spike['move_pct']:+.2f}%\n")
            f.write(f"Price: ${spike['open']:.2f} → ${spike['close']:.2f}\n")
            f.write(f"Search Twitter: https://twitter.com/search?q=(from:federalreserve OR from:BLS_gov OR from:SECGov) until:{spike['datetime'].strftime('%Y-%m-%d_%H:%M:%S_UTC')} since:{(spike['datetime'] - timedelta(hours=1)).strftime('%Y-%m-%d_%H:%M:%S_UTC')}\n")
            f.write(f"News Event: _______________________________________________\n")
            f.write(f"Exact Time: _______________________________________________\n")
            f.write("-" * 100 + "\n\n")
    
    print(f"   ✅ Saved to: data/hourly_spikes_for_news_search.txt")
    
    print("\n" + "=" * 100)
    print("✅ STEP 1 COMPLETE")
    print(f"   Next: Manually correlate spikes with news events")
    print(f"   Then: Run step 2 to verify with 1-second data")
    print("=" * 100)
    
    return significant_spikes

def step2_correlate_with_existing_events():
    """
    Check which of our curated events align with the detected spikes
    """
    print("\n" + "=" * 100)
    print("STEP 2: CORRELATING SPIKES WITH EXISTING CURATED EVENTS")
    print("=" * 100)
    
    conn = sqlite3.connect('data/hedgemony.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get spikes
    c.execute("SELECT * FROM hourly_volatility_spikes ORDER BY z_score DESC")
    spikes = c.fetchall()
    
    # Get curated events
    c.execute("SELECT title, timestamp FROM curated_events")
    events = c.fetchall()
    
    print(f"\n🔗 Checking {len(events)} curated events against {len(spikes)} spikes...")
    
    matched = []
    unmatched_spikes = []
    
    for spike in spikes:
        spike_dt = datetime.fromisoformat(spike['datetime'])
        if spike_dt.tzinfo is not None:
            spike_dt = spike_dt.replace(tzinfo=None)
        
        # Search for events within ±1 hour
        found = False
        for event in events:
            event_dt = datetime.fromisoformat(event['timestamp'])
            if event_dt.tzinfo is not None:
                event_dt = event_dt.replace(tzinfo=None)
            time_diff = abs((spike_dt - event_dt).total_seconds())
            
            if time_diff <= 3600:  # Within 1 hour
                matched.append({
                    'spike': spike,
                    'event': event['title'],
                    'time_diff': time_diff,
                    'z_score': spike['z_score']
                })
                found = True
                break
        
        if not found:
            unmatched_spikes.append(spike)
    
    print(f"\n✅ MATCHED: {len(matched)} spikes correlate with curated events")
    print(f"❌ UNMATCHED: {len(unmatched_spikes)} spikes have NO event match")
    
    if matched:
        print(f"\n📊 TOP MATCHED EVENTS:")
        print(f"   {'EVENT':<50} | {'Z-SCORE':<9} | {'TIME DIFF':<10}")
        print("   " + "-" * 75)
        
        matched.sort(key=lambda x: x['z_score'], reverse=True)
        for m in matched[:20]:
            print(f"   {m['event'][:48]:<50} | {m['z_score']:>7.2f}σ | {m['time_diff']:>8.0f}s")
    
    if unmatched_spikes:
        print(f"\n⚠️  MISSING EVENTS - Major spikes with NO curated event:")
        print(f"   {'DATETIME':<20} | {'Z-SCORE':<9} | {'MOVE%':<9}")
        print("   " + "-" * 50)
        
        for spike in unmatched_spikes[:15]:
            dt = datetime.fromisoformat(spike['datetime'])
            print(f"   {dt.strftime('%Y-%m-%d %H:%M'):<20} | {spike['z_score']:>7.2f}σ | {spike['move_pct']:>+7.2f}%")
    
    conn.close()
    
    print("\n" + "=" * 100)
    
    return matched, unmatched_spikes

if __name__ == "__main__":
    print("🚀 PROFESSIONAL EVENT MINING PIPELINE")
    print("   Based on HFT and academic event study best practices\n")
    
    # Step 1: Find hourly spikes
    spikes = step1_find_hourly_spikes()
    
    # Step 2: Correlate with existing events
    matched, unmatched = step2_correlate_with_existing_events()
    
    print(f"\n📈 SUMMARY:")
    print(f"   Total Hourly Spikes Detected: {len(spikes)}")
    print(f"   Matched to Curated Events: {len(matched)}")
    print(f"   Missing Events: {len(unmatched)}")
    
    print(f"\n💡 NEXT STEPS:")
    print(f"   1. Review data/hourly_spikes_for_news_search.txt")
    print(f"   2. For unmatched spikes, search for tier-1 news announcements")
    print(f"   3. Add missing events to curated list")
    print(f"   4. For matched events, verify exact timestamp with 1s data")
