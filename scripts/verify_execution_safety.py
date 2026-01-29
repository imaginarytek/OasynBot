
import logging
import asyncio
import sys
import os
from datetime import datetime

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.core.engine import HedgemonyEngine
from src.trading.live_executor import LiveTradingExecutor
from src.ingestion.base import NewsItem

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("hedgemony.verify_safety")

async def main():
    logger.info("Starting Execution Safety Verification...")
    
    # 1. Force Config to LIVE mode but DRY RUN
    overrides = {
        "system": {
            "mode": "live", 
            "dry_run": True,
            "project_name": "SafetyTest"
        },
        "trading": {
            "exchange": "binance", # Test binance path
            "binance": {"testnet": True} # Use testnet anyway just in case
        }
    }
    
    # Initialize Engine with overrides (we need to patch config loading or manual init)
    # Since Engine loads config from file, we'll manually instantiate components to test logic
    # or better, let's just test LiveTradingExecutor directly with a mock config.
    
    config = {
        "system": {"mode": "live", "dry_run": True},
        "trading": {
            "exchange": "binance",
            "binance": {"testnet": True, "api_key": "test", "api_secret": "test"},
            "risk": {"max_position_size_pct": 0.1}
        },
        "brain": {"confidence_threshold": 0.5},
        "telegram": {"enabled": False} # Disable alerts for test
    }
    
    executor = LiveTradingExecutor(config, db=None)
    
    logger.info(f"Executor initialized. Exchange: {executor.exchange_name}")
    
    # 2. Simulate a Signal
    signal = {
        'source_item': NewsItem("test", "Test News", "http://test", datetime.now(), "Test Content", "tester"),
        'analysis': {'score': 0.99, 'confidence': 0.95, 'label': 'positive', 'impact': 5},
        'symbol': 'BTC/USDT'
    }
    
    logger.info("Sending TEST BUY signal to LiveExecutor (Dry Run: True)...")
    
    # 3. Execute
    # We expect a "filled" status but checks logs for "DRY RUN" warning
    result = await executor.execute_signal(signal)
    
    if result:
        logger.info(f"Result Status: {result.status}")
        logger.info(f"Result Order ID: {result.order_id}")
        
        if "dry-run" in result.order_id:
            logger.info("✅ SUCCESS: Order ID contains 'dry-run'. Safety lock active.")
        else:
            logger.error("❌ FAILURE: Order ID does not indicate dry run! REAL ORDER MIGHT HAVE BEEN SENT.")
    else:
        logger.error("❌ FAILURE: Execution returned None.")

if __name__ == "__main__":
    asyncio.run(main())
