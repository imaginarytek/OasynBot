#!/usr/bin/env python3
"""
PHASE 3: Build Verified Event Dataset
Fetch 1-SECOND price data for all verified events and create optimized dataset
"""
import sqlite3
import ccxt.async_support as ccxt
from datetime import datetime, timedelta, timezone
import asyncio
import json

async def fetch_1s_data(exchange, symbol: str, event_time: datetime):
    """Fetch ~125 mins of 1s data using Binance Spot API"""
    start_time = event_time - timedelta(minutes=5)
    end_time = event_time + timedelta(minutes=120)
    
    all_candles = []
    current_since = int(start_time.timestamp() * 1000)
    end_ts = int(end_time.timestamp() * 1000)
    
    retries_per_request = 3
    
    while current_since < end_ts:
        for attempt in range(retries_per_request):
            try:
                # Fetch up to 1000 candles at 1s resolution
                ohlcv = await exchange.fetch_ohlcv(symbol, '1s', since=current_since, limit=1000)
                if not ohlcv:
                    break
                
                for c in ohlcv:
                    ts = c[0]
                    if ts > end_ts:
                        break
                    
                    all_candles.append({
                        'timestamp': datetime.fromtimestamp(ts/1000, timezone.utc).isoformat(),
                        'open': c[1],
                        'high': c[2],
                        'low': c[3],
                        'close': c[4],
                        'volume': c[5]
                    })
                
                # Advance cursor
                last_ts = ohlcv[-1][0]
                if last_ts == current_since:
                    break  # Stuck, exit
                current_since = last_ts + 1000  # +1s
                
                if len(ohlcv) < 1000:
                    break  # Partial batch = end of data
                
                await asyncio.sleep(0.1)  # Rate limit protection
                break  # Success, exit retry loop
                
            except ccxt.RateLimitExceeded:
                print(f"   Rate limit hit, waiting...")
                await asyncio.sleep(10)
            except ccxt.NetworkError as e:
                if attempt < retries_per_request - 1:
                    print(f"   Network error (attempt {attempt+1}/{retries_per_request}), retrying...")
                    await asyncio.sleep(5)
                else:
                    print(f"   Network error after {retries_per_request} attempts: {e}")
                    return all_candles
            except Exception as e:
                print(f"   Unexpected error: {e}")
                if attempt < retries_per_request - 1:
                    await asyncio.sleep(5)
                else:
                    return all_candles
    
    return all_candles

