#!/usr/bin/env python3
"""
TEST: Can we fetch historic 1s data via API?
Target: Feb 2022 (Russia Invasion)
Symbol: BTC/USDT
Timeframe: 1s
"""
import asyncio
import ccxt.async_support as ccxt
from datetime import datetime

async def test_fetch():
    exchange = ccxt.binance() # Spot API supports 1s?
    
    # Russia Invasion: 2022-02-24 03:00:00 UTC
    # Ts: 1645671600000
    timestamp = 1645671600000 
    
    print(f"Testing API fetch for 2022-02-24 (Timestamp: {timestamp})...")
    await exchange.load_markets()
    
    # Debug Symbols
    btc_symbols = [s for s in exchange.symbols if 'BTC/USDT' in s]
    print(f"Available BTC pairs: {btc_symbols}")
    
    symbol = btc_symbols[0] if btc_symbols else "BTC/USDT"
    print(f"Using symbol: {symbol}")
    
    try:
        # Fetch 1s candles
        ohlcv = await exchange.fetch_ohlcv(symbol, '1s', since=timestamp, limit=10)
        
        if ohlcv:
            print(f"✅ SUCCESS ({symbol})! API returned 1s data:")
            for c in ohlcv:
                dt = datetime.fromtimestamp(c[0]/1000)
                print(f"  {dt} | {c[1]} | {c[4]}")
        else:
            print(f"❌ FAILURE ({symbol}): API returned empty list (Data too old?)")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        
    await exchange.close()
            


if __name__ == "__main__":
    asyncio.run(test_fetch())
