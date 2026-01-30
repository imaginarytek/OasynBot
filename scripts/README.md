# Scripts Directory

This directory has been organized to improve maintainability and reduce AI assistant overhead.

## Directory Structure

### 📊 `data_analysis/`
Scripts for analyzing, auditing, and scoring events and market data:
- Event quality analysis
- Correlation auditing
- Spike detection
- Volatility scanning
- Performance measurement

**Key scripts:**
- `analyze_event_quality.py` - Evaluate event dataset quality
- `audit_dataset.py` - Comprehensive dataset validation
- `detect_volatility_spikes.py` - Find high-volatility periods

### 📥 `data_fetching/`
Scripts for fetching and generating market data and news:
- 1-second price data fetching
- News event mining
- Historical data backfilling
- Web scraping for verbatim text

**Key scripts:**
- `fetch_real_1s_data_smart.py` - Smart 1s data fetcher
- `backfill_1s_data.py` - Backfill historical 1s data
- `scrape_verbatim_text.py` - Extract exact news text

### 💧 `data_hydration/`
Scripts for enriching events with additional data:
- Headline hydration
- Verbatim text enrichment
- Exact report matching

**Key scripts:**
- `hydrate_all_headlines.py` - Add headlines to all events
- `hydrate_final_verbatim.py` - Add verbatim text from sources

### 🧪 `backtest/`
Scripts for backtesting trading strategies:
- Backtest execution
- Training data export
- Test data preparation

**Key scripts:**
- `run_backtest.py` - Execute backtests
- `prepare_backtest_data.py` - Prepare datasets for testing

### 🛠️ `utilities/`
General-purpose utility scripts:
- Database schema upgrades
- Data cleanup and deduplication
- Manual data entry
- Event curation
- Progress monitoring

**Key scripts:**
- `curated_events_list.py` - Manage curated event list
- `quick_progress.py` - Check pipeline progress
- `upgrade_db_schema.py` - Update database schema

### 📦 `archive/`
Deprecated, experimental, and test scripts:
- `experiments/` - Test and verification scripts
- `old_versions/` - Superseded script versions

## Common Workflows

### Building the Event Dataset
1. `data_fetching/mine_events_professional.py` - Find candidate events
2. `utilities/curated_events_list.py` - Curate event list
3. `data_hydration/hydrate_all_headlines.py` - Add headlines
4. `data_fetching/fetch_real_1s_data_smart.py` - Fetch price data
5. `data_analysis/analyze_event_quality.py` - Validate quality

### Running Backtests
1. `backtest/prepare_backtest_data.py` - Prepare data
2. `backtest/run_backtest.py` - Execute backtest
3. `data_analysis/analyze_30m_impact.py` - Analyze results

### Monitoring Progress
- `utilities/quick_progress.py` - Quick status check
- `data_analysis/audit_dataset.py` - Full dataset audit

## Notes

- Scripts in `archive/` are kept for reference but not actively maintained
- Most scripts expect to be run from the project root: `python3 scripts/category/script.py`
- Check individual script docstrings for detailed usage
