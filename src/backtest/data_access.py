"""
Data Access Layer - Bias-Free Event Loading

CRITICAL: This module ONLY reads from hedgemony.db (input database).
It is FORBIDDEN to access hedgemony_validation.db in any backtest code.

This ensures zero look-ahead bias - the AI cannot see future price movements
or validation metrics when making trading decisions.
"""

import sqlite3
import json
import pandas as pd
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass
import logging


@dataclass
class Event:
    """
    Event data object containing ONLY input fields (no validation metadata).

    This represents what a human trader would have seen at event time:
    - Verbatim event title and description
    - Event timestamp
    - Source information
    - Price data (will be filtered to past-only by strategy)

    CRITICAL: This object does NOT contain:
    - move_5s, move_30s, move_5m (future price movements)
    - time_to_impact_seconds (measured lag to price movement)
    - tradeable, impact_score (post-hoc judgments)
    - quality_level, verified (QA metadata)

    Those fields are in hedgemony_validation.db which bot CANNOT access.
    """
    id: int
    title: str
    description: str
    timestamp: datetime
    source: Optional[str]
    source_url: Optional[str]
    category: Optional[str]
    price_data: Optional[pd.DataFrame]  # Will be filtered to past-only
    date_added: Optional[str]
    last_updated: Optional[str]


