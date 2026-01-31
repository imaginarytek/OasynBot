#!/usr/bin/env python3
"""
Event-Driven Backtest - Bias-Free Historical Testing

This script demonstrates the complete event-driven backtesting workflow:
1. Load events from hedgemony.db (input database ONLY)
2. Feed events to strategy (verbatim text analysis)
3. Simulate realistic execution (latency + slippage)
4. Calculate performance metrics
5. Generate report

CRITICAL: This script NEVER accesses hedgemony_validation.db
All trading decisions are made using ONLY input data (what traders saw).
"""

import sys
import os
import logging
import argparse
from datetime import datetime
from typing import List

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from src.backtest.data_access import EventDataAccess, Event
from src.backtest.strategy import VerbatimSentimentStrategy, SimpleEventStrategy


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("hedgemony.event_backtest")


class EventBacktestResult:
    """Results from event-driven backtest."""

    def __init__(
        self,
        strategy_name: str,
        initial_balance: float,
        symbol: str = 'SOL-USD'
    ):
        self.strategy_name = strategy_name
        self.initial_balance = initial_balance
        self.symbol = symbol
        self.balance = initial_balance

        self.trades = []
        self.event_count = 0
        self.signals_generated = 0

    def record_trade(
        self,
        event: Event,
        side: str,
        entry_price: float,
        exit_price: float,
        confidence: float,
        reason: str
    ):
        """Record a completed trade."""
        # Calculate P&L
        if side == 'buy':
            pnl_pct = (exit_price - entry_price) / entry_price
        else:  # sell/short
            pnl_pct = (entry_price - exit_price) / entry_price

        # Calculate position size (10% of portfolio * confidence)
        position_value = self.balance * 0.1 * confidence
        pnl_dollars = position_value * pnl_pct

        # Update balance
        self.balance += pnl_dollars

        # Record trade
        self.trades.append({
            'event_id': event.id,
            'event_title': event.title,
            'timestamp': event.timestamp,
            'side': side,
            'entry_price': entry_price,
            'exit_price': exit_price,
            'pnl_pct': pnl_pct * 100,
            'pnl_dollars': pnl_dollars,
            'confidence': confidence,
            'reason': reason
        })

    def print_summary(self):
        """Print backtest results summary."""
        print("\n" + "=" * 80)
        print(f"EVENT-DRIVEN BACKTEST RESULTS: {self.strategy_name}")
        print("=" * 80)

        print(f"\nDataset:")
        print(f"  Total Events: {self.event_count}")
        print(f"  Signals Generated: {self.signals_generated}")
        print(f"  Trade Rate: {self.signals_generated / max(self.event_count, 1) * 100:.1f}%")

        print(f"\nPerformance:")
        print(f"  Initial Balance: ${self.initial_balance:,.2f}")
        print(f"  Final Balance:   ${self.balance:,.2f}")

        total_pnl = self.balance - self.initial_balance
        total_pnl_pct = total_pnl / self.initial_balance * 100
        print(f"  Total P&L:       ${total_pnl:,.2f} ({total_pnl_pct:+.2f}%)")

        if self.trades:
            winners = [t for t in self.trades if t['pnl_dollars'] > 0]
            losers = [t for t in self.trades if t['pnl_dollars'] <= 0]

            win_rate = len(winners) / len(self.trades) * 100
            print(f"  Win Rate:        {win_rate:.1f}% ({len(winners)}/{len(self.trades)})")

            if winners:
                avg_win = sum(t['pnl_dollars'] for t in winners) / len(winners)
                print(f"  Avg Win:         ${avg_win:,.2f}")

            if losers:
                avg_loss = sum(t['pnl_dollars'] for t in losers) / len(losers)
                print(f"  Avg Loss:        ${avg_loss:,.2f}")

            if winners and losers:
                win_loss_ratio = avg_win / abs(avg_loss)
                print(f"  Win/Loss Ratio:  {win_loss_ratio:.2f}")

        print("\n" + "-" * 80)
        print("TRADES:")
        print("-" * 80)

        if self.trades:
            for trade in self.trades:
                print(
                    f"{trade['timestamp'].date()} | "
                    f"{trade['side'].upper():4} @ ${trade['entry_price']:,.2f} -> ${trade['exit_price']:,.2f} | "
                    f"P&L: {trade['pnl_pct']:+.2f}% (${trade['pnl_dollars']:+,.2f}) | "
                    f"{trade['event_title'][:50]}"
                )
        else:
            print("No trades executed.")

        print("=" * 80 + "\n")


