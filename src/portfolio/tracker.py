"""
Portfolio Tracker

Tracks portfolio value, PnL, and performance metrics over time.
"""

import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Optional
import math

from src.utils.db import Database


@dataclass
class PortfolioSnapshot:
    """A point-in-time snapshot of portfolio state."""
    timestamp: datetime
    balance: float
    pnl_daily: float
    pnl_total: float
    trade_count: int
    win_count: int
    loss_count: int
    win_rate: float


class PortfolioTracker:
    """
    Tracks portfolio performance over time.
    
    Records daily snapshots and calculates running metrics.
    """
    
    def __init__(self, db: Database = None, initial_balance: float = 100000.0):
        self.logger = logging.getLogger("hedgemony.portfolio.tracker")
        self.db = db or Database()
        self.initial_balance = initial_balance
    
    def record_snapshot(self) -> PortfolioSnapshot:
        """
        Record current portfolio state as a snapshot.
        
        Calculates metrics from trades table.
        """
        # Get all trades
        trades = self.db.get_recent_trades(limit=10000)
        
        # Calculate metrics
        total_pnl = sum(t.get('pnl', 0) for t in trades)
        balance = self.initial_balance + total_pnl
        
        # Daily PnL (trades from today)
        today = datetime.now().date()
        daily_trades = [
            t for t in trades 
            if self._parse_date(t.get('timestamp', '')).date() == today
        ]
        daily_pnl = sum(t.get('pnl', 0) for t in daily_trades)
        
        # Win/loss counts
        win_count = sum(1 for t in trades if t.get('pnl', 0) > 0)
        loss_count = sum(1 for t in trades if t.get('pnl', 0) < 0)
        trade_count = len(trades)
        win_rate = (win_count / trade_count * 100) if trade_count > 0 else 0
        
        snapshot = PortfolioSnapshot(
            timestamp=datetime.now(),
            balance=balance,
            pnl_daily=daily_pnl,
            pnl_total=total_pnl,
            trade_count=trade_count,
            win_count=win_count,
            loss_count=loss_count,
            win_rate=win_rate
        )
        
        # Save to database
        self._save_snapshot(snapshot)
        
        return snapshot
    
    def _parse_date(self, timestamp) -> datetime:
        """Parse timestamp to datetime."""
        if isinstance(timestamp, datetime):
            return timestamp
        if isinstance(timestamp, str):
            try:
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            except:
                return datetime.now()
        return datetime.now()
    
    def _save_snapshot(self, snapshot: PortfolioSnapshot):
        """Save snapshot to database."""
        try:
            conn = self.db.get_connection()
            c = conn.cursor()
            c.execute('''
                INSERT INTO portfolio_snapshots 
                (timestamp, balance, pnl_daily, pnl_total, trade_count, win_count, loss_count, win_rate)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                snapshot.timestamp,
                snapshot.balance,
                snapshot.pnl_daily,
                snapshot.pnl_total,
                snapshot.trade_count,
                snapshot.win_count,
                snapshot.loss_count,
                snapshot.win_rate
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Failed to save snapshot: {e}")
    
    def get_snapshots(self, days: int = 30) -> List[dict]:
        """Get portfolio snapshots for the last N days."""
        try:
            conn = self.db.get_connection()
            import sqlite3
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            
            since = datetime.now() - timedelta(days=days)
            c.execute('''
                SELECT * FROM portfolio_snapshots 
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            ''', (since,))
            
            rows = [dict(row) for row in c.fetchall()]
            conn.close()
            return rows
        except Exception as e:
            self.logger.error(f"Failed to get snapshots: {e}")
            return []
    
    def get_current_stats(self) -> dict:
        """Get current portfolio statistics."""
        trades = self.db.get_recent_trades(limit=10000)
        
        if not trades:
            return {
                'balance': self.initial_balance,
                'total_pnl': 0,
                'total_pnl_pct': 0,
                'trade_count': 0,
                'win_rate': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0
            }
        
        # Basic stats
        pnls = [t.get('pnl', 0) for t in trades]
        total_pnl = sum(pnls)
        balance = self.initial_balance + total_pnl
        
        win_count = sum(1 for p in pnls if p > 0)
        win_rate = (win_count / len(trades) * 100) if trades else 0
        
        # Sharpe ratio
        if len(pnls) > 1:
            avg_return = sum(pnls) / len(pnls)
            variance = sum((p - avg_return) ** 2 for p in pnls) / len(pnls)
            std_dev = math.sqrt(variance) if variance > 0 else 1
            sharpe = (avg_return / std_dev) * math.sqrt(252) if std_dev > 0 else 0
        else:
            sharpe = 0
        
        # Max drawdown
        peak = self.initial_balance
        max_dd = 0
        running_balance = self.initial_balance
        
        for pnl in pnls:
            running_balance += pnl
            if running_balance > peak:
                peak = running_balance
            dd = (peak - running_balance) / peak * 100 if peak > 0 else 0
            max_dd = max(max_dd, dd)
        
        return {
            'balance': round(balance, 2),
            'total_pnl': round(total_pnl, 2),
            'total_pnl_pct': round(total_pnl / self.initial_balance * 100, 2),
            'trade_count': len(trades),
            'win_rate': round(win_rate, 1),
            'sharpe_ratio': round(sharpe, 2),
            'max_drawdown': round(max_dd, 2)
        }
