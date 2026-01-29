# HedgemonyBot: Project Context & Strategy

## 1. Executive Summary
**HedgemonyBot** is a high-frequency, event-driven trading system designed to capture alpha from major geopolitical and macroeconomic shocks. It uses a "Hybrid Brain" approach (LLM + specialized NLP) to interpret breaking news in real-time and execute directional trades on crypto futures (BTC/ETH).

**Philosophy**: "Simple. Fast. Directional. High Conviction."
We do not scalp noise. We wait for high-impact events (War, Fed, Regulations) and strike aggressively.

## 2. Core Strategy (Locked)
*   **Trigger**: Breaking news from Tier-1 sources (Twitter:@DeItaone, Reuters, AP).
*   **Analysis**:
    *   **Groq (Llama-3)**: Semantic reasoning & structured data extraction.
    *   **FinBERT**: Specialized financial sentiment classification (Backup/Validation).
    *   **Vector Memory (ChromaDB)**: Retrieval of historical analogies (RAG) to ground current decisions.
*   **Execution**:
    *   **Assets**: BTC-USDT, ETH-USDT Perpetual Futures.
    *   **Logic**: Directional Market Orders upon confirmation.
    *   **Risk**: Dynamic Position Sizing (5-8%), ATR-based Trailing Stops.

## 3. Technology Stack

### Ingestion Layer ("The Ears")
*   **Twitter/X**: `tweepy.asynchronous` for real-time stream (Targeting specific alpha accounts).
*   **RSS**: `feedparser` with `asyncio` for high-frequency polling (15s intervals).
*   **Direct Ingester**: Custom `aiohttp` pollers for Tier-1 sites (request-based).
*   **Architecture**: Multiprocessing Worker (`src/ingestion/worker.py`) pushing to a `multiprocessing.Queue`.

### Brain Layer ("The Mind")
*   **LLM**: Groq API (Llama-3-70b) for sub-second inference.
*   **Sentiment**: HuggingFace `ProsusAI/finbert` (Local) for fast classification.
*   **Memory**: `chromadb` (Local Vector Store) with `sentence-transformers` (`all-MiniLM-L6-v2`) for semantic history.
*   **Ensemble**: Weighted average of Groq and FinBERT scores.

### Execution Layer ("The Hands")
*   **Exchange Connector**: `ccxt` (Async) connected to Binance Futures.
*   **Safety**:
    *   `dry_run`: Configurable flag to simulate orders in production pipeline.
    *   **Sanity Bounds**: Hard-coded limits on order size and leverage.
*   **Mode**: Supports `paper` (simulated) and `live` (real connection).

### Data & Infrastructure
*   **Database**: SQLite (`data/hedgemony.db`) for relational data (Trades, News, OHLCV).
*   **Vector DB**: ChromaDB (`data/chromadb`) for embeddings.
*   **Dashboard**: Streamlit (`src/dashboard/app.py`) for real-time monitoring.
*   **Notifications**: Telegram Bot API for alerts.

## 4. Current Implementation Status (as of Jan 2026)
*   [x] **Ingestion**: Hybrid Polling/Streaming stable.
*   [x] **Brain**: Ensemble Logic + Vector Memory Integration active.
*   [x] **Execution**: Live Executor wired to Binance (Testnet) with Safety Lock (`dry_run=True`).
*   [x] **Interface**: Streamlit Dashboard operational.
*   [ ] **Optimization**: Latency probing and kernel tuning pending.
*   [ ] **Validation**: Walk-forward backtesting on "Gold Standard" dataset (2022-2025).

## 5. Directory Structure Key
*   `src/core`: Main Engine loop & orchestration.
*   `src/ingestion`: Data fetching (Worker process).
*   `src/brain`: AI logic (Sentiment, Memory, LLM).
*   `src/trading`: Executor logic (Live & Paper).
*   `config/`: YAML configuration and source lists.
*   `scripts/`: Utilities for backfilling, verifying, and testing.

## 6. Critical Rules for Agents
1.  **Safety First**: Never disable `dry_run` without explicit user confirmation.
2.  **No Hallucinations**: Do not invent trades or PnL data.
3.  **Module Integrity**: Respect the architecture split (Ingestion Worker vs Main Engine).
