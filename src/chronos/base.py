"""
Base classes for historical data fetchers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncGenerator, Optional
import logging


@dataclass
class PriceCandle:
    """OHLCV price candle data."""
    timestamp: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float


class HistoricalFetcher(ABC):
    """
    Abstract base class for historical data fetchers.
    
    Subclasses implement the fetch method to retrieve data from
    various sources (Yahoo Finance, news archives, etc.)
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.logger = logging.getLogger(f"hedgemony.chronos.{self.get_source_name()}")
    
    @abstractmethod
    def get_source_name(self) -> str:
        """Return the identifier for this data source."""
        pass
    
    @abstractmethod
    async def fetch(
        self, 
        start_date: datetime, 
        end_date: datetime,
        symbols: Optional[list] = None
    ) -> AsyncGenerator:
        """
        Fetch historical data for the given date range.
        
        Args:
            start_date: Start of the date range (inclusive)
            end_date: End of the date range (inclusive)
            symbols: Optional list of symbols to fetch (source-specific)
            
        Yields:
            Data items (PriceCandle, NewsItem, etc. depending on source)
        """
        pass
