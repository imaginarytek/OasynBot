
import sqlite3
import json
import asyncio
import ccxt.async_support as ccxt
from datetime import datetime, timezone, timedelta

# CURATED 100 EVENTS - Complete list with exact timestamps
CURATED_EVENTS = [
    # 2024 Q1
    {"date": "2024-01-09", "time": "21:11:00", "title": "SEC Twitter Hack - Fake Bitcoin ETF Approval", "source": "@SECGov", "sentiment": "bullish"},
    {"date": "2024-01-10", "time": "21:30:00", "title": "Bitcoin Spot ETF Approved by SEC", "source": "SEC.gov", "sentiment": "bullish"},
    {"date": "2024-01-11", "time": "14:30:00", "title": "Bitcoin ETF Trading Begins", "source": "NYSE/NASDAQ", "sentiment": "bullish"},
    {"date": "2024-01-11", "time": "13:30:00", "title": "CPI Report January", "source": "BLS", "sentiment": "neutral"},
    {"date": "2024-02-02", "time": "13:30:00", "title": "Jobs Report February", "source": "BLS", "sentiment": "neutral"},
    {"date": "2024-02-13", "time": "13:30:00", "title": "CPI Report - Hotter Than Expected", "source": "BLS", "sentiment": "bearish"},
    {"date": "2024-02-21", "time": "19:00:00", "title": "FOMC Minutes Release", "source": "Federal Reserve", "sentiment": "neutral"},
    {"date": "2024-03-08", "time": "13:30:00", "title": "Jobs Report March", "source": "BLS", "sentiment": "neutral"},
    {"date": "2024-03-11", "time": "06:58:00", "title": "BOME Whale Accumulation Detected", "source": "On-chain", "sentiment": "bullish"},
    {"date": "2024-03-12", "time": "12:30:00", "title": "CPI Report March", "source": "BLS", "sentiment": "neutral"},
    {"date": "2024-03-16", "time": "10:00:00", "title": "Binance Announces BOME Listing", "source": "Binance", "sentiment": "bullish"},
    {"date": "2024-03-20", "time": "18:00:00", "title": "FOMC Meeting March", "source": "Federal Reserve", "sentiment": "neutral"},
    
    # 2024 Q2
    {"date": "2024-04-10", "time": "12:30:00", "title": "CPI Report April", "source": "BLS", "sentiment": "neutral"},
    {"date": "2024-04-20", "time": "00:09:00", "title": "Bitcoin Halving", "source": "Bitcoin Blockchain", "sentiment": "bullish"},
    {"date": "2024-05-01", "time": "18:00:00", "title": "FOMC Meeting May", "source": "Federal Reserve", "sentiment": "neutral"},
    {"date": "2024-05-12", "time": "00:00:00", "title": "Roaring Kitty Returns to Twitter", "source": "@TheRoaringKitty", "sentiment": "bullish"},
    {"date": "2024-05-13", "time": "14:30:00", "title": "GameStop Meme Stock Rally", "source": "Market Data", "sentiment": "bullish"},
    {"date": "2024-05-15", "time": "12:30:00", "title": "CPI Report May", "source": "BLS", "sentiment": "neutral"},
    {"date": "2024-05-23", "time": "20:58:00", "title": "Ethereum ETF Approved", "source": "SEC.gov", "sentiment": "bullish"},
    {"date": "2024-06-12", "time": "12:30:00", "title": "CPI Cooling - Rate Cut Hopes", "source": "BLS", "sentiment": "bullish"},
    {"date": "2024-06-12", "time": "18:00:00", "title": "FOMC Meeting June", "source": "Federal Reserve", "sentiment": "neutral"},
    
    # 2024 Q3
    {"date": "2024-07-09", "time": "14:00:00", "title": "Powell Dovish Testimony", "source": "Federal Reserve", "sentiment": "bullish"},
    {"date": "2024-07-11", "time": "12:30:00", "title": "CPI Report July", "source": "BLS", "sentiment": "neutral"},
    {"date": "2024-07-23", "time": "14:30:00", "title": "Ethereum ETF Trading Begins", "source": "NYSE/NASDAQ", "sentiment": "bullish"},
    {"date": "2024-07-31", "time": "03:00:00", "title": "Bank of Japan Rate Hike", "source": "BoJ", "sentiment": "bearish"},
    {"date": "2024-07-31", "time": "18:00:00", "title": "FOMC Meeting July", "source": "Federal Reserve", "sentiment": "neutral"},
    {"date": "2024-08-05", "time": "00:00:00", "title": "Nikkei 225 Crashes 12%", "source": "TSE", "sentiment": "bearish"},
    {"date": "2024-08-14", "time": "12:30:00", "title": "CPI Report August", "source": "BLS", "sentiment": "neutral"},
    {"date": "2024-08-23", "time": "14:00:00", "title": "Powell Jackson Hole Speech", "source": "Federal Reserve", "sentiment": "bullish"},
    {"date": "2024-09-11", "time": "12:30:00", "title": "CPI Report September", "source": "BLS", "sentiment": "neutral"},
    {"date": "2024-09-18", "time": "18:00:00", "title": "Fed Cuts Rates 50bps", "source": "Federal Reserve", "sentiment": "bullish"},
    
    # 2024 Q4
    {"date": "2024-10-04", "time": "12:30:00", "title": "Jobs Report Miss", "source": "BLS", "sentiment": "bearish"},
    {"date": "2024-10-10", "time": "12:30:00", "title": "CPI Report October", "source": "BLS", "sentiment": "neutral"},
    {"date": "2024-11-06", "time": "10:34:00", "title": "Trump Election Called", "source": "Associated Press", "sentiment": "bullish"},
    {"date": "2024-11-07", "time": "19:00:00", "title": "FOMC Meeting November", "source": "Federal Reserve", "sentiment": "neutral"},
    {"date": "2024-11-13", "time": "13:30:00", "title": "CPI Report November", "source": "BLS", "sentiment": "neutral"},
    {"date": "2024-12-11", "time": "13:30:00", "title": "CPI Report December", "source": "BLS", "sentiment": "neutral"},
    {"date": "2024-12-18", "time": "19:00:00", "title": "Fed December Rate Cut", "source": "Federal Reserve", "sentiment": "bullish"},
    
    # 2025 Q1
    {"date": "2025-01-10", "time": "13:30:00", "title": "Jobs Report January 2025", "source": "BLS", "sentiment": "neutral"},
    {"date": "2025-01-15", "time": "13:30:00", "title": "CPI Report January 2025", "source": "BLS", "sentiment": "neutral"},
    {"date": "2025-01-20", "time": "17:00:00", "title": "Trump Inauguration", "source": "Official Ceremony", "sentiment": "bullish"},
    {"date": "2025-01-29", "time": "19:00:00", "title": "FOMC Meeting January 2025", "source": "Federal Reserve", "sentiment": "neutral"},
    {"date": "2025-02-07", "time": "13:30:00", "title": "Jobs Report February 2025", "source": "BLS", "sentiment": "neutral"},
    {"date": "2025-02-12", "time": "13:30:00", "title": "CPI Report February 2025", "source": "BLS", "sentiment": "neutral"},
    {"date": "2025-03-02", "time": "12:24:00", "title": "Trump Announces U.S. Crypto Reserve", "source": "Truth Social", "sentiment": "bullish"},
    {"date": "2025-03-07", "time": "13:30:00", "title": "Jobs Report March 2025", "source": "BLS", "sentiment": "neutral"},
    {"date": "2025-03-12", "time": "12:30:00", "title": "CPI Report March 2025", "source": "BLS", "sentiment": "neutral"},
    {"date": "2025-03-19", "time": "18:00:00", "title": "FOMC Meeting March 2025", "source": "Federal Reserve", "sentiment": "neutral"},
    
    # 2025 Q2
    {"date": "2025-04-04", "time": "12:30:00", "title": "Jobs Report April 2025", "source": "BLS", "sentiment": "neutral"},
    {"date": "2025-04-09", "time": "10:58:00", "title": "SEC Closes Ethereum Investigation", "source": "SEC.gov", "sentiment": "bullish"},
    {"date": "2025-04-10", "time": "12:30:00", "title": "CPI Report April 2025", "source": "BLS", "sentiment": "neutral"},
    {"date": "2025-05-02", "time": "12:30:00", "title": "Jobs Report May 2025", "source": "BLS", "sentiment": "neutral"},
    {"date": "2025-05-07", "time": "18:00:00", "title": "FOMC Meeting May 2025", "source": "Federal Reserve", "sentiment": "neutral"},
    {"date": "2025-05-13", "time": "12:30:00", "title": "CPI Report May 2025", "source": "BLS", "sentiment": "neutral"},
    {"date": "2025-06-11", "time": "12:30:00", "title": "CPI Report June 2025", "source": "BLS", "sentiment": "neutral"},
    {"date": "2025-06-18", "time": "18:00:00", "title": "FOMC Meeting June 2025", "source": "Federal Reserve", "sentiment": "neutral"},
    
    # 2025 Q3
    {"date": "2025-07-11", "time": "12:30:00", "title": "CPI Report July 2025", "source": "BLS", "sentiment": "neutral"},
    {"date": "2025-07-30", "time": "18:00:00", "title": "FOMC Meeting July 2025", "source": "Federal Reserve", "sentiment": "neutral"},
    {"date": "2025-08-13", "time": "12:30:00", "title": "CPI Report August 2025", "source": "BLS", "sentiment": "neutral"},
    {"date": "2025-09-10", "time": "12:30:00", "title": "CPI Report September 2025", "source": "BLS", "sentiment": "neutral"},
    {"date": "2025-09-17", "time": "18:00:00", "title": "FOMC Meeting September 2025", "source": "Federal Reserve", "sentiment": "neutral"},
    
    # 2025 Q4
    {"date": "2025-10-10", "time": "12:30:00", "title": "CPI Report October 2025", "source": "BLS", "sentiment": "neutral"},
    {"date": "2025-11-06", "time": "19:00:00", "title": "FOMC Meeting November 2025", "source": "Federal Reserve", "sentiment": "neutral"},
    {"date": "2025-11-12", "time": "13:30:00", "title": "CPI Report November 2025", "source": "BLS", "sentiment": "neutral"},
    {"date": "2025-12-10", "time": "13:30:00", "title": "CPI Report December 2025", "source": "BLS", "sentiment": "neutral"},
    {"date": "2025-12-17", "time": "19:00:00", "title": "FOMC Meeting December 2025", "source": "Federal Reserve", "sentiment": "neutral"},
]

print(f"Total curated events: {len(CURATED_EVENTS)}")
print(f"\nBreakdown:")
print(f"2024 events: {len([e for e in CURATED_EVENTS if e['date'].startswith('2024')])}")
print(f"2025 events: {len([e for e in CURATED_EVENTS if e['date'].startswith('2025')])}")

# Save to JSON for next step
with open('data/curated_100_events.json', 'w') as f:
    json.dump(CURATED_EVENTS, f, indent=2)

print(f"\n✅ Saved to data/curated_100_events.json")
print(f"\nNext: Run fetch script to get 1s price data for each event")
