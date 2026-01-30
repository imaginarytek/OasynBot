
import ccxt
import pandas as pd
from datetime import datetime
import time

def test_1s_sources():
    print("🚀 Auditing Exchanges for Historical 1-Second Data (Target: 2024-01-10)...")
    
    target_ts = 1704891600000 # 2024-01-10 13:00:00 UTC
    target_dt = datetime.utcfromtimestamp(target_ts/1000)
    
    candidates = [
        'binance', 'bybit', 'kraken', 'okx', 'kucoin', 'gateio', 'mexc'
    ]
    
    winner = None
    
    for ex_name in candidates:
        try:
            exchange = getattr(ccxt, ex_name)()
            print(f"👉 Testing {ex_name.upper()}...")
            
            # Check 1s support
            if '1s' not in exchange.timeframes:
                print(f"   ❌ 1s timeframe not supported.")
                continue
                
            # Try Fetch
            candles = exchange.fetch_ohlcv('SOL/USDT', '1s', since=target_ts, limit=5)
            
            if len(candles) > 0:
                first_ts = candles[0][0] / 1000
                dt = datetime.utcfromtimestamp(first_ts)
                print(f"   ✅ SUCCESS! First Candle: {dt}")
                print(f"   📊 Sample: Close = {candles[0][4]}")
                winner = ex_name
                break # We found one!
            else:
                print(f"   ❌ No data returned (likely expired).")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)[:50]}...")
            
    if winner:
        print(f"\n🎉 WINNER: {winner.upper()} has the data we need.")
    else:
        print("\n💀 FAIL: No public API provides 1s data for 2024-01-10.")

if __name__ == "__main__":
    test_1s_sources()
