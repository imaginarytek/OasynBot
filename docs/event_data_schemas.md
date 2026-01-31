# Database Schemas & API Response Shapes

This document defines all data structures used in HedgemonyBot.

## Database Tables

### `news`

Stores raw news items from all ingestion sources.

```sql
CREATE TABLE news (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT,              -- Unique ID from source (e.g., RSS guid)
    title TEXT,                  -- Headline
    published_at TIMESTAMP,      -- When news was published
    sentiment_score REAL,        -- -1 to +1 (negative to positive)
    sentiment_label TEXT,        -- 'positive', 'negative', 'neutral'
    confidence REAL,             -- 0 to 1 (AI confidence)
    impact_score INTEGER DEFAULT 0,  -- 1-10 scale (7-10 for tradeable events)
    ingested_at TIMESTAMP,       -- When we fetched it
    raw_data TEXT                -- JSON blob of original data
)
```

**Indexes:**
- `published_at` - For time-range queries
- `source_id` - For deduplication

---

### `master_events`

**Purpose:** The unified, verified dataset used for all backtesting. It combines data from all other sources, filtered by quality.

```sql
CREATE TABLE master_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Event Information
    title TEXT NOT NULL,
    description TEXT,
    timestamp TEXT NOT NULL,  -- ISO format with timezone
    source TEXT,
    source_url TEXT,
    category TEXT,
    
    -- Quality Metadata
    quality_level INTEGER,    -- 0=archive, 1=normal, 2=high-impact
    methodology TEXT,         -- 'event-first' or 'spike-first'
    verified BOOLEAN DEFAULT 1,
    timestamp_precision TEXT, -- 'hour', 'minute', 'second'
    
    -- Price Data (1-second resolution)
    sol_price_data TEXT,
    
    -- Price Impact Metrics
    move_5s REAL,
    move_30s REAL,
    move_5m REAL,
    move_30m REAL,
    move_1h REAL,
    volatility_z_score REAL,
    time_to_impact_seconds INTEGER,  -- Diagnostic only (Time from News to Market Move)
    
    -- Tracking
    impact_score INTEGER,
    tradeable BOOLEAN DEFAULT 1,
    date_added TEXT,
    last_updated TEXT,
    
    UNIQUE(title, timestamp)
)
```

**Quality Levels:**
- **Level 2 (High-Impact):** Validated with `time_to_impact_seconds` (<60s) for causality.
- **Level 1 (Normal):** Good for general testing, may lack precise 1s lag measurement.
- **Level 0 (Archive):** Low quality, use with caution.

---

### `trades`

Logs all executed trades (both backtest and live).

```sql
CREATE TABLE trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP,         -- When trade was executed
    symbol TEXT,                 -- e.g., 'SOL/USD', 'BTC/USD'
    side TEXT,                   -- 'buy' or 'sell'
    price REAL,                  -- Entry price
    quantity REAL,               -- Position size
    confidence REAL,             -- AI confidence that triggered trade
    pnl REAL DEFAULT 0.0,        -- Profit/Loss in USD
    status TEXT                  -- 'filled', 'pending', 'cancelled'
)
```

**Indexes:**
- `timestamp` - For performance analysis
- `symbol` - For per-asset analytics

---

### `price_history`

Stores OHLCV candles for backtesting and analysis.

```sql
CREATE TABLE price_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP,
    symbol TEXT,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    volume REAL,
    UNIQUE(timestamp, symbol)    -- Prevent duplicates
)
```

**Indexes:**
- `(symbol, timestamp)` - For fast time-series queries

**Data Sources:**
- Binance API (1m, 5m, 1h candles)
- Hyperliquid API (1s candles for high-fidelity events)

---

### `portfolio_snapshots`

Tracks portfolio performance over time.

```sql
CREATE TABLE portfolio_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP,
    balance REAL,                -- Total account balance
    pnl_daily REAL,              -- Daily P&L
    pnl_total REAL,              -- Cumulative P&L
    trade_count INTEGER,         -- Total trades executed
    win_count INTEGER,           -- Winning trades
    loss_count INTEGER,          -- Losing trades
    win_rate REAL                -- win_count / trade_count
)
```

---

### `curated_events`

High-quality, manually verified news events for backtesting.

