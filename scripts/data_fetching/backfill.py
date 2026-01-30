#!/usr/bin/env python3
"""
Chronos Backfill Script

Fetches historical market data and stores it in the database
for backtesting trading strategies.

Usage:
    python3 scripts/backfill.py --start 2024-01-01 --end 2024-12-31
    python3 scripts/backfill.py --start 2024-01-01  # End defaults to today
"""

import argparse
import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import yaml
from src.chronos.manager import ChronosManager
from src.utils.db import Database


def parse_args():
    parser = argparse.ArgumentParser(
        description="Backfill historical market data for backtesting"
    )
    parser.add_argument(
        "--start", 
        type=str, 
        help="Start date (YYYY-MM-DD). Defaults to config value.",
        default=None
    )
    parser.add_argument(
        "--end", 
        type=str, 
        help="End date (YYYY-MM-DD). Defaults to today.",
        default=None
    )
    parser.add_argument(
        "--symbols",
        type=str,
        nargs="+",
        help="Symbols to fetch (e.g., BTC-USD ETH-USD)",
        default=None
    )
    parser.add_argument(
        "--config",
        type=str,
        help="Path to config file",
        default="config/config.yaml"
    )
    return parser.parse_args()


async def main():
    args = parse_args()
    
    # Load config
    with open(args.config, 'r') as f:
        config = yaml.safe_load(f)
    
    # Parse dates
    start_date = None
    end_date = None
    
    if args.start:
        start_date = datetime.strptime(args.start, "%Y-%m-%d")
    if args.end:
        end_date = datetime.strptime(args.end, "%Y-%m-%d")
    
    # Initialize database
    db = Database()
    db.init_db()
    
    # Initialize Chronos Manager
    print("🕐 Initializing Chronos Manager...")
    manager = ChronosManager(config, db)
    
    # Run backfill
    print(f"📊 Starting historical data backfill...")
    if start_date:
        print(f"   Start: {start_date.strftime('%Y-%m-%d')}")
    if end_date:
        print(f"   End: {end_date.strftime('%Y-%m-%d')}")
    if args.symbols:
        print(f"   Symbols: {', '.join(args.symbols)}")
    
    results = await manager.run_backfill(
        start_date=start_date,
        end_date=end_date,
        symbols=args.symbols
    )
    
    # Print results
    print("\n✅ Backfill Complete!")
    print("-" * 40)
    for source, count in results.items():
        if isinstance(count, int):
            print(f"   {source}: {count} records")
        else:
            print(f"   {source}: {count}")
    print("-" * 40)


if __name__ == "__main__":
    asyncio.run(main())
