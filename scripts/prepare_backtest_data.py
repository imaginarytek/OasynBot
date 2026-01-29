
import asyncio
import logging
import csv
import os
from datetime import datetime
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.chronos.yahoo import YahooFinanceFetcher
from src.utils.db import Database
from src.utils.backfill import BackfillEngine

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("hedgemony.prepare_data")

async def main():
    logger.info("Starting Data Preparation for Backtest...")
    
    db = Database()
    db.init_db()
    
    # 1. Fetch Price History (Jan 2024 - Bitcoin ETF Era)
    fetcher = YahooFinanceFetcher({"symbols": ["BTC-USD"]})
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)
    
    logger.info(f"Fetching Price Data: {start_date.date()} to {end_date.date()}")
    
    count = 0
    # Store price data
    async for candle in fetcher.fetch(start_date, end_date):
        db.log_price_candle(candle)
        count += 1
        
    logger.info(f"Stored {count} price candles for BTC-USD.")

    # 2. Create Synthetic News History (Mocking "Alpha")
    # We create a CSV with known market moving events to test if strategy picks them up.
    
    news_file = "data/backtest_news_jan24.csv"
    logger.info(f"Creating mock news file: {news_file}")
    
    with open(news_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['title', 'url', 'published_at', 'source', 'content'])
        
        # Event 1: ETF Approval Fakeout (Jan 9) - Volatility
        writer.writerow([
            "SEC Twitter Hacked: Bitcoin ETF Approved False Claim", 
            "http://fake.com/1", "2024-01-09T16:00:00", "twitter", 
            "The SEC account was compromised announcing ETF approval."
        ])
        
        # Event 2: Real Approval (Jan 10) - Bullish
        writer.writerow([
            "SEC Officially Approves First Spot Bitcoin ETFs", 
            "http://fake.com/2", "2024-01-10T16:00:00", "reuters", 
            "Landmark decision approves 11 spot bitcoin ETFs including BlackRock."
        ])
        
        # Event 3: Grayscale Outflows (Jan 12) - Bearish
        writer.writerow([
            "Grayscale GBTC Outflows Hit $500M as Fees Bite", 
            "http://fake.com/3", "2024-01-12T10:00:00", "bloomberg", 
            "Massive selling pressure observed from Grayscale trust conversion."
        ])
        
        # Event 4: Stabilization (Jan 20) - Neutral/Positive
        writer.writerow([
            "Bitcoin Stabilizes as ETF Flows Turn Net Positive", 
            "http://fake.com/4", "2024-01-20T09:00:00", "coindesk", 
            "Inflows into BlackRock and Fidelity offset GBTC dumps."
        ])

    # 3. Import News to DB using BackfillEngine (Which runs Sentiment Analysis)
    logger.info("Importing Synthetic News into Database (Analyzed by Brain)...")
    # Need a config mock
    config = {"brain": {"model_name": "ProsusAI/finbert", "device": "auto"}}
    backfill = BackfillEngine(config)
    
    # Run the import (synchronous wrapper logic)
    backfill.import_csv(news_file)
    logger.info("Data Preparation Complete!")

if __name__ == "__main__":
    asyncio.run(main())
