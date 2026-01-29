"""
Backtest - Strategy Testing Module

Tests trading strategies against historical data from Chronos.
"""

from .engine import BacktestEngine
from .strategy import Strategy, SentimentStrategy
from .metrics import calculate_metrics

__all__ = [
    'BacktestEngine',
    'Strategy',
    'SentimentStrategy',
    'calculate_metrics',
]
