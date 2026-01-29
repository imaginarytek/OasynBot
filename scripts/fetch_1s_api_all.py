#!/usr/bin/env python3
"""
GOLD STANDARD: API FETCHER (High Speed)
Fetches official 1s data via Binance Spot API (Historical).
Targets exact window (-5m to +30m) for BTC and SOL.
No ZIP downloads required.
"""

import sys
import os
import json
import sqlite3
import asyncio
import ccxt.async_support as ccxt
from datetime import datetime, timedelta, timezone
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.db import Database

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("api_fetcher")

class ApiFetcher:
    def __init__(self):
        self.db = Database()
        self.exchange = ccxt.binance({
            'enableRateLimit': True,  # Critical for loop
            'rateLimit': 50 # Conservative
        })

    async def fetch_window(self, symbol: str, event_time: datetime):
        """Fetch ~35 mins of 1s data (approx 2100 candles)"""
        # API limit is usually 1000 per request. Need paginated fetch.
        
        start_time = event_time - timedelta(minutes=5)
        end_time = event_time + timedelta(minutes=30)
        
        all_candles = []
        current_since = int(start_time.timestamp() * 1000)
        end_ts = int(end_time.timestamp() * 1000)
        
        retries = 3
        
        while current_since < end_ts:
            try:
                # Fetch up to 1000
                ohlcv = await self.exchange.fetch_ohlcv(symbol, '1s', since=current_since, limit=1000)
                if not ohlcv: break
                
                for c in ohlcv:
                    ts = c[0]
                    if ts > end_ts: break
                    
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
                if last_ts == current_since: break # Stuck
                current_since = last_ts + 1000 # +1s
                
                if len(ohlcv) < 1000: break # Partial batch = end
                
            except Exception as e:
                logger.error(f"Error fetching {symbol}: {e}")
                retries -= 1
                if retries == 0: break
                await asyncio.sleep(1)
        
        return all_candles

    async def run(self):
        logger.info("🚀 Starting API Data Update (BTC + SOL)...")
        
        await self.exchange.load_markets()
        
        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT * FROM gold_events ORDER BY timestamp DESC")
        events = [dict(row) for row in c.fetchall()]
        
        count = 0
        for e in events:
            # Skip Mocks
            if '2025-' in e['timestamp']: continue
            
            title = e['title']
            ts_str = e['timestamp']
            
            # Parse time (handle isoformat Z or offset)
            try:
                event_dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            except:
                # Fallback for simple strings
                event_dt = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)

            logger.info(f"🔄 Processing: {title} ({ts_str})")
            
            # 1. Fetch BTC
            btc_data = await self.fetch_window("BTC/USDT", event_dt)
            if btc_data:
                logger.info(f"   BTC: Found {len(btc_data)} ticks")
            else:
                logger.warning("   BTC: No data found")
                
            # 2. Fetch SOL
            sol_data = await self.fetch_window("SOL/USDT", event_dt)
            if sol_data:
                logger.info(f"   SOL: Found {len(sol_data)} ticks")
            else:
                 logger.warning("   SOL: No data found")

            # 3. Update DB
            if btc_data:
                # We overwrite price_data with High Fidelity Spot Data
                c2 = conn.cursor()
                c2.execute("""
                    UPDATE gold_events 
                    SET price_data = ?, sol_price_data = ? 
                    WHERE id = ?
                """, (
                    json.dumps(btc_data), 
                    json.dumps(sol_data), 
                    e['id'] 
                ))
                conn.commit()
                count += 1
            
            # Rate limit
            # await asyncio.sleep(0.2) 
        
        conn.close()
        await self.exchange.close()
        logger.info(f"🏆 Updated {count} events with High-Fidelity API Data.")

if __name__ == "__main__":
    fetcher = ApiFetcher()
    asyncio.run(fetcher.run())
