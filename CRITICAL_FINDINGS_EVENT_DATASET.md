# CRITICAL FINDINGS: Event Dataset Analysis

## Executive Summary
**MAJOR ISSUE IDENTIFIED**: Our curated event dataset is missing 98.3% of significant market-moving events.

## Analysis Results

### Volatility Spike Detection (2024-2026)
- **Total Hourly Spikes Detected**: 357 (Z-score > 3.0σ)
- **Matched to Curated Events**: 6 (1.7%)
- **Missing Events**: 351 (98.3%)

### Top Matched Events (with timing issues)
| Event | Z-Score | Time Lag |
|-------|---------|----------|
| Jobs Report July 2024 | 6.33σ | 30 minutes |
| Trump Election Called | 6.29σ | 34 minutes |
| Nikkei 225 Crashes 12% | 5.77σ | 0 seconds ✓ |
| Trump Inauguration | 5.16σ | 60 minutes |
| CPI Report August 2025 | 3.27σ | 30 minutes |
| Bitcoin Spot ETF Approved | 3.21σ | 30 minutes |

### Top 15 Missing Events (Biggest Movers)
| Date | Z-Score | Move | Status |
|------|---------|------|--------|
| 2025-04-10 03:00 | 13.80σ | +10.24% | **MISSING** |
| 2025-03-03 01:00 | 13.70σ | +11.83% | **MISSING** |
| 2024-08-05 23:00 | 12.75σ | +9.55% | **MISSING** |
| 2024-03-06 05:00 | 12.30σ | -9.04% | **MISSING** |
| 2024-06-18 11:00 | 11.85σ | -6.31% | **MISSING** |
| 2025-08-23 00:00 | 11.31σ | +6.39% | **MISSING** |
| 2024-06-27 23:00 | 10.42σ | +6.02% | **MISSING** |
| 2024-11-17 14:00 | 9.65σ | +6.24% | **MISSING** |
| 2025-03-03 02:00 | 9.38σ | +9.30% | **MISSING** |
| 2025-01-20 07:00 | 9.35σ | -8.12% | **MISSING** |

## Root Cause Analysis

### Why Low 30-Second Moves in Our Dataset?
Our audit showed average 30s move of only 0.075% because:

1. **Wrong Events**: We curated "important sounding" events, not actual market movers
2. **Wrong Timing**: Even correct events have 30-60 minute timestamp errors
3. **Missing Events**: 98% of real volatility spikes have no corresponding event

### What Professional HFT Firms Do
Based on research:
- Start with **price action** (volatility spikes)
- Then find **news** that caused it
- Verify **exact timestamp** to the second
- Result: 80%+ of events show >0.5% move in first 5 seconds

## Recommendations

### Immediate Actions
1. **Investigate Top 50 Missing Spikes**
   - Search Twitter/news for each spike time ±30 minutes
   - Focus on tier-1 sources (@federalreserve, @BLS_gov, @SECGov, @binance)
   - Document exact announcement timestamp

2. **Re-timestamp Existing Events**
   - For the 6 matched events, find exact announcement time
   - Re-fetch 1-second data from corrected timestamp
   - Verify 30s move improves to >0.5%

3. **Build New Dataset**
   - Use spike-first methodology
   - Target: 100-150 events with Z-score > 5.0σ
   - Each event must show >0.5% move in 30 seconds

### Long-term Strategy
- Implement automated spike detection + news correlation
- Subscribe to professional news feeds (Bloomberg Terminal, RavenPack)
- Build real-time event detection system

## Files Generated
- `data/hourly_volatility_spikes` (database table with 357 spikes)
- `data/hourly_spikes_for_news_search.txt` (manual research template)

## Next Steps
1. Manual research on top 50 spikes
2. Correlate with Twitter/news archives
3. Build verified high-quality event dataset
4. Re-run backtest with corrected data
