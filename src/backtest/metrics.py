"""
Performance metrics for backtesting.
"""

from dataclasses import dataclass
from typing import List
import math


@dataclass
class BacktestMetrics:
    """Container for backtest performance metrics."""
    total_pnl: float
    total_pnl_pct: float
    win_rate: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    max_drawdown: float
    max_drawdown_pct: float
    sharpe_ratio: float
    avg_trade_pnl: float
    best_trade: float
    worst_trade: float


def calculate_metrics(
    trades: List[dict],
    initial_balance: float = 100000.0,
    risk_free_rate: float = 0.02
) -> BacktestMetrics:
    """
    Calculate performance metrics from a list of trades.
    
    Args:
        trades: List of trade dicts with keys: pnl, timestamp
        initial_balance: Starting portfolio balance
        risk_free_rate: Annual risk-free rate for Sharpe calculation
        
    Returns:
        BacktestMetrics object with all calculated metrics
    """
    if not trades:
        return BacktestMetrics(
            total_pnl=0.0,
            total_pnl_pct=0.0,
            win_rate=0.0,
            total_trades=0,
            winning_trades=0,
            losing_trades=0,
            max_drawdown=0.0,
            max_drawdown_pct=0.0,
            sharpe_ratio=0.0,
            avg_trade_pnl=0.0,
            best_trade=0.0,
            worst_trade=0.0
        )
    
    # Extract PnLs
    pnls = [t.get('pnl', 0) for t in trades]
    
    # Basic stats
    total_pnl = sum(pnls)
    total_pnl_pct = (total_pnl / initial_balance) * 100
    total_trades = len(trades)
    
    winning_trades = sum(1 for p in pnls if p > 0)
    losing_trades = sum(1 for p in pnls if p < 0)
    win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
    
    avg_trade_pnl = total_pnl / total_trades if total_trades > 0 else 0
    best_trade = max(pnls) if pnls else 0
    worst_trade = min(pnls) if pnls else 0
    
    # Max Drawdown
    peak = initial_balance
    max_dd = 0
    max_dd_pct = 0
    balance = initial_balance
    
    for pnl in pnls:
        balance += pnl
        if balance > peak:
            peak = balance
        drawdown = peak - balance
        drawdown_pct = (drawdown / peak) * 100 if peak > 0 else 0
        if drawdown > max_dd:
            max_dd = drawdown
            max_dd_pct = drawdown_pct
    
    # Sharpe Ratio (simplified daily)
    if len(pnls) > 1:
        avg_return = sum(pnls) / len(pnls)
        variance = sum((p - avg_return) ** 2 for p in pnls) / len(pnls)
        std_dev = math.sqrt(variance) if variance > 0 else 1
        
        # Annualize (assume 252 trading days)
        daily_rf = risk_free_rate / 252
        sharpe = ((avg_return / initial_balance) - daily_rf) / (std_dev / initial_balance) if std_dev > 0 else 0
        sharpe = sharpe * math.sqrt(252)  # Annualize
    else:
        sharpe = 0.0
    
    return BacktestMetrics(
        total_pnl=round(total_pnl, 2),
        total_pnl_pct=round(total_pnl_pct, 2),
        win_rate=round(win_rate, 2),
        total_trades=total_trades,
        winning_trades=winning_trades,
        losing_trades=losing_trades,
        max_drawdown=round(max_dd, 2),
        max_drawdown_pct=round(max_dd_pct, 2),
        sharpe_ratio=round(sharpe, 2),
        avg_trade_pnl=round(avg_trade_pnl, 2),
        best_trade=round(best_trade, 2),
        worst_trade=round(worst_trade, 2)
    )


def format_metrics(metrics: BacktestMetrics) -> str:
    """Format metrics for display."""
    return f"""
╔══════════════════════════════════════╗
║        BACKTEST RESULTS              ║
╠══════════════════════════════════════╣
║  Total PnL:      ${metrics.total_pnl:>12,.2f}     ║
║  Return:         {metrics.total_pnl_pct:>12.2f}%    ║
║  Sharpe Ratio:   {metrics.sharpe_ratio:>12.2f}     ║
╠══════════════════════════════════════╣
║  Total Trades:   {metrics.total_trades:>12}     ║
║  Win Rate:       {metrics.win_rate:>12.1f}%    ║
║  Winning:        {metrics.winning_trades:>12}     ║
║  Losing:         {metrics.losing_trades:>12}     ║
╠══════════════════════════════════════╣
║  Best Trade:     ${metrics.best_trade:>12,.2f}     ║
║  Worst Trade:    ${metrics.worst_trade:>12,.2f}     ║
║  Avg Trade:      ${metrics.avg_trade_pnl:>12,.2f}     ║
╠══════════════════════════════════════╣
║  Max Drawdown:   ${metrics.max_drawdown:>12,.2f}     ║
║  Max DD %:       {metrics.max_drawdown_pct:>12.2f}%    ║
╚══════════════════════════════════════╝
"""
