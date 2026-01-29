# Changelog

All notable changes to the Hedgemony Bot project will be documented in this file.

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
