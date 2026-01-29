"""
Backtesting Engine - Core simulation logic.

Iterates through historical data and simulates trading.
"""

import logging
from datetime import datetime
from typing import List, Dict, Optional, Type
from dataclasses import dataclass, field

from .strategy import Strategy, Signal
from .metrics import calculate_metrics, BacktestMetrics
from src.utils.db import Database


@dataclass
class BacktestTrade:
    """Record of a simulated trade."""
    timestamp: datetime
    symbol: str
    side: str
    entry_price: float
    exit_price: float = 0.0
    quantity: float = 0.0
    pnl: float = 0.0
    confidence: float = 0.0
    reason: str = ""
    status: str = 'open'


@dataclass 
class BacktestResult:
    """Complete backtest results."""
    strategy_name: str
    symbol: str
    start_date: datetime
    end_date: datetime
    initial_balance: float
    final_balance: float
    trades: List[BacktestTrade]
    metrics: BacktestMetrics


class BacktestEngine:
    """
    Core backtesting engine.
    
    Loads historical data, runs strategy, and simulates trades.
    """
    
    def __init__(
        self, 
        strategy: Strategy,
        db: Database = None,
        initial_balance: float = 100000.0,
        position_size_pct: float = 0.05
    ):
        self.logger = logging.getLogger("hedgemony.backtest.engine")
        self.strategy = strategy
        self.db = db or Database()
        self.initial_balance = initial_balance
        self.position_size_pct = position_size_pct
        
        # State
        self.balance = initial_balance
        self.position = None  # Current open position
        self.trades: List[BacktestTrade] = []
        
    def reset(self):
        """Reset engine state for new backtest."""
        self.balance = self.initial_balance
        self.position = None
        self.trades = []
        self.strategy.reset()
        
    def run(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        sentiment_data: Optional[List[dict]] = None
    ) -> BacktestResult:
        """
        Run backtest for a symbol over date range.
        
        Args:
            symbol: Trading symbol (e.g., 'BTC-USD')
            start_date: Start of backtest period
            end_date: End of backtest period
            sentiment_data: Optional list of sentiment signals by date
            
        Returns:
            BacktestResult with all trades and metrics
        """
        self.reset()
        
        self.logger.info(f"Starting backtest: {symbol} from {start_date} to {end_date}")
        self.logger.info(f"Strategy: {self.strategy.name}")
        
        # Load price history
        price_data = self.db.get_price_history(
            symbol=symbol,
            start=start_date,
            end=end_date
        )
        
        if not price_data:
            self.logger.warning(f"No price data found for {symbol}")
            return self._build_result(symbol, start_date, end_date)
        
        self.logger.info(f"Loaded {len(price_data)} price candles")
        
        # Build sentiment lookup by date if provided
        sentiment_lookup = {}
        if sentiment_data:
            for s in sentiment_data:
                date_key = s.get('timestamp', s.get('date'))
                if date_key:
                    if isinstance(date_key, str):
                        date_key = datetime.fromisoformat(date_key).date()
                    elif isinstance(date_key, datetime):
                        date_key = date_key.date()
                    sentiment_lookup[date_key] = s
        
        # Iterate through candles
        for candle in price_data:
            timestamp = candle['timestamp']
            if isinstance(timestamp, str):
                timestamp = datetime.fromisoformat(timestamp)
            
            # Get sentiment for this date
            candle_date = timestamp.date() if isinstance(timestamp, datetime) else timestamp
            sentiment = sentiment_lookup.get(candle_date)
            
            # Build candle dict for strategy
            candle_dict = {
                'timestamp': timestamp,
                'symbol': symbol,
                'open': candle['open'],
                'high': candle['high'],
                'low': candle['low'],
                'close': candle['close'],
                'volume': candle['volume']
            }
            
            # Get strategy signal
            signal = self.strategy.on_candle(candle_dict, sentiment)
            
            # Process signal
            if signal:
                self._process_signal(signal, candle_dict)
        
        # Close any open position at end
        if self.position and price_data:
            last_candle = price_data[-1]
            self._close_position(last_candle['close'], "End of backtest")
        
        return self._build_result(symbol, start_date, end_date)
    
    def _process_signal(self, signal: Signal, candle: dict):
        """Process a trading signal."""
        current_price = candle['close']
        
        # If we have an open position
        if self.position:
            # Check if signal is opposite (close position)
            if signal.side != self.position.side:
                self._close_position(current_price, signal.reason)
                # Open new position in opposite direction
                self._open_position(signal, current_price)
        else:
            # No position, open one
            self._open_position(signal, current_price)
    
    def _open_position(self, signal: Signal, price: float):
        """Open a new position."""
        trade_amount = self.balance * self.position_size_pct
        quantity = trade_amount / price
        
        self.position = BacktestTrade(
            timestamp=signal.timestamp,
            symbol=signal.symbol,
            side=signal.side,
            entry_price=price,
            quantity=quantity,
            confidence=signal.confidence,
            reason=signal.reason,
            status='open'
        )
        
        self.logger.debug(
            f"OPEN {signal.side.upper()} {signal.symbol} @ ${price:,.2f} "
            f"(qty: {quantity:.6f}, reason: {signal.reason})"
        )
    
    def _close_position(self, price: float, reason: str):
        """Close current position and calculate PnL."""
        if not self.position:
            return
            
        self.position.exit_price = price
        self.position.status = 'closed'
        
        # Calculate PnL
        if self.position.side == 'buy':
            pnl = (price - self.position.entry_price) * self.position.quantity
        else:  # sell/short
            pnl = (self.position.entry_price - price) * self.position.quantity
            
        self.position.pnl = pnl
        self.balance += pnl
        
        self.trades.append(self.position)
        
        self.logger.debug(
            f"CLOSE {self.position.side.upper()} {self.position.symbol} @ ${price:,.2f} "
            f"(PnL: ${pnl:,.2f}, reason: {reason})"
        )
        
        self.position = None
    
    def _build_result(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> BacktestResult:
        """Build final backtest result."""
        # Convert trades to dicts for metrics
        trade_dicts = [
            {'pnl': t.pnl, 'timestamp': t.timestamp}
            for t in self.trades
        ]
        
        metrics = calculate_metrics(
            trades=trade_dicts,
            initial_balance=self.initial_balance
        )
        
        return BacktestResult(
            strategy_name=self.strategy.name,
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            initial_balance=self.initial_balance,
            final_balance=self.balance,
            trades=self.trades,
            metrics=metrics
        )
