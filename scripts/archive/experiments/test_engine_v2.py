#!/usr/bin/env python3
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import logging
from multiprocessing import Queue
from src.core.engine import HedgemonyEngine

# Setup basic logging to see process output
logging.basicConfig(level=logging.INFO)

async def test_main():
    print("🚀 Testing Engine V2 (Multiprocessing)...")
    
    engine = HedgemonyEngine()
    
    # Run for 15 seconds then kill
    try:
        await asyncio.wait_for(engine.start(), timeout=15)
    except asyncio.TimeoutError:
        print("✅ Test Complete (Timeout Reached)")
    except Exception as e:
        print(f"❌ Test Failed: {e}")

if __name__ == "__main__":
    # Needed for MacOS spawn method safety
    import multiprocessing
    multiprocessing.set_start_method("spawn", force=True)
    try:
        asyncio.run(test_main())
    except KeyboardInterrupt:
        pass
