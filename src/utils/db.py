import sqlite3
import json
from datetime import datetime
import logging

class Database:
    def __init__(self, db_path="data/hedgemony.db"):
        self.db_path = db_path
        self.logger = logging.getLogger("hedgemony.db")

    def get_connection(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def init_db(self):
        conn = self.get_connection()
        c = conn.cursor()
        
        # News Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS news (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_id TEXT,
                title TEXT,
                published_at TIMESTAMP,
                sentiment_score REAL,
                sentiment_label TEXT,
                confidence REAL,
                impact_score INTEGER DEFAULT 0,
                ingested_at TIMESTAMP,
                raw_data TEXT
            )
        ''')
        
        # Trades Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP,
                symbol TEXT,
                side TEXT,
                price REAL,
                quantity REAL,
                confidence REAL,
                pnl REAL DEFAULT 0.0,
                status TEXT
            )
        ''')
        
        # Price History Table (Chronos)
        c.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP,
                symbol TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                UNIQUE(timestamp, symbol)
            )
        ''')
        
        # Portfolio Snapshots Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP,
                balance REAL,
                pnl_daily REAL,
                pnl_total REAL,
                trade_count INTEGER,
                win_count INTEGER,
                loss_count INTEGER,
                win_rate REAL
            )
        ''')
        
        conn.commit()
        conn.close()
        self.logger.info(f"Database initialized at {self.db_path}")

    def log_news(self, item, analysis):
        try:
            conn = self.get_connection()
            c = conn.cursor()
            
            # Check if column exists (migration for v1)
            # Simple hack: just try to insert, if fails, we might need to alter table, 
            # but for this MVP iteration, assuming user can wipe DB or we handle it.
            # Let's just create table if not exists, but if it exists without column we have an issue.
            # Doing a quick "ALTER TABLE" check is better.
            try:
                c.execute("ALTER TABLE news ADD COLUMN ingested_at TIMESTAMP")
            except Exception:
                pass

            c.execute('''
                INSERT INTO news (source_id, title, published_at, sentiment_score, sentiment_label, confidence, impact_score, ingested_at, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                item.source_id,
                item.title,
                item.published_at,
                analysis['score'],
                analysis['label'],
                analysis['confidence'],
                item.impact_score,
                item.ingested_at,
                json.dumps(item.raw_data) if item.raw_data else "{}"
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Failed to log news: {e}")

    def log_trade(self, trade):
        try:
            conn = self.get_connection()
            c = conn.cursor()
            c.execute('''
                INSERT INTO trades (timestamp, symbol, side, price, quantity, confidence, pnl, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                trade.timestamp,
                trade.symbol,
                trade.side,
                trade.price,
                trade.quantity,
                trade.confidence,
                trade.pnl,
                trade.status
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Failed to log trade: {e}")

    def get_recent_news(self, limit=50):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM news ORDER BY published_at DESC LIMIT ?', (limit,))
        rows = [dict(row) for row in c.fetchall()]
        conn.close()
        return rows
    
    def get_news_by_date_range(self, start: datetime, end: datetime):
        """Retrieve news items within a specific date range."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Adjust query to handle ISO strings or datetime objects
        start_str = start.isoformat() if isinstance(start, datetime) else str(start)
        end_str = end.isoformat() if isinstance(end, datetime) else str(end)
        
        c.execute('''
            SELECT * FROM news 
            WHERE published_at >= ? AND published_at <= ?
            ORDER BY published_at ASC
        ''', (start_str, end_str))
        
        rows = [dict(row) for row in c.fetchall()]
        conn.close()
        return rows
    
    def get_recent_trades(self, limit=50):
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute('SELECT * FROM trades ORDER BY timestamp DESC LIMIT ?', (limit,))
        rows = [dict(row) for row in c.fetchall()]
        conn.close()
        return rows


    def log_price_candle(self, candle):
        """Log a price candle from Chronos historical fetch."""
        try:
            conn = self.get_connection()
            c = conn.cursor()
            c.execute('''
                INSERT OR REPLACE INTO price_history 
                (timestamp, symbol, open, high, low, close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                candle.timestamp,
                candle.symbol,
                candle.open,
                candle.high,
                candle.low,
                candle.close,
                candle.volume
            ))
            conn.commit()
            conn.close()
        except Exception as e:
            self.logger.error(f"Failed to log price candle: {e}")

    def get_price_history(self, symbol, start=None, end=None, limit=1000):
        """Retrieve price history for a symbol."""
        conn = self.get_connection()
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        query = 'SELECT * FROM price_history WHERE symbol = ?'
        params = [symbol]
        
        if start:
            # Convert datetime to string if needed
            if hasattr(start, 'strftime'):
                start = start.strftime('%Y-%m-%d')
            query += ' AND date(timestamp) >= date(?)'
            params.append(start)
        if end:
            # Convert datetime to string if needed
            if hasattr(end, 'strftime'):
                end = end.strftime('%Y-%m-%d')
            query += ' AND date(timestamp) <= date(?)'
            params.append(end)
            
        query += ' ORDER BY timestamp ASC LIMIT ?'
        params.append(limit)
        
        c.execute(query, params)
        rows = [dict(row) for row in c.fetchall()]
        conn.close()
        return rows