def run_event_backtest(
    strategy_class,
    strategy_config: dict = None,
    initial_balance: float = 100000.0,
    execution_delay_seconds: int = 0,
    exit_delay_seconds: int = 300,  # Exit 5 minutes after entry
    symbol: str = 'SOL-USD'
):
    """
    Run event-driven backtest.

    Args:
        strategy_class: Strategy class (e.g., VerbatimSentimentStrategy)
        strategy_config: Strategy configuration dict
        initial_balance: Starting portfolio value
        execution_delay_seconds: Simulated execution latency
        exit_delay_seconds: How long to hold position after entry
        symbol: Trading symbol

    Returns:
        EventBacktestResult with all trades and metrics
    """
    logger.info("=" * 80)
    logger.info("EVENT-DRIVEN BACKTEST")
    logger.info("=" * 80)

    # Initialize components
    data_access = EventDataAccess()
    strategy = strategy_class(strategy_config or {})

    logger.info(f"Strategy: {strategy.name}")
    logger.info(f"Initial Balance: ${initial_balance:,.2f}")
    logger.info(f"Execution Delay: {execution_delay_seconds}s")
    logger.info(f"Exit Delay: {exit_delay_seconds}s")

    # Load all events
    logger.info("\nLoading events from hedgemony.db...")
    events = data_access.load_all_events()

    if not events:
        logger.warning("No events found in database!")
        return None

    logger.info(f"Loaded {len(events)} events")

    # Safety check: Verify we're not accidentally using validation DB
    logger.info("\nRunning anti-bias security check...")
    if 'validation' in data_access.db_path.lower():
        raise ValueError(
            "SECURITY VIOLATION: Using validation database! "
            "This would create look-ahead bias."
        )
    logger.info("✓ Security check passed - using input database only")

    # Initialize result tracker
    result = EventBacktestResult(
        strategy_name=strategy.name,
        initial_balance=initial_balance,
        symbol=symbol
    )

    result.event_count = len(events)

    # Iterate through events chronologically
    logger.info("\nSimulating trades...")
    logger.info("-" * 80)

    for event in events:
        logger.info(f"\nEvent {event.id}: {event.title}")
        logger.info(f"  Timestamp: {event.timestamp}")
        logger.info(f"  Source: {event.source}")

        # Get past prices (what would have been available at decision time)
        past_prices = data_access.get_past_prices(event, lookback_seconds=300)

        if past_prices.empty:
            logger.warning("  ⚠ No past price data - skipping")
            continue

        # Feed event to strategy
        signal = strategy.analyze_event(event, past_prices, symbol)

        if signal is None:
            logger.info("  → HOLD (no signal)")
            continue

        result.signals_generated += 1

        logger.info(f"  → SIGNAL: {signal.side.upper()}")
        logger.info(f"     Confidence: {signal.confidence:.2f}")
        logger.info(f"     Reason: {signal.reason}")

        # Get execution price (simulates latency)
        entry_price = data_access.get_execution_price(event, delay_seconds=execution_delay_seconds)

        if entry_price is None:
            logger.warning("  ⚠ No execution price available - skipping")
            continue

        logger.info(f"     Entry Price: ${entry_price:,.2f}")

        # Get exit price (simulates holding period)
        exit_price = data_access.get_execution_price(event, delay_seconds=exit_delay_seconds)

        if exit_price is None:
            logger.warning("  ⚠ No exit price available - skipping")
            continue

        logger.info(f"     Exit Price: ${exit_price:,.2f}")

        # Record trade
        result.record_trade(
            event=event,
            side=signal.side,
            entry_price=entry_price,
            exit_price=exit_price,
            confidence=signal.confidence,
            reason=signal.reason
        )

        # Calculate P&L for this trade
        if signal.side == 'buy':
            pnl_pct = (exit_price - entry_price) / entry_price * 100
        else:
            pnl_pct = (entry_price - exit_price) / entry_price * 100

        logger.info(f"     P&L: {pnl_pct:+.2f}%")

    logger.info("\n" + "=" * 80)

    # Print summary
    result.print_summary()

    return result


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run event-driven backtest using master_events"
    )
    parser.add_argument(
        '--strategy',
        choices=['verbatim_sentiment', 'simple_buy', 'simple_sell'],
        default='verbatim_sentiment',
        help='Strategy to use'
    )
    parser.add_argument(
        '--initial-balance',
        type=float,
        default=100000.0,
        help='Starting portfolio value'
    )
    parser.add_argument(
        '--confidence-threshold',
        type=float,
        default=0.7,
        help='Minimum confidence to trade (for sentiment strategy)'
    )
    parser.add_argument(
        '--execution-delay',
        type=int,
        default=0,
        help='Execution delay in seconds (simulates latency)'
    )
    parser.add_argument(
        '--exit-delay',
        type=int,
        default=300,
        help='Exit delay in seconds (how long to hold position)'
    )

    args = parser.parse_args()

    # Select strategy
    if args.strategy == 'verbatim_sentiment':
        strategy_class = VerbatimSentimentStrategy
        strategy_config = {
            'confidence_threshold': args.confidence_threshold,
            'position_size_pct': 0.1
        }
    elif args.strategy == 'simple_buy':
        strategy_class = SimpleEventStrategy
        strategy_config = {
            'default_side': 'buy',
            'confidence': 0.8,
            'position_size_pct': 0.1
        }
    elif args.strategy == 'simple_sell':
        strategy_class = SimpleEventStrategy
        strategy_config = {
            'default_side': 'sell',
            'confidence': 0.8,
            'position_size_pct': 0.1
        }

    # Run backtest
    result = run_event_backtest(
        strategy_class=strategy_class,
        strategy_config=strategy_config,
        initial_balance=args.initial_balance,
        execution_delay_seconds=args.execution_delay,
        exit_delay_seconds=args.exit_delay
    )

    if result:
        logger.info("Backtest complete!")
    else:
        logger.error("Backtest failed - no events found")
        sys.exit(1)


if __name__ == "__main__":
    main()
