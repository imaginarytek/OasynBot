#!/usr/bin/env python3
"""
GOLD STANDARD: PRIORITY FETCHER
Only downloads the 3 most critical historic events:
1. Russia Invasion (2022-02)
2. USDT Depeg (2022-05)
3. FTX Collapse (2022-11)
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
logger = logging.getLogger("priority_fetcher")

class PriorityFetcher:
    def __init__(self):
        self.db = Database()
        self.BASE_URL = "https://data.binance.vision/data/spot/monthly/klines/BTCUSDT/1s"
        self.cache_dir = "data/binance_cache"
        os.makedirs(self.cache_dir, exist_ok=True)

    def download_month_zip(self, year, month):
        filename = f"BTCUSDT-1s-{year}-{month:02d}.zip"
        local_path = os.path.join(self.cache_dir, filename)
        
        if os.path.exists(local_path):
            logger.info(f"✅ Found cached: {filename}")
            return local_path
            
        url = f"{self.BASE_URL}/{filename}"
        logger.info(f"⬇️ Downloading {url} ...")
        
        try:
            r = requests.get(url, stream=True)
            if r.status_code != 200:
                logger.error(f"Failed to download {url}")
                return None
                
            total_size = int(r.headers.get('content-length', 0))
            downloaded = 0
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        print(f"   Progress: {downloaded/1024/1024:.1f}MB", end='\r')
            print()
            return local_path
        except Exception as e:
            logger.error(f"Error: {e}")
            if os.path.exists(local_path): os.remove(local_path)
            return None

    def extract_event_window(self, zip_path, event_time: datetime):
        if not zip_path: return []
        start_ts = int((event_time - timedelta(minutes=5)).timestamp() * 1000)
        end_ts = int((event_time + timedelta(minutes=30)).timestamp() * 1000)
        extracted = []
        try:
            with zipfile.ZipFile(zip_path, 'r') as z:
                csv_name = z.namelist()[0]
                with z.open(csv_name) as f:
                    for line in io.TextIOWrapper(f):
                        parts = line.split(',')
                        ts = int(parts[0])
                        if ts >= start_ts and ts <= end_ts:
                            extracted.append({
                                "timestamp": datetime.fromtimestamp(ts/1000).isoformat(),
                                "open": float(parts[1]),
                                "high": float(parts[2]),
                                "low": float(parts[3]),
                                "close": float(parts[4]),
                                "volume": float(parts[5])
                            })
                        elif ts > end_ts: break
            return extracted
        except Exception as e:
            logger.error(f"Extract Error: {e}")
            return []

    def run(self):
        logger.info("🚀 Starting Priority Fetcher (Russia, Depeg, FTX)...")
        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # PRIORITY MONTHS
        target_months = [(2022, 2), (2022, 5), (2022, 11)]
        
        for (year, month) in target_months:
            logger.info(f"📅 Priority Month: {year}-{month:02d}")
            zip_path = self.download_month_zip(year, month)
            if not zip_path: continue
            
            # Find events in this month
            start_date = f"{year}-{month:02d}-01"
            end_date = f"{year}-{month:02d}-31"
            c.execute("SELECT * FROM gold_events WHERE timestamp BETWEEN ? AND ?", (start_date, end_date))
            events = [dict(row) for row in c.fetchall()]
            
            for event in events:
                logger.info(f"  🛠️ Upgrading {event['title']}...")
                event_dt = datetime.fromisoformat(event['timestamp'])
                new_data = self.extract_event_window(zip_path, event_dt)
                
                if new_data:
                    c.execute("UPDATE gold_events SET price_data = ? WHERE id = ?", (json.dumps(new_data), event['id']))
                    conn.commit()
                    logger.info("     ✅ Done.")
                    
        conn.close()
        logger.info("🏆 Priority Data Ready.")

if __name__ == "__main__":
    fetcher = PriorityFetcher()
    fetcher.run()
