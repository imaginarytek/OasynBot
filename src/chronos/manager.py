"""
Chronos Manager - Orchestrates historical data fetching.

Reads configuration and coordinates data fetchers to backfill
historical market and news data for backtesting.
"""

import asyncio
from datetime import datetime
from typing import List, Optional
import logging

from .base import HistoricalFetcher, PriceCandle
from .yahoo import YahooFinanceFetcher
from .news_archive import NewsArchiveFetcher
from src.utils.db import Database


class ChronosManager:
    """
    Orchestrates historical data fetching from multiple sources.
    
    Reads the 'chronos' section from config and initializes
    appropriate fetchers based on configured data_sources.
    """
    
    # Map config names to fetcher classes
    FETCHER_MAP = {
        "yahoo_finance": YahooFinanceFetcher,
        "news_archive": NewsArchiveFetcher,
        "common_crawl_news": NewsArchiveFetcher,  # Alias for now
    }
    
    def __init__(self, config: dict, db: Database = None):
        self.logger = logging.getLogger("hedgemony.chronos.manager")
        self.config = config.get("chronos", {})
        self.db = db or Database()
        self.fetchers: List[HistoricalFetcher] = []
        
        self._init_fetchers()
        
    def _init_fetchers(self):
        """Initialize fetchers based on config."""
        data_sources = self.config.get("data_sources", ["yahoo_finance"])
        
        for source in data_sources:
            fetcher_class = self.FETCHER_MAP.get(source)
            if fetcher_class:
                self.fetchers.append(fetcher_class(self.config))
                self.logger.info(f"Initialized fetcher: {source}")
            else:
                self.logger.warning(f"Unknown data source: {source}")
                
        self.logger.info(f"ChronosManager initialized with {len(self.fetchers)} fetchers")
    
    async def run_backfill(
        self, 
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        symbols: Optional[List[str]] = None
    ) -> dict:
        """
        Run historical data backfill from all configured sources.
        
        Args:
            start_date: Start of date range (default: from config)
            end_date: End of date range (default: today)
            symbols: Optional symbol filter
            
        Returns:
            dict with counts of fetched items per source
        """
        # Parse dates from config if not provided
        if start_date is None:
            start_str = self.config.get("start_date", "2024-01-01")
            start_date = datetime.strptime(start_str, "%Y-%m-%d")
            
        if end_date is None:
            end_date = datetime.now()
            
        self.logger.info(f"Starting backfill: {start_date} to {end_date}")
        
        results = {}
        
        for fetcher in self.fetchers:
            source_name = fetcher.get_source_name()
            count = 0
            
            try:
                async for item in fetcher.fetch(start_date, end_date, symbols):
                    # Store based on item type
                    if isinstance(item, PriceCandle):
                        self.db.log_price_candle(item)
                    else:
                        # NewsItem - store for sentiment analysis
                        pass  # Would need analysis first
                        
                    count += 1
                    
                results[source_name] = count
                self.logger.info(f"Fetched {count} items from {source_name}")
                
            except Exception as e:
                self.logger.error(f"Error fetching from {source_name}: {e}")
                results[source_name] = f"error: {e}"
                
        self.logger.info(f"Backfill complete: {results}")
        return results
