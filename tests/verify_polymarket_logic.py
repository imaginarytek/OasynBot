
import asyncio
import logging
from datetime import datetime
from src.trading.executor import PaperTradingExecutor
from src.ingestion.base import NewsItem
from src.utils.db import Database

# Setup logging manually since we aren't running main app
logging.basicConfig(level=logging.INFO)

async def main():
    print("--- Verifying Polymarket Logic (No ML) ---")
    
    # 1. Setup minimal components
    db = Database()
    config = {
        "trading": {
            "risk": {"max_position_size_pct": 0.05},
            "polymarket_api_key": "sim_key"
        }
    }
    
    executor = PaperTradingExecutor(config, db)
    
    # 2. Create Mock Signal (High Impact Trump News)
    item = NewsItem(
        source_id="test-1",
        title="Trump announces huge rally, polls show lead in 2024 Election",
        url="http://test.com",
        published_at=datetime.now(),
        content="...",
        author="tester"
    )
    
    analysis = {
        "score": 0.95,
        "confidence": 0.99,
        "label": "positive",
        "impact": 10 # MAXIMUM IMPACT -> Should trigger 2x sizing
    }
    
    signal = {
        "source_item": item,
        "analysis": analysis,
        "symbol": "TRUMP-2024" # Should be found by handler
    }
    
    # 3. Execute
    print("\n[Test] Executing Signal...")
    trade = await executor.execute_signal(signal)
    
    # 4. Verify
    if trade:
        print(f"\n[Success] Trade Executed: {trade.side.upper()} {trade.symbol}")
        print(f"Quantity: {trade.quantity:.4f} | Price: {trade.price}")
        
        # Check if size was doubled (Base is 5% * 100k = 5k. 2x = 10k)
        # Price for Yes is 0.60
        expected_size_usd = 10000.0
        actual_size_usd = trade.quantity * trade.price
        
        print(f"Trade Value: ${actual_size_usd:,.2f} (Expected ~$10,000 for High Impact)")
        
        if 9900 < actual_size_usd < 10100:
            print("✅ Position Sizing Correct (2x Multiplier Applied)")
        else:
            print(f"❌ Position Sizing Incorrect. Got ${actual_size_usd}")
            
    else:
        print("\n[Fail] No trade returned.")

if __name__ == "__main__":
    asyncio.run(main())
