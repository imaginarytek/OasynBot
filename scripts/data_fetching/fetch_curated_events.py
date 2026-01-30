
import sqlite3
import json
import asyncio
import ccxt.async_support as ccxt
from datetime import datetime, timezone, timedelta
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.db import Database

class CuratedEventsFetcher:
    def __init__(self):
        self.db = Database()
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'adjustForTimeDifference': True}
        })
        
    async def fetch_1s_data(self, symbol: str, event_time: datetime):
        """Fetch ~125 mins of 1s data using proven working method from fetch_1s_api_all.py"""
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
                    ohlcv = await self.exchange.fetch_ohlcv(symbol, '1s', since=current_since, limit=1000)
                    if not ohlcv:
                        break
                    
                    for c in ohlcv:
                        ts = c[0]
                        if ts > end_ts:
                            break
                        
                        all_candles.append({
                            "timestamp": datetime.fromtimestamp(ts/1000, timezone.utc).isoformat(),
                            "open": c[1],
                            "high": c[2],
                            "low": c[3],
                            "close": c[4],
                            "volume": c[5]
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
    
    async def process_all_events(self):
        """Process all curated events and store in new table"""
        print("🚀 FETCHING 1S DATA FOR ALL CURATED EVENTS\n")
        
        # Load curated events
        with open('data/curated_100_events.json', 'r') as f:
            events = json.load(f)
        
        conn = self.db.get_connection()
        c = conn.cursor()
        
        # Create new table for curated events
        c.execute("""
            CREATE TABLE IF NOT EXISTS curated_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                source TEXT,
                sentiment TEXT,
                description TEXT,
                sol_price_data TEXT,
                verified BOOLEAN DEFAULT 0,
                lag_seconds REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        success_count = 0
        failed_count = 0
        
        for idx, event in enumerate(events, 1):
            try:
                # Parse timestamp
                event_dt = datetime.fromisoformat(f"{event['date']} {event['time']}").replace(tzinfo=timezone.utc)
                
                print(f"\n[{idx}/{len(events)}] {event['title']}")
                print(f"   Time: {event_dt.isoformat()}")
                
                # Fetch price data
                print(f"   Fetching 1s data...")
                price_data = await self.fetch_1s_data('SOL/USDT', event_dt)
                
                if len(price_data) > 100:
                    # Insert into database
                    c.execute("""
                        INSERT INTO curated_events 
                        (title, timestamp, source, sentiment, sol_price_data)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        event['title'],
                        event_dt.isoformat(),
                        event['source'],
                        event['sentiment'],
                        json.dumps(price_data)
                    ))
                    conn.commit()
                    success_count += 1
                    print(f"   ✅ Stored {len(price_data)} candles")
                else:
                    failed_count += 1
                    print(f"   ❌ Insufficient data ({len(price_data)} candles)")
                    
            except Exception as e:
                failed_count += 1
                print(f"   ❌ Error: {e}")
                continue
        
        await self.exchange.close()
        conn.close()
        
        print(f"\n{'='*80}")
        print(f"COMPLETE:")
        print(f"  ✅ Success: {success_count}")
        print(f"  ❌ Failed: {failed_count}")
        print(f"{'='*80}")

if __name__ == "__main__":
    fetcher = CuratedEventsFetcher()
    asyncio.run(fetcher.process_all_events())
