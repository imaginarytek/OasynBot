"""
Unit tests for the Chronos historical data module.
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import pandas as pd

from src.chronos.base import PriceCandle, HistoricalFetcher
from src.chronos.yahoo import YahooFinanceFetcher
from src.chronos.manager import ChronosManager


class TestPriceCandle:
    def test_candle_creation(self):
        candle = PriceCandle(
            timestamp=datetime(2024, 1, 1),
            symbol="BTC-USD",
            open=42000.0,
            high=43000.0,
            low=41000.0,
            close=42500.0,
            volume=1000000.0
        )
        assert candle.symbol == "BTC-USD"
        assert candle.close == 42500.0


class TestYahooFinanceFetcher:
    def test_init_with_defaults(self):
        fetcher = YahooFinanceFetcher()
        assert fetcher.get_source_name() == "yahoo_finance"
        assert "BTC-USD" in fetcher.symbols
    
    def test_init_with_custom_symbols(self):
        fetcher = YahooFinanceFetcher({"symbols": ["ETH-USD"]})
        assert fetcher.symbols == ["ETH-USD"]
    
    @pytest.mark.asyncio
    async def test_fetch_returns_candles(self):
        """Test that fetch yields PriceCandle objects."""
        # Skip if yfinance not available
        try:
            import yfinance
        except ImportError:
            pytest.skip("yfinance not installed")
        
        # Create mock DataFrame like yfinance returns
        mock_data = pd.DataFrame({
            'Open': [42000.0, 42100.0],
            'High': [43000.0, 43100.0],
            'Low': [41000.0, 41100.0],
            'Close': [42500.0, 42600.0],
            'Volume': [1000000.0, 1100000.0]
        }, index=pd.to_datetime(['2024-01-01', '2024-01-02']))
        
        fetcher = YahooFinanceFetcher({"symbols": ["BTC-USD"]})
        
        with patch.object(fetcher, '_fetch_symbol', return_value=mock_data):
            candles = []
            async for candle in fetcher.fetch(
                datetime(2024, 1, 1),
                datetime(2024, 1, 3)
            ):
                candles.append(candle)
            
            assert len(candles) == 2
            assert all(isinstance(c, PriceCandle) for c in candles)
            assert candles[0].close == 42500.0
            assert candles[1].close == 42600.0


class TestChronosManager:
    def test_init_with_default_sources(self):
        config = {
            "chronos": {
                "data_sources": ["yahoo_finance"]
            }
        }
        manager = ChronosManager(config)
        assert len(manager.fetchers) == 1
        assert isinstance(manager.fetchers[0], YahooFinanceFetcher)
    
    def test_init_with_multiple_sources(self):
        config = {
            "chronos": {
                "data_sources": ["yahoo_finance", "news_archive"]
            }
        }
        manager = ChronosManager(config)
        assert len(manager.fetchers) == 2
    
    def test_init_skips_unknown_source(self):
        config = {
            "chronos": {
                "data_sources": ["unknown_source"]
            }
        }
        manager = ChronosManager(config)
        assert len(manager.fetchers) == 0
