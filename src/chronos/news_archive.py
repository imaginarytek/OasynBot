"""
Historical news archive fetcher.

Provides historical news data for backtesting sentiment analysis.
For MVP, uses sample data or NewsAPI if configured.
"""

import asyncio
from datetime import datetime
from typing import AsyncGenerator, Optional, List
import logging

from src.ingestion.base import NewsItem
from .base import HistoricalFetcher


class NewsArchiveFetcher(HistoricalFetcher):
    """
    Fetches historical news for sentiment backtesting.
    
    For MVP iteration, provides sample data or uses NewsAPI.org
    if an API key is configured.
    """
    
    def __init__(self, config: dict = None):
        super().__init__(config)
        self.api_key = self.config.get("newsapi_key")
        
    def get_source_name(self) -> str:
        return "news_archive"
    
    async def fetch(
        self, 
        start_date: datetime, 
        end_date: datetime,
        symbols: Optional[List[str]] = None
    ) -> AsyncGenerator[NewsItem, None]:
        """
        Fetch historical news items.
        
        For MVP: Returns sample data for testing.
        Future: Integrate with NewsAPI, Common Crawl, or GDELT.
        
        Args:
            start_date: Start date for news fetch
            end_date: End date for news fetch
            symbols: Optional keywords to filter news
            
        Yields:
            NewsItem objects for sentiment analysis
        """
        # MVP: Return sample data for testing the pipeline
        sample_news = [
            NewsItem(
                source_id="sample_archive",
                title="Bitcoin ETF Approved by SEC - Historic Moment for Crypto",
                url="https://example.com/btc-etf",
                published_at=datetime(2024, 1, 10, 14, 30),
                content="The SEC has approved the first Bitcoin spot ETF...",
            ),
            NewsItem(
                source_id="sample_archive", 
                title="Federal Reserve Announces Surprise Rate Hike",
                url="https://example.com/fed-rates",
                published_at=datetime(2024, 1, 15, 18, 0),
                content="In an unexpected move, the Federal Reserve raised rates...",
            ),
            NewsItem(
                source_id="sample_archive",
                title="Major Exchange Hack: $100M in Crypto Stolen",
                url="https://example.com/hack",
                published_at=datetime(2024, 1, 20, 9, 15),
                content="A major cryptocurrency exchange suffered a security breach...",
            ),
        ]
        
        self.logger.info(f"Returning {len(sample_news)} sample news items for backtesting")
        
        for item in sample_news:
            # Filter by date range
            if start_date <= item.published_at <= end_date:
                yield item
                await asyncio.sleep(0)  # Yield control
                
        self.logger.info("Sample news fetch complete")
