# Changelog

All notable changes to the Hedgemony Bot project will be documented in this file.

---

## [2026-01-31] - Professional Architecture & Documentation Overhaul

### Added
- **Root README.md:** Comprehensive project landing page with Three Brains Council explanation, architecture overview, quick start guide, and feature highlights
- **docs/README.md:** Navigation index for all documentation with organized sections (Getting Started, Core Systems, Development, Archives)
- **docs/archive/README.md:** Index of 20 archived historical progress documents with context about what each covers
- **Immediate Priorities Section in ROADMAP.md:** Paper trading and live trading preparation roadmap

### Changed
- **Documentation Structure:** Archived 20 historical status/progress docs from root to `docs/archive/` for better organization
- **docs/architecture.md:** Complete rewrite reflecting current professional setup
  - Added Three Brains Council section (Groq + FinBERT + DeBERTa voting system)
  - Added Event Discovery Layer with spike-first methodology
  - Added Database Separation for bias prevention
  - Updated all data flow diagrams to show event-driven architecture
  - Removed outdated references (news table → master_events)
- **Dashboard (src/dashboard/app.py):** Migrated from deprecated `BacktestEngine` to modern event-driven approach
  - Now uses `EventDataAccess`, `VerbatimSentimentStrategy`, and `HardcoreEngine`
  - Backtesting tab supports event-driven simulation with confidence thresholds
  - Trade display supports both dict and object formats for backward compatibility
- **ROADMAP.md:** Updated with current status showing completed Phase 1, immediate priorities (paper trading), and January 2026 milestones
- **scripts/backtest/ Organization:** Moved deprecated scripts (run_backtest.py, prepare_backtest_data.py, export_training_data.py) to `archive/` subdirectory with explanatory README

### Removed
- **src/backtest/engine.py:** Deleted deprecated simple backtest engine (superseded by `hardcore_engine.py` with Monte Carlo simulation)
- **BacktestEngine exports:** Removed from `src/backtest/__init__.py` module exports

### Fixed
- **Import Error in strategy.py:** Added missing `import pandas as pd` (NameError when using EventDataAccess)
- **Module Exports:** Updated `src/backtest/__init__.py` to expose modern components (EventDataAccess, VerbatimSentimentStrategy, HardcoreEngine)

### Documentation
- **docs/BACKTEST_AUDIT.md:** Professional audit of backtest components identifying modern vs legacy architecture
- **docs/DATABASE_SEPARATION.md:** Explains physical DB separation for bias prevention (hedgemony.db vs hedgemony_validation.db)
- **docs/backtesting_methodology.md:** Documents spike-first approach and event-driven testing
- **src/backtest/README.md:** Complete API reference for backtest module
- **.agent/skills/event_scraping/SKILL.md:** Spike-first event discovery methodology

---

## [V2.0.0] - In-Progress (Parallel & Resilient)

### Added
- **Vector Memory (`src/brain/memory.py`):** Added `MemoryManager` using ChromaDB to store and retrieve historical news events (Semantic Search).
- **Parallel Brain (`src/brain/sentiment.py`):** Upgraded `SentimentEngine` to run `AsyncGroq` and `FinBERT` in parallel (`asyncio.gather`) for faster, enlisted decision making.
- **Latency Tracker (`src/dashboard/app.py`):** Added `ingested_at` timestamp tracking and dashboard metric to measure news feed latency.
- **Async Groq Client (`src/brain/llm_sentiment.py`):** Switched from synchronous `Groq` to `AsyncGroq` to prevent event loop blocking.

### Changed
- **Architecture Split (`src/core/engine.py`, `src/ingestion/worker.py`):** Decoupled ingestion into a separate multiprocessing Worker. The main engine now consumes from a thread-safe Queue.
- **Ingestion Logic:** Removed blocking `poll_sources` loop in favor of properly managed async streams.
- **Config:** Updated `config.yaml` to include Memory settings (`chromadb`) and updated Groq model to `llama-3.3-70b-versatile`.

### Fixed
- **Critical Bug (Ingestion):** Fixed `IngestionWorker` failing to start streams by switching from a naive polling loop to `stream_manager.start()` with callbacks.
- **Model Deprecation:** Updated default Groq model from decommissioned `llama3-70b` to supported version.

## [V1.0.0] - MVP
- Initial release with Paper Trading, Basic FinBERT, and Streamlit Dashboard.
