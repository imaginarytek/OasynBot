
import ccxt.async_support as ccxt
import asyncio
import pandas as pd
from datetime import datetime, timedelta

async def scan_sol_moves():
    print("🚀 Scanning SOL/USDT for Top 100 Moves (Last 12 Months)...")
    exchange = ccxt.binance()
    
    # 2024 Vintage
    since = exchange.parse8601('2024-01-01T00:00:00Z')
    today = exchange.parse8601('2025-01-01T00:00:00Z')
    
    all_candles = []
    
    while since < today:
        try:
            ohlcv = await exchange.fetch_ohlcv('SOL/USDT', '1h', since, 1000)
            if not ohlcv: break
            all_candles.extend(ohlcv)
            since = ohlcv[-1][0] + 1
            print(f"Fetched up to {datetime.fromtimestamp(since/1000).date()}", end='\r')
        except Exception as e:
            print(f"Error: {e}")
            break
            
    await exchange.close()
    
    df = pd.DataFrame(all_candles, columns=['ts', 'open', 'high', 'low', 'close', 'vol'])
    df['datetime'] = pd.to_datetime(df['ts'], unit='ms')
    
    # Calculate 1H Move Abs
    df['move_pct'] = (df['close'] - df['open']) / df['open']
    df['abs_move'] = df['move_pct'].abs()
    
    # Top 100
    top_100 = df.sort_values('abs_move', ascending=False).head(100)
    
    print("\n\n🏆 TOP 20 SOL MOVES (1H) - PRELIMINARY SCAN")
    print(f"{'RANK':<5} | {'DATE':<20} | {'MOVE %':<8} | {'PRICE':<8}")
    print("-" * 50)
    
    rank = 1
    for _, row in top_100.head(20).iterrows():
        print(f"{rank:<5} | {row['datetime']} | {row['move_pct']:>7.2%} | ${row['close']:.2f}")
        rank += 1
        
    # Save CSV
    top_100.to_csv("data/top_sol_moves_2024.csv")

if __name__ == "__main__":
    asyncio.run(scan_sol_moves())
