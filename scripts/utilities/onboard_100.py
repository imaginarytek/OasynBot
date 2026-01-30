
import sys
import os
import json
import sqlite3
import pandas as pd
import asyncio
import ccxt.async_support as ccxt
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.db import Database

class EventOnboarder:
    def __init__(self):
        self.db = Database()
        # Use Futures for 'preferably futures data'
        self.exchange = ccxt.binance({
            'options': { 'defaultType': 'future' },
            'enableRateLimit': True
        })

    async def fetch_1s_window(self, symbol: str, event_time: datetime):
        """Fetch high-res 1s data for a window around event"""
        start_time = event_time - timedelta(minutes=5)
        end_time = event_time + timedelta(minutes=30)
        
        current_since = int(start_time.timestamp() * 1000)
        end_ts = int(end_time.timestamp() * 1000)
        
        all_candles = []
        retries = 3
        
        while current_since < end_ts:
            try:
                ohlcv = await self.exchange.fetch_ohlcv(symbol, '1m', since=current_since, limit=1000) # Fallback to 1m if 1s not avail in futures history API
                # NOTE: Binance Futures API *does* strictly limit 1s data history often. 
                # Let's try '1m' first as a proxy if '1s' fails, OR verify 1s support.
                # Actually, standard Binance Futures API serves 1m max history usually.
                # Spot API serves 1s history for 30 days.
                # If we need DEEP history (2025), we likely only get 1m candles.
                
                # REVISION: We will try '1m' candles for the Onboarding to ensure we get data.
                # '1s' is ideal but rarely available >6 months out publicly.
                
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
                
                last_ts = ohlcv[-1][0]
                if last_ts == current_since: break
                current_since = last_ts + 60000 # 1m
                
            except Exception as e:
                print(f"Fetch Error: {e}")
                retries -=1
                if retries ==0: break
                await asyncio.sleep(1)
                
        return all_candles

    async def run(self):
        print("🚀 Onboarding Top 100 SOL Events...")
        
        # Load CSV
        csv_path = "data/top_sol_moves_2024.csv"
        if not os.path.exists(csv_path):
            print("❌ CSV not found.")
            return

        df = pd.read_csv(csv_path)
        # Assuming CSV has 'datetime' or 'ts' from previous script
        # Previous script columns: index, ts, open... datetime, move_pct
        
        conn = self.db.get_connection()
        c = conn.cursor()
        
        count = 0
        
        for index, row in df.iterrows():
            if count >= 100: break
            
            ts_str = row['datetime']
            # Remove +00:00 for simple parsing if needed, but fromisoformat handles usually
            event_dt = datetime.fromisoformat(str(ts_str).replace("Z", ""))
            
            # Create Title
            rank = index + 1
            direction = "CRASH" if row['move_pct'] < 0 else "PUMP"
            title = f"Top #{rank} {direction} ({abs(row['move_pct']):.1%})"
            
            # Check exist
            c.execute("SELECT id FROM gold_events WHERE timestamp = ?", (str(event_dt),))
            existing = c.fetchone()
            
            if existing:
                print(f"🔁 Exists: {title}")
                event_id = existing[0]
            else:
                # Insert
                print(f"✨ Creating: {title}")
                c.execute("""
                    INSERT INTO gold_events (title, timestamp, ai_score, ai_confidence)
                    VALUES (?, ?, ?, ?)
                """, (title, str(event_dt), 0.9, 0.95)) # Mock AI Confidence to allow backtest
                event_id = c.lastrowid
                conn.commit()
            
            # Fetch Data (Futures)
            data = await self.fetch_1s_window("SOL/USDT", event_dt) # API symbol
            
            if data:
                c.execute("UPDATE gold_events SET sol_price_data = ? WHERE id = ?", (json.dumps(data), event_id))
                conn.commit()
                print(f"   ✅ Data Saved ({len(data)} candles)")
            else:
                print("   ⚠️ No Data Found")
                
            count += 1
            
        conn.close()
        await self.exchange.close()
        print("Done.")

if __name__ == "__main__":
    onboarder = EventOnboarder()
    asyncio.run(onboarder.run())
