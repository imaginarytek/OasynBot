#!/usr/bin/env python3
"""
DRY RUN VERIFICATION
Tests the V2.9.2 Execution Pipeline with a fake signal.
Uses Replay of recent price data to simulate "Confirmation".
"""

import asyncio
import logging
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from src.trading.live_executor import LiveTradingExecutor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def run_test():
    print("🚀 STARTED: V2.9.2 Dry Run Verification")
    
    # Init Executor (will default to Hyperliquid defined in config)
    executor = LiveTradingExecutor()
    
    # Mock the Exchange's get_price to simulate a pump
    # We overwrite the method on the instance
    original_get_price = executor.exchange.get_price
    
    # Stateful mock
    prices = [20.00, 20.00, 20.01, 20.02, 20.05, 20.10, 20.20, 20.25, 20.30] # +1.5% move
    # 20.00 -> 20.05 is +0.25% (Trigger Confirmation)
    
    price_iter = iter(prices)
    
    async def mock_get_price(symbol):
        try:
            p = next(price_iter)
            print(f"   [Mock Exchange] {symbol} Price: {p}")
            return p
        except StopIteration:
            return 20.30 # Steady state
            
    # Mock Balance to allow entry
    async def mock_get_balance(currency):
        return 1000.0 # $1000 equity
        
    async def mock_place_order(symbol, side, qty, type, price=None):
        from src.trading.exchange import OrderResult
        from datetime import datetime
        print(f"   ✅ [Mock Exchange] ORDER PLACED: {side} {qty} {symbol}")
        return OrderResult("mock-id", symbol, side, qty, 20.05, "filled", datetime.now())
        
    # Inject Mocks
    executor.exchange.get_price = mock_get_price
    executor.exchange.get_balance = mock_get_balance
    executor.exchange.place_order = mock_place_order
    # No close_position mock needed for now unless we wait for stop
    
    # Override Window to 5s for fast test (instead of 300s)
    executor.CONFIRM_WINDOW_SEC = 5
    
    # Create Signal
    signal = {
        'source_item': {'title': 'TEST: Fake Bullish News', 'url': 'http://test.com'},
        'analysis': {'score': 0.9, 'confidence': 0.95, 'label': 'positive'},
        'symbol': 'SOL/USD'
    }
    
    print("\n--- STEP 1: Sending Signal ---\n")
    # Trigger (Async)
    await executor.execute_signal(signal)
    
    # Wait for async task to process
    print("\n--- STEP 2: Waiting for Confirmation Loop ---\n")
    await asyncio.sleep(6) # Wait slightly longer than window
    
    print("\n--- TEST COMPLETE ---\n")

if __name__ == "__main__":
    asyncio.run(run_test())