```sql
CREATE TABLE curated_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP,         -- Event publication time
    title TEXT,                  -- Headline
    verbatim_text TEXT,          -- Exact text from Tier 1 source
    source TEXT,                 -- e.g., 'Bloomberg', 'Reuters'
    impact_score INTEGER,        -- 7-10 (only high-impact events)
    ai_score REAL,               -- Sentiment score from LLM
    ai_confidence REAL,          -- Confidence from LLM
    price_data TEXT,             -- JSON: BTC 1s price data (120 min)
    sol_price_data TEXT,         -- JSON: SOL 1s price data (120 min)
    notes TEXT                   -- Manual annotations
)
```

**Purpose:** Gold-standard dataset for strategy validation.

---

### `gold_events` (Legacy)

Earlier version of curated events. Being migrated to `curated_events`.

---

### `hourly_volatility_spikes`

Detected high-volatility periods for event mining.

```sql
CREATE TABLE hourly_volatility_spikes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP,
    symbol TEXT,
    volatility REAL,             -- % price range in that hour
    volume REAL,
    spike_rank INTEGER           -- Ranking by volatility
)
```

---

## API Response Shapes

### News Ingestion (RSS/API)

**Input from RSS Feed:**
```json
{
    "guid": "https://example.com/article-123",
    "title": "Bitcoin Surges Past $50K",
    "link": "https://example.com/article-123",
    "pubDate": "2024-01-15T14:30:00Z",
    "description": "Bitcoin reached a new high...",
    "source": "CoinDesk"
}
```

**Normalized to:**
```python
{
    "source_id": "https://example.com/article-123",
    "title": "Bitcoin Surges Past $50K",
    "published_at": datetime(2024, 1, 15, 14, 30, 0),
    "raw_data": {...},  # Original JSON
    "ingested_at": datetime.now()
}
```

---

### Sentiment Analysis Output

**From `brain/llm_sentiment.py`:**
```python
{
    "label": "positive",      # or "negative", "neutral"
    "score": 0.85,            # -1 to +1
    "confidence": 0.92,       # 0 to 1
    "reasoning": "The article mentions strong institutional adoption..."
}
```

---

### Trading Signal

**From Brain → Trading Engine:**
```python
{
    "analysis": {
        "label": "positive",
        "score": 0.85,
        "confidence": 0.92
    },
    "source_item": {
        "title": "Bitcoin Surges Past $50K",
        "published_at": "2024-01-15T14:30:00Z",
        "impact_score": 9
    },
    "symbol": "BTC/USD"
}
```

---

### Exchange API Responses

**Binance - Get Price:**
```json
{
    "symbol": "BTCUSDT",
    "price": "50123.45"
}
```

**Hyperliquid - Place Order:**
```json
{
    "status": "filled",
    "orderId": "0x123abc...",
    "price": 50125.30,
    "quantity": 0.5,
    "side": "buy"
}
```

**Normalized to `OrderResult`:**
```python
OrderResult(
    status="filled",
    order_id="0x123abc...",
    price=50125.30,
    quantity=0.5,
    raw_response={...}
)
```

---

### Price Data (1s Candles)

**Stored in `curated_events.price_data` as JSON:**
```json
[
    {
        "timestamp": "2024-01-15T14:30:00Z",
        "open": 50100.0,
        "high": 50150.0,
        "low": 50090.0,
        "close": 50125.0,
        "volume": 123.45
    },
    ...
]
```

**Total records:** 7200 candles (120 minutes × 60 seconds)

---

## Data Validation Rules

### News Items
- `published_at` must be in the past
- `title` must not be empty
- `source_id` must be unique per source

### Trades
- `price` must be > 0
- `quantity` must be > 0
- `confidence` must be 0-1
- `side` must be 'buy' or 'sell'

### Price Data
- `timestamp` must be sequential
- OHLC must satisfy: `low <= open, close <= high`
- `volume` must be >= 0

---

## Schema Migration History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-01-10 | Initial schema |
| 1.1 | 2024-01-15 | Added `ingested_at` to `news` |
| 1.2 | 2024-01-20 | Added `curated_events` table |
| 1.3 | 2024-01-25 | Added `sol_price_data` to `curated_events` |

**Note:** Migrations are currently manual. See [ROADMAP.md](ROADMAP.md) for planned migration system.

---

**Last Updated:** 2026-01-30
