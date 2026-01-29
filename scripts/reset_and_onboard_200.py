
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

class MasterOnboarder:
    def __init__(self):
        self.db = Database()
        # Using futures for data fetch
        self.exchange = ccxt.binance({
            'options': { 'defaultType': 'future' },
            'enableRateLimit': True
        })

    async def fetch_1s_window(self, symbol: str, event_time: datetime):
        """Reuse fetch logic from previous onboarder"""
        start_time = event_time - timedelta(minutes=5)
        end_time = event_time + timedelta(minutes=30)
        current_since = int(start_time.timestamp() * 1000)
        end_ts = int(end_time.timestamp() * 1000)
        
        all_candles = []
        retries = 3
        
        while current_since < end_ts:
            try:
                ohlcv = await self.exchange.fetch_ohlcv(symbol, '1m', since=current_since, limit=1000)
                if not ohlcv: break
                for c in ohlcv:
                    ts = c[0]
                    if ts > end_ts: break
                    all_candles.append({
                        "timestamp": datetime.fromtimestamp(ts/1000, timezone.utc).isoformat(),
                        "open": c[1], "high": c[2], "low": c[3], "close": c[4], "volume": c[5]
                    })
                if not ohlcv: break
                last_ts = ohlcv[-1][0]
                if last_ts == current_since: break
                current_since = last_ts + 60000
            except:
                retries -=1
                if retries ==0: break
                await asyncio.sleep(1)
        return all_candles

    async def run(self):
        print("🚀 RESETTING AND ONBOARDING 200 UNIQUE EVENTS...")
        
        # 1. Reset Table matches schema upgrade
        conn = self.db.get_connection()
        c = conn.cursor()
        c.execute("DELETE FROM gold_events") # Wipe clean
        conn.commit()
        print("   🗑️  Database Wiped Clean.")
        
        # 2. Load New Unique CSV
        df = pd.read_csv("data/unique_200_events.csv")
        
        count = 0 
        for index, row in df.iterrows():
            ts_str = row['datetime']
            # Re-parse
            try:
                event_dt = datetime.fromisoformat(ts_str.replace("Z", ""))
            except:
                event_dt = datetime.strptime(ts_str.split('+')[0], "%Y-%m-%d %H:%M:%S")
            
            # Ensure UTC aware if needed for formatting, but isoformat usually fine
            
            move_pct = row['move_pct']
            direction = "CRASH" if move_pct < 0 else "PUMP"
            title = f"Unmapped {direction} ({abs(move_pct):.1%})"
            
            # Insert Placeholder
            c.execute("""
                INSERT INTO gold_events (title, timestamp, ai_score, ai_confidence, source, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (title, str(event_dt), 0.9, 0.95, "Unknown Tier 1 Source", "Exact text waiting for hydration."))
            event_id = c.lastrowid
            conn.commit()
            
            # Fetch Data
            # print(f"   Fetching Data for #{index+1}: {ts_str}...")
            data = await self.fetch_1s_window("SOL/USDT", event_dt)
            
            if data:
                c.execute("UPDATE gold_events SET sol_price_data = ? WHERE id = ?", (json.dumps(data), event_id))
                conn.commit()
            
            count += 1
            if count % 10 == 0:
                print(f"   ✅ Onboarded {count}/200 events...")
                
        conn.close()
        await self.exchange.close()
        print("🎉 Done. 200 Unique Events Ready for Hydration.")

if __name__ == "__main__":
    onboarder = MasterOnboarder()
    asyncio.run(onboarder.run())