async def build_verified_dataset():
    """
    For each verified event, fetch 1-second SOL price data
    """
    print("=" * 100)
    print("PHASE 3: BUILDING VERIFIED EVENT DATASET (1-SECOND DATA)")
    print("=" * 100)
    
    conn = sqlite3.connect('data/hedgemony.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get verified events
    c.execute("""
        SELECT * FROM hourly_volatility_spikes 
        WHERE news_event IS NOT NULL AND verified = 1
        ORDER BY z_score DESC
    """)
    verified_events = c.fetchall()
    
    print(f"\n📊 Found {len(verified_events)} verified events")
    
    if len(verified_events) == 0:
        print("\n⚠️  No verified events yet!")
        print("   Complete Phase 1 (manual research) first")
        conn.close()
        return
    
    # Create new optimized events table
    c.execute("""
        CREATE TABLE IF NOT EXISTS optimized_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            timestamp TEXT,
            category TEXT,
            z_score REAL,
            hourly_move_pct REAL,
            sol_price_data TEXT,
            move_5s REAL,
            move_30s REAL,
            move_5m REAL,
            move_30m REAL,
            ai_score REAL,
            ai_confidence REAL,
            impact_score INTEGER,
            source_url TEXT,
            notes TEXT
        )
    """)
    
    # Clear existing data
    c.execute("DELETE FROM optimized_events")
    
    # Initialize exchange
    exchange = ccxt.binance({
        'enableRateLimit': True,
        'options': {'defaultType': 'spot'}  # SPOT has 1s data!
    })
    
    print(f"\n🔄 Fetching 1-SECOND price data for verified events...")
    print(f"   Using Binance Spot API (supports 1s resolution)\n")
    
    successful = 0
    failed = 0
    
    for i, event in enumerate(verified_events, 1):
        event_dt = datetime.fromisoformat(event['datetime'])
        if event_dt.tzinfo is None:
            event_dt = event_dt.replace(tzinfo=timezone.utc)
        
        print(f"[{i}/{len(verified_events)}] {event['news_event']}")
        print(f"   Time: {event_dt.strftime('%Y-%m-%d %H:%M UTC')}")
        
        try:
            # Fetch 1-second data
            price_data = await fetch_1s_data(exchange, 'SOL/USDT', event_dt)
            
            if not price_data or len(price_data) < 30:
                print(f"   ❌ Insufficient data")
                failed += 1
                continue
            
            # Calculate moves with TRUE 1-second resolution
            start_price = price_data[0]['close']
            
            # 5-second move (index 4 = 5th second)
            move_5s = abs((price_data[min(4, len(price_data)-1)]['close'] - start_price) / start_price * 100) if len(price_data) > 4 else 0
            
            # 30-second move (index 29 = 30th second)
            move_30s = abs((price_data[min(29, len(price_data)-1)]['close'] - start_price) / start_price * 100) if len(price_data) > 29 else 0
            
            # 5-minute move (index 299 = 300th second = 5 minutes)
            move_5m = abs((price_data[min(299, len(price_data)-1)]['close'] - start_price) / start_price * 100) if len(price_data) > 299 else 0
            
            # 30-minute move (index 1799 = 1800th second = 30 minutes)
            move_30m = abs((price_data[min(1799, len(price_data)-1)]['close'] - start_price) / start_price * 100) if len(price_data) > 1799 else 0
            
            # Insert into optimized_events
            c.execute("""
                INSERT INTO optimized_events 
                (title, timestamp, category, z_score, hourly_move_pct, sol_price_data, 
                 move_5s, move_30s, move_5m, move_30m)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event['news_event'],
                event['datetime'],
                'Unknown',
                event['z_score'],
                event['move_pct'],
                json.dumps(price_data),
                move_5s,
                move_30s,
                move_5m,
                move_30m
            ))
            
            print(f"   ✅ 5s: {move_5s:.2f}% | 30s: {move_30s:.2f}% | 5m: {move_5m:.2f}% | 30m: {move_30m:.2f}%")
            successful += 1
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            failed += 1
            continue
    
    await exchange.close()
    conn.commit()
    
    # Generate report
    print(f"\n{'='*100}")
    print("📊 DATASET BUILD COMPLETE")
    print(f"{'='*100}")
    print(f"   Successful: {successful}")
    print(f"   Failed: {failed}")
    
    if successful > 0:
        # Calculate statistics
        c.execute("SELECT AVG(move_5s), AVG(move_30s), AVG(move_5m), AVG(move_30m) FROM optimized_events")
        result = c.fetchone()
        avg_5s, avg_30s, avg_5m, avg_30m = result if result else (0, 0, 0, 0)
        
        c.execute("SELECT COUNT(*) FROM optimized_events WHERE move_30s > 0.5")
        strong_30s = c.fetchone()[0]
        
        print(f"\n📈 QUALITY METRICS (1-SECOND DATA):")
        print(f"   Average 5s move: {avg_5s:.3f}%")
        print(f"   Average 30s move: {avg_30s:.3f}%")
        print(f"   Average 5m move: {avg_5m:.3f}%")
        print(f"   Average 30m move: {avg_30m:.3f}%")
        print(f"   Events with >0.5% 30s move: {strong_30s}/{successful} ({strong_30s/successful*100:.1f}%)")
    
    print(f"\n💡 NEXT STEPS:")
    print(f"   1. Review optimized_events table")
    print(f"   2. Run sentiment scoring")
    print(f"   3. Run backtest with optimized dataset")
    
    conn.close()

if __name__ == "__main__":
    asyncio.run(build_verified_dataset())

