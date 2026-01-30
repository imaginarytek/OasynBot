#!/usr/bin/env python3
"""
GOLD STANDARD: SOL DATA FETCHER (Hyperliquid Proxy)
Downloads official 1s klines for SOLUSDT from Binance Vision.
Used as a high-fidelity proxy for Hyperliquid SOL-USD price action.
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
logger = logging.getLogger("sol_fetcher")

class SolDataFetcher:
    def __init__(self):
        self.db = Database()
        self.BASE_URL = "https://data.binance.vision/data/spot/monthly/klines/SOLUSDT/1s"
        self.cache_dir = "data/binance_cache"
        os.makedirs(self.cache_dir, exist_ok=True)

    def download_month_zip(self, year, month):
        """Download and cache monthly ZIP if not exists"""
        filename = f"SOLUSDT-1s-{year}-{month:02d}.zip"
        local_path = os.path.join(self.cache_dir, filename)
        
        if os.path.exists(local_path):
            logger.info(f"Using cached: {filename}")
            return local_path
            
        url = f"{self.BASE_URL}/{filename}"
        logger.info(f"⬇️ Downloading {url} ...")
        
        try:
            r = requests.get(url, stream=True)
            if r.status_code != 200:
                logger.error(f"Failed to download {url} (Status: {r.status_code})")
                return None
                
            with open(local_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
            return local_path
        except Exception as e:
            logger.error(f"Download Error: {e}")
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
        logger.info("🚀 Starting SOL Data Fetcher (Hyperliquid Proxy)...")
        
        conn = self.db.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Fetch events 2024 only for rapid validation
        c.execute("SELECT * FROM gold_events WHERE timestamp LIKE '2024%'")
        events = [dict(row) for row in c.fetchall()]
        
        logger.info(f"Found {len(events)} 2024 events to upgrade to SOL.")
        
        events_by_month = {}
        for e in events:
            dt = datetime.fromisoformat(e['timestamp'])
            key = (dt.year, dt.month)
            if key not in events_by_month: events_by_month[key] = []
            events_by_month[key].append(e)
            
        for (year, month), monthly_events in events_by_month.items():
            logger.info(f"Processing {year}-{month:02d}...")
            
            zip_path = self.download_month_zip(year, month)
            if not zip_path: continue
                
            for event in monthly_events:
                event_dt = datetime.fromisoformat(event['timestamp'])
                
                candles_1s = self.extract_event_window(zip_path, event_dt)
                
                if candles_1s:
                    # Update DB - Store as SEPARATE field 'price_data_sol'?
                    # Or overwrite price_data? 
                    # Let's overwrite since we are switching strat entirely.
                    c.execute("UPDATE gold_events SET price_data = ? WHERE id = ?", (json.dumps(candles_1s), event['id']))
                    conn.commit()
                    logger.info(f"  ✅ Upgraded {event['title']} to SOL data")
                    
        conn.close()
        logger.info("SOL Upgrade Complete.")

if __name__ == "__main__":
    fetcher = SolDataFetcher()
    fetcher.run()
