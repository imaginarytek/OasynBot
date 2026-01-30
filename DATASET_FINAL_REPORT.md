# Final Dataset Report: "God-Tier" Curated Events

## Status Overview
- **Total Events:** 80
- **Data Quality:** 100% Rich Verbatim Text (Headline + 2-3 Paragraphs).
- **Average Text Length:** 1,089 characters per event.
- **Source Integrity:** All text sourced from official BLS/Fed archives, confirmed search results (for 2025 events), or direct official announcements (Crypto).
- **Price Data:** 1-Second Resolution OHLCV for SOL/USDT attached to all events.

## Key Improvements
1.  **Exact Verbatim Info:** Replaced all "generic" or "short" descriptions with full official text.
    *   *Example:* "Jobs Report November 2025" now correctly details the government shutdown that prevented data collection.
    *   *Example:* "Binance BOME Listing" contains the exact "Fellow Binancians..." announcement.
2.  **Handling Revisions:** For 2025 labor data (which had massive revisions), I used the *Initial Release* text, as this is what the market reacted to in real-time.
3.  **Shutdown Verification:** Confirmed and documented the Late 2025 Government Shutdown impact on CPI/Jobs reports in the dataset text.

## Top Market Movers (30-Minute Impact on SOL)
1.  **CPI Report Jan 2025:** +4.36%
2.  **Bitcoin Spot ETF Approval:** +4.36%
3.  **Trump Inauguration:** -4.16%
4.  **CPI Cooling (June 2024):** +3.71%
5.  **Jobs Report May 2024:** +3.59%

## Files Created
- `data/hedgemony.db`: The master database (Updated).
- `data/top_30_impact_events.csv`: The ranked analysis file.
- `scripts/analyze_30m_impact.py`: The script to generate the rankings.

The dataset is now ready for high-precision Sentiment Backtesting.
