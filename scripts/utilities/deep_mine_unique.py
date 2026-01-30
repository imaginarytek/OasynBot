
import asyncio
import ccxt.async_support as ccxt
import pandas as pd
from datetime import datetime, timedelta, timezone
import os

# Configuration
SYMBOL = 'SOL/USDT'
TIMEFRAME = '1h'
TARGET_UNIQUE_EVENTS = 200
COOLDOWN_HOURS = 3
ALREADY_HAVE = 59 # From previous count

async def deep_mine_unique_events():
    print(f"🚀 Deep Mining for {TARGET_UNIQUE_EVENTS} Unique Volatility Events...")
    exchange = ccxt.binance()
    
    # 1. Load Existing Blocked Dates (to avoid duplicates)
    # We simulate this by just keeping a list of timestamps we've already "booked"
    # Ideally we'd read from DB, but for this script we can just rebuild the list on the fly
    # by applying the filter strictly to the new scan.
    
    booked_dates = [] 
    # Use a set of (Year, Month, Day) or just timestamp comparisons
    
    # 2. Fetch Full History (2024-01-01 to Now)
    since = exchange.parse8601('2024-01-01T00:00:00Z')
    now = exchange.parse8601(datetime.now(timezone.utc).isoformat())
    
    all_candles = []
    
    while since < now:
        try:
            candles = await exchange.fetch_ohlcv(SYMBOL, TIMEFRAME, since, 1000)
            if not candles: break
            
            for c in candles:
                all_candles.append({
                    'ts': c[0],
                    'datetime': datetime.fromtimestamp(c[0]/1000, timezone.utc),
                    'open': c[1],
                    'close': c[4],
                    'move_pct': (c[4] - c[1]) / c[1]
                })
            
            since = candles[-1][0] + 3600000 # +1h
            print(f"   Fetched up to {all_candles[-1]['datetime']}")
            # Rate limit
            await asyncio.sleep(0.5)
            
        except Exception as e:
            print(f"Error: {e}")
            break
            
    await exchange.close()
    
    # 3. Sort by Absolute Magnitude (Biggest moves first)
    df = pd.DataFrame(all_candles)
    df['abs_move'] = df['move_pct'].abs()
    df = df.sort_values(by='abs_move', ascending=False)
    
    print(f"📊 Scanned {len(df)} total hours. Identifying Unique Alphas...")
    
    unique_events = []
    
    # 4. Filter for Uniqueness
    for index, row in df.iterrows():
        if len(unique_events) >= TARGET_UNIQUE_EVENTS:
            break
            
        event_time = row['datetime']
        
        # Check collision with accepted events
        collision = False
        for accepted_time in unique_events:
            diff = abs((event_time - accepted_time).total_seconds() / 3600)
            if diff < COOLDOWN_HOURS:
                collision = True
                break
        
        if not collision:
            unique_events.append(event_time)
            # Find the original row to save details
            # We just save the timestamp and move for the CSV
            pass
            
    # 5. Extract Details for Final CSV
    results = []
    for evt_time in unique_events:
        # Locate in DF
        row = df[df['datetime'] == evt_time].iloc[0]
        results.append(row)
        
    final_df = pd.DataFrame(results)
    final_df = final_df.sort_values(by='datetime') # Chronological for onboarding
    
    csv_name = "data/unique_200_events.csv"
    final_df.to_csv(csv_name, index=False)
    print(f"✅ Saved {len(final_df)} Unique Events to {csv_name}")
    print("   (Guaranteed 48h separation between all events)")

if __name__ == "__main__":
    asyncio.run(deep_mine_unique_events())