class EventDataAccess:
    """
    Data access layer for loading events from input database.

    CRITICAL SECURITY RULES:
    1. ONLY connects to data/hedgemony.db (input database)
    2. NEVER connects to data/hedgemony_validation.db (forbidden)
    3. ONLY reads from master_events table
    4. Returns Event objects with ONLY input fields
    5. Filters price data to show ONLY past prices

    This physical separation prevents the AI from accidentally seeing
    future price movements or validation metrics during backtesting.
    """

    # CRITICAL: Only allow connection to input database
    INPUT_DB_PATH = 'data/hedgemony.db'

    def __init__(self, db_path: str = None):
        """
        Initialize data access layer.

        Args:
            db_path: Path to input database (defaults to hedgemony.db)
                     MUST be input database, never validation database
        """
        self.db_path = db_path or self.INPUT_DB_PATH
        self.logger = logging.getLogger("hedgemony.backtest.data_access")

        # Safety check: Ensure we're NOT accidentally connecting to validation DB
        if 'validation' in self.db_path.lower():
            raise ValueError(
                "SECURITY VIOLATION: Attempted to connect to validation database! "
                "Backtest code must ONLY access input database (hedgemony.db). "
                "This would create look-ahead bias."
            )

        self.logger.info(f"Data access initialized: {self.db_path}")

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection to input database."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def load_all_events(self) -> List[Event]:
        """
        Load ALL events from master_events table.

        Returns events in chronological order (oldest first) for realistic
        backtesting simulation.

        Returns:
            List of Event objects with input fields only
        """
        conn = self.get_connection()

        try:
            rows = conn.execute("""
                SELECT id, title, description, timestamp, source, source_url,
                       category, sol_price_data, date_added, last_updated
                FROM master_events
                ORDER BY timestamp ASC
            """).fetchall()

            events = [self._row_to_event(row) for row in rows]
            self.logger.info(f"Loaded {len(events)} events from {self.db_path}")

            return events

        finally:
            conn.close()

    def load_events_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[Event]:
        """
        Load events within a specific date range.

        Args:
            start_date: Start of date range (inclusive)
            end_date: End of date range (inclusive)

        Returns:
            List of Event objects in chronological order
        """
        conn = self.get_connection()

        try:
            start_str = start_date.isoformat()
            end_str = end_date.isoformat()

            rows = conn.execute("""
                SELECT id, title, description, timestamp, source, source_url,
                       category, sol_price_data, date_added, last_updated
                FROM master_events
                WHERE timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp ASC
            """, (start_str, end_str)).fetchall()

            events = [self._row_to_event(row) for row in rows]
            self.logger.info(
                f"Loaded {len(events)} events between "
                f"{start_date.date()} and {end_date.date()}"
            )

            return events

        finally:
            conn.close()

    def load_event_by_id(self, event_id: int) -> Optional[Event]:
        """
        Load a specific event by ID.

        Args:
            event_id: Event ID from master_events table

        Returns:
            Event object or None if not found
        """
        conn = self.get_connection()

        try:
            row = conn.execute("""
                SELECT id, title, description, timestamp, source, source_url,
                       category, sol_price_data, date_added, last_updated
                FROM master_events
                WHERE id = ?
            """, (event_id,)).fetchone()

            if row:
                return self._row_to_event(row)
            else:
                self.logger.warning(f"Event {event_id} not found")
                return None

        finally:
            conn.close()

    def _row_to_event(self, row: sqlite3.Row) -> Event:
        """
        Convert database row to Event object.

        Parses timestamp and price data, but does NOT filter price data yet.
        Price filtering happens in strategy layer to show only past prices.
        """
        # Parse timestamp
        timestamp_str = row['timestamp']
        timestamp = pd.to_datetime(timestamp_str)
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize('UTC')

        # Parse price data if available
        price_data = None
        if row['sol_price_data']:
            try:
                price_json = json.loads(row['sol_price_data'])
                df = pd.DataFrame(price_json)
                df['timestamp'] = pd.to_datetime(df['timestamp'])

                # Normalize timezone
                if df['timestamp'].dt.tz is None:
                    df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')

                # Convert price columns to numeric
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col])

                price_data = df

            except (json.JSONDecodeError, ValueError) as e:
                self.logger.warning(
                    f"Failed to parse price data for event {row['id']}: {e}"
                )

        return Event(
            id=row['id'],
            title=row['title'],
            description=row['description'],
            timestamp=timestamp,
            source=row['source'],
            source_url=row['source_url'],
            category=row['category'],
            price_data=price_data,
            date_added=row['date_added'],
            last_updated=row['last_updated']
        )

    def get_past_prices(
        self,
        event: Event,
        lookback_seconds: int = 300
    ) -> pd.DataFrame:
        """
        Get price data BEFORE the event timestamp.

        This is the anti-cheat mechanism - strategy sees ONLY past prices,
        simulating what would have been available at decision time.

        Args:
            event: Event object
            lookback_seconds: How many seconds of past data to include (default 5min)

        Returns:
            DataFrame of price candles BEFORE event timestamp
        """
        if event.price_data is None or event.price_data.empty:
            return pd.DataFrame()

        # Filter to ONLY prices before event
        past_df = event.price_data[
            event.price_data['timestamp'] < event.timestamp
        ].copy()

        # Optionally limit to lookback window
        if lookback_seconds and not past_df.empty:
            lookback_start = event.timestamp - pd.Timedelta(seconds=lookback_seconds)
            past_df = past_df[past_df['timestamp'] >= lookback_start]

        return past_df

    def get_execution_price(self, event: Event, delay_seconds: int = 0) -> Optional[float]:
        """
        Get realistic execution price AFTER the event.

        Simulates latency: uses first available price candle after event timestamp
        plus an optional execution delay.

        Args:
            event: Event object
            delay_seconds: Additional execution delay to simulate (default 0)

        Returns:
            Execution price (close of first candle after event + delay) or None
        """
        if event.price_data is None or event.price_data.empty:
            return None

        # Calculate execution time (event time + delay)
        execution_time = event.timestamp + pd.Timedelta(seconds=delay_seconds)

        # Find first candle at or after execution time
        future_df = event.price_data[
            event.price_data['timestamp'] >= execution_time
        ]

        if future_df.empty:
            self.logger.warning(
                f"No price data available after event {event.id} + delay {delay_seconds}s"
            )
            return None

        # Return close price of first candle (realistic execution)
        return float(future_df.iloc[0]['close'])

    def count_events(self) -> int:
        """
        Count total number of events in database.

        Useful for validation and reporting.
        """
        conn = self.get_connection()

        try:
            count = conn.execute("SELECT COUNT(*) FROM master_events").fetchone()[0]
            return count
        finally:
            conn.close()

    def get_event_date_range(self) -> tuple[Optional[datetime], Optional[datetime]]:
        """
        Get earliest and latest event timestamps in database.

        Returns:
            Tuple of (earliest, latest) datetime or (None, None) if no events
        """
        conn = self.get_connection()

        try:
            row = conn.execute("""
                SELECT MIN(timestamp) as earliest, MAX(timestamp) as latest
                FROM master_events
            """).fetchone()

            if row['earliest'] and row['latest']:
                earliest = pd.to_datetime(row['earliest'])
                latest = pd.to_datetime(row['latest'])
                return (earliest, latest)
            else:
                return (None, None)

        finally:
            conn.close()


# Anti-Bias Validation Function
def validate_no_validation_db_access():
    """
    Security check: Ensure backtest code is not importing validation database.

    Run this at startup to verify the codebase is not accidentally accessing
    hedgemony_validation.db during backtesting.

    Raises:
        SecurityError if validation DB access is detected
    """
    import sys
    import os

    # Check if validation DB file path appears anywhere in loaded modules
    validation_db = 'hedgemony_validation.db'

    for module_name, module in sys.modules.items():
        if module and hasattr(module, '__file__') and module.__file__:
            try:
                with open(module.__file__, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if validation_db in content:
                        raise SecurityError(
                            f"SECURITY VIOLATION: Module '{module_name}' references "
                            f"validation database! This would create look-ahead bias. "
                            f"Remove all references to {validation_db} from backtest code."
                        )
            except (IOError, UnicodeDecodeError):
                pass  # Skip binary files or unreadable files


class SecurityError(Exception):
    """Raised when look-ahead bias security violation is detected."""
    pass
