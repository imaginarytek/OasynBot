"""
Yahoo Finance historical data fetcher.

Uses the yfinance library to retrieve OHLCV price data.
"""

import asyncio
from datetime import datetime
from typing import AsyncGenerator, Optional, List
import logging

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    yf = None

from .base import HistoricalFetcher, PriceCandle


class YahooFinanceFetcher(HistoricalFetcher):
    """
    Fetches historical OHLCV data from Yahoo Finance.
    
    Default symbols: BTC-USD, ETH-USD
    """
    
    DEFAULT_SYMBOLS = ["BTC-USD", "ETH-USD"]
    
    def __init__(self, config: dict = None):
        super().__init__(config)
        self.symbols = self.config.get("symbols", self.DEFAULT_SYMBOLS)
        
        if not YFINANCE_AVAILABLE:
            self.logger.warning(
                "yfinance not installed. Run: pip install yfinance"
            )
    
    def get_source_name(self) -> str:
        return "yahoo_finance"
    
    async def fetch(
        self, 
        start_date: datetime, 
        end_date: datetime,
        symbols: Optional[List[str]] = None
    ) -> AsyncGenerator[PriceCandle, None]:
        """
        Fetch historical price data from Yahoo Finance.
        
        Args:
            start_date: Start date for data fetch
            end_date: End date for data fetch  
            symbols: List of ticker symbols (e.g., ['BTC-USD', 'ETH-USD'])
            
        Yields:
            PriceCandle objects for each data point
        """
        if not YFINANCE_AVAILABLE:
            self.logger.error("yfinance not available, cannot fetch data")
            return
            
        target_symbols = symbols or self.symbols
        
        for symbol in target_symbols:
            self.logger.info(f"Fetching {symbol} from {start_date} to {end_date}")
            
            # yfinance is synchronous, run in executor to not block
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: self._fetch_symbol(symbol, start_date, end_date)
            )
            
            if df is None or df.empty:
                self.logger.warning(f"No data returned for {symbol}")
                continue
                
            # Yield each row as a PriceCandle
            for idx, row in df.iterrows():
                candle = PriceCandle(
                    timestamp=idx.to_pydatetime(),
                    symbol=symbol,
                    open=float(row['Open']),
                    high=float(row['High']),
                    low=float(row['Low']),
                    close=float(row['Close']),
                    volume=float(row['Volume'])
                )
                yield candle
                
            self.logger.info(f"Fetched {len(df)} candles for {symbol}")
    
    def _fetch_symbol(self, symbol: str, start: datetime, end: datetime):
        """Synchronous fetch using yfinance."""
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(
                start=start.strftime("%Y-%m-%d"),
                end=end.strftime("%Y-%m-%d"),
                interval="1d"
            )
            return df
        except Exception as e:
            self.logger.error(f"Error fetching {symbol}: {e}")
            return None
