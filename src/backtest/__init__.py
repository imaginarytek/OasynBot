"""
Backtest - Professional Strategy Testing Module

Tests trading strategies against historical event data with bias-free simulation.
"""

# Core Components
from .data_access import EventDataAccess, Event
from .metrics import calculate_metrics, format_metrics, BacktestMetrics

# Strategy Framework
from .strategy import (
    Strategy,
    EventStrategy,
    Signal,
    # Event-Driven Strategies
    VerbatimSentimentStrategy,
    SimpleEventStrategy,
    # Legacy Candle-Based (kept for compatibility)
    SentimentStrategy,
    MomentumStrategy
)

# Engines
from .hardcore_engine import StrategyTester as HardcoreEngine

__all__ = [
    # Data Access
    'EventDataAccess',
    'Event',
    # Metrics
    'calculate_metrics',
    'format_metrics',
    'BacktestMetrics',
    # Strategy Framework
    'Strategy',
    'EventStrategy',
    'Signal',
    # Event-Driven Strategies
    'VerbatimSentimentStrategy',
    'SimpleEventStrategy',
    # Legacy Candle-Based Strategies (kept for compatibility)
    'SentimentStrategy',
    'MomentumStrategy',
    # Engines
    'HardcoreEngine',
]
