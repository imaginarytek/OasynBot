#!/usr/bin/env python3
"""
GOLD STANDARD: GAP FILLER (Smart Fetcher)
Downloads Binance 1s Data ONLY for months where we have Gold Events.
Skipping months without events to save time/bandwidth.
"""

import sys
import os
import json
import sqlite3
import pandas as pd
import requests
import zipfile
import io
from datetime import datetime, timedelta
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.utils.db import Database

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger("1s_fetcher")

class SmartFetcher:
    def __init__(self):
        self.db = Database()
        self.BASE_URL = "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1s"
        self.cache_dir = "data/binance_cache"
        os.makedirs(self.cache_dir, exist_ok=True)

    def download_month_zip(self, year, month):
        """Download and cache monthly ZIP if not exists"""
        filename = f"BTCUSDT-1s-{year}-{month:02d}.zip"
        local_path = os.path.join(self.cache_dir, filename)
        
        if os.path.exists(local_path):
            logger.info(f"✅ Found cached: {filename}")
            return local_path
            
        url = f"{self.BASE_URL}/{filename}"
        logger.info(f"⬇️ Downloading {url} ... (This is large ~70MB)")
        
        try:
            r = requests.get(url, stream=True)
            if r.status_code != 200:
                logger.error(f"❌ Failed to download {url} (Status: {r.status_code})")
                return None
                
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*1024): # 1MB chunks
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        print(f"   Progress: {downloaded/1024/1024:.1f}MB", end='\r')
            
            print() # Newline
            return local_path
        except Exception as e:
            logger.error(f"Download Error: {e}")
            if os.path.exists(local_path): os.remove(local_path) # cleanup partial
            return None

    def extract_event_window(self, zip_path, event_time: datetime):
        """Extract specific -5m to +30m window"""
        if not zip_path: return []
        
        start_ts = int((event_time - timedelta(minutes=5)).timestamp() * 1000)
        end_ts = int((event_time + timedelta(minutes=30)).timestamp() * 1000)
        
        extracted_candles = []
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                csv_name = z.namelist()[0]
                with z.open(csv_name) as f:
                    for line in io.TextIOWrapper(f):
                        parts = line.split(',')
                        ts = int(parts[0])
                        
                        if ts >= start_ts and ts <= end_ts:
                            extracted_candles.append({
                                "timestamp": datetime.fromtimestamp(ts/1000).isoformat(),
                                "open": float(parts[1]),
                                "high": float(parts[2]),
                                "low": float(parts[3]),
                                "close": float(parts[4]),
                                "volume": float(parts[5])
                            })
                        elif ts > end_ts:
                            break
            return extracted_candles
        except Exception as e:
            logger.error(f"Extraction Error: {e}")
            return []

    def run(self):
        logger.info("🚀 Starting Smart Gap Filler...")
        
        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        c.execute("SELECT * FROM gold_events")
        events = [dict(row) for row in c.fetchall()]
        
        logger.info(f"Scanning {len(events)} events for missing data...")
        
        events_by_month = {}
        for e in events:
            # Skip Mocks (2025/2026)
            if '2025-' in e['timestamp'] or '2026-' in e['timestamp']: continue
            
            dt = datetime.fromisoformat(e['timestamp'])
            key = (dt.year, dt.month)
            if key not in events_by_month: events_by_month[key] = []
            events_by_month[key].append(e)
            
        sorted_keys = sorted(events_by_month.keys())
        
        for (year, month) in sorted_keys:
            monthly_events = events_by_month[(year, month)]
            logger.info(f"📅 Checking {year}-{month:02d} ({len(monthly_events)} events)...")
            
            # Check if we already have valid data for ALL events in this month
            # Actually, easiest to just check if ZIP exists. If not, download.
            zip_path = self.download_month_zip(year, month)
            
            if not zip_path: 
                logger.warning(f"⚠️ Skipped {year}-{month:02d} (Download failed or not found)")
                continue
                
            # Process events for this month
            for event in monthly_events:
                # Check if event already has Real 1s data
                current_data = json.loads(event['price_data']) if event['price_data'] else []
                is_real = False
                if len(current_data) > 2:
                    t1 = pd.to_datetime(current_data[0]['timestamp'])
                    t2 = pd.to_datetime(current_data[1]['timestamp'])
                    if (t2-t1).total_seconds() <= 1.1:
                        is_real = True
                
                if is_real:
                    # logger.info(f"  ✨ {event['title']} already has Real Data.")
                    continue
                
                # If not real, update it
                logger.info(f"  🛠️ Upgrading {event['title']} to Real 1s Data...")
                event_dt = datetime.fromisoformat(event['timestamp'])
                new_data = self.extract_event_window(zip_path, event_dt)
                
                if new_data:
                    c.execute("UPDATE gold_events SET price_data = ? WHERE id = ?", (json.dumps(new_data), event['id']))
                    conn.commit()
                    logger.info("     ✅ Done.")
                else:
                    logger.warning("     ⚠️ Extraction yielded no data.")

        conn.close()
        logger.info("🏆 Gap Fill Complete.")

if __name__ == "__main__":
    fetcher = SmartFetcher()
    fetcher.run()
