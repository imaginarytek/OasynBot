
import sqlite3
import pandas as pd
import sys
import os
import json
import asyncio
import ccxt.async_support as ccxt
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.db import Database

class DataBackfiller:
    def __init__(self):
        self.db = Database()
        # USE SPOT (Historical 1s support)
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'adjustForTimeDifference': True} 
        })

    async def fetch_1s_precise(self, symbol: str, event_time: datetime):
        # Fetch window: -2 mins BEFORE to +120 mins AFTER
        # Total 122 mins = 7320 seconds. 
        # Binance 1s limit is 1000 candles.
        
        start_time = event_time - timedelta(minutes=2)
        # We need roughly 7500 candles. 
        chunks = 10 
        
        all_candles = []
        current_since = int(start_time.timestamp() * 1000)
        
        for _ in range(chunks):
            try:
                # SPOT uses '1s'. 
                # Note: Some older timestamps might return empty on spot if pairs didn't exist, 
                # but SOL/USDT existed in 2024.
                ohlcv = await self.exchange.fetch_ohlcv(symbol, '1s', since=current_since, limit=1000)
                if not ohlcv: break
                
                for c in ohlcv:
                    ts = c[0]
                    all_candles.append({
                        "timestamp": datetime.fromtimestamp(ts/1000, timezone.utc).isoformat(),
                        "open": c[1], "high": c[2], "low": c[3], "close": c[4], "volume": c[5]
                    })
                    
                current_since = ohlcv[-1][0] + 1000 # +1s
                await asyncio.sleep(1.0) # Throttled
            except Exception as e:
                print(f"Fetch Error: {e}")
                await asyncio.sleep(5)
                break
                
        return all_candles

    async def run(self):
        print("🚀 Backfilling 1-Second Spot Data (REPAIRED ROWID)...")
        
        conn = self.db.get_connection()
        c = conn.cursor()
        
        # Select using ROWID because 'id' column might be NULL due to schema mismatch
        c.execute("SELECT rowid, timestamp, title FROM gold_events")
        rows = c.fetchall()
        
        print(f"   Targeting {len(rows)} events...")
        
        success_count = 0
        
        for r in rows:
            rid, ts_str, title = r
            
            # Parse Date
            try:
                event_dt = datetime.fromisoformat(ts_str.replace("Z", ""))
            except:
                event_dt = datetime.strptime(ts_str.split('+')[0], "%Y-%m-%d %H:%M:%S")
            
            # Check if already done (Resume)
            # Use ROWID for the check
            c.execute("SELECT sol_price_data FROM gold_events WHERE rowid = ?", (rid,))
            fetch_res = c.fetchone()
            if not fetch_res: continue 
            
            existing = fetch_res[0]
            if existing is not None and len(existing) > 100000: # Check for >100KB (Deep data)
                 # print(f"   Skipping {rid} (Already has data)")
                 continue
            
            # Fetch
            # print(f"   Downloading 1s Data: {ts_str}...")
            data = await self.fetch_1s_precise("SOL/USDT", event_dt)
            
            if data and len(data) > 100:
                # Update DB using ROWID
                c.execute("UPDATE gold_events SET sol_price_data = ? WHERE rowid = ?", (json.dumps(data), rid))
                conn.commit()
                success_count += 1
                if success_count % 5 == 0:
                    print(f"   ✅ Backfilled {success_count} new events...")
            else:
                print(f"   ⚠️ Failed/Empty Data for {ts_str}")
        
        await self.exchange.close()
        conn.close()
        print(f"🎉 Complete. {success_count} Events Updated.")

if __name__ == "__main__":
    backfiller = DataBackfiller()
    asyncio.run(backfiller.run())
