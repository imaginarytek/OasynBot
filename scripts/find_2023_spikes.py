#!/usr/bin/env python3
"""
SPIKE-FIRST METHODOLOGY - Find 2023 SOL/USDT Volatility Spikes
Step 1: Detect abnormal hourly volatility (Z-score > 3.0σ)
Step 2: Output timestamps for manual news correlation
"""
import sqlite3
import statistics
from datetime import datetime

DB_PATH = 'data/hedgemony.db'

def find_volatility_spikes():
    """Scan hourly data for abnormal volatility spikes."""

    print("=" * 80)
    print("SPIKE-FIRST METHODOLOGY - 2023 SOL/USDT Volatility Detection")
    print("=" * 80)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # Fetch 2023 hourly data
    c.execute("""
        SELECT timestamp, open, high, low, close, volume
        FROM price_history
        WHERE symbol = 'SOL/USDT'
        AND timestamp >= '2023-01-01'
        AND timestamp < '2024-01-01'
        ORDER BY timestamp ASC
    """)

    candles = c.fetchall()
    print(f"\n📊 Loaded {len(candles)} hourly candles from 2023")

    # Calculate hourly returns
    returns = []
    for i in range(1, len(candles)):
        prev_close = candles[i-1]['close']
        curr_close = candles[i]['close']
        ret = (curr_close - prev_close) / prev_close
        returns.append({
            'timestamp': candles[i]['timestamp'],
            'return_pct': ret * 100,
            'abs_return_pct': abs(ret) * 100,
            'high': candles[i]['high'],
            'low': candles[i]['low'],
            'open': candles[i]['open'],
            'close': candles[i]['close'],
            'volume': candles[i]['volume']
        })

    # Calculate statistics
    abs_returns = [r['abs_return_pct'] for r in returns]
    mean_vol = statistics.mean(abs_returns)
    std_vol = statistics.stdev(abs_returns)

    print(f"\n📈 Volatility Statistics:")
    print(f"   Mean hourly volatility: {mean_vol:.3f}%")
    print(f"   Std deviation: {std_vol:.3f}%")
    print(f"   3σ threshold: {mean_vol + 3*std_vol:.3f}%")

    # Calculate Z-scores and find spikes
    spikes = []
    for r in returns:
        z_score = (r['abs_return_pct'] - mean_vol) / std_vol
        r['z_score'] = z_score

        if z_score > 3.0:  # 3-sigma threshold
            spikes.append(r)

    # Sort by Z-score (biggest spikes first)
    spikes.sort(key=lambda x: x['z_score'], reverse=True)

    print(f"\n🔥 Found {len(spikes)} ABNORMAL VOLATILITY SPIKES (Z > 3.0σ)")
    print("\n" + "=" * 80)
    print("TOP 20 BIGGEST SPIKES (Candidates for News Correlation)")
    print("=" * 80)
    print(f"{'RANK':<5} | {'TIMESTAMP':<20} | {'Z-SCORE':<8} | {'MOVE%':<8} | {'DIRECTION':<10}")
    print("-" * 80)

    for i, spike in enumerate(spikes[:20], 1):
        direction = "📈 UP" if spike['return_pct'] > 0 else "📉 DOWN"
        dt = datetime.fromisoformat(spike['timestamp'])

        print(f"{i:<5} | {dt.strftime('%Y-%m-%d %H:%M'):<20} | "
              f"{spike['z_score']:>6.2f}σ | {spike['return_pct']:>+6.2f}% | {direction}")

    print("\n" + "=" * 80)
    print("NEXT STEPS (Spike-First Methodology):")
    print("=" * 80)
    print("For each spike above:")
    print("  1. Search for news at that EXACT timestamp (±5 minutes)")
    print("  2. Find the FIRST tier-1 source that broke the news")
    print("  3. Get verbatim title + description from that source")
    print("  4. Verify timestamp correlation (<60 seconds)")
    print("  5. Download 1-second data for that event window")
    print("  6. Add to master_events if verified")
    print("\n❌ REJECT if:")
    print("  - Can't find news source with timestamp")
    print("  - Source timestamp is >60s from spike")
    print("  - Not tier-1 source (Bloomberg, Reuters, Official, etc.)")
    print("=" * 80)

    # Save spike data to file for reference
    with open('data/2023_volatility_spikes.txt', 'w') as f:
        f.write("2023 SOL/USDT VOLATILITY SPIKES (Z > 3.0)\n")
        f.write("=" * 80 + "\n\n")
        for i, spike in enumerate(spikes, 1):
            dt = datetime.fromisoformat(spike['timestamp'])
            direction = "UP" if spike['return_pct'] > 0 else "DOWN"
            f.write(f"{i}. {dt.strftime('%Y-%m-%d %H:%M')} | "
                   f"Z={spike['z_score']:.2f}σ | "
                   f"{spike['return_pct']:+.2f}% {direction}\n")

    print(f"\n💾 Spike data saved to: data/2023_volatility_spikes.txt")

    conn.close()
    return spikes

if __name__ == "__main__":
    spikes = find_volatility_spikes()
